## What changed

<!-- One paragraph, then a bullet list of the substantive changes. -->

## Design coverage

<!-- Which sections of which design documents does this PR implement?
     Example: "Architecture v0.2 §6.1–6.4; PolicyTaxonomy §6." -->

- Architecture §
- PolicyTaxonomy §
- MetricsSpec §

## Tests

<!-- Commands run and their result. Paste the pytest summary line.
     If CI is red or anything is skipped, say so here. -->

```text
$ ruff check .
$ ruff format --check .
$ mypy
$ pytest -q
```

## Known gaps and shortcuts

<!-- Be explicit. Anything not implemented, deferred, or done the cheap way. -->

## Decisions needed from the maintainer

<!-- Anything ambiguous in the design, any deviation, any open question.
     New entries in docs/DECISIONS.md go here too. -->

## Checklist

- [ ] One phase, one branch, one PR; `main` untouched.
- [ ] Conventional commit messages.
- [ ] Design documents unchanged, or changed only through this PR with the reason stated above.
- [ ] `docs/DECISIONS.md` updated for every choice not dictated by the design.
- [ ] No secrets, no credentials, no network calls to production services.
- [ ] No new dependency without a written justification above.
- [ ] CI green (ruff, type check, pytest on Python 3.12).
