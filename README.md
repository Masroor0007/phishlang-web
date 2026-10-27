# PhishLang-Web

**Auditing and deploying fully in-browser phishing detection with MobileBERT**

CS 8027 Advanced Networking & Architecture (Fall 2026) research project · Masroor Ul Hasan Syed, Deepthi Kondreddy

> **Work in progress.** The results below are from 2026-10-27 and come from a single training seed.

## What this project does

[PhishLang](https://www.ndss-symposium.org/ndss-paper/phishlang-a-real-time-fully-client-side-phishing-detection-framework-using-mobilebert/) (Saha Roy & Nilizadeh, NDSS 2026) detects phishing websites by running MobileBERT, a small language model, over a parsed text view of each page's HTML.
- It reports 0.96 accuracy and F1.
- Its client-side app is a local Python server that a browser extension queries.

We do two things:

1. **Audit the evaluation.** We re-evaluate PhishLang without train/test leakage and with duplicates removed. Later we'll also test it on phishing pages from 2024–25 ([PhreshPhish](https://huggingface.co/datasets/phreshphish/phreshphish)).
2. **Deploy it fully in the browser.** We run MobileBERT inside a Chrome MV3 extension with ONNX Runtime Web and INT8 quantization: no local server, no cloud and no native install.

The research questions and experiment plan are in [`docs/research_plan.md`](docs/research_plan.md). Verified facts about the paper, its code and its data are in [`docs/phishlang_notes.md`](docs/phishlang_notes.md). The proposal is [`proposal/main.pdf`](proposal/main.pdf).

## Findings so far

From PhishLang's released code (commit [`6b72838`](https://github.com/UTA-SPRLab/phishlang/tree/6b7283854ef8a6edc73f945c1ce7e51b2e1dc4fd)) and its training data:

1. **Train/test leakage in the released training script.** K-fold indices computed on a shuffled frame are applied to the unshuffled dataset. Replaying that logic on synthetic ids ([`scripts/check_upstream_leakage.py`](scripts/check_upstream_leakage.py)) puts 51–76% of the test rows into each fold's training set.
2. **Most phishing pages are duplicates.** The released archive holds 29,048 phishing and 23,611 benign parsed pages. Removing empty pages and exact duplicates leaves 7,503 phishing pages (−74%) and 21,892 benign pages (−7%).
3. **Training sees a tiny prefix of each page.** Training truncates every page to its first 128 tokens.
   - The median page is 15,892 tokens long (benign) or 2,332 tokens (phishing).
   - 98% of benign and 83% of phishing pages are longer than even MobileBERT's 512-token maximum.
4. **Identical model inputs.** After exact duplicates are removed, the 29,395 pages yield only 20,814 distinct 128-token inputs.
   - On our split, 55% of test phishing pages share their input with some training page.
   - 58 inputs occur with both labels.
5. **Short pages are always "benign" at inference.** The released sliding-window inference only scores full 128-token windows. Pages shorter than that get a phishing probability of 0; that's 1.7% of phishing pages.
6. **Lower phishing recall on a clean split.** Here are the results of retraining with upstream's hyper-parameters on our deduplicated, leakage-free split:

| Model (our test split: 8,819 pages, 25.5% phishing) | Accuracy | Phishing precision | Phishing recall | Phishing F1 | Weighted F1 |
|---|---|---|---|---|---|
| Paper, Table 2 (averaging not stated) | 0.96 | 0.95 | 0.96 | 0.96 | — |
| Released model, as-is (not a held-out score\*) | 0.934 | 0.903 | 0.830 | 0.865 | 0.933 |
| Retrained on the clean split (seed 42) | 0.954 | 0.938 | 0.876 | 0.906 | 0.953 |

\* The released model was probably trained on many of these pages.

The raw numbers are in [`results/local_wsl/`](results/local_wsl/). Next we'll run two more seeds and compute an upper bound on what any 128-token model can reach.

## Repository layout

| Path | Contents |
|---|---|
| [`notebooks/phishlang_colab_train.ipynb`](notebooks/phishlang_colab_train.ipynb) | The pipeline in one notebook: download and verify, clean, E0 token lengths, leakage-free split, E1 released-model check, E2 retraining. Runs on Colab or locally. |
| [`notebooks/run_local_wsl.sh`](notebooks/run_local_wsl.sh) | Runs the notebook locally in a quarantined WSL sandbox (see below) |
| [`notebooks/test_notebook.py`](notebooks/test_notebook.py) | Runs the whole notebook on synthetic, harmless pages; use it to test changes |
| [`scripts/check_upstream_leakage.py`](scripts/check_upstream_leakage.py) | Reproduces the leakage finding with no data |
| [`results/local_wsl/`](results/local_wsl/) | Aggregate results of the 2026-10-27 run (CSV/JSON only) |
| [`docs/`](docs/) | Research plan and verified notes |
| [`proposal/`](proposal/), [`report/`](report/) | LaTeX sources and PDFs (proposal: ≤ 3 pages; report: IEEE two-column, ≤ 8 pages) |
| [`literature/`](literature/) | The PhishLang paper (arXiv v3, CC BY 4.0) |
| [`CLAUDE.md`](CLAUDE.md), [`KICKOFF_PROMPT.md`](KICKOFF_PROMPT.md) | Instructions for the Claude Code assistant used in this project, including the project's safety rules |

## Reproducing the results

⚠ **The training data contains real phishing pages** (HTML and JavaScript converted to text).
- When one copy was unpacked into a Windows folder, Microsoft Defender flagged and quarantined 2,408 files.
- Defender's deletions aren't random, so they silently bias the dataset.
- This repository never stores the data. Both options below keep it isolated and never unpack it to disk.

### Option A: Google Colab (free tier)

1. In [Colab](https://colab.research.google.com), choose **File → Upload notebook** and pick `notebooks/phishlang_colab_train.ipynb`.
2. Select a **T4 GPU** and choose **Runtime → Run all**.
3. The data stays on the Colab VM (`/content`). Only metrics and model weights are written to your Google Drive.
4. If Colab disconnects, choose **Run all** again: training resumes from the last finished epoch.

### Option B: locally, quarantined in WSL Ubuntu (NVIDIA GPU)

From a WSL terminal, in the repository folder:

```bash
bash notebooks/run_local_wsl.sh
```

The script:

1. Creates `~/phish-research` (mode 700) on the Linux disk, with a Python environment pinned to the notebook's library versions.
2. Downloads only the 10 needed upstream files at commit `6b72838`, checks each one against its git blob hash, and makes them read-only.
3. Runs the notebook with **no network** and with the **Windows drives hidden**. It uses `unshare` user, network and mount namespaces, with an empty tmpfs mounted over `/mnt`.
4. Copies only aggregate CSV/JSON files into `results/local_wsl/`. Per-page files, model weights and logs stay in `~/phish-research`.

On an RTX 5070, training takes about 11 minutes per seed, plus a few minutes of data preparation and a one-time environment install of about 3 GB.

### Testing changes without any phishing data

```bash
TEST_GPU=1 ~/phish-research/venv/bin/python notebooks/test_notebook.py notebooks/phishlang_colab_train.ipynb ~/phish-test-synth [crash]
```

This builds a fake archive with the upstream layout and runs every cell; `crash` simulates a Colab disconnect. See the script's docstring for the options.

## Building the PDFs

```bash
cd proposal && latexmk -pdf main.tex      # same for report/
```

If a build fails with "missing \item", delete the stale `main.bbl` and rebuild.

## Safety rules we follow

- Never unpack, render or open phishing pages, and never visit URLs taken from the data.
- Never install PhishLang's released `.deb` or `.crx` files.
- Load third-party model weights only from `.safetensors` files, never pickles. MobileBERT's base weights come from Hugging Face's safetensors conversion, pinned to a revision.
- Never commit data, per-page outputs or model weights.

## Credits and licenses

- **Our code** (`notebooks/`, `scripts/`): [MIT](LICENSE).
- **Our documents** (README, `docs/`, `proposal/`, `report/`, `results/`): [CC BY 4.0](LICENSE-docs).
- **Third-party material:** see [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
  - The PhishLang paper PDF is CC BY 4.0, by its authors.
  - PhishLang's code and data have no license, so they are **not** redistributed here. The notebook downloads them at a pinned commit for research use.
  - MobileBERT's weights are Apache-2.0.
  - The top of `CLAUDE.md` is copied from [andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills), which its README says is MIT-licensed.

If you use the findings, please also cite the original work:

```bibtex
@inproceedings{roy2026phishlang,
  author    = {Sayak {Saha Roy} and Shirin Nilizadeh},
  title     = {{PhishLang}: A Real-Time, Fully Client-Side Phishing Detection Framework Using {MobileBERT}},
  booktitle = {Network and Distributed System Security Symposium (NDSS)},
  year      = {2026},
  note      = {arXiv:2408.05667}
}
```
