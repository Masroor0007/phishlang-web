# PhishLang: paper, code and dataset notes

Facts checked on 2026-10-26. Each fact has its source next to it. Anything not verified is in the last section.

## Paper (`literature/2408.05667v3.pdf`, arXiv v3, 16 Apr 2025; NDSS 2026)

- **Venue:** NDSS 2026.
  - Page: https://www.ndss-symposium.org/ndss-paper/phishlang-a-real-time-fully-client-side-phishing-detection-framework-using-mobilebert/
  - PDF: `2026-s1037-paper.pdf`; slides: `s1037-SahaRoy-slides.pdf`; video: https://youtu.be/iNa1tZfCe7k
- **Parser:** keeps 18 tag types: h1, h2, h3, p, a, ul, ol, li, title, footer, form, script, input, button, iframe, meta, map, area. Text is lowercased, and empty tags become `<EMPTY>` (§3.1).
- **Data:** Phishpedia dataset. 22,419 phishing pages have HTML, and 26K benign pages come from Alexa (§3.2.1).
  - The paper says 70/30 train/test, 5-fold CV, 10 epochs.
- **Table 2 (MobileBERT):** accuracy 0.96, precision 0.95, recall 0.96, F1 0.96, median inference 0.39 s, memory 74 MB.
  - DistilBERT: 0.94 / 0.85 s / 502 MB. Llama 2 7B: F1 0.96 / 33.71 s / 4,873 MB.
- **Table 3:** PhishLang F1 0.94, artifact 7 KB, 0.9 s. PhishIntention F1 0.95, 348 KB, 10.7 s.
- **§4:** Certstream run from 2023-09-28 to 2024-01-11 over 42.7M domains flagged 25,796 phishing pages (0.057%).
- **§5:** 15 problem-space attacks from Montaruli et al. (AISec 2023). Six patches (parser changes plus adversarial retraining) bring the per-attack false-negative rate to ≤ 1.68%.
- **§6:** the client-side app is a local server (Python) plus a Chromium extension.
  - Table 9: precision/recall 0.95/0.96; RAM 28–308 MB; median inference 0.44–0.81 s across 4 machines.
  - Trade-offs: needs TensorFlow + PyTorch (up to 2.5 GB). The authors rejected TF.js in-browser inference as slower and inconsistent.
- **§5.4.1:** non-English pages are a known false-negative source (118 missed: Japanese 57, Spanish 36, German 18, Italian 7).

## Upstream repo: github.com/UTA-SPRLab/phishlang @ `6b7283854ef8a6edc73f945c1ce7e51b2e1dc4fd` (2024-12-28)

- The paper's link `UTASPRLab/phishlang` returns 404. **There is no license file.**
- The README cites the older arXiv title ("Utilizing Large Language Models to Optimize the Detection and Explainability of Phishing Websites").

| Path | What | Use? |
|---|---|---|
| `src/training.py` | fine-tuning script (transformers 4.44 API) | read/replay only, it has bugs (below) |
| `src/parser_for_training_no_patch.py` | BeautifulSoup parser used to build training data | yes, as the reference parser |
| `src/patched_parser_prediction.py` | patched parser + sliding-window inference | yes, as the reference inference |
| `src/adversarial_choose_primary_attack/` | Montaruli-style manipulations + primary-attack selection | later, if time allows |
| `src/model/` | `config.json`, `model.safetensors` (98.5 MB FP32), tokenizer (`vocab.txt`) | yes, safetensors only |
| `src/requirements.txt` | torch 2.4.0, transformers 4.44.0, CUDA 12.1 wheels | don't install as-is: CUDA 12.1 doesn't support the RTX 5070 |
| `training_data/parsed_samples_part_aa..ae` | split zip (~344 MB) → `parsed_phish_samples.zip` + `parsed_benign_samples.zip` | **phishing content: isolated location only** |
| `phishlang_clientside_app/installer.deb`, `phishlang_extension.crx` | Linux installer + packed extension | **never install** |

- **Model config:** `MobileBertForSequenceClassification`, 24 layers, hidden 512, true_hidden 128, 4 heads, `max_position_embeddings` 512, vocab 30,522, lowercased.

### Code-audit findings (read from source; leakage confirmed by replay)

1. **Training truncation.** In `training.py`, `tokenize_function` uses `padding="max_length", truncation=True, max_length=128`. Without the optional `chunk` flag, the model sees only the first 128 tokens of each parsed page.
2. **Train/inference mismatch.** `patched_parser_prediction.py` `predict_with_sliding_window` uses window 128 and stride 64, and returns the **max** phishing probability over all windows. Inference therefore sees windows that training never labelled on their own.
3. **Leakage.**
   - `train_df, test_df = train_test_split(df, ...)` shuffles. Then `kf.split(train_df)` yields positions inside `train_df`, but `full_dataset.select(train_index)` reads those positions from `full_dataset`, which follows `df` order (phishing first).
   - `scripts/check_upstream_leakage.py` shows that 51.4%, 58.0%, 66.9%, 67.6% and 76.4% of test rows fall in folds 1–5's training data, at 22,419/26,000.
   - The training phishing share is 57.9% against a true 46.3%.
4. **Other details:**
   - The test split is 0.2, not the paper's 0.3.
   - Metrics use `average='weighted'`, not phishing-class P/R.
   - Only the last fold's model is saved.
   - Whether the published numbers came from this exact script is **unknown**. Say "the released script", not "the paper".
5. **Short pages are always "benign" at inference** (read from source, 2026-10-27).
   - `predict_with_sliding_window` breaks out of its loop at the first window shorter than 128 tokens.
   - A page with fewer than 128 tokens (including [CLS]/[SEP]) therefore gets no window, and its phishing probability stays at the initial 0.0.
   - The trailing partial window of longer pages is dropped too.
   - The released `tokenizer_config.json` sets `model_max_length` to 1e30, so `truncation=True` doesn't cut pages at 512.
   - E0 shows this affects 1.7% of (deduplicated) phishing pages.

### Defender incident (2026-10-26)

- Extracting `parsed_phish_samples.zip` under the Windows project folder caused 116 detection events covering 2,408 files.
  - 115 events (2,407 files) happened between 16:42 and 16:46.
  - The last event was at 18:33, on a sample that was being deleted (`C:\$Extend\$Deleted\...`, touched by `du`).
- All were quarantined and `DidThreatExecute=False`.
- The threat names included `Trojan:HTML/Phish.*`, `TrojanSpy:JS/Phish.*`, `PWS:HTML/Phish.*` and `Trojan:JS/Kryptik.SK!MTB`.
- The 2,407 named sample files carry timestamps from 2019-07-28 to 2020-10-01 (86 from 2019, 2,321 from 2020). This is the evidence for "2019–2020" in the proposal.
- Defender removes samples non-randomly, so any copy of this dataset that touched a scanned Windows path is biased.

### Dataset audit (local quarantined run, 2026-10-27; aggregates in `results/local_wsl/`)

- **What the archive holds.** `training_data` holds two inner zips with 29,048 phishing pages (`phish_samples/`) and 23,611 benign pages (`benign_samples/`). The paper says 22,419 phishing and ~26K benign.
- **Cleaning.** It removed 1,300 empty pages, 7 pages whose text appears in both classes, and 21,957 exact duplicates.
  - Kept: 7,503 phishing and 21,892 benign pages.
  - That is 74% of phishing pages removed (21,545; at least 20,238 of them duplicates), against 7% of benign pages.
- **Token lengths (E0).**
  - Median 15,892 tokens for benign pages and 2,332 for phishing.
  - About 99% of pages in both classes are longer than the 128-token training window.
  - Even 512 tokens covers whole pages for only 1.8% of benign and 17.2% of phishing pages.
- **Input-level duplicates.**
  - The 29,395 kept pages give only 20,814 distinct 128-token model inputs; one input is shared by 1,467 pages.
  - On our split, 55.0% of test phishing pages and 24.8% of test benign pages have an input identical to a training page's.
  - 58 inputs occur with both labels (3,538 benign and 545 phishing pages), so no 128-token model can classify all of those correctly.
- **Results so far (one seed):**

  | Model | Accuracy | Phishing P / R / F1 | Weighted F1 |
  |---|---|---|---|
  | E1: released model on our test split (not held out) | 0.934 | 0.903 / 0.830 / 0.865 | 0.933 |
  | E2: retrained on the clean split with upstream hyper-parameters | 0.954 | 0.938 / 0.876 / 0.906 | 0.953 |
  | Paper, Table 2 | 0.96 | 0.95 / 0.96 / 0.96 | n/a (averaging not stated) |

### Base model and training behaviour

- **Safetensors weights.** `google/mobilebert-uncased` has no safetensors file on `main`, only `pytorch_model.bin`. We load revision `a34c332593aea210dcccd7eaacdb3c9f62aa2700`, Hugging Face's automated safetensors conversion (PR #8, 2024-03-28).
- **Huge starting loss.** Fine-tuning starts with a loss of about 1e5–1e6, because the logits reach about 1e6. Others report the same in discussion #9 on the model's Hugging Face page.
  - In our runs it fell to about 0.5 within 100 steps.
  - FP16 would overflow (its maximum is 65,504), so we train in FP32.
- **Speed.** Training takes 11.2 min per seed on an RTX 5070 (18,518 pages × 10 epochs, FP32).

## Datasets

- **Phishpedia** (Lin et al., USENIX Security 2021): the original release is a Google Drive link in github.com/lindsey98/Phishpedia. We use PhishLang's parsed release instead.
- **PhreshPhish** (Dalton et al., arXiv:2507.10854):
  - HF `phreshphish/phreshphish`, CC BY 4.0, not gated, last modified 2026-10-24.
  - 666,315 rows (train 498,255 / test 168,060), about 36.6 GB of parquet (test ≈ 9.2 GB), 8 columns including URL and raw HTML.
  - The paper describes a temporally later test split, LSH/TF-IDF leakage filtering, and benchmarks at base rates from 0.05% to 5%.
  - Contains real phishing HTML, so the same safety rules apply.

## In-browser stack notes

- Transformers.js runs models through ONNX Runtime Web, and exports via Optimum. A ready MobileBERT *sequence-classification* ONNX checkpoint was not found, so we export our own.
- MV3: the default CSP is `script-src 'self'`. Add `'wasm-unsafe-eval'` for WebAssembly, and remote code is not allowed. Bundle the ORT `.wasm` files and point `wasmPaths` at the extension's own files.

## Verified related work (BibTeX keys in `proposal/references.bib`)

| Key | Why it matters |
|---|---|
| `roy2026phishlang` | base paper |
| `sun2020mobilebert` | model |
| `lin2021phishpedia` | PhishLang's training data |
| `pourmohamad2024clientside` | deployed client-side measures detected only 14% of phishing sites; 10% of login phishing blocked within the first hour (abstract) |
| `oest2020phishtime` | blocklist speed/coverage gaps |
| `arp2022dos`, `pendlebury2019tesseract` | evaluation pitfalls, temporal bias |
| `dalton2025phreshphish` | fresh temporal benchmark |
| `montaruli2023raze` | adversarial HTML attacks used by PhishLang |
| `koide2024chatphishdetector`, `li2024knowphish`, `cao2025phishagent` | LLM-based detectors (cloud-scale contrast) |
| `zafrir2019q8bert`, `jacob2018quantization` | INT8 quantization |
| `onnxruntime`, `transformersjs` | in-browser runtime |

## Not verified (do not cite yet)

- Chrome uses on-device Gemini Nano for scam detection under Enhanced Protection (announced May 2025). Only secondary news coverage was found; the primary Google blog post was not retrieved.
- PhishIntention's venue/year: PhishLang's bibliography says "USENIX Security 21", which may be wrong (likely USENIX Security 2022). Check before citing.
