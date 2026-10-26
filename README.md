# Video Edit Method Bench

A **method comparison / research evaluation** repo, not a finished production pipeline. Open Source
Films (OSF) tested six emerging video-editing/reskin generation methods against the same
production shot-editing problem — removing an actor and reconstructing a background while preserving
exact camera motion — to find out which, if any, could produce production-usable results.

This is the comparative R&D that preceded OSF's later published H3-based approach
([`opensourcefilms-orbitturn`](https://github.com/OpenSourceFilms/opensourcefilms-orbitturn)), not a
replacement for it. None of the six methods compared here is claimed to be production-ready; this
repo documents what was actually tried and found.

## The six methods compared

| # | Method | Approach | Canonical form used |
|---|---|---|---|
| 1 | **Edit Anything** (for LTX 2.3) | LoRA-based motion transfer / reference-conditioned editing | ComfyUI — 4 workflow variants (Motion Transfer r256/r128, Reference V2V full/simple) |
| 2 | **FlexAM** | Motion-transfer diffusion on Wan2.2-Fun | ComfyUI |
| 3 | **Ditto / Editto** | Video-to-video diffusion, actor-removal focused | ComfyUI (see note below — graph not redistributed here) |
| 4 | **LTX 2.3 Sync-LoRA** | Native LTX-2 in-context LoRA conditioning | CLI (`ltx_pipelines.ic_lora`) — no faithful ComfyUI graph asserted |
| 5 | **Kiwi-Edit** | Reference-image-conditioned diffusion | Diffusers CLI — no canonical ComfyUI graph asserted |
| 6 | **Ditto high-quality path** | Same model, non-quantized/non-distilled runtime | Official repository CLI runner |

Full per-component licensing findings: `THIRD_PARTY_LICENSES.md`.

**Upstream-workflow attribution:** the Edit Anything and FlexAM ComfyUI
graphs in this repository were adapted from their respective upstream
Apache-2.0-licensed workflow JSON, not authored wholly from scratch by
OSF. The original graph expression retains its upstream licence, while
OSF's own additions are licensed only to the extent OSF owns them. See
[UPSTREAM_NOTICES.md](workflows/UPSTREAM_NOTICES.md) for sources and recorded
modifications, and [Apache-2.0 licence text](LICENSES/Apache-2.0.txt).
The base models and checkpoints are not redistributed here.

## What's here

- **`env/scan_runpod_envs.py`** — a real Runpod-environment-fit scanner: walks the pod's existing
  ComfyUI/CLI installs, scores each against every method's actual requirements (custom nodes,
  model file patterns, Python/torch/CUDA versions), and recommends reuse vs. a bespoke environment.
  See `RUNPOD.md`.
- **`env/stage_inputs.py`** — symlinks/copies the shot's source plate and reference frames into a
  ComfyUI install's `input/` directory.
- **`env/write_runtime_leftovers.py`** — turns the scanner's JSON output into a human-readable
  "what still needs a bespoke environment" report.
- **`materialize/materialize_upstream_workflows.py`** — generates ComfyUI-loadable workflow variants
  from each method's official upstream workflow JSON, applying the specific parameters this
  comparison used (frame count, resolution, sampler mode).
- **`validation/validate_comfy_workflows.py`** — checks that generated workflow JSON is structurally
  loadable before spending GPU time on it.
- **`cli/sync_lora/`, `cli/kiwi_edit/`, `cli/ditto_high_quality/`** — OSF-authored runner scripts for
  the three methods with no canonical ComfyUI graph, each calling an official, unvendored upstream
  tool the user installs themselves.
- **`config/fit_requirements.json`** — per-method environment requirements (custom node markers,
  model file patterns, ideal Python/torch/CUDA versions) the scanner checks against.
- **`config/orbit_turn.json`** — the specific comparison parameters used (frame counts, output paths)
  for this shot, as a worked example.
- **`workflows/`** — OSF-materialized ComfyUI workflow graphs for Edit Anything and FlexAM (both
  Apache-2.0 upstream) and the LTX-2-native Clean-Plate IC-LoRA comparison graph. Ditto's graph is
  deliberately not included — see below.

## What's deliberately excluded, and why

- **Ditto/Editto's own ComfyUI workflow graph** — Ditto's code and model weights are licensed
  CC-BY-NC-SA-4.0 (non-commercial, ShareAlike). A workflow graph derived from Ditto's own authored
  graph structure falls under that ShareAlike requirement, unlike the Apache-2.0-licensed graphs
  included here. Get it from [github.com/EzioBy/Ditto](https://github.com/EzioBy/Ditto) directly.
  OSF's own `cli/ditto_high_quality/` runner script is kept — it only calls an external installation.
- **Any model weights or checkpoints**, for any of the six methods — fetch these from the sources
  documented in `THIRD_PARTY_LICENSES.md` and `config/fit_requirements.json`'s `required_model_patterns`.
- **The three upstream tool repos themselves** (EditAnything's LoRA host, FlexAM, Ditto, LTX-2,
  Kiwi-Edit) — clone them yourself; each keeps its own license.
- **Any generated output** from any of the six methods — none is included, since several of the
  methods are non-commercial-licensed and the source/reference imagery used for this comparison is
  production plate material, not something OSF can redistribute.
- **The production shot's own source footage and reference frames** — referenced only by filename
  pattern in `config/orbit_turn.json`; not included, and every script here takes the shot directory
  as a required argument or environment variable rather than assuming a fixed path.

## Running this yourself

1. Install whichever of the six upstream tools you want to compare, following each project's own
   instructions.
2. Run `env/scan_runpod_envs.py` to see which existing installs (if any) already satisfy a method's
   requirements, using `config/fit_requirements.json`.
3. Use `env/stage_inputs.py` to link your own source plate and reference frames into a ComfyUI
   install's `input/` directory. The helper checks **all four required source
   files and destination conflicts before staging any file**. Default mode
   creates symlinks; `--copy` streams into a hidden same-directory
   `.staging` file, fsyncs it, then atomically publishes a complete regular
   file under its final name using create-only hard-link semantics. **ComfyUI
   will not see a partial final filename during copying**, and an existing
   file or dangling symlink is never overwritten, even if another process
   claims the target during the copy. A failed copy removes only its own
   temporary staging file. Previously staged symlinks to the same source
   are accepted; copied files already at the destination are treated as
   conflicts. Source files and other existing destination files are never
   deleted. Symlinked `input/` directories are refused for this historical
   helper. Use a destination on a filesystem supporting same-directory
   hard links; concurrent mutation of the input directory is not protected
   by a process-level lock. Copied files use normal exclusive-file
   creation permissions (mode `0666` filtered by the staging process
   umask), rather than `mkstemp`'s always-private `0600`; ensure
   that the operator's umask and directory access permit the intended
   ComfyUI user to read the result. The unpredictable hidden staging
   pathname exists while data is written and is not a confidentiality
   boundary for other users with directory access.
4. For the ComfyUI-based methods (Edit Anything, FlexAM), load a graph from `workflows/` or
   `workflows/generated/`. For the CLI-based methods (Sync-LoRA, Kiwi-Edit, Ditto high-quality),
   use the corresponding script under `cli/` — each requires you to set an environment variable or
   argument pointing at your own tool installation and shot directory; none assumes a fixed path.
5. `validation/validate_comfy_workflows.py` checks a graph loads correctly before you spend GPU time
   running it.

See `RUNPOD.md` for how this was actually run on a Runpod pod, including the environment-fit
scanning approach.

## Offline validation and CI

The [offline acceptance workflow](.github/workflows/offline-acceptance.yml)
runs on GitHub Actions without ComfyUI, GPUs, model weights or source footage.
It invokes the existing shell/Python syntax and publication checks, 13
synthetic validator regressions, and the structural validator against all
**11 published workflow JSON files**.

The validator recognises both editor/UI graphs and ComfyUI API prompts. API
node IDs may be numeric strings or namespaced strings such as `489:311`.
Malformed/missing API upstream links and invalid node declarations now fail
instead of reporting a successful check of **zero graphs**.

**Limits:** Several official upstream UI exports contain nested, object-form
link records that this standalone validator cannot fully interpret. Those
records produce warnings, not a claim of validated runtime connectivity.
A clean CI result proves basic JSON/known-link consistency only. It does
not prove upstream node availability, weights, licences, correct inputs,
ability to run inference, or video quality. The archived comparison results
and original experimental methods are unchanged.

## Status

Research evaluation / method comparison, run once to completion on 2026-08-06 against a specific
production shot and pod configuration. Not maintained as a production tool, and no single method
here is asserted to be production-ready — treat this as a point-in-time record of what was tried and
found, not a recommendation to adopt any one method as-is.

---

Runpod-sponsored GPU compute made this comparison possible.
[Open Source Films](https://opensourcefilms.org).
