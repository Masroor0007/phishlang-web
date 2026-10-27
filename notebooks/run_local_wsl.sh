#!/usr/bin/env bash
# Runs phishlang_colab_train.ipynb locally inside WSL Ubuntu, quarantined:
#   - phishing data lives only in ~/phish-research on the Linux disk, never on a Windows drive, and is never unpacked
#   - downloads happen first; the notebook then runs with no network and with the Windows drives (/mnt) hidden
#   - only aggregate numbers (CSV/JSON) are copied back into this repo's results/local_wsl/ folder
# usage, from a WSL terminal: bash notebooks/run_local_wsl.sh
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
Q="$HOME/phish-research"
case "$(realpath -m "$Q")" in /mnt/*) echo "refusing: $Q is on a Windows drive" >&2; exit 1 ;; esac
mkdir -p "$Q/run"
chmod 700 "$Q"

# 1. Python environment with the same pins as the notebook's Colab setup (online; no phishing data involved)
if [ ! -x "$Q/venv/bin/python" ]; then
    python3 -m venv "$Q/venv"
    "$Q/venv/bin/pip" install -q torch --index-url https://download.pytorch.org/whl/cu128
    "$Q/venv/bin/pip" install -q "transformers==4.57.6" "accelerate==1.15.0" scikit-learn pandas nbconvert ipython
fi
export PATH="$Q/venv/bin:$PATH"
cd "$Q/run"

# 2. The notebook, plus a fetch-only copy of it (its setup, settings and download cells, and the pinned base model)
cp "$REPO/notebooks/phishlang_colab_train.ipynb" train.ipynb
python - <<'PY'
import json
nb = json.load(open("train.ipynb"))
keep = ("# Setup", "# Settings", "# Download")
nb["cells"] = [c for c in nb["cells"] if c["cell_type"] == "code" and "".join(c["source"]).startswith(keep)]
nb["cells"].append(dict(cell_type="code", id="cache-base-model", metadata={}, execution_count=None, outputs=[], source=
    "from transformers import AutoTokenizer, MobileBertTokenizer, MobileBertForSequenceClassification\n"
    "AutoTokenizer.from_pretrained(**BASE)\n"
    "MobileBertTokenizer.from_pretrained(**BASE)\n"
    "MobileBertForSequenceClassification.from_pretrained(**BASE, use_safetensors=True, num_labels=2)\n"
    "print('base model cached')"))
json.dump(nb, open("fetch.ipynb", "w"))
PY
jupyter nbconvert --to python --log-level ERROR train.ipynb fetch.ipynb

# 3. Online: download and hash-check the upstream files, cache the base model; then make the downloads read-only
ipython fetch.py
chmod a-w "$Q"/data/training_data/* "$Q"/data/src/model/*

# 4. Offline: own network namespace (no network at all) and an empty /mnt (Windows drives invisible)
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 unshare --user --map-root-user --net --mount \
    sh -c 'mount -t tmpfs none /mnt && exec ipython train.py' 2>&1 | tee log.txt

# 5. Only aggregate numbers go back to the repo
R="$REPO/results/local_wsl"
mkdir -p "$R"
cp "$Q/out/results/e0_token_length_summary.csv" "$Q/out/results/summary.csv" "$R/"
cp "$Q/out/results/e1_released_model/test_metrics.json" "$R/e1_test_metrics.json"
for d in "$Q"/out/runs/e2_seed*; do
    cp "$d/test_metrics.json" "$R/$(basename "$d")_test_metrics.json"
    cp "$d/log_history.json" "$R/$(basename "$d")_log_history.json"
done
echo "done: aggregate results in $R; data, model weights and the full log stay in $Q"
