# PolicyBench

PolicyBench measures how the policy compliance of tool-using AI agents changes as policy
complexity increases.

It is a research-grade, open-source benchmark and evaluation framework. Its unit of work is a
**trace**: an append-only JSONL record of one episode. Every score is recomputed from traces by
deterministic, programmatic grading — no LLM-as-judge, no parsing of free text.

## What it is not

- Not an application, a SaaS product, or a hosted service.
- Not an agent framework. It wraps existing models behind a thin adapter.
- Not a UI. V1 is CLI-only and local-first: no web interface, authentication, user model,
  billing, or database server.

## Status

**Phase 0 (foundation) only.** The design is complete as v0.2 and approved; implementation
proceeds phase by phase, one pull request per phase. There is no runnable CLI yet — the
commands in the design documents describe the target, not the current state.

| Phase | Scope |
| --- | --- |
| 0 | Repository scaffold, archival design PDFs, Markdown transcriptions, CI, templates |
| 2 | Schemas (Task, Family, Policy, Condition, Trace events, Manifest, RunScore), loader, `policybench validate` |
| 3 | Policy engine, condition evaluator, independent test-only evaluator |
| 4 | Mock tools, scripted user simulator, adversarial injection channels |
| 5 | Trace logger, manifest writer, SQLite index, `policybench index` |
| 6 | Replay evaluator, `policybench grade`, golden-trace tests |
| 7 | Metrics engine, confidence intervals, slicing, paired analysis |
| 8 | Adapters and episode runner, baselines, `policybench run`, `policybench baseline` |
| 9 | Dataset v0.1, dataset card, generator, report generator |

## Design documents

The design is the single source of truth for this repository. It lives in `docs/`:

- [Architecture](docs/Architecture.md) — components, agent-environment protocol, policy engine,
  trace format, CLI, repository layout, testing, reproducibility
- [PolicyTaxonomy](docs/PolicyTaxonomy.md) — complexity levels L1–L5, adversarial axis A0–A4,
  matched families, condition language reference
- [MetricsSpec](docs/MetricsSpec.md) — per-episode flags, every metric, statistics, baseline
  expectations
- [Critique](docs/Critique.md) — self-critique of the v0.1 design and how v0.2 responds
- [Changelog](docs/Changelog.md) — v0.1 → v0.2 changes and open questions

The frozen originals are archived unchanged in [`docs/design-pdfs/`](docs/design-pdfs/). The
Markdown files are verbatim transcriptions of those PDFs and are the editable source for future
design changes, which happen as docs PRs — never silently in code.

Decisions taken outside the design documents (including answers to the open questions) are
recorded in [docs/DECISIONS.md](docs/DECISIONS.md).

## Development quickstart

Requires Python 3.12.

```bash
git clone https://github.com/Sammy-t3ch/policybench.git
cd policybench
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
ruff check . && ruff format --check . && mypy
```

The benchmark itself will run offline against local models (Ollama, LM Studio, or any
OpenAI-compatible endpoint) once the runner lands in Phase 8. PolicyBench never contacts
production services and never stores credentials.

## Repository layout

The layout follows Architecture v0.2 Section 13:

```text
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

The top-level research folders are kept as the brief specified; importable code lives under
`src/policybench/`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and the
[Code of Conduct](CODE_OF_CONDUCT.md). One branch and one pull request per phase; the maintainer
merges.

## License

MIT. See [LICENSE](LICENSE).
