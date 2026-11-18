# PolicyBench

**PolicyBench** is a research-grade, CLI-first, local-first benchmark and evaluation framework for measuring how the policy compliance of tool-using AI agents changes as policy complexity increases.

## What PolicyBench Is

- **A benchmark and evaluation framework** for tool-using AI agents across five policy complexity levels (`L1`–`L5`) and an orthogonal adversarial pressure axis (`A0`–`A4`), organized into matched task families across six domains (`payments`, `email`, `database`, `calendar`, `tickets`, `filesystem`).
- **Deterministic and replayable**: canonical append-only JSONL traces are the source of truth (with SQLite used strictly as a derived, rebuildable index). Grading is a pure function of `(trace, task, policies)`—no LLM-as-judge and no free-text decision parsing.
- **Policy as versioned data**: rules live in JSON Schema-validated policy files using a restricted, strictly typed, non-Turing-complete condition language, evaluated in both `enforce` and `audit` modes.
- **Safe and local-first**: pure, seedable mock tool simulators (no network, no wall clock, no external side effects) and a single OpenAI-compatible function-calling client targeting Ollama, LM Studio, and compatible endpoints, validated by four built-in baseline agents (`oracle`, `always-refuse`, `always-comply`, `random`).

## What PolicyBench Is Not

- **Not** an application, SaaS product, hosted service, or general-purpose agent framework.
- **No** web UI, authentication, user model, or billing in V1.
- **No** LLM-as-judge grading, free-text decision parsing, or connections to real/production services.
- **No** constrained-JSON fallback adapter for models lacking native function calling in V1.

## Documentation

The approved v0.2 design lives in [`docs/`](docs/):

- [`docs/Architecture.md`](docs/Architecture.md) — system overview, components, agent-environment protocol, policy engine, mock simulators, trace and manifest format, CLI, repository layout, testing, reproducibility, and dependencies.
- [`docs/PolicyTaxonomy.md`](docs/PolicyTaxonomy.md) — complexity levels `L1`–`L5`, adversarial variants `A0`–`A4`, matched task families, complexity covariates, validity labels, condition language reference, and dataset construction guidelines.
- [`docs/MetricsSpec.md`](docs/MetricsSpec.md) — unit definitions, per-episode flags, headline metrics (`Safe Completion Rate`, `Policy Violation Rate`, `Attempted Violation Rate`, `Over-Refusal Rate`, `Recovery Rate`, `pass^k` and `pass@k`, latency), slicing, paired degradation analysis, cluster bootstrap statistics, baseline expectations, and output artifacts.
- [`docs/Critique.md`](docs/Critique.md) — self-critique of v0.1, threats to validity, resolutions reflected in v0.2, and open risks.
- [`docs/Changelog.md`](docs/Changelog.md) — v0.1-to-v0.2 design changes and open questions.
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — maintainer decisions answering the v0.2 open questions and engineering choices not fully specified by the design PDFs.
- [`docs/design-pdfs/`](docs/design-pdfs/) — frozen archival PDF originals of the five v0.2 design documents.

Any change to the design is made as a documentation PR to `docs/*.md` first, never silently in code.

## Project Status

PolicyBench is currently at **Phase 0 (Foundation)**: repository scaffold, archival design PDFs, verbatim Markdown design specifications, packaging, CI, and contribution templates. Implementation proceeds phase by phase (Schemas → Policy Engine → Mock Tools → Trace Logger → Evaluator → Metrics Engine → Adapters & Runner → Dataset v0.1 & Report) via small, reviewable pull requests.

## Repository Layout

```
policybench/
  datasets/        # task files, family definitions, dataset card
  policies/        # versioned policy JSON + JSON Schema
  runners/         # episode runner, agent adapters, user simulator
  evaluators/      # replay grader
  metrics/         # aggregation, CIs, slicing
  tools/           # mock tool simulators
  traces/          # run outputs (gitignored except fixtures)
  reports/         # generated reports (gitignored except fixtures/samples)
  tests/
  docs/            # Architecture, PolicyTaxonomy, MetricsSpec, Critique, Changelog, DECISIONS
  src/policybench/ # package code (CLI, models, schemas, engine)
```

## Development Quickstart

Requires **Python 3.12**.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"

# Verify CLI, lint, types, and tests
policybench --version
ruff check src tests
ruff format --check src tests
mypy src tests
pytest
```

## Contributing and Governance

- Contribution workflow and engineering rules: [`CONTRIBUTING.md`](CONTRIBUTING.md)
- Community standards: [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)
- License: [MIT](LICENSE)
