# Running on Runpod

This comparison was run on a single Runpod GPU pod, sequentially across all six methods, per the
project lead's explicit direction: fetch every method's models once, reuse the pod rather than
spinning up one per method, and let the environment-fit scanner below decide what can share an
existing install versus what needs its own.

## The environment-fit scanner

`env/scan_runpod_envs.py` is the actual tool used to decide, for each of the six methods, whether an
existing ComfyUI or CLI install on the pod could be reused or whether a bespoke environment was
needed. It:

1. Walks `/workspace`, `/opt`, and `/root` (bounded depth) looking for ComfyUI roots
   (`main.py` + `custom_nodes/` + `models/`) and CLI tool roots (a `diffusers_demo.py` or
   `ltx_pipelines` package).
2. For each candidate root, probes its Python interpreter (preferring a local `venv`/`.venv` over
   the system interpreter) for torch/CUDA/transformers/diffusers versions — with a 90-second budget
   for a cold `import torch`, after an earlier run mistook a slow first import on a real
   torch+CUDA venv for a missing one.
3. Scores each candidate against `config/fit_requirements.json`'s per-method requirements (required
   custom-node markers, required model file patterns, ideal Python/torch/CUDA versions) and reports
   `safe_reuse`, `install_nodes_or_models_only`, or `bespoke_required`.
4. `env/write_runtime_leftovers.py` turns the scanner's JSON output into a plain-language report of
   which methods still need a from-scratch environment.

Run it with:

```bash
python env/scan_runpod_envs.py --out /path/to/env_fit_report
```

It writes both `env_fit_report.json` and `env_fit_report.md`.

## A real environment-fitting decision this surfaced

The scanner's raw node-marker overlap alone would have ranked one existing ComfyUI install above the
actually-correct one for the Ditto comparison, because both installs happened to share several
custom-node markers. `config/fit_requirements.json`'s `avoid_roots` field for `Ditto` exists
specifically to override that: an install that superficially matched on node markers was excluded
by name because it had already been ruled out as a comparison path for this shot (for reasons
unrelated to the scanner's own scoring) and had none of the required Wan2.1/Ditto model weights
staged either. Worth knowing if you adapt this scanner to your own multi-install pod: node-marker
scoring alone isn't always sufficient, and the requirements file needs a way to express "never use
this root" independent of the score.

## A real technical finding, not just tooling

While comparing method #6 (the LTX-2-native Clean-Plate IC-LoRA path), the project lead's direction
overturned an earlier working assumption (that clean-plate IC-LoRA conditioning couldn't take
altered first/middle/last keyframes) after tracing ComfyUI's own live `/object_info` for
`LTXAddVideoICLoRAGuide(Advanced)`: it conditions one contiguous run starting at a given frame index,
and is designed to be **chained** — called again with a different, non-contiguous `frame_idx` — to
add more guide points. An existing workflow already had the middle/last-frame image-loading and
resize nodes wired in but unused, because the sampler chain only ever consumed the first-frame path.
The fix was two additional chained guide calls, not a fresh install or a different tool. This is the
kind of finding the environment/workflow tooling in this repo is built to surface and record, not
just execute.

## GPU note

This was run once against a single pod and GPU configuration on 2026-08-06. It has not been
re-verified against other GPU generations, and none of the six methods' relative quality/speed
findings here should be read as a benchmark independent of that specific hardware.
