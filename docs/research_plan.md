# Research plan: PhishLang-Web

Living document. The proposal (`proposal/main.tex`) is the frozen summary of this plan. Update this file as decisions are made.

## Question

**Can a MobileBERT phishing detector run entirely inside the user's browser (no cloud, no blocklist, no native install) while keeping the accuracy it shows under a leakage-free, temporally realistic evaluation?**

| RQ | Question | Answered by |
|---|---|---|
| RQ1 | How do PhishLang's precision, recall and F1 change when the train/test leakage is removed and the model is tested on 2024–25 phishing? | E1, E2, E3 |
| RQ2 | How much does the 128-token training window limit detection? Does training on the sliding-window view used at inference close the gap? | E0, E4 |
| RQ3 | What accuracy, latency, memory and size trade-offs result from running an INT8 MobileBERT inside a Chrome MV3 extension? | E5, E6, E7 |

## Experiments

| ID | What | Data | Output | Done when |
|---|---|---|---|---|
| E0 | Token-length distribution of parsed pages: how much of each page do 128 tokens cover? | PhishLang parsed samples | `results/token_lengths.csv` plus a summary | median, p90 and the fraction of pages over 128/512 tokens are reported |
| E1 | Released checkpoint, as-is, on our test split. **Sanity check only**: not held out for this model, which was probably trained on these pages | PhishLang parsed samples | P/R/F1/PR-AUC | labels and tokenization are shown to match upstream |
| E2 | Retrain with upstream hyper-parameters (lr 2e-5, 10 epochs, batch 32, grad-accum 4, max_len 128) on a corrected, deduplicated split, 3 seeds | same | mean ± std | the leakage check passes on the new split (0% test rows in train) |
| E2b | Input-level overlap: test pages whose 128-token input also occurs in train, and the best accuracy any 128-token model can reach when identical inputs must get identical predictions | same | shares + ceiling | the ceiling is ≥ every observed accuracy |
| E3 | Temporal test: E1 and E2 models on PhreshPhish test pages (parsed with the upstream parser) | PhreshPhish test split | P/R/F1, PR-AUC at base rates 0.1/0.5/1/5% | drop vs. E2 is quantified with a CI |
| E4 | Window ablation: first-128 vs. sliding-window training and inference vs. 512-token | both corpora | table | same split and seeds as E2 |
| E5 | ONNX export (FP32), then dynamic INT8; parity in Python (onnxruntime) | E3 test pages | agreement %, ΔF1 | INT8 agreement with FP32 ≥ 98%, or the reason it falls short is documented |
| E6 | JS parser over the live DOM vs. Python parser over saved HTML | saved benign pages first | exact-match % per tag type | differences are categorized |
| E7 | MV3 extension benchmarks: parse/tokenize/infer latency, peak memory, package size; WASM vs. WebGPU | desktop + low-end laptop | table + CDF plot | median latency < 1 s on the laptop (target) |

## Status (2026-10-27)

All runs used `notebooks/run_local_wsl.sh` (quarantined, in WSL). Aggregate outputs are in `results/local_wsl/`; the exact numbers are in `CLAUDE.md` → *Data and results*.

| ID | Status |
|---|---|
| E0 | done |
| E1 | done (sanity check; phishing F1 0.865) |
| E2 | seed 42 done (phishing F1 0.906, weighted F1 0.953); seeds 43 and 44 next |
| E2b | overlap shares done (55.0% of test phishing pages); ceiling not computed yet |
| E3–E7 | not started |

Findings so far that change the story:

1. **Duplicates.** Cleaning removes 74% of the archive's phishing pages (21,545 of 29,048), at least 20,238 of them as exact duplicates. Upstream's random split puts copies on both sides of train and test.
2. **Input-level leakage.** Even after exact duplicates are removed, 55% of test phishing pages give the model the same 128-token input as some training page, and 58 inputs carry both labels.
3. **Short-page bug.** Upstream's inference script scores pages under 128 tokens as benign; that's 1.7% of phishing pages.
4. **Lower recall.** Retrained on a clean split, phishing recall is 0.876, against 0.96 in the paper.

## Steps (goal-driven: each step has a check)

### Phase A: audit (RQ1–2)

1. ✅ Choose the data location → WSL `~/phish-research` (2026-10-27). Verified: no phishing file under any Windows path, and 0 new Defender detections.
2. ✅ Create a dedicated Python env → `~/phish-research/venv` (versions in `CLAUDE.md`). Verified: the GPU is visible, including inside the sandbox.
3. ✅ (changed) No clone. The notebook downloads only the 10 needed files at the pinned commit and checks each file's git blob hash. Archive counts: 29,048 phishing and 23,611 benign pages.
4. ⏳ Score one benign HTML string with the upstream parser and the released model → moved to E6 (parser parity). E1 already exercises the released model.
5. ✅ E0 token lengths, computed by the notebook → `results/local_wsl/e0_token_length_summary.csv`.
6. ✅ Leakage-free split: exact-duplicate removal, then a stratified split → `~/phish-research/out/results/split.csv`. It stays in WSL because it lists per-page ids. Verified: no text crosses splits, and every part is 25.5% phishing.
7. E1 ✅. E2 seed 42 ✅; seeds 43 and 44 are next, then the E2b ceiling.
8. Download only the PhreshPhish **test** split (~9 GB parquet) into the data location; parse it with the upstream parser → verify: the row count matches HF metadata and every row parses or is logged.
9. E3, then E4.

### Phase B: in-browser (RQ3)

1. Export the ONNX model (opset ≥ 17), with dynamic axes for batch and sequence → verify: max |logit diff| vs. PyTorch is below 1e-4 on 100 pages.
2. Apply INT8 dynamic quantization (onnxruntime.quantization) → E5.
3. Write the MV3 skeleton: a content script parses the DOM, and an offscreen document runs ONNX Runtime Web with bundled `.wasm` files. The manifest CSP gets `'wasm-unsafe-eval'` → verify: the extension loads unpacked with no CSP errors and scores one page offline (network disabled).
4. Port the parser to JS → E6.
5. Run the benchmark harness → E7.

## Open decisions (ask the user)

- ~~Data location~~: decided 2026-10-27, WSL `~/phish-research` (Colab as the alternative).
- **Proposal update:** add the duplicate and input-level findings to the proposal? This depends on whether it has been submitted already.
- **Headline metric:** report phishing-class P/R/F1 (recommended; the base rate is 25.5% after cleaning), with weighted F1 alongside for comparison with the paper.
- **D2L deadlines:** proposal, presentation, report. The timeline currently assumes the semester ends about 2026-12-13.
- **Topic approval:** has the topic been approved, and did the instructor give any feedback?
- **Low-end laptop:** which machine will be used for the client benchmarks?
- **Division of work** between the two members. One possible split is Phase A / Phase B in parallel, with shared evaluation scripts.

## Presentation (30 min, graded 30 pts)

The rubric weights content 10, organization 5, slide quality 5, delivery 5, Q&A 3 and use of technology 2. Draft outline:

| Minutes | Section |
|---|---|
| 0–3 | Problem: cloud blocklists vs. client-side; 14% client-side detection [pourmohamad2024] |
| 3–8 | PhishLang in one slide; what it gets right |
| 8–13 | Audit findings: truncation mismatch, leakage replay (one diagram) |
| 13–20 | Results so far: E1–E4 |
| 20–26 | In-browser architecture + E5–E7 numbers + demo/video |
| 26–30 | Limitations, next steps, Q&A |
