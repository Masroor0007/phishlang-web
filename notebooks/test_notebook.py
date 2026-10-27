"""Runs phishlang_colab_train.ipynb end to end on synthetic, harmless pages (no phishing data), so notebook changes
can be tested before a real run. It builds a fake archive with the upstream layout (outer zip -> two inner zips ->
<class>_samples/*.txt, split into 5 parts, plus an empty page, duplicates, a cross-class page and junk entries),
patches the notebook's file hashes to match, and executes every code cell except the Colab-only ones.

usage, from WSL with the project env:
    TEST_GPU=1 ~/phish-research/venv/bin/python notebooks/test_notebook.py notebooks/phishlang_colab_train.ipynb ~/phish-test-synth [crash]
then delete ~/phish-test-synth.
  crash          raise right after the first epoch checkpoint is saved (simulates a Colab disconnect; run again to resume)
  TEST_GPU=1     keep the notebook's GPU code path (otherwise it runs on CPU)
  TEST_EPOCHS=n  training epochs (default 2)
  N_PAGES=n      phishing pages to generate (default 230; benign = n - 20)
  LONG=n         multiply page lengths by n (memory tests)
The released model files are downloaded by the notebook itself into <root>/data/src/model (they contain no phishing data).
"""
import hashlib, io, json, os, random, sys, time, zipfile
import psutil

nb_path, root = sys.argv[1], sys.argv[2]
crash = "crash" in sys.argv
data, out = f"{root}/data", f"{root}/out"
nb = json.load(open(nb_path, encoding="utf-8"))
cells = ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]

def blob_sha1(b):
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()

# --- synthetic archive with the upstream layout: outer zip -> two inner zips -> <class>_samples/*.txt
parts_dir = f"{data}/training_data"
if not os.path.exists(f"{parts_dir}/parsed_samples_part_ae"):
    rnd = random.Random(0)
    words = "account login verify update secure bank page welcome home news sport weather contact about help shop cart price".split()
    def page(label):
        n = rnd.choice([10, 30, 60, 200, 700]) * int(os.environ.get("LONG", "1"))  # some pages under 128 tokens, some over 512
        head = 'INPUT: { "type": "password", "name": "pass" } ' if label else 'P: { "text": "daily news" } '
        return head + " ".join(f'P: {{ "text": "{rnd.choice(words)}" }}' for _ in range(n))
    def inner(folder, label, n, extra):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr(f"{folder}/", "")
            for i in range(n):
                z.writestr(f"{folder}/{folder[:5]}_{i:04d}.txt", page(label))
            for name, text in extra:
                z.writestr(name, text)
            z.writestr(f"__MACOSX/{folder}/._x.txt", "junk")
            z.writestr(f"{folder}/readme.md", "not a page")
        return buf.getvalue()
    dup = page(1)
    phish = inner("phish_samples", 1, int(os.environ.get("N_PAGES", "230")), [("phish_samples/zz_empty.txt", "  "), ("phish_samples/zz_dup1.txt", dup),
                                             ("phish_samples/zz_dup2.txt", dup), ("phish_samples/zz_both.txt", "same text in both")])
    benign = inner("benign_samples", 0, int(os.environ.get("N_PAGES", "230")) - 20, [("benign_samples/zz_both.txt", "same text in both")])
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as z:
        z.writestr("parsed_benign_samples.zip", benign)
        z.writestr("parsed_phish_samples.zip", phish)
    blob = buf.getvalue()
    os.makedirs(parts_dir, exist_ok=True)
    size = len(blob) // 4 + 1
    for i, suffix in enumerate(["aa", "ab", "ac", "ad", "ae"]):
        open(f"{parts_dir}/parsed_samples_part_{suffix}", "wb").write(blob[i * size:(i + 1) * size])

# --- patch the notebook source for a local run and execute it cell by cell
fake_sha = {f"training_data/parsed_samples_part_{s}": blob_sha1(open(f"{parts_dir}/parsed_samples_part_{s}", "rb").read())
            for s in ["aa", "ab", "ac", "ad", "ae"]}
ns = {}
for i, src in enumerate(cells):
    if "drive.mount" in src or "rmtree(DATA" in src:
        print(f"--- cell {i}: skipped (Colab-only / cleanup)")
        continue
    lines = [l[:len(l) - len(l.lstrip())] + "pass" if l.lstrip().startswith("!") else l for l in src.splitlines()]
    src = "\n".join(lines)
    if not os.environ.get("TEST_GPU"):  # CPU run: drop the GPU requirement
        src = src.replace('assert torch.cuda.is_available(), "no GPU: Runtime > Change runtime type > T4 GPU"', "")
        src = src.replace('DEVICE, GPU = "cuda", torch.cuda.get_device_name(0)', 'DEVICE, GPU = "cpu", "cpu-local-test"')
    for rel, sha in fake_sha.items():
        src = src.replace(f'"{rel}": "', f'"{rel}": "{sha}", "_orig_{rel}": "')
    if "FILES = {" in src:  # drop the _orig_ entries again after the dict literal is built
        src = src.replace("\ndef git_blob_sha1", "\nFILES = {k: v for k, v in FILES.items() if not k.startswith('_orig_')}\ndef git_blob_sha1")
    print(f"--- cell {i}")
    t0 = time.time()
    exec(compile(src, f"cell{i}", "exec"), ns)
    m = psutil.Process().memory_info()
    peak = getattr(m, "peak_wset", None) or __import__("resource").getrusage(__import__("resource").RUSAGE_SELF).ru_maxrss * 1024
    print(f"[cell time: {time.time() - t0:.1f} s | peak RAM so far: {peak / 1e9:.2f} GB]")
    if src.lstrip().startswith("# Settings"):  # point everything at the test folders
        ns.update(SEEDS=[42], EPOCHS=int(os.environ.get("TEST_EPOCHS", "2")), DATA=data, OUT=out)
        if crash:
            import transformers
            class Disconnect(transformers.TrainerCallback):
                def on_save(self, args, state, control, **kw):
                    raise RuntimeError(f"simulated disconnect after saving step {state.global_step}")
            orig_init = transformers.Trainer.__init__
            def init(self, *a, **k):
                orig_init(self, *a, **k)
                self.add_callback(Disconnect())
            transformers.Trainer.__init__ = init
print("=== notebook ran to the end")
