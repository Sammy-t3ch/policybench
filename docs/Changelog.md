# PolicyBench Design Changelog and Open Questions

## v0.1 to v0.2 changes

| # | Change | Why |
| --- | --- | --- |
| 1 | Adversarial pressure moved from level L6 to a separate axis (A0 to A4) | Make complexity effects attributable; allow interaction analysis |
| 2 | Matched task families, complexity covariates (`rule_count`, `precondition_depth`, and others) | Reduce difficulty confound; allow numeric complexity analysis |
| 3 | Agent-environment protocol with explicit meta tools (`escalate_to_human`, `refuse`, `ask_clarification`, `finish`) | Deterministic grading without parsing prose |
| 4 | Enforce and audit modes; attempted vs. executed violation; strict vs. lenient Safe Completion | Remove metric ambiguity |
| 5 | Replay grading as a first-class command (`policybench grade`) | Scores always recomputable from traces; no model re-runs after grader fixes |
| 6 | Reproducibility claim re-scoped: replay grading exact, model sampling best effort | Original claim was not achievable on local backends |
| 7 | pass^k as the headline reliability metric, pass@k secondary | For compliance, consistency matters more than best-of-k |
| 8 | Cluster bootstrap CIs over families; `low-n` flags; no automatic significance | Episodes and tasks are not independent |
| 9 | Baseline agents (oracle, always-refuse, always-comply, random) as tests | Self-validate the benchmark |
| 10 | Independent oracle paths, `forbidden_calls`, final-state assertions per task | Break circularity between enforcer and grader |
| 11 | Condition language specified with limits (depth 8, 64 nodes, strict typing) | Keep policy-as-data from becoming code |
| 12 | Denial `feedback` level and `policy_visibility` as recorded run parameters | Recovery and compliance depend on what the agent is told |
| 13 | JSONL canonical, SQLite derived | Remove storage ambiguity |
| 14 | Latency reported only, always with hardware | Non-deterministic, hardware dependent |
| 15 | Over-refusal always shown alongside compliance curves; valid variants at every level | Prevent "more refusal" being read as "better compliance" |

## Open questions for you (decisions needed before coding)

1. **Policy visibility in the headline.** Should the main results use `policy_visibility=full` (agent sees the policy text) or test discovery through denials? My recommendation: `full` as headline, `none` as a secondary study.
2. **Reliability headline.** Confirm pass^k as the headline for policy compliance.
3. **Adversarial as a separate axis.** Confirm. If you want the literal six-level taxonomy for compatibility with your original brief, we can keep a mapping, but analysis would be weaker.
4. **Dataset size target for V1.** Suggested roughly 200 to 300 tasks at A0, plus a smaller adversarial subset. Local-model speed may force a smaller number.
5. **Second independent policy evaluator.** Worth the extra effort to guard against circularity? My recommendation: yes, as a small test-only implementation.
6. **Private held-out split.** Do you want one, given contamination risk? This is a governance decision more than an engineering one.
7. **Models without native tool calling.** Out of scope for V1, or add a constrained-JSON adapter?
8. **Feedback default.** Denials return `rule_id` plus a reason code by default. Acceptable?
9. **Dataset authoring.** Hand-written tasks only, or hand-written templates with a parameterized generator for variants?

## Status

Design is complete as v0.2 and awaiting your review. No implementation code has been written. Coding will begin only after you reply **"approved"** (and answer or defer the open questions above). It will then proceed phase by phase (schemas, policy engine, tools, trace logger, evaluator, metrics, runner, report), pausing after each phase for review.
