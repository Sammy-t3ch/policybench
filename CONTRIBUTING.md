# Contributing to PolicyBench

PolicyBench is a research artifact. Correctness and reproducibility matter more than features.
Please read the design documents in `docs/` before changing anything.

## Ground rules

1. **The design documents are the source of truth.** `docs/Architecture.md`,
   `docs/PolicyTaxonomy.md`, `docs/MetricsSpec.md`, `docs/Critique.md`, and `docs/Changelog.md`
   govern the behaviour. Where code and design disagree, the design wins.
2. **Design changes are docs PRs first.** Never change the design silently in code. Open a PR
   that edits the Markdown documents, get it reviewed, then implement.
3. **The PDFs in `docs/design-pdfs/` are frozen.** Do not edit, re-generate, or replace them.
   They are the archival originals.
4. **Policy is data.** Policies are versioned JSON validated against a JSON Schema, expressed in
   a restricted, non-Turing-complete condition language. Never hardcode policy logic in Python.
5. **No LLM-as-judge, no free-text decision parsing.** Grading is a pure function of
   (trace, task, policies).
6. **Traces are canonical.** SQLite is a derived, rebuildable index. A change that makes a trace
   insufficient to reproduce a score is a bug.
7. **Determinism.** Mock tools are pure, seedable state machines: no network, no wall clock, no
   randomness outside the seed.
8. **Dependencies.** Runtime stack is fixed: Python 3.12, Pydantic v2, Typer, Pytest, stdlib
   `sqlite3`, `httpx`, `jsonschema`. Adding anything else requires a written justification in
   the PR description.
9. **Never commit secrets.** No credentials, tokens, keys, or `.env` files. PolicyBench never
   connects to production services.

## Workflow

- Work in one branch per phase and open one pull request per phase. `main` is protected: never
  push to it and never merge your own pull request.
- Do not begin the next phase until the current PR is merged and the maintainer says "go phase N".
- Use [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`,
  `test:`, `chore:`, `refactor:`, `ci:`.
- Keep pull requests small and reviewable.

Every pull request description states:

1. What changed.
2. Which sections of which design document it implements (for example, "Architecture §6").
3. Test results (commands run and their outcome).
4. Known gaps, shortcuts, and anything not done.
5. Decisions needed from the maintainer.

## Local checks

CI runs on Python 3.12 only and must be green before review:

```bash
pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy
pytest -q
```

Formatting: `ruff format .` before committing.

## Tests

- Unit: condition-language operators (including type-error cases), each simulator transition,
  metric formulas against hand-computed fixtures.
- Property: replay grading equals runtime verdicts for every baseline run; trace-to-state replay
  reproduces final state hashes.
- Integration: the four baseline agents must meet the expectations in MetricsSpec §7.
- Golden traces: committed traces with expected scores. A grader change must keep them passing or
  bump the grader version.

## Recording decisions

Any choice not fully dictated by the design documents gets an entry in
[docs/DECISIONS.md](docs/DECISIONS.md), with the date, the choice, and the reason. If the design
is ambiguous or appears wrong, stop and ask instead of guessing.
