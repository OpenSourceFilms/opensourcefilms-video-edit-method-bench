# Third-Party Licenses

This repository does not redistribute any evaluated model weights. **Some included ComfyUI
workflow JSON is derived from upstream Apache-2.0-licensed workflow graphs**
(Edit Anything and FlexAM), with OSF parameter and graph modifications.
These inherited portions are not solely OSF-authored and do not become
exclusive OSF MIT material. OSF's independently authored code, configuration,
documentation and original modifications are MIT-licensed; the upstream
portions retain their licences and required notices. See
[workflow-specific provenance and modification notices](workflows/UPSTREAM_NOTICES.md)
and the included [Apache-2.0 licence text](LICENSES/Apache-2.0.txt).
The model/checkpoint and software licences below remain separate.

Verified directly against each upstream project's own repository LICENSE file or Hugging Face model
card `license` metadata (not inferred from README prose or reputation), 2026-08-20.

## Edit Anything (for LTX 2.3)

- **Upstream:** [huggingface.co/Alissonerdx/EditAnything](https://huggingface.co/Alissonerdx/EditAnything) — a LoRA adapter, `base_model: Lightricks/LTX-2.3`.
- **LoRA license:** Apache-2.0.
- **Base model dependency:** requires LTX-2.3 weights to run — see the **LTX-2** entry below for the
  license actually governing generation output and commercial use.
- **Commercial-use verdict:** the LoRA adapter itself is unrestricted (Apache-2.0), but running it
  requires LTX-2.3 weights under the LTX-2.x Community License — see below. Not independently clear
  of that license just because the adapter is Apache-2.0.
- **What's included here:** OSF-materialized ComfyUI workflow graphs (`workflows/generated/01_*`,
  `02_*`, `05_*`, `06_*`) referencing this LoRA and LTX-2.3's stock node types by name — no LTX-2.3
  weights, no LoRA weights, redistributed.

## FlexAM

- **Upstream:** [github.com/IGL-HKUST/FlexAM](https://github.com/IGL-HKUST/FlexAM)
- **Code license:** Apache-2.0 (confirmed via `gh api repos/IGL-HKUST/FlexAM`).
- **Base model dependency:** Wan2.2-Fun 5B (Wan-AI). Not independently re-verified as part of this
  audit — the underlying Wan2.1-T2V-14B base model is confirmed Apache-2.0 on Hugging Face, but the
  specific Wan2.2-Fun-5B checkpoint FlexAM's config references was not individually checked.
- **Commercial-use verdict:** code is clean (Apache-2.0). Weights: not independently verified —
  treat as an open question if evaluating for commercial use.
- **What's included here:** the upstream workflow JSON's OSF-materialized variant
  (`workflows/generated/03_FlexAM_MotionTransfer_97f_OFFICIAL_BASE.json`, plus the two top-level
  `workflows/02_*`/`03_*_CORRECTED.json` graphs) and OSF's own CLI/config around it. No FlexAM
  weights redistributed.

## Ditto / Editto

- **Upstream:** [github.com/EzioBy/Ditto](https://github.com/EzioBy/Ditto)
- **Code license:** **CC-BY-NC-SA-4.0** (Creative Commons Attribution-NonCommercial-ShareAlike),
  confirmed by reading the repository's actual `LICENSE` file text.
- **Model weights** ([huggingface.co/QingyanBai/Ditto_models](https://huggingface.co/QingyanBai/Ditto_models)):
  same **CC-BY-NC-SA-4.0**, per the model card's `license` metadata. Fine-tuned from
  `Wan-AI/Wan2.1-T2V-14B` (Apache-2.0 base), but the Ditto fine-tune itself carries the more
  restrictive NC-SA terms.
- **Commercial-use verdict:** **non-commercial only**, both code and weights. The ShareAlike clause
  also means any derivative of Ditto's own workflow graph would need to carry the same NC-SA terms.
- **What's excluded here, and why:** Ditto's own ComfyUI workflow graph (both the raw
  official-upstream JSON and OSF's materialized variant of it) is **not included** in this
  repository — it derives directly from Ditto's own authored graph, which the ShareAlike license
  covers. Obtain it directly from the upstream repository if reproducing this comparison.
- **What's kept:** OSF's own `cli/ditto_high_quality/run_orbit_turn.sh` runner script — it only calls
  an external, unvendored Ditto installation the user provides themselves (`$DITTO_ROOT`), and
  contains no Ditto source or graph content of its own.

## LTX-2 / LTX 2.3 Sync-LoRA

- **Upstream:** [github.com/Lightricks/LTX-2](https://github.com/Lightricks/LTX-2) and
  [github.com/Lightricks/ComfyUI-LTXVideo](https://github.com/Lightricks/ComfyUI-LTXVideo)
- **License:** the **LTX-2.x Community License Agreement** (Lightricks Ltd., source-available, not
  an OSI-approved license). Read directly from both repositories' `LICENSE`/`LICENSE.md` files.
- **Commercial-use verdict:** **conditional, not blanket permissive or NC.** Free for individuals and
  for non-commercial use by any entity. Commercial Entities with **annual revenue ≥ $10,000,000**
  require a separate paid Commercial Use Agreement from Lightricks for any use beyond the
  non-commercial carve-out (testing/evaluation/non-production R&D). Below that revenue threshold,
  ordinary commercial use is permitted under the Agreement's terms — this is not the same shape as
  a strict non-commercial license (e.g. Ditto's above), and should not be described as one.
- **What's included here:** the LTX-2-native Clean-Plate IC-LoRA comparison graph
  (`workflows/generated/08_CleanPlate_ICLoRA_FML.json`/`.api.json`) — an OSF-authored graph
  referencing LTX-2's stock node types by name, not LTX-2's model weights or source code — and OSF's
  own `cli/sync_lora/run_orbit_turn.sh` runner, which calls the official `ltx_pipelines.ic_lora` CLI
  the user installs themselves from their own LTX-2 clone. No LTX-2 weights redistributed.

## Kiwi-Edit

- **Code upstream:** [github.com/showlab/Kiwi-Edit](https://github.com/showlab/Kiwi-Edit)
- **Code license:** MIT (confirmed via `gh api repos/showlab/Kiwi-Edit`).
- **Model weights:** [huggingface.co/linyq/kiwi-edit-5b-instruct-reference-diffusers](https://huggingface.co/linyq/kiwi-edit-5b-instruct-reference-diffusers)
  — **no license metadata is set on the model card.** Not independently verified; do not assume this
  means public domain or freely reusable. Treat the weights' redistribution/commercial-use rights as
  an open question until the authors clarify, separate from the MIT-licensed code repository.
- **What's included here:** OSF's own `cli/kiwi_edit/run_orbit_turn.py` runner, which downloads the
  model via its Hugging Face repo ID at runtime rather than vendoring any weights.

## Shared ComfyUI ecosystem dependencies

Reused verdicts already established and independently verified for
`opensourcefilms-comfyui-workflows`/`opensourcefilms-orbitturn` in this org — not re-audited here:

| Component | License | Commercial use |
|---|---|---|
| `Comfy-Org/ComfyUI` | GPL-3.0 | Yes (GPL is copyleft, not non-commercial) |
| `Comfy-Org/ComfyUI_frontend` | GPL-3.0 | Yes |
| `Comfy-Org/workflow_templates` | MIT | Yes |
| `Kosinkadink/ComfyUI-VideoHelperSuite` | GPL-3.0 | Yes |
| `kijai/ComfyUI-KJNodes` | GPL-3.0 | Yes |
| `kijai/ComfyUI-WanVideoWrapper` | Apache-2.0 | Yes |
| `alisson-anjos/ComfyUI-BFSNodes` | GPL-3.0 | Yes |

Per the same reasoning already established for this org's other ComfyUI-workflow repos: an
OSF-authored workflow graph that references a GPL/Apache node's class name is very unlikely to be a
derivative work of that node's source code — see `renewal-evidence-framing`/prior org licensing
research. This does not extend to Ditto's ShareAlike terms above, which is why Ditto's graph is
excluded rather than included under the same reasoning.

## How these verdicts were reached

Verified directly against each upstream project's own repository `LICENSE` file or Hugging Face
model card `license` field via the GitHub/Hugging Face APIs, not inferred from README prose,
reputation, or third-party summaries. Anything not explicitly confirmed above is marked "not
independently verified" — treat those as open questions if evaluating this for commercial use, not
as settled.
