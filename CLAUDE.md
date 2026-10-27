# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

---

# Project-specific instructions

Everything above this line is copied verbatim from
[multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills/blob/2c606141936f1eeef17fa3043a72095b4765b9c2/CLAUDE.md)
(commit `2c60614`); its README says it is MIT-licensed (see `THIRD_PARTY_NOTICES.md`). Do not edit it. Everything below is specific to this project.

## What this project is

- **Course:** CS 8027 Advanced Networking & Architecture, Fall 2026 (PhD, semester 1).
- **Team:** Masroor Ul Hasan Syed, Deepthi Kondreddy.
- **Topic (as written for the D2L topic submission; approval status not recorded):** a feasible, fully client-side, real-time phishing detector built on MobileBERT, with no cloud analysis. It focuses on accuracy, inference speed, resource efficiency and privacy (`course/Research Topic Information.docx`).
- **Base paper:** PhishLang, Saha Roy & Nilizadeh, NDSS 2026 (`literature/2408.05667v3.pdf`, arXiv v3).
  - Code: https://github.com/UTA-SPRLab/phishlang at commit `6b7283854ef8a6edc73f945c1ce7e51b2e1dc4fd`.
  - The paper's link `UTASPRLab/phishlang` is dead (404); use the hyphenated org name.
  - The repo has **no license file**: use it for reference and research only, and do not redistribute its code or data.
- **Public repo:** https://github.com/Masroor0007/phishlang-web (created 2026-10-27).
  - `course/` is git-ignored and never published.
  - Code is MIT (`LICENSE`); docs are CC BY 4.0 (`LICENSE-docs`).
  - Everything pushed there is public. Run the pre-push checks every time: no data, no per-page files, no secrets.
- **Chosen direction (2026-10-26):** "audit + in-browser". See `docs/research_plan.md`.
  1. Audit PhishLang's evaluation: a leakage-free split, a temporal split (2019–20 training → 2024–25 testing on PhreshPhish), and the cost of the 128-token training window.
  2. Run MobileBERT entirely inside a Chrome MV3 extension (ONNX Runtime Web, INT8). No local server and no cloud. Compare it with PhishLang's local-server design on accuracy, latency, memory and install size.

## Deliverables (source: `course/Research_Project_requirements.pdf`)

| Deliverable | Format / limit | Folder |
|---|---|---|
| Topic selection | D2L | submitted? (confirm with user) |
| Proposal | LaTeX → PDF, **≤3 pages excluding references**, ≥5 references | `proposal/` |
| Presentation | 30 min, in class, covers proposal + progress; slides to D2L | not started |
| Final report | **IEEE double-column, ≤8 pages** | `report/` |

- The proposal must contain these sections: Title, Introduction, Motivation/Background, Problem statement, Objectives and goals, Expected challenges, Significance, References, Resources, Timeline.
- The grading rubric also scores "Approach and methodology" (5 pts), so keep that section too.
- **Deadlines live on D2L and are NOT recorded here yet.** The proposal timeline assumes the semester ends about 2026-12-13. Ask the user before relying on any date.

## Layout

```
README.md     human overview          KICKOFF_PROMPT.md   prompt for the next session
course/       course handouts (read-only)
literature/   papers (PDFs)
docs/         research_plan.md (living plan), phishlang_notes.md (paper + code-audit facts, verified refs)
proposal/     main.tex + references.bib  -> latexmk -pdf main.tex
report/       IEEEtran skeleton + references.bib (copy of proposal's; keep in sync by hand)
scripts/      small standalone analysis scripts (stdlib/numpy/pandas/sklearn only)
notebooks/    phishlang_colab_train.ipynb (E0-E2; runs on Colab or locally in WSL)
              run_local_wsl.sh (the quarantined local run), test_notebook.py (runs the notebook on synthetic pages)
results/      small aggregate outputs, committed (local_wsl/ = the 2026-10-27 run)
```

Create these only when first needed:
- `src/` for the Python pipeline.
- `extension/` for the MV3 extension.

After any change to the notebook, re-run `notebooks/test_notebook.py` on synthetic pages before a real run. It needs no phishing data; see its docstring.

Never commit datasets, model weights, or `external/` clones.

## SAFETY RULES for phishing data (mandatory)

**Incident, 2026-10-26.** Extracting PhishLang's parsed phishing samples under this Windows folder triggered 116 Microsoft Defender detections covering 2,408 files (the last one at 18:33, on a sample that was mid-deletion) (`Trojan:HTML/Phish.*`, `TrojanSpy:JS/Phish.*`, and others). Nothing executed. The extracted folder and the upstream clone were deleted. The user was alarmed. Do not repeat this.

- **Never download, extract, or write phishing samples to any Windows path, including this folder.** That covers raw HTML, PhishLang's parsed `.txt` samples, `training_data/parsed_samples_part_*`, and PhreshPhish parquet files.
- **Data location (decided 2026-10-27): WSL Ubuntu `~/phish-research`**, on the Linux disk, folder mode 700. Colab is the alternative: data in `/content`, never Google Drive.
  - Run data work only through `notebooks/run_local_wsl.sh`. It downloads and hash-checks the files and makes them read-only. Then it runs the notebook under `unshare --user --map-root-user --net --mount` with a tmpfs over `/mnt`: no network, and the Windows drives are invisible.
  - Pages are never unpacked to disk. The notebook reads them from the zip into memory and never prints them.
  - Only aggregate CSV/JSON files go back to the repo (`results/local_wsl/`). Per-page files (`split.csv`, predictions), model weights and logs stay in `~/phish-research/out` and `~/phish-research/run`.
  - Never open `~/phish-research` with Windows tools (Read/Grep/Glob, Explorer, `\\wsl$` paths), because that exposes the samples to Defender. Inspect it only through `wsl -e ...` commands that print names, sizes or aggregates.
  - After every data step, check `Get-MpThreatDetection` for new events. There were 0 after the 2026-10-27 run.
- Never change Windows Defender settings or add exclusions. That is the user's decision only.
- Never install or run upstream binaries (`phishlang_clientside_app/installer.deb`, `phishlang_extension.crx`).
- Never visit or render live phishing URLs. Work only on stored HTML, offline.
- Load third-party model weights only from `.safetensors`. Never `torch.load` or unpickle third-party files.
- Defender removes samples selectively, not at random. A dataset that touched a scanned Windows path may be silently biased. If file counts don't match the expected counts, stop and report.

## Verified facts (2026-10-26). Re-verify before relying on anything that may have changed.

**Upstream `src/training.py`** (commit `6b72838`):
- It tokenizes with `max_length=128, truncation=True`, so training sees only the first 128 tokens of each parsed page.
- `src/patched_parser_prediction.py` predicts with the **max** phishing probability over 128-token windows (stride 64). Training and inference therefore do not match.
- It has a train/test leakage bug. KFold indices come from the shuffled `train_df` but are applied to `full_dataset`, which is in the original (phishing-first) `df` order.
  - `scripts/check_upstream_leakage.py` replays this logic. At the paper's sizes (22,419 phishing / 26,000 benign), **51–76% of test rows land in each fold's training set**, and the training phishing share is 58% against a true 46%.
- Also: it uses an 80/20 split (the paper says 70/30), weighted-average P/R/F1, and saves only the last fold's model.

**Upstream code and model:**
- The upstream code uses the transformers 4.44 API (`evaluation_strategy`). It will not run unmodified on transformers 5.x.
- The released model is `google/mobilebert-uncased` fine-tuned for 2 classes: 24 layers, FP32 `model.safetensors` at about 98 MB.
- The parser keeps 18 tag types (h1–h3, p, a, ul, ol, li, title, footer, form, script, input, button, iframe, meta, map, area) and lowercases the text.

**Paper:**
- Table 2: MobileBERT accuracy/F1 0.96, median inference 0.39 s, 74 MB.
- The client-side app is a local Python server that the extension queries. It needs TensorFlow + PyTorch, up to 2.5 GB.
- The released installer is a `.deb` only, despite the paper claiming Windows support.

**PhreshPhish:**
- Hugging Face `phreshphish/phreshphish`, CC BY 4.0, not gated.
- About 36.6 GB of parquet and 666,315 rows (498,255 train / 168,060 test) as of 2026-10-26.
- Each row has a URL and raw HTML. The test split is later in time than the training split and has been filtered for leakage.

**More upstream and model facts (2026-10-27):**
- `predict_with_sliding_window` scores only full 128-token windows.
  - A page under 128 tokens gets no window, so its probability stays 0 and it is called benign.
  - The trailing partial window of longer pages is dropped.
  - The released tokenizer's `model_max_length` is 1e30, so inference otherwise covers the whole page.
- `google/mobilebert-uncased` has only `pytorch_model.bin` on `main`. Load it with `revision="a34c332593aea210dcccd7eaacdb3c9f62aa2700"` (Hugging Face's safetensors conversion, PR #8) and `use_safetensors=True`.
- MobileBERT's starting classification loss is about 1e5–1e6, because its logits reach about 1e6. This is also reported in discussion #9 on the model's Hugging Face page.
  - At lr 2e-5 the loss is normal within about 100 steps.
  - FP16 is unsafe (its maximum is 65,504), so train in FP32.

**Data and results (local run 2026-10-27, `results/local_wsl/`, one seed so far):**
- **Archive vs. cleaned data.** The archive holds 29,048 phishing and 23,611 benign parsed pages; the paper says 22,419 phishing and ~26K benign.
  - Cleaning removed 1,300 empty pages, 7 whose text is in both classes, and 21,957 exact duplicates.
  - That leaves 7,503 phishing and 21,892 benign pages. 74% of phishing pages were removed (21,545 of 29,048), against 7% of benign pages.
- **E0, on kept pages** (token counts include [CLS]/[SEP]):

  | | Benign | Phishing |
  |---|---|---|
  | Median length | 15,892 | 2,332 |
  | Over 128 tokens | 99.1% | 98.3% |
  | Over 512 tokens | 98.2% | 82.8% |
  | Under 128 tokens (upstream inference scores them 0) | 0.8% | 1.7% |
- **Split.** Stratified 70/30, then 10% of train held out for validation, seed 42.
  - 18,518 train / 2,058 validation / 8,819 test, with 25.5% phishing in each.
  - No page text crosses splits.
- **Input-level duplicates.** The 29,395 pages give only 20,814 distinct 128-token inputs; the largest group is 1,467 pages.
  - 55.0% of test phishing pages (1,238 of 2,251) and 24.8% of test benign pages have an input identical to some training page's.
  - 58 inputs occur with both labels; 3,538 benign and 545 phishing pages carry them.
- **E1: the released model on our test split.** This is NOT held out, because the model was probably trained on many of these pages.
  - Accuracy 0.934, phishing P/R/F1 0.903/0.830/0.865, weighted F1 0.933.
- **E2: retrained with upstream hyper-parameters on the clean split, seed 42.**
  - Accuracy 0.954, phishing P/R/F1 0.938/0.876/0.906, weighted F1 0.953, PR-AUC 0.958.
  - Phishing F1 is 0.885 on test pages whose input never occurs in training.
  - Validation F1 levels off at about 0.88 from epoch 6.
  - Training took 11.2 min on the RTX 5070.
- **Paper's Table 2, for comparison:** accuracy 0.96, P/R/F1 0.95/0.96/0.96. The paper doesn't state the averaging; upstream's script reports weighted metrics.

**Machine:**
- Ryzen 7 9700X, 32 GB RAM, RTX 5070 12 GB (Blackwell, so it needs PyTorch CUDA 12.8+ builds), 1.2 TB free.
- WSL2 Ubuntu is installed. MiKTeX 24.1 with IEEEtran; auto-install is on.

**Python environments:**
- The project env was created 2026-10-27 at `~/phish-research/venv` in WSL: Python 3.12.3, torch 2.11.0+cu128, transformers 4.57.6, accelerate 1.15.0, scikit-learn 1.9.1, pandas 3.1.0.
  - WSL sees the RTX 5070 (driver 610.88), including inside the `unshare` sandbox.
  - The Hugging Face cache in WSL holds the pinned base model, so sandboxed runs work offline.
- The Windows conda `base` env has torch 2.11+cu128 and transformers 5.12. Don't use it for this project.
- On Windows (not in WSL), Python `urllib` fails SSL verification, but `requests` and `curl` work.
- The dblp and Semantic Scholar APIs are bot-blocked here, so use Crossref (`https://api.crossref.org/works/<doi>`) for citation metadata.

## Working rules

- **Citations:** never invent a reference, venue, page range, or number.
  - Check every BibTeX entry against Crossref, the venue page, or the paper itself.
  - Mark anything unverified as `TODO-verify` and don't put it in a submitted PDF.
- **Numbers:** every number in the proposal or report must come from a script in this repo or from a cited source.
- **LaTeX:** build with `latexmk -pdf main.tex` inside `proposal/` or `report/`, and check the page count after every edit. The proposal body must end by page 3, before References.
  - If a build fails with "missing \item", delete the stale `main.bbl` and rebuild.
- **Git:** don't commit or push unless asked. Commits use the GitHub no-reply address that is set in this repo's local git config.
