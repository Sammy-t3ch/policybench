# Contributing to PolicyBench

PolicyBench is built in small, reviewable phases. Please read the design in
[`docs/`](docs/) before proposing changes.

## Approval gates

- Work proceeds **one phase at a time**. A later phase starts only after the previous
  phase's PR has been merged by the maintainer and the maintainer replies `go phase N`.
- One feature branch and one PR per phase. **Never push to `main`.**
- Use [Conventional Commits](https://www.conventionalcommits.org/) (for example
  `docs: transcribe Architecture.pdf`, `chore: scaffold Phase 0 layout`).
- Do not merge your own PRs. Leave review and merge to the maintainer.
- Each PR description states: what changed, which sections of which attached design file
  it implements, test results, known gaps, and decisions needed from the maintainer.
- Be honest about failing tests, shortcuts, and incomplete work.

## Design changes

- The PDFs in [`docs/design-pdfs/`](docs/design-pdfs/) are frozen archival originals.
  Never edit them.
- The Markdown files in [`docs/`](docs/) are the editable source. **Any design change
  must be a docs PR first**, never a silent change in code.
- If code and the design disagree, the design wins. If the design is ambiguous or wrong,
  stop and ask; do not guess.
- Record every choice not fully dictated by the design in
  [`docs/DECISIONS.md`](docs/DECISIONS.md).

## Hard rules

- JSONL traces are the source of truth; SQLite is a derived, rebuildable index only.
- Deterministic, programmatic grading only. No LLM-as-judge. Free text is never parsed
  for decisions.
- Policy is data: versioned JSON, restricted condition language, JSON Schema validated.
  Never hardcode policies.
- Mock tool simulators only: pure, seedable, no network, no wall clock, no randomness
  outside the seed.
- Stack: Python 3.12, Pydantic v2, Typer, Pytest, stdlib `sqlite3`, `httpx`,
  `jsonschema`. Adding anything else requires a written justification in the PR
  description.
- Never commit secrets or real credentials. Never connect to production services.
- No web UI, auth, user model, or billing in V1.

## Local checks

Python 3.12 is the only supported version.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
ruff check .
mypy
pytest
```

CI runs the same checks on every PR. Add tests with every behavioural change; metric
formulas need hand-computed fixtures and grader changes must keep the golden traces
passing or bump the grader version.

## Issues and PRs

Use the issue templates in [`.github/ISSUE_TEMPLATE/`](.github/ISSUE_TEMPLATE/) and the
PR template in [`.github/pull_request_template.md`](.github/pull_request_template.md).
One issue exists per later phase, with acceptance criteria quoted from the design.
