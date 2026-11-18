# Decision log

Every choice that is not fully dictated by the design documents is recorded here, with the
reason and the date. Design documents are `docs/Architecture.md`, `docs/PolicyTaxonomy.md`,
`docs/MetricsSpec.md`, `docs/Critique.md`, `docs/Changelog.md`; the frozen originals are in
`docs/design-pdfs/`.

Status values: **accepted** (decided, in force), **open** (needs a decision before the affected
phase).

---

## A. Decisions from the maintainer (answers to Changelog.md open questions)

| ID | Decision | Status | Source |
| --- | --- | --- | --- |
| D-001 | Headline results use `policy_visibility=full`. `policy_visibility=none` is a secondary study: supported, not default. | accepted | Changelog Q1 |
| D-002 | The headline reliability metric is `pass^k`. `pass@k` is secondary. | accepted | Changelog Q2 |
| D-003 | Adversarial pressure is a separate axis (A0–A4) crossed with L1–L5. There is no L6. | accepted | Changelog Q3 |
| D-004 | Build a small, independent, test-only policy evaluator to cross-check the main engine. | accepted | Changelog Q5 |
| D-005 | Denial feedback default is `rule` (`rule_id` + reason code). | accepted | Changelog Q8 |
| D-006 | V1 requires native function calling. No constrained-JSON adapter in V1. | accepted | Changelog Q7 |
| D-007 | Dataset is hand-written task templates plus a seeded generator for variants. No private held-out split in V1, but the dataset format must allow adding one later. | accepted | Changelog Q9, Q6 |

## B. Phase 0 implementation choices

| ID | Choice | Reason | Status |
| --- | --- | --- | --- |
| D-010 | Repository is `Sammy-t3ch/policybench`, public, MIT. | The maintainer's existing repository; matches the default in the task brief. | accepted |
| D-011 | `ruff` (lint + format) and `mypy` (type check) are dev dependencies. | Phase 0 requires a CI gate with ruff, a type check, and pytest. Architecture §16 lists only `pytest` and `hypothesis` as dev dependencies, so this is an addition and is justified here and in the Phase 0 PR. Both are test-time only; no runtime dependency is added. | accepted |
| D-012 | Build backend is `setuptools` (already required for any `src/` layout), not hatchling/poetry. | Keeps the dependency surface minimal; architecture only constrains runtime dependencies. | accepted |
| D-013 | Version lives in one place: `src/policybench/__init__.py::__version__`, read by `pyproject.toml` via `[tool.setuptools.dynamic]`. | Avoids two version strings that can drift; the manifest records the PolicyBench version (Architecture §10). | accepted |
| D-014 | No `policybench` console-script entry point in Phase 0. | The CLI module does not exist yet; declaring an entry point that cannot resolve would be misleading. It is added in Phase 2 with `policybench validate`. | accepted |
| D-015 | The ten top-level folders from Architecture §13 are created exactly as listed (`datasets/`, `policies/`, `runners/`, `evaluators/`, `metrics/`, `tools/`, `traces/`, `reports/`, `tests/`, `docs/`) plus `src/policybench/`, each empty placeholder holding a `.gitkeep`. | §13 keeps the brief's flat layout while putting importable code under `src/`. Which module eventually lives in which top-level folder is not specified; that is settled per phase (Phase 2 onwards). | accepted |
| D-016 | `traces/` and `reports/` are ignored except `.gitkeep`, `traces/fixtures/`, and `reports/samples/`. | Phase 0 requirement ("traces/ and reports/ ignored except fixtures"), consistent with Architecture §13. | accepted |
| D-017 | Each Markdown transcription carries a short HTML comment identifying it as a verbatim transcription and naming the PDF it came from. | Documents provenance for readers and reviewers; the transcribed body text is untouched. | accepted |
| D-018 | A pytest test asserts the sha256 of each archived PDF and that every fenced ```json example in `docs/*.md` parses. | Turns the PDF extraction check into a CI gate, so a future edit cannot silently corrupt the archival originals or the JSON examples. | accepted |
| D-019 | CI runs on Python 3.12 only, on `pull_request` and on pushes to `main`. | Phase 0 requirement ("Python 3.12 only"); pushes to `main` only happen via merged PRs. | accepted |
| D-020 | One GitHub issue is created per later phase (2–9) with acceptance criteria quoted from the design documents. | Phase 0 requirement. | accepted |

## C. Open design ambiguities (not changed here; decisions needed)

These were found while transcribing the PDFs. Nothing was edited: the transcriptions reproduce the
documents verbatim, and each item is raised in the Phase 0 PR description and in the issue for the
phase that first needs it.

| ID | Ambiguity | Needs decision by |
| --- | --- | --- |
| Q-01 | Reference-node syntax differs between documents: Architecture §6.2 writes `history.has(tool, where)` and `history.count(tool, where)`, while PolicyTaxonomy §6 specifies `{"history_has": {...}}` and `{"history_count": {...}}` object nodes. | Phase 3 |
| Q-02 | Operand keys are specified only for `left`/`right` comparisons and `args` for `and`. The PDFs do not say what `in`, `not_in`, `domain_in`, `startswith`, `path_under`, `or`, and `not` take, nor their arity. | Phase 3 |
| Q-03 | `require_prior` is an effect with its own severity rank, but the `Decision.verdict` enum (Architecture §4) is only `allow \| deny \| require_escalation`. How a `require_prior` verdict is surfaced is unspecified. | Phase 3 |
| Q-04 | Architecture §9 says "One JSONL file per run" and then names one file per episode: `traces/<run_id>/<task_id>__<sample>.jsonl`. Confirm the intended granularity (one file per episode inside a per-run directory). | Phase 5 |
| Q-05 | The `recoverable` flag is listed as a per-episode flag (MetricsSpec §2) but is defined as a static, per-task property. Confirm it is emitted per episode with the task's constant value. | Phase 6 |
| Q-06 | `goal_achieved` for `should_refuse` accepts "`finish` after a clean no-op"; "clean no-op" is not defined. A precise test is needed. | Phase 6 |
| Q-07 | The `terminated` flag admits `error`, while §2 says error episodes are excluded from violation-rate denominators and counted as failure for Safe Completion. The interaction needs one written rule. | Phase 6 |
| Q-08 | Baseline agent names differ: the CLI (Architecture §12) uses `--agent oracle\|refuse\|comply\|random`; §2, §14, and MetricsSpec §7 use "always-refuse" and "always-comply". Confirm which identifiers are canonical and whether CLI aliases are kept. | Phase 8 |
| Q-09 | `policy_visibility=none` is annotated "(enforce mode only)" (Architecture §5) but nothing says what happens for `none` in audit mode: validation error, or silently disallowed. | Phase 8 |
| Q-10 | Changelog open question 4 (dataset size target: "roughly 200 to 300 tasks at A0") is not among the answers. Phase 9 asks for at least 20 families across six domains at L1–L5 with variants; confirm whether that supersedes the 200–300 figure as the V1 target. | Phase 9 |
| Q-11 | Level names are inconsistent in PolicyTaxonomy §2 (`L1 Static permissions`, `L2 Argument constraints`, but `L3 Stateful`, `L5 Conflicting`). The dataset card needs canonical level names. | Phase 9 |
| Q-12 | The second, independent policy evaluator (D-004) has no section in Architecture v0.2 ("recommended, not yet specified", Critique §3). Its scope and interface should be added as a docs change before or with the Phase 3 implementation. | Phase 3 |
