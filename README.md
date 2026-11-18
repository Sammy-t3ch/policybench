# PolicyBench

PolicyBench is a research-grade, open-source benchmark for measuring how the policy
compliance of tool-using AI agents changes as policy complexity increases.

It is a **CLI-first, local-first benchmark and evaluation framework**. Grading is
deterministic and replayable from JSONL traces; there is no LLM-as-judge, no free-text
decision parsing, and no network calls from the mock tool simulators.

It is **not** an application, a SaaS product, a hosted service, or an agent framework.
V1 has no web UI, authentication, user model, or billing. The repository contains no
production credentials and connects to no production services.

## Status

Phase 2 (schemas) is implemented on a feature branch and awaiting review: Pydantic v2
models are the single source of truth, the JSON Schemas under `schemas/` are generated from
them (with a drift test), the dataset and policy loaders exist, and `policybench validate`
runs schema, `policy_refs`, family-lint, `recoverable`, `required_escalation_fields` and
`policy_visibility`/mode checks. **No policy engine, tool simulators, runner, grader,
metrics or dataset are implemented yet.** See the
[phase issues](https://github.com/Sammy-t3ch/policybench/issues).

```sh
policybench validate tests/fixtures/datasets/refund_family.json --policies tests/fixtures/policies
python -m policybench.schemas_export --check   # fail if committed schemas drift
```

## Design documents

The approved design is v0.2.1. The Markdown files in [`docs/`](docs/) are the editable
source for design changes (via docs PRs); the PDFs in
[`docs/design-pdfs/`](docs/design-pdfs/) are byte-for-byte frozen v0.2 originals.

- [Architecture.md](docs/Architecture.md) — components, agent-environment protocol, policy engine, trace format, CLI, repo layout, tests
- [PolicyTaxonomy.md](docs/PolicyTaxonomy.md) — levels L1–L5, adversarial axis A0–A4, matched families, condition language
- [MetricsSpec.md](docs/MetricsSpec.md) — per-episode flags, metrics, statistics, baseline expectations
- [Critique.md](docs/Critique.md) — why the design is the way it is, and remaining risks
- [Changelog.md](docs/Changelog.md) — v0.1 → v0.2 changes, the v0.2.1 fixes, and the open questions
- [DECISIONS.md](docs/DECISIONS.md) — choices not fully dictated by the attached design

## Quickstart (clean clone, Phase 0)

Requires Python 3.12 (the only supported version).

```sh
git clone https://github.com/Sammy-t3ch/policybench.git
cd policybench
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
ruff check .
mypy
```

There is nothing to run yet beyond the test suite and the CI checks. Once V1 is complete,
the headline command will be:

```sh
policybench run dataset.json --model <name> --k 5 --mode enforce
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
Work happens in small, reviewable phases; each phase is one feature branch and one PR,
and no phase starts before the previous PR is merged and explicitly approved.

## License

MIT — see [LICENSE](LICENSE).
