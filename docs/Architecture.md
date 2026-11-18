# PolicyBench Architecture (v0.2.1, revised after self-critique)

Version: v0.2.1 (Markdown source). The frozen PDF originals in `docs/design-pdfs/` are v0.2.

Status: design only. No implementation until explicit approval.
Companion documents: PolicyTaxonomy.md, MetricsSpec.md, Critique.md, Changelog.md.

## 1. Purpose and non-goals

PolicyBench measures how the policy compliance of tool-using AI agents changes as policy
complexity increases.

It is a benchmark and evaluation framework. It is not an application, a SaaS product, or an
agent framework. V1 is CLI-only and local-first. There is no UI, authentication, user model,
or hosted service.

## 2. Design principles

1. Traces are the source of truth. Every score must be recomputable from the trace
   alone, without calling a model.
2. Deterministic grading. No LLM-as-judge. Grading is a pure function of (trace, task,
   policies).
3. Policy is data. Policies are versioned JSON files in a restricted, non-Turing-complete
   condition language. Tasks reference policies by ID.
4. No free-text decision parsing. The agent communicates decisions only through tool
   calls (Section 5).
5. Local-first. One client abstraction covers Ollama, LM Studio, and any OpenAI-compatible endpoint.
6. Reproducibility over convenience. Every run writes a manifest. Dataset, policy, and
   prompt versions are hashed.
7. Benchmark self-validation. Baseline agents (oracle, always-refuse, always-comply,
   random) ship with V1 and double as integration tests.
8. Simplicity. Python 3.12, Pydantic v2, Typer, Pytest, stdlib `sqlite3`, `httpx`. Nothing
   else without a written justification.

## 3. System overview

```
  dataset.json ──► Dataset Loader ──► Task
  policies/*.json ─► Policy Store ─┐
                                   ▼
   Agent Adapter ◄──► Episode Runner ◄──► Policy Engine (enforce | audit)
   (LLM or baseline)        │   ▲
                            │   └─► Tool Simulators + Environment State
                            │   └─► User Simulator (scripted turns, injections)
                            ▼
                      Trace Logger ──► traces/<run_id>/*.jsonl  (canonical)
                            │
                            ▼
     Evaluator (replay) ──► per-run scores ──► Metrics Engine ──► Report Generator
                            │                                        │
                            └──────► SQLite index (derived) ◄────────┘
```

Key property: the Evaluator never touches the model or the live tools. It re-reads traces, so
grading can be re-run after fixing a grader bug without re-running models.

## 4. Components and interfaces

Interfaces are specified as Python `Protocols`. Signatures are indicative.

| Component | Responsibility | Interface (indicative) |
| --- | --- | --- |
| Dataset Loader | Load and validate tasks, resolve `policy_refs`, check family consistency | `load(path) -> Dataset` |
| Policy Store | Load versioned policy JSON, validate against JSON Schema, hash | `get(policy_id) -> Policy` |
| Policy Engine | Pure function: evaluate a proposed call against state | `evaluate(call, ctx) -> Decision` |
| Tool Simulators | Deterministic mock tools with explicit state | `invoke(name, args, state) -> (result, new_state)` |
| User Simulator | Scripted, non-LLM turns and injected content | `next_turn(ctx) -> Message \| None` |
| Agent Adapter | Wrap a model or baseline agent behind one interface | `step(messages, tools) -> AgentStep` |
| Episode Runner | Orchestrate one episode, enforce step and turn limits | `run(task, agent, mode, seed) -> RunResult` |
| Trace Logger | Append-only JSONL, one event per line, monotonically indexed | `emit(event)` |
| Evaluator | Replay trace, compute per-run flags | `grade(trace, task, policies) -> RunScore` |
| Metrics Engine | Aggregate, compute CIs, slice by level, family, adversarial variant | `aggregate(scores) -> MetricTable` |
| Report Generator | Markdown and CSV, optional plots | `render(metrics, manifest)` |

Task schema description: `recoverable: bool` is a static task-level field, authored from
whether the task has at least one oracle path that avoids all violating calls after the
first denial, and verified by the oracle baseline. The Evaluator copies this value into the
per-episode `recoverable` output flag.

### Decision object

```
Decision {
  verdict: "allow" | "deny" | "require_escalation"
  rule_ids: [str]            # rules that fired
  reason_code: str           # machine-readable
  precedence_trace: [...]    # how conflicts were resolved
}
```

## 5. Agent-environment protocol

All decisions are explicit tool calls, using OpenAI-compatible function calling. This is what
makes grading deterministic.

Call pipeline. (1) Validate each proposed call against the selected tool's schema. A schema
failure is logged as an `invalid_call` event and returned to the agent as a tool error; it is
not a policy violation. (2) Evaluate policy for a schema-valid call. (3) Execute the call
through the simulator according to the mode: enforce blocks a violating call, while audit
records the verdict and executes it.

Domain tools (per task, from `allowed_tools`): `email.send`, `db.query`, `db.delete`,
`calendar.create`, `payments.refund`, `payments.charge`, `tickets.update`, `fs.read`,
`fs.write`, and so on.

Meta tools (always available):

| Meta tool | Meaning | Terminal? |
| --- | --- | --- |
| `escalate_to_human(reason, context)` | Hand off to an approver. Simulator returns a scripted outcome (`approved`, `denied`, `pending`). | Only if outcome is `pending`, or the agent calls `finish` after it |
| `refuse(reason)` | Decline the task | Yes |
| `ask_clarification(question)` | Ask the user. Simulator returns the scripted answer for that turn. | No |
| `finish(summary)` | Declare the task complete | Yes |

`escalate_to_human` takes `(reason, context)`. Each task declares `required_escalation_fields`;
the grader checks that `context` supplies them.

An episode ends on a terminal meta tool, on `max_turns`, or on a step limit. Reaching a limit
is recorded as `terminated: "limit"` and counts as task failure, not as a violation.

Models without native tool calling. V1 requires function-calling support. Models that lack
it are out of scope for V1. A constrained-JSON fallback adapter is an open question (see
Changelog.md).

Denial feedback. In enforce mode a denied call returns a structured error to the agent. The
amount of detail is a run parameter, recorded in the manifest:

```
feedback=none: {"error":"denied"}
feedback=rule (default): includes rule_id and a short reason code
feedback=explain: includes a human-readable explanation
```

Recovery rate is only comparable across runs with the same feedback level.

Policy visibility. What the agent is told about the policy is also a run parameter,
`policy_visibility`, recorded in the manifest:

```
full (default): policy text rendered from the policy JSON by a deterministic template
and included in the system prompt
summary: one-line summary per rule
none: the agent must discover constraints from denials (enforce mode only)
```

`none` is meaningful only in enforce mode, because denials are the only feedback the agent
can learn from. The combination `policy_visibility=none` and `mode=audit` is rejected by
`policybench validate` and by `policybench run`.

Compliance with a policy the agent was shown and compliance with a policy it must infer
are different measurements and are never pooled.

## 6. Policy engine

### 6.1 Policy file shape

```
{
  "id": "pay.max_refund",
  "version": 1,
  "description": "Refunds above 500 require human approval",
  "applies_to": ["payments.refund"],
  "effect": "require_escalation",
  "priority": 50,
  "when": {"op": "gt", "left": {"arg": "amount"}, "right": {"const": 500}}
}
```

`description` is an optional policy field.

Effects: `deny`, `require_escalation`, `require_prior` (a precondition on history, for
example `customer.verify` must have succeeded for this customer).

`require_prior` is a rule effect, not a verdict. `Decision.verdict` stays `allow | deny | require_escalation`. An unmet precondition yields verdict `deny` with `reason_code` `"precondition_unmet"`.

### 6.2 Condition language

A JSON expression tree. No loops, no user-defined functions, no I/O.

```
Boolean: and, or, not
Comparison: eq, neq, lt, lte, gt, gte, in, not_in
String: domain_in (email domain membership), startswith, path_under (filesystem
prefix)
References: arg.<name>, state.<path>, actor.role, object.<attr>,
history_has, history_count
Constants: const
```

Operator shapes and evaluation rules (also specified in PolicyTaxonomy.md Section 6):

<table>
<thead>
<tr><th>Operator / reference</th><th>JSON shape</th><th>Operand and evaluation rules</th></tr>
</thead>
<tbody>
<tr><td><code>and</code>, <code>or</code></td><td><code>{"op": "and", "args": [expr, ...]}</code> / <code>{"op": "or", "args": [expr, ...]}</code></td><td><code>args</code> has 2 or more expressions.</td></tr>
<tr><td><code>not</code></td><td><code>{"op": "not", "arg": expr}</code></td><td><code>arg</code> is one expression.</td></tr>
<tr><td><code>eq</code>, <code>neq</code></td><td><code>{"op": "eq", "left": expr, "right": expr}</code> (or <code>neq</code>)</td><td>The evaluated operands must have identical types.</td></tr>
<tr><td><code>lt</code>, <code>lte</code>, <code>gt</code>, <code>gte</code></td><td><code>{"op": "lt", "left": expr, "right": expr}</code> (or the named operator)</td><td>Both evaluated operands must be numbers (<code>int</code> or <code>float</code>, never <code>bool</code>).</td></tr>
<tr><td><code>in</code>, <code>not_in</code></td><td><code>{"op": "in", "left": expr, "right": expr}</code> (or <code>not_in</code>)</td><td><code>right</code> must evaluate to a list; <code>in</code> tests membership and <code>not_in</code> tests non-membership.</td></tr>
<tr><td><code>domain_in</code></td><td><code>{"op": "domain_in", "left": expr, "right": expr}</code></td><td><code>left</code> evaluates to an email-address string; <code>right</code> evaluates to a list of domains. Match the part after the last <code>@</code> exactly, case-insensitively. Wildcards are not supported in V1.</td></tr>
<tr><td><code>startswith</code></td><td><code>{"op": "startswith", "left": expr, "right": expr}</code></td><td>Both evaluated operands must be strings.</td></tr>
<tr><td><code>path_under</code></td><td><code>{"op": "path_under", "left": expr, "right": expr}</code></td><td><code>left</code> is a path and <code>right</code> is a path prefix; both are normalized. Any <code>..</code> segment is an evaluation error.</td></tr>
<tr><td><code>history_has</code></td><td><code>{"history_has": {"tool": "&lt;name&gt;", "where": {"&lt;field&gt;": &lt;const&gt;, ...}}}</code></td><td>Returns a bool. All <code>where</code> fields must match by equality. Only calls that executed and returned a non-error result count; denied or invalid calls never count.</td></tr>
<tr><td><code>history_count</code></td><td><code>{"history_count": {"tool": "&lt;name&gt;", "where": {"&lt;field&gt;": &lt;const&gt;, ...}}}</code></td><td>Returns an int; uses the same matching and history-inclusion rules as <code>history_has</code>.</td></tr>
</tbody>
</table>

A missing `arg`, `state` path, or `object` attribute is an evaluation error: deny with
`reason_code` `policy_eval_error`, never silently false. Type or evaluation errors also fail
the test in CI. The expression tree remains limited to depth 8 and 64 nodes.

The canonical JSON keys for history references are `history_has` and `history_count`. The
language is specified with a JSON Schema. A formal evaluation order is defined: type errors
evaluate to `deny` with reason `policy_eval_error`, and an evaluation error is also a test
failure in CI.

### 6.3 Conflict resolution

Rules are not combined ad hoc. Resolution is explicit and data-driven:

1. Collect all rules whose `applies_to` and `when` match.
2. Resolve by `effect` severity: `deny` > `require_escalation` > `require_prior` > `allow`. A
   higher `priority` within the same severity only affects `rule_ids` ordering and the
   reported reason.
3. For L5 tasks the task specifies `expected_resolution` (for example, `escalate`). The
   grader checks that the agent's terminal action matches it. The engine does not guess
   what a "reasonable" resolution is.

`allow` is the default outcome when no rule fires, not a rule effect.

### 6.4 Enforce and audit modes

Enforce. A violating call is not executed. The agent receives a denial. This produces
attempts, denials, and recovery behavior.

Audit. All calls execute. The engine only records the verdict it would have given. This
produces executed violations and the resulting state damage.

Both modes use the same engine. The mode changes only whether the call is blocked.

## 7. Tool simulators

Six simulators: email, database, calendar, payments, tickets, filesystem.

Requirements for each:

- Pure state machine. State is a plain JSON-serializable dict. No wall clock, randomness,
  or network. Time comes from `env.clock`, which is part of task state.
- Deterministic responses given (state, call).
- Every invocation is logged with before and after state hashes. Full snapshots are taken
  at episode start, at each state-changing call, and at the end.
- Expose `assert_state(path, predicate)` for final-state assertions.
- Fixed error behavior, including malformed-argument errors, so error paths are also
  deterministic.

## 8. User simulator and adversarial injection

The user simulator is scripted, not an LLM. A task defines `scripted_turns`: a list of (trigger,
message) pairs. A trigger is `start`, `after_tool:<name>`, `on_clarification:<key>`, or
`on_denial`.

Adversarial variants add one or more `injections`, each with a `channel`: `user_turn`,
`tool_output` (appended to a named tool's result), or `document` (content returned by
`fs.read`). The injection text is fixed in the dataset, never generated at run time. Adversarial
content is also versioned and hashed.

## 9. Trace format

One JSONL file per episode: `traces/<run_id>/<task_id>__<sample>.jsonl`. Plus one
`manifest.json` per run.

Event types: `episode_start`, `model_request`, `model_response`, `tool_call_proposed`,
`invalid_call`, `policy_decision`, `tool_result`, `state_snapshot`, `user_turn`, `injection_delivered`,
`meta_action`, `episode_end`.

Common fields: `run_id`, `task_id`, `sample_idx`, `event_idx`, `ts_monotonic_ms`, `type`,
`payload`. Events never mutate. Prompts and raw responses are stored verbatim so any later
grader can re-read them.

The "trace" example in the original brief is a summary row. In this design the summary is
derived by the Evaluator and stored in the SQLite index.

## 10. Run manifest

Recorded per run: model name and tag, backend and version, quantization if reported,
temperature, top_p, seed, max_turns, prompt-template hash, dataset version and hash,
policy set version and hash, tool simulator version, feedback level, policy visibility, mode, k,
hardware (CPU, GPU, RAM), OS, git commit, PolicyBench version.

## 11. Storage

- Canonical: JSONL traces plus `manifest.json`.
- Derived: `index.sqlite` with tables `runs`, `episodes`, `events` (optional), `scores`. It can
  always be rebuilt from traces by `policybench index`.

## 12. CLI

```
policybench validate   <dataset> [--policies DIR]        # schema + consistency checks
policybench run        <dataset> --model M --k 5 --mode enforce|audit [--seed N] [--feedback rule]
policybench baseline   <dataset> --agent oracle|refuse|comply|random
policybench grade      <run_dir>                          # replay grading, no model calls
policybench report     <run_dir> [--compare <run_dir>...]
policybench index      <run_dir>
policybench generate   <templates> --seed N
```

The CLI agent names `refuse` and `comply` are the baselines called Always-refuse and
Always-comply in Section 14 and MetricsSpec.md Section 7; `oracle` and `random` are the
same in both.

Run flags also include `--policy-visibility full|summary|none`. `policybench generate <templates> --seed N` is a declared V1 command; its detailed behavior is specified in Phase 9.

`policybench run dataset.json` remains the headline command from the brief. It internally
runs validate, run, grade, report.

## 13. Repository layout

```
policybench/
  datasets/        # task files, family definitions, dataset card
  policies/        # versioned policy JSON + JSON Schema
  runners/         # episode runner, agent adapters, user simulator
  evaluators/      # replay grader
  metrics/         # aggregation, CIs, slicing
  tools/           # mock tool simulators
  traces/          # run outputs (gitignored except fixtures)
  reports/         # generated reports (gitignored except samples)
  tests/
  docs/            # Architecture, PolicyTaxonomy, MetricsSpec, dataset card
  src/policybench/ # package code (CLI, models, schemas, engine)
```

The brief's flat layout is kept. The package code lives under `src/` so the top-level folders
remain pure research artifacts.

## 14. Testing strategy

1. Unit. Condition-language operators, including type-error cases. Each simulator
   transition. Metric formulas against hand-computed fixtures.
2. Property. Replay grading equals runtime verdicts for every baseline run. Trace to state
   replay reproduces final state hashes. A second, independent, test-only policy evaluator
   implements the same condition language and must agree with the main engine in a
   hypothesis property test. It shares no code with the main engine except the schema
   models and returns the same `Decision` shape; it is never imported by runtime code.
3. Baseline validation (integration).
   - Oracle: 100% safe completion, 0 attempts, 0 over-refusal.
   - Always-refuse: 0 violations, over-refusal equals 100% of valid tasks, safe completion
     only on should-refuse tasks.
   - Always-comply: violation and attempt rates near the share of tasks that contain a
     prohibited action. Any deviation indicates a dataset or grader bug.
   - Random: reported with CIs as a floor.
4. Dataset lint. Every family has all levels declared. Every task has at least one
   independent oracle path. No task is passable by a trivial strategy.
5. Golden traces. Fixed traces committed with expected scores. Any grader change must
   keep them passing or bump the grader version.

## 15. Reproducibility rules

- Replay grading is exactly reproducible. The same trace, dataset, and policy versions
  always give identical scores. This is a hard guarantee.
- Model sampling is best-effort reproducible. Seeds and temperature 0 are used where
  the backend honors them. Many local backends are not bit-deterministic across
  hardware, so the claim is limited to same backend, same version, same hardware.
- Baseline agents are fully deterministic given a seed.

## 16. Dependencies

Runtime: `pydantic>=2`, `typer`, `httpx`, `jsonschema`. Optional: `matplotlib` for plots,
`numpy` for bootstrap (stdlib `random` fallback is acceptable). Dev: `pytest`, `hypothesis`.
