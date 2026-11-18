# Contributing to PolicyBench

Thank you for contributing to PolicyBench. This project prioritizes scientific validity, exact replay reproducibility, and small, reviewable changes.

## Core Engineering Rules

1. **Design docs first.** The specifications in [`docs/`](docs/) are the single source of truth (transcribed verbatim from the frozen originals in [`docs/design-pdfs/`](docs/design-pdfs/)). Never introduce silent design changes in code—propose a docs PR first and record non-obvious engineering choices in [`docs/DECISIONS.md`](docs/DECISIONS.md).
2. **Traces are canonical.** Append-only JSONL traces and `manifest.json` are the source of truth. SQLite (`index.sqlite`) is strictly a derived, rebuildable index.
3. **Deterministic grading only.** No LLM-as-judge. Never parse free-text prose to infer agent decisions; decisions happen exclusively through tool calls. Replay grading must be an exact pure function of `(trace, task, policies)`.
4. **Policy is data.** Never hardcode policies in Python. All policies live as versioned JSON files validated against JSON Schema in the restricted condition language.
5. **Pure mock simulators.** No network calls, no wall-clock reads, no production credentials or services, and no randomness outside explicit seeds.
6. **Minimal dependency surface.** Runtime stack is fixed to Python 3.12, Pydantic v2, Typer, stdlib `sqlite3`, `httpx`, and `jsonschema` (optional `matplotlib` and `numpy`; dev `pytest`, `hypothesis`, `ruff`, `mypy`). Adding any dependency requires an explicit written justification in the PR description and maintainer approval.
7. **Never commit secrets.** Never include API keys, tokens, credentials, or real user data in code, tests, datasets, or traces.

## Local Development Setup

PolicyBench targets **Python 3.12**.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Run the full CI suite locally before opening a pull request:

```bash
ruff check src tests
ruff format --check src tests
mypy src tests
pytest
```

## Git and Pull Request Workflow

- Never push directly to `main`.
- Keep changes focused: one feature branch and one pull request per phase or logical change.
- Use [Conventional Commits](https://www.conventionalcommits.org/) (e.g., `feat:`, `fix:`, `docs:`, `test:`, `ci:`, `chore:`).
- Fill out every section of `.github/PULL_REQUEST_TEMPLATE.md`:
  - What changed
  - Which sections of which design document(s) are implemented
  - Test results
  - Known gaps, shortcuts, or limitations (be candid)
  - Any decisions needed from the maintainer
- Generated traces (`traces/`) and reports (`reports/`) are gitignored; only minimal, intentional test fixtures (`traces/fixtures/`, `reports/fixtures/`) and sample reports (`reports/samples/`) should be committed.

## Code of Conduct

All contributors are expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
