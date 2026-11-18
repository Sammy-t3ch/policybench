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

Phase 0 (foundation) only. The layout, the frozen design PDFs, their verbatim Markdown
transcriptions, project metadata, and CI are in place. **No CLI commands, schemas,
policy engine, simulators, evaluator, metrics, or dataset are implemented yet.** The
`policybench` command will appear in later phases; see the [phase issues](https://github.com/Sammy-t3ch/policybench/issues).

## Design documents

The approved design is v0.2. The Markdown files in [`docs/`](docs/) are the editable
source for design changes (via docs PRs); the PDFs in
[`docs/design-pdfs/`](docs/design-pdfs/) are byte-for-byte frozen archival originals.

- [Architecture.md](docs/Architecture.md) — components, agent-environment protocol, policy engine, trace format, CLI, repo layout, tests
- [PolicyTaxonomy.md](docs/PolicyTaxonomy.md) — levels L1–L5, adversarial axis A0–A4, matched families, condition language
- [MetricsSpec.md](docs/MetricsSpec.md) — per-episode flags, metrics, statistics, baseline expectations
- [Critique.md](docs/Critique.md) — why the design is the way it is, and remaining risks
- [Changelog.md](docs/Changelog.md) — v0.1 → v0.2 changes and the open questions
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
