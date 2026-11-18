# PolicyBench Decisions Log

This file records every design and engineering decision not fully dictated by the frozen v0.2 archival PDFs (`docs/design-pdfs/`). Any change to the v0.2 design itself must be made via a docs PR against `docs/*.md` first, never silently in code.

---

## 1. Maintainer Decisions on v0.2 Open Questions (2026-11-18)

These resolve the open questions in `docs/Changelog.md` and are fixed unless explicitly revised by the maintainer.

| ID | Topic | Decision | Source / Changelog ref |
| --- | --- | --- | --- |
| D-01 | Policy visibility in headline results | Headline results use `policy_visibility=full`. `policy_visibility=none` is supported as a secondary study, not default. (`summary` is also supported per `docs/Architecture.md` Section 5.) | Maintainer decision #1; `Changelog.md` Open Question 1 |
| D-02 | Headline reliability metric | `pass^k` is the headline reliability metric; `pass@k` is secondary. | Maintainer decision #2; `Changelog.md` Open Question 2 |
| D-03 | Adversarial pressure axis | Adversarial pressure is a separate axis (`A0` to `A4`) crossed with complexity levels `L1` to `L5`. There is no `L6`. | Maintainer decision #3; `Changelog.md` Open Question 3 |
| D-04 | Independent policy evaluator | Build a small, independent, test-only policy evaluator in Phase 3 to cross-check the main engine (verified with a `hypothesis` property test). | Maintainer decision #4; `Changelog.md` Open Question 5; `Critique.md` item 3 |
| D-05 | Denial feedback default | Default is `feedback=rule` (returns `rule_id` plus a short machine-readable reason code). | Maintainer decision #5; `Changelog.md` Open Question 8 |
| D-06 | Native function calling requirement | V1 requires native OpenAI-compatible function calling. No constrained-JSON fallback adapter in V1. | Maintainer decision #6; `Changelog.md` Open Question 7 |
| D-07 | Dataset authoring and held-out split | Hand-written task templates plus a seeded generator for variants. No private held-out split in V1, but the dataset format must allow adding one later (e.g., via an explicit split field). | Maintainer decision #7; `Changelog.md` Open Questions 6 and 9 |
| D-08 | Dataset v0.1 size target | At least 20 families across the six domains (`payments`, `email`, `database`, `calendar`, `tickets`, `filesystem`), each at `L1` to `L5` with valid and prohibited variants, a hand-written oracle path per task, and `A1` to `A4` variants for a subset. | Phase 9 specification; `Changelog.md` Open Question 4; `Critique.md` item 11 |
| D-09 | Docs site and Vercel | Do not deploy or configure Vercel until V1 is complete and explicitly approved ("go docs site"). At that point: static read-only docs site from `docs/` plus sample reports, preview first, no serverless functions, databases, environment variables, or analytics. | Maintainer prompt (Vercel section) |

---

## 2. Phase 0 Engineering Decisions (2026-11-18)

| ID | Topic | Decision and justification |
| --- | --- | --- |
| E-01 | Source-of-truth hierarchy for design docs | The five attached v0.2 PDFs are committed byte-for-byte unchanged under `docs/design-pdfs/` as frozen archival originals. Verbatim Markdown transcriptions live under `docs/` (`Architecture.md`, `PolicyTaxonomy.md`, `MetricsSpec.md`, `Critique.md`, `Changelog.md`) and serve as the editable source for future design-change PRs. |
| E-02 | `Architecture.pdf` Section 12 right-edge clip recovery | In `docs/design-pdfs/Architecture.pdf` (page 7, Section 12 CLI code block), three lines visually extend past the `<pre>` clip rectangle (`# schema + consistency c`, `[--seed N] `, `# replay grading, no mo`), but all 31 clipped characters are intact in the underlying PDF text stream (`checks`, `[--feedback rule]`, `del calls`). The complete unclipped lines from the PDF stream are transcribed verbatim in `docs/Architecture.md`. |
| E-03 | Packaging and build backend | Uses standard `setuptools>=77` (`setuptools.build_meta`, PEP 639 license metadata) with a `src/` layout (`src/policybench/`), `requires-python = ">=3.12"`, PEP 561 `py.typed` marker, and console script `policybench = "policybench.cli:app"`. Runtime dependencies match `docs/Architecture.md` Section 16 exactly (`pydantic>=2`, `typer`, `httpx`, `jsonschema`); optional extras `plots` (`matplotlib`) and `bootstrap` (`numpy`) match Section 16. |
| E-04 | Dev/CI dependencies (`ruff`, `mypy`) | In addition to `pytest` and `hypothesis` (`docs/Architecture.md` Section 16), the `dev` optional extra includes `ruff` (linting and formatting) and `mypy` (strict static type checking), required by Phase 0 CI ("ruff, type check, pytest, Python 3.12 only"). Neither is a runtime dependency. |
| E-05 | `.gitignore` rules for `traces/`, `reports/`, and SQLite | Ignores everything under `traces/` except `traces/fixtures/`, ignores everything under `reports/` except both `reports/fixtures/` (Phase 0 specification) and `reports/samples/` (`docs/Architecture.md` Section 13), and ignores derived `*.sqlite` / `*.sqlite3` index files (`docs/Architecture.md` Section 11). |
| E-06 | Scaffolded empty directories | Empty top-level artifact directories from `docs/Architecture.md` Section 13 (`datasets/`, `policies/`, `runners/`, `evaluators/`, `metrics/`, `tools/`, plus `traces/fixtures/`, `reports/fixtures/`, `reports/samples/`) are tracked with `.gitkeep` placeholders to be removed as real artifacts land in later phases. |
| E-07 | Repository visibility and license | Public repository (`Sammy-t3ch/policybench`) under the MIT License (`LICENSE`), copyright initialized to `2026 Samuel Campbell` (matching the repository owner/initial commit author; adjustable on request). |

---

## 3. Open Design Clarifications (Flagged in Phase 0, Deferred to Relevant Phases)

These cross-document ambiguities were noticed while transcribing the v0.2 PDFs and left **unedited** in `docs/*.md`:

1. **`require_prior` in `Decision.verdict` (`Architecture.md` Sections 4, 6.1, 6.3; `MetricsSpec.md` Section 1):** `Decision.verdict` lists `"allow" | "deny" | "require_escalation"`, whereas policy effects and conflict-resolution severity include `require_prior` (`deny > require_escalation > require_prior > allow`). Before Phase 2/3, confirm whether an unmet `require_prior` emits `verdict: "deny"` with a precondition `reason_code` (e.g., `unmet_precondition`) or a distinct verdict literal.
2. **History reference syntax (`Architecture.md` Section 6.2 vs. `PolicyTaxonomy.md` Section 6):** `Architecture.md` uses shorthand `history.has(tool, where)` / `history.count(tool, where)`, while `PolicyTaxonomy.md` gives JSON keys `history_has` / `history_count`. Confirm canonical JSON representation in Phase 2 (and add the full operator table / JSON Schema referenced by `Architecture.md` Section 6.2).
3. **`Policy.description` required vs. optional (`Architecture.md` Section 6.1 vs. `PolicyTaxonomy.md` Section 6):** Present in the Section 6.1 example, omitted in the `PolicyTaxonomy.md` Section 6 L4 example; relevant to `policy_visibility=summary` rendering.
4. **Error-episode handling in denominators (`MetricsSpec.md` Section 2 vs. Sections 3.1 and 3.4):** Section 2 states error episodes are "counted as failure for Safe Completion, and excluded from violation-rate numerators and denominators", whereas Section 3.1 specifies Safe Completion's denominator as "all non-error episodes", and Section 3.4 specifies Over-Refusal Rate's denominator as "episodes on `valid` tasks" without stating whether error episodes are excluded. Clarify before Phase 7.
5. **`escalate_to_human` context fields (`Architecture.md` Section 5 vs. `MetricsSpec.md` Section 2 and `Critique.md` item 16):** Section 5 shows `escalate_to_human(reason)`, while `MetricsSpec.md` Section 2 and `Critique.md` item 16 require "all required context fields". Confirm exact tool parameter signature before Phase 2/8.
6. **Trace file wording (`Architecture.md` Section 9):** "One JSONL file per run: `traces/<run_id>/<task_id>__<sample>.jsonl`" describes one JSONL file per episode within a run directory alongside one `manifest.json` per run.
7. **Injection channel mapping for A2 (`Architecture.md` Section 8 vs. `PolicyTaxonomy.md` Section 7):** `Architecture.md` distinguishes `user_turn`, `tool_output`, and `document` (`fs.read`) channels, while `PolicyTaxonomy.md` Section 7 groups both tool outputs and fetched documents under variant `A2`'s `Tool output` channel label.
