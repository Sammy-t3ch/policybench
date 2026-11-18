# Decisions

This file records every choice not fully dictated by the five approved v0.2 design PDFs
in [`docs/design-pdfs/`](design-pdfs/). The PDFs are frozen archival originals; the
Markdown files in [`docs/`](./) are the editable source for design changes, which
must land as docs PRs first.

Status: Phase 0 (foundation). Last updated 2026-11-18.

## A. Maintainer answers to the open questions in Changelog.md (fixed unless revised)

| # | Decision | Changelog open question answered |
| --- | --- | --- |
| A1 | Headline results use `policy_visibility=full`. `policy_visibility=none` is a secondary study, supported but not the default. | 1, and Critique item 9 |
| A2 | Headline reliability metric is `pass^k`; `pass@k` is secondary. | 2 |
| A3 | Adversarial pressure is a separate axis (A0–A4) crossed with L1–L5. There is no L6. | 3 |
| A4 | Build a small, independent, **test-only** policy evaluator to cross-check the main engine. | 5, Critique item 3 |
| A5 | Denial feedback default is `rule` (`rule_id` + reason code). | 8 |
| A6 | V1 requires native function calling. No constrained-JSON adapter in V1. | 7, Critique item 12 |
| A7 | Dataset: hand-written task templates plus a seeded generator for variants. No private held-out split in V1, but the dataset format must allow adding one later. | 6 and 9, Critique item 4 |

### Still open

- **Changelog open question 4 (dataset size target for V1)** is not explicitly answered
  by the seven decisions above. The only guidance is the design's suggestion ("roughly
  200 to 300 tasks at A0, plus a smaller adversarial subset", Changelog.md open question
  4; Critique.md item 11) and the Phase 9 scope ("at least 20 families across the six
  domains, each at L1–L5 with valid and prohibited variants, A1–A4 variants for a
  subset"). A decision is needed before Phase 9; Phase 0 does not require it.
- Changelog.md and Critique.md still contain the original "Open" wording. Per the
  instruction to keep the Markdown transcriptions verbatim, those passages are **not**
  edited here; this file is the record of the resolved status.

## B. Repository and workflow choices (Phase 0)

| # | Choice | Rationale |
| --- | --- | --- |
| B1 | Use the existing public GitHub repository `Sammy-t3ch/policybench`; do not create a new one. | Repo already exists and is public; owner and visibility are unambiguous, so no question was needed. |
| B2 | MIT license, `LICENSE` at the root. | Default specified by the maintainer. |
| B3 | The Phase 0 feature branch is `arena/5d1de76e-policybench`, branched from `main`; nothing is pushed to `main`. | Arena session branch is the single feature branch for this phase; later phases get their own branch and PR. |
| B4 | Phase numbering follows the maintainer's list exactly: Phase 0, then Phases 2–9. There is no Phase 1 issue or PR. | The maintainer's phase list has no Phase 1; no phase was invented. |
| B5 | Later phases start only after the previous PR is merged and the maintainer replies `go phase N`. PRs are never merged by the agent. | Approval gates. |
| B6 | One GitHub issue per later phase (Phases 2–9), with acceptance criteria quoted from the design. | Required by Phase 0 step 6. |
| B7 | Conventional commits. | Required by the git workflow. |
| B8 | Vercel is untouched until V1 is done and the maintainer says `go docs site`. | Explicit instruction. |

## C. Documentation choices (Phase 0)

| # | Choice | Rationale |
| --- | --- | --- |
| C1 | All five PDFs are committed byte-for-byte unchanged under `docs/design-pdfs/`; SHA-256 verified against the attachments. | Frozen archival originals. |
| C2 | The five Markdown transcriptions are verbatim: same wording, section numbers, tables, JSON examples, formulas, and the ASCII overview diagram. No summarising, improvement, or fixing. | Required; apparent errors are listed in the Phase 0 PR description instead. |
| C3 | Code fences in the transcriptions carry no language labels, so the Markdown source adds no words that are absent from the PDFs. | Keeps the transcriptions byte-close to the source; verified by a normalised token comparison against two independent PDF extractors. |
| C4 | `docs/` Markdown is the editable design source; PDFs are never edited; design changes are docs PRs first. | Required. |
| C5 | Apparent inconsistencies noticed while transcribing are reported in the Phase 0 PR description, not corrected in the Markdown and not implemented in code. | Required. |

## D. Stack and CI choices (Phase 0)

| # | Choice | Rationale / justification |
| --- | --- | --- |
| D1 | `requires-python = ">=3.12,<3.13"`; CI uses Python 3.12 only. | "Python 3.12 only" from the stack rule and CI requirement. |
| D2 | Runtime dependencies are exactly `pydantic>=2`, `typer`, `httpx`, `jsonschema`. | Architecture.md Section 16. |
| D3 | Dev-only extras: `pytest`, `hypothesis`, `ruff`, `mypy`. `hypothesis` is specified by Architecture.md Section 16 and needed for the Phase 3 property test. `ruff` and `mypy` are **CI-only tools**, not runtime dependencies: the Phase 0 CI requirement asks for ruff, a type check, and pytest, and neither ruff nor a type checker appears in the design's dependency list. Justification for adding them is recorded here and in the PR description. | "Add nothing else without a written justification in the PR description." |
| D4 | `setuptools>=68` is a build-system requirement only (no runtime dependency). | Needed for a `pyproject.toml`-only, `src/`-layout package; not a new runtime library. |
| D5 | CI runs `ruff check .`, `mypy`, and `pytest` on every PR, on Python 3.12 only. | Phase 0 step 5. |
| D6 | Empty scaffold directories are kept with `.gitkeep` files; `traces/` and `reports/` are ignored except `traces/fixtures/` and `reports/samples/`. | Architecture.md Sections 11 and 13. |
| D7 | `src/policybench/__init__.py` contains only a docstring, so the type checker and test runner have a package target. No CLI, schemas, engine, or implementation code exists in Phase 0. | Scaffolding only; keeps Phase 0 reviewable. |
| D8 | `tests/test_phase0_layout.py` is a smoke test for the scaffold, the frozen PDFs, and the JSON examples in the transcriptions. It is not an implementation test. | CI must have a passing `pytest` run in Phase 0. |
| D9 | `pyproject.toml` declares no `project.scripts` entry for `policybench`. | The CLI is not implemented until Phase 2+; declaring a script now would be a false claim. |

## D-bis. Repo-wide GitHub state found during Phase 0

| # | Choice | Rationale |
| --- | --- | --- |
| D9 | Eight phase issues (#1 Phase 2 … #8 Phase 9) already exist in `Sammy-t3ch/policybench`, created 2026-11-18 07:55–07:56 UTC, each with acceptance criteria quoted from the design. **They were not duplicated.** | Phase 0 step 6 is satisfied repo-wide; creating eight duplicate issues would add noise. Verified by reading all eight issue bodies. |
| D10 | An open Phase 0 PR (#9, from branch `arena/d5f5a1a1-policybench`) predates this branch. It was not merged, closed, edited, or pushed to. This branch keeps its own Phase 0 PR. | Arena tracks work per branch; other branches are out of scope. The duplication is flagged as a decision needed from the maintainer in the PR description. |
| D11 | The existing issues reference `docs/DECISIONS.md` items Q-01 … Q-12 from the other branch's decision log. Those IDs are **not** used in this branch's `DECISIONS.md`; the corresponding apparent design inconsistencies are listed in the Phase 0 PR description instead. | Avoids silently depending on another branch's files. |

## E. Hard rules carried forward

- JSONL traces are the source of truth; SQLite is a derived, rebuildable index only.
- Deterministic, programmatic grading only; no LLM-as-judge; free text is never parsed
  for decisions.
- Policy is data: versioned JSON, restricted condition language, JSON Schema validated;
  never hardcoded.
- Mock tool simulators only: pure, seedable, no network, no wall clock, no randomness
  outside the seed.
- No secrets or real credentials are committed; no production services are contacted.
- No web UI, auth, user model, or billing in V1.
