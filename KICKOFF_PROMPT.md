# Kickoff prompt for the next Claude Code session

Open Claude Code in this folder and paste everything inside the box below.

```text
Continue the CS 8027 research project in this folder (PhishLang-Web). CLAUDE.md is loaded automatically: follow it exactly, including the Karpathy guidelines and the SAFETY RULES. Phishing data lives only in WSL ~/phish-research and is touched only through notebooks/run_local_wsl.sh. Before doing anything else, read docs/research_plan.md (especially "Status (2026-10-27)") and docs/phishlang_notes.md.

Where things stand: E0, E1 and E2 seed 42 are done (results/local_wsl/).
- 74% of the archive's phishing pages are removed as empty or duplicate.
- 55% of test phishing pages share their 128-token model input with a training page, and 58 inputs carry both labels.
- E2 phishing F1 is 0.906, against the paper's 0.96.

Before taking any action, ask me these together in one message (don't guess):
1. The D2L deadlines (proposal, presentation, final report). Is the topic approved, and has the proposal been submitted?
2. Should the proposal include the new findings (duplicates, input-level leakage, the short-page inference bug)?
3. Which low-end laptop will we use for the client benchmarks, and how are Deepthi and I splitting the work?

Then work through these steps one at a time, checking each before moving on:
1. E2 seeds 43 and 44. Set SEEDS = [42, 43, 44] in notebooks/phishlang_colab_train.ipynb. Re-test with notebooks/test_notebook.py (see its docstring), then run `bash notebooks/run_local_wsl.sh` from WSL; seed 42 is skipped automatically.
   Verify: results/local_wsl/ has three e2_seed*_test_metrics.json, the summary prints mean ± std, and Get-MpThreatDetection shows no new detections.
2. E2b ceiling. Write a script in scripts/ that runs inside WSL and reads ~/phish-research/out/results/split.csv (ids and hashes only, no page text). On the test split, compute the best accuracy and phishing recall any model can reach when identical 128-token inputs must get identical predictions. Copy only the aggregate CSV to results/local_wsl/.
   Verify: the ceiling is ≥ every observed accuracy (E1, E2), and the script reports 58 inputs with both labels.
3. Update docs/research_plan.md, docs/phishlang_notes.md and the numbers in CLAUDE.md. Change the proposal only if my answer to question 2 was yes; if so, rebuild and check the page limit.

Stop after step 3. Summarize what you found and what changed, and propose the next experiment (E3 on PhreshPhish, or E4 window ablation). Don't commit or push unless I ask.
```
