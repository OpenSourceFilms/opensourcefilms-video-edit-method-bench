# Upstream workflow provenance and modification notices

This directory contains OSF-modified workflow JSON as well as wholly OSF-authored
tooling. **Where an upstream graph was used as a base, the upstream graph's
copyright and Apache-2.0 rights remain in force.** OSF's MIT grant applies to
OSF-authored additions and independently authored content only, not as an
exclusive claim to upstream graph structure or expression.

## Edit Anything-derived workflow exports

- **Original source and author:** [Alissonerdx / EditAnything](https://huggingface.co/Alissonerdx/EditAnything/tree/main/workflows),
  source workflow `edit_anything_with_ref_or_motion_transfer_v0.1.json`.
- **Upstream permission basis:** model repository identifies Apache-2.0; the
  original workflow source is downloaded from that repository by
  [OSF's materializer](../materialize/materialize_upstream_workflows.py).
  Re-check the source repository's actual distribution terms when rematerializing.
- **Derived output files:** `generated/01_EditAnything_Motion_R256.json`,
  `generated/02_EditAnything_Motion_R128.json`,
  `generated/05_EditAnything_RefV2V_Full.json`,
  `generated/06_EditAnything_RefV2V_Simple.json`, and OSF-generated API/UI
  variants based on those upstream graphs.
- **Modifications made by OSF:** frame count/rate, model and sampler selections,
  prompts, input/output paths and naming, reference conditioning and active
  output wiring for the comparison shot. These are **modified exports**,
  not original unmodified upstream files.

## FlexAM-derived workflow exports

- **Original source and authors:** [FlexAM, IGL-HKUST](https://github.com/IGL-HKUST/FlexAM),
  authors Mingzhi Sheng, Zekai Gu, Peng Li, Cheng Lin, Hao-Xiang Guo,
  Ying-Cong Chen and Yuan Liu.
- **Original graph:** [assets/flexam_workflow.json](https://github.com/IGL-HKUST/FlexAM/blob/main/assets/flexam_workflow.json).
  The materializer records the expected upstream Git blob SHA as
  `ae43d1c1164382298e55146625de6badd197364b`.
- **Upstream licence:** [Apache License 2.0](https://github.com/IGL-HKUST/FlexAM/blob/main/LICENSE);
  a full text copy is included at [../LICENSES/Apache-2.0.txt](../LICENSES/Apache-2.0.txt).
- **Derived output files:** `generated/03_FlexAM_MotionTransfer_97f_OFFICIAL_BASE.json`,
  `02_FlexAM_MotionTransfer_97f_COMFY.json`, and
  `03_FlexAM_MotionTransfer_97f_CORRECTED.json`.
- **Modifications made by OSF:** comparison-shot input paths, frames,
  prompts, active outputs, sampler and mode parameters, display metadata and
  fixes needed to materialize runnable graph variants.

## Third-party content and redistribution boundaries

- These adapted graphs are **not** entirely OSF-original merely because OSF
  saved the modified files. Read their Apache-2.0 origins and preservation of
  upstream notices alongside OSF's own MIT terms.
- Apache-2.0 does not convey any licence to separately downloaded models,
  datasets, checkpoints or media. In particular, LTX-2.x weights and any
  other separately governed dependencies require independent compliance.
- Ditto's upstream CC-BY-NC-SA-4.0 authored graph is intentionally **not**
  included in the published exports. The materializer may retrieve it at
  runtime into a user's working directory, under the upstream terms.
- JSON files cannot reliably include licence comments without changing their
  expected ComfyUI format. This adjacent notice documents provenance and
  modifications for all files above. It is not a substitute for retaining
  any upstream notices that may be embedded in the original work.

For detailed upstream project terms and the uncertain model-weight
licensing verdicts, see [../THIRD_PARTY_LICENSES.md](../THIRD_PARTY_LICENSES.md).
