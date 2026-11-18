# PolicyBench Design Changelog and Open Questions

Version: v0.2.1 (Markdown source). The frozen PDF originals in `docs/design-pdfs/` are v0.2.

## v0.1 to v0.2 changes

| # | Change | Why |
| --- | --- | --- |
| 1 | Adversarial pressure moved from level L6 to a separate axis (A0 to A4) | Make complexity effects attributable; allow interaction analysis |
| 2 | Matched task families, complexity covariates (`rule_count`, `precondition_depth`, and others) | Reduce difficulty confound; allow numeric complexity analysis |
| 3 | Agent-environment protocol with explicit meta tools (`escalate_to_human`, `refuse`, `ask_clarification`, `finish`) | Deterministic grading without parsing prose |
| 4 | Enforce and audit modes; attempted vs. executed violation; strict vs. lenient Safe Completion | Remove metric ambiguity |
| 5 | Replay grading as a first-class command (`policybench grade`) | Scores always recomputable from traces; no model re-runs after grader fixes |
| 6 | Reproducibility claim re-scoped: replay grading exact, model sampling best effort | Original claim was not achievable on local backends |
| 7 | `pass^k` as the headline reliability metric, `pass@k` secondary | For compliance, consistency matters more than best-of-k |
| 8 | Cluster bootstrap CIs over families; `low-n` flags; no automatic significance | Episodes and tasks are not independent |
| 9 | Baseline agents (oracle, always-refuse, always-comply, random) as tests | Self-validate the benchmark |
| 10 | Independent oracle paths, `forbidden_calls`, final-state assertions per task | Break circularity between enforcer and grader |
| 11 | Condition language specified with limits (depth 8, 64 nodes, strict typing) | Keep policy-as-data from becoming code |
| 12 | Denial `feedback` level and `policy_visibility` as recorded run parameters | Recovery and compliance depend on what the agent is told |
| 13 | JSONL canonical, SQLite derived | Remove storage ambiguity |
| 14 | Latency reported only, always with hardware | Non-deterministic, hardware dependent |
| 15 | Over-refusal always shown alongside compliance curves; valid variants at every level | Prevent "more refusal" being read as "better compliance" |

## v0.2 to v0.2.1 changes

1. Architecture.md Section 4 and Section 6.1 — `require_prior` is a rule effect, not a
   verdict; `Decision.verdict` stays `allow | deny | require_escalation`; an unmet
   precondition yields verdict `deny` with `reason_code` `"precondition_unmet"`.
2. Architecture.md Section 6.2 — canonical JSON keys `history_has` and `history_count`
   replace `history.has(tool, where)` / `history.count(tool, where)`.
3. MetricsSpec.md Sections 2 and 3.1 — error episodes count as failures for Safe
   Completion and Enforced Completion; the denominator is all episodes.
4. MetricsSpec.md Sections 2, 3.6 and 8 — error episodes count as failures for pass^k with
   an all-episode denominator; the error count is always reported and runs above 5% errors
   are flagged.
5. MetricsSpec.md Sections 3.2-3.5 — error episodes are excluded from violation, attempt,
   over-refusal and recovery rates.
6. Architecture.md Section 5 and MetricsSpec.md Section 2 — `escalate_to_human` takes
   `(reason, context)`.
7. Architecture.md Section 5, PolicyTaxonomy.md Section 8 and MetricsSpec.md Section 2 —
   each task declares `required_escalation_fields`, checked by the grader.
8. Architecture.md Section 6.1 and PolicyTaxonomy.md Section 6 — `description` is an
   optional policy field; added to the L4 role-dependent example.
9. Architecture.md Section 9 — one JSONL file per episode (was "per run").
10. Architecture.md Section 6.3 — `allow` is the default outcome when no rule fires, not a
    rule effect.
11. Architecture.md Section 12 — CLI agent names `refuse` / `comply` are aliases for the
    Always-refuse / Always-comply baselines.
12. Architecture.md Section 12 — corrected the `policybench generate` cross-reference to
    Changelog.md open question 9.
13. Architecture.md Section 14.2 — the second, independent policy evaluator is test-only,
    implements the same condition language, and must agree with the main engine in a
    hypothesis property test.
14. PolicyTaxonomy.md Section 2 — L1-L5 are the canonical level identifiers; the words
    following them are descriptive labels.
15. MetricsSpec.md Section 2 — defined `terminal_action` as ending on a terminal meta tool.
16. PolicyTaxonomy.md Section 8 and DECISIONS.md — V1 targets about 200 tasks at A0
    (20 families x 5 levels x valid and prohibited variants), plus an adversarial subset of
    one family per domain at all levels with A1-A4 variants; shrink the adversarial subset
    first if runtime forces a cut. Answers Changelog.md open question 4.
17. All five Markdown design files and README.md — version bumped to v0.2.1; the PDFs in
    `docs/design-pdfs/` remain frozen v0.2 originals.
18. Changelog.md open questions 1-3 and 5-9 — answers recorded in DECISIONS.md; question 4
    is answered by entry 16.

## Follow-up review decisions for v0.2.1

The following items raised during PR #13 review are now resolved in the Markdown source:

19. PolicyTaxonomy.md Section 6 and Architecture.md Section 6.2 — added mirrored operator
    tables specifying JSON shapes, operand arity, type rules, history matching, and missing-
    reference evaluation errors.
20. Architecture.md Sections 5 and 9 — specified schema validation → policy evaluation →
    execution; schema-invalid calls emit `invalid_call`, return a tool error, are not policy
    violations, and `invalid_call` is a trace event type.
21. Architecture.md Section 4 and MetricsSpec.md Section 2 — named the static Task field
    `recoverable: bool`; the per-episode output flag copies its value.
22. MetricsSpec.md Section 2 — defined clean no-op as `finish`, zero state-changing calls,
    and domain state hash equal to the initial hash; read-only calls are allowed.
23. Architecture.md Section 5 — `policy_visibility=none` with audit mode is rejected by
    `policybench validate` and `policybench run`.
24. Architecture.md Section 14.2 — independent test-only evaluator shares no code with the
    main engine except schema models and returns the same `Decision` shape.
25. Architecture.md Section 12 — declared `policybench generate <templates> --seed N` a V1
    command; detailed behavior is specified in Phase 9.
26. DECISIONS.md — recorded each follow-up decision and marked the four former review items
    resolved. The design remains v0.2.1; the archival PDFs remain v0.2.

## Open questions for you (decisions needed before coding)

Answered on 2026-11-18; see `DECISIONS.md`. Open question 9 is resolved: `policybench
generate <templates> --seed N` is a declared V1 command, with detailed behavior specified in
Phase 9. The original questions below are retained as the v0.2 record.

1. Policy visibility in the headline. Should the main results use `policy_visibility=full`
   (agent sees the policy text) or test discovery through denials? My recommendation:
   `full` as headline, `none` as a secondary study.
2. Reliability headline. Confirm pass^k as the headline for policy compliance.
3. Adversarial as a separate axis. Confirm. If you want the literal six-level taxonomy for
   compatibility with your original brief, we can keep a mapping, but analysis would be
   weaker.
4. Dataset size target for V1. Suggested roughly 200 to 300 tasks at A0, plus a smaller
   adversarial subset. Local-model speed may force a smaller number.
5. Second independent policy evaluator. Worth the extra effort to guard against
   circularity? My recommendation: yes, as a small test-only implementation.
6. Private held-out split. Do you want one, given contamination risk? This is a governance
   decision more than an engineering one.
7. Models without native tool calling. Out of scope for V1, or add a constrained-JSON
   adapter?
8. Feedback default. Denials return `rule_id` plus a reason code by default. Acceptable?
9. Dataset authoring. Hand-written tasks only, or hand-written templates with a
   parameterized generator for variants?

## Status

Design is complete as v0.2 and awaiting your review. No implementation code has been
written. Coding will begin only after you reply "approved" (and answer or defer the open
questions above). It will then proceed phase by phase (schemas, policy engine, tools, trace
logger, evaluator, metrics, runner, report), pausing after each phase for review.

## Status (v0.2.1)

The v0.2 PDFs are frozen in `docs/design-pdfs/`. The Markdown files in `docs/` are the
editable v0.2.1 source. The maintainer's decisions, the applied fixes, and the remaining
open items are recorded in `DECISIONS.md` and in the v0.2.1 PR description. Coding still
proceeds phase by phase, pausing after each phase for review.
