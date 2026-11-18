# PolicyBench Self-Critique of the v0.1 Design

<!--
Transcription note: this Markdown file is a faithful transcription of
design-pdfs/Critique.pdf. Wording, section numbers, tables, code blocks, and
formulas are reproduced verbatim. The PDF is the frozen archival original; this file
is the editable source for design changes (via docs PRs).
-->

This critique was applied to the first draft. Each item states the weakness, the severity, and the resolution now reflected in v0.2 (see Changelog.md). Items marked **Open** are not fully solved and need a decision from you.

Severity: **S1** invalidates the research claim. **S2** materially weakens it. **S3** quality or usability.

## S1: threats to validity

**1. Level and difficulty are confounded.** Higher levels are also harder tasks (more steps, more tools). A drop from L2 to L4 could be task difficulty, not policy complexity.
Resolution: matched families (same business intent at every level), complexity covariates, and a paired within-family analysis. **Open:** matched families reduce but do not eliminate the confound, because L4 inherently needs more steps. The report must state this limit.

**2. Adversarial level was ranked as the next rung of complexity (L6).** An L6 drop cannot be attributed to complexity.
Resolution: adversarial pressure became a separate axis (A0 to A4) crossed with L1 to L5.

**3. Grader and enforcer share one engine, which is circular.** If the engine has a bug, enforcement and grading are wrong in the same way and nothing notices.
Resolution: each task carries independent `forbidden_calls`, final-state assertions, and a hand-written oracle path. A property test checks that replayed verdicts equal runtime verdicts. The oracle baseline must pass every task. **Open:** a second, independent policy evaluator (for example, a minimal separate implementation used only in tests) would be stronger. It costs extra effort. Recommended, not yet specified.

**4. Dataset contamination and overfitting.** A public, static benchmark ends up in training data, and published policies become something models learn to pass.
Resolution (partial): versioned datasets with hashes, and a template-parameterized generator so fresh instances can be created (names, amounts, thresholds). **Open:** a held-out private split is a governance decision. The generator is not yet specified in detail.

## S2: materially weakens results

**5. Original success criterion promised identical results for the same seed.** LLM sampling on local backends is not bit-deterministic across hardware or versions, so this claim was false.
Resolution: the guarantee is now two-part. Replay grading is exactly reproducible. Model sampling is best effort, with the limits documented.

**6. Metric ambiguity.** "Attempted violation" and "violation" were not distinguishable in enforce mode, and Safe Completion was ambiguous when a denied attempt was followed by a correct recovery.
Resolution: explicit enforce and audit modes, strict and lenient Safe Completion, attempted vs. executed violation. See MetricsSpec.md.

**7. Statistical independence was assumed.** Episodes within a task, and tasks within a family, are correlated. Naive Wilson or binomial intervals would be too narrow.
Resolution: cluster bootstrap over families; Wilson only where valid; `low-n` flags.

**8. Prompt sensitivity.** Results will depend on the system prompt, tool descriptions, and policy phrasing. A benchmark that measures one prompt measures one prompt.
Resolution (partial): prompt-template hash in the manifest; policy visible to the agent is rendered from the policy JSON by a deterministic template. **Open:** whether to report across multiple templates, and whether the agent sees the policy text at all (policy-in-context vs. policy-discovered-through-denials). These test different things. See Open Questions.

**9. What the agent is told about the policy is under-specified.** Compliance with a policy the agent was shown is different from compliance with a policy it must infer from denials.
Resolution: add a run parameter `policy_visibility` = `full` | `summary` | `none` recorded in the manifest. Default `full`. **Open:** which settings belong in the headline results.

**10. Mock-environment realism and ecological validity.** Simulators are cleaner than real systems, and scripted users do not behave like people.
Resolution: stated as a limitation in the report template. Not solvable in V1. Scripted user turns are fixed, which gives control but limits realism.

**11. Small-sample noise with local models.** Local models are slow, so `k` and dataset size will be small, and many slices will be underpowered.
Resolution: `low-n` flags, no automatic significance claims, a recommended minimum dataset size in the dataset card. **Open:** target size for V1 (my suggestion: at least 20 families x 5 levels x valid and prohibited variants, roughly 200 to 300 tasks at A0, with a smaller adversarial subset).

## S3: design and usability

**12. Tool-calling dependence excludes some local models.** Models without function calling cannot run.
Resolution: stated as a V1 limit. **Open:** a constrained-JSON adapter would widen coverage but introduces parsing failure as a new error source.

**13. Latency was graded-adjacent.** It is non-deterministic and hardware dependent.
Resolution: recorded and reported only, always with hardware, never used in scoring.

**14. Storage ambiguity (JSONL vs. SQLite).**
Resolution: JSONL canonical; SQLite is a derived, rebuildable index.

**15. Condition language could grow into a programming language.**
Resolution: no loops, user functions, or I/O; depth and node limits; JSON Schema validation; type errors are failures, not silent false.

**16. Escalation semantics were underspecified.** What counts as a "correct" escalation, and what does the approver respond?
Resolution: `escalate_to_human` returns a scripted outcome per task; correct escalation requires specified context fields; the simulator never grants approval unless the task script says so.

**17. Over-refusal can be mistaken for good compliance.** Stricter policies mechanically lower violation rates while raising over-refusal.
Resolution: every compliance curve is displayed together with over-refusal on the same axis in the report; valid variants exist at every level.

## Ranking summary

| Rank | Item | Status |
| --- | --- | --- |
| 1 | Level and difficulty confound (1) | Mitigated, residual risk stated |
| 2 | Adversarial as a rung (2) | Resolved |
| 3 | Circular grader and enforcer (3) | Mitigated, second evaluator Open |
| 4 | Reproducibility claim (5) | Resolved (re-scoped) |
| 5 | Metric ambiguity (6) | Resolved |
| 6 | Non-independence (7) | Resolved |
| 7 | Policy visibility and prompt sensitivity (8, 9) | Open |
| 8 | Contamination (4) | Partial, Open |
| 9 | Sample size (11) | Open |
| 10 | Realism (10) | Stated limitation |
| 11 to 17 | Remaining items | Resolved or documented |
