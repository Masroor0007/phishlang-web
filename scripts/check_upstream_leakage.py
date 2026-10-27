"""Replay the train/test index logic of PhishLang's released training script.

Upstream: github.com/UTA-SPRLab/phishlang, src/training.py @ 6b72838.
No phishing data is needed: rows are synthetic ids ordered phishing-first,
exactly as training.py builds its DataFrame.

    python scripts/check_upstream_leakage.py            # paper sizes (22,419 / 26,000)
    python scripts/check_upstream_leakage.py 30000 30000
"""
import sys

import pandas as pd
from sklearn.model_selection import KFold, train_test_split

n_phish, n_benign = (int(a) for a in sys.argv[1:3]) if len(sys.argv) == 3 else (22419, 26000)

df = pd.DataFrame({"row_id": range(n_phish + n_benign),
                   "label": [1] * n_phish + [0] * n_benign})
train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)
test_ids = set(test_df["row_id"])

kf = KFold(n_splits=5, shuffle=True, random_state=42)
for fold, (train_index, _) in enumerate(kf.split(train_df), 1):
    # training.py: full_dataset (in df order) .select(train_index), where train_index indexes train_df
    used = df.iloc[train_index]
    overlap = len(test_ids & set(used["row_id"])) / len(test_ids)
    print(f"fold {fold}: {overlap:.1%} of test rows are in the training set; "
          f"phishing share in training {used['label'].mean():.1%} (true {df['label'].mean():.1%})")
