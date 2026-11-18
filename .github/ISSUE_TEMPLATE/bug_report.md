---
name: Bug report
about: Something is incorrect: a crash, a wrong verdict, a wrong metric, a non-reproducible score
title: "bug: "
labels: ""
assignees: ""
---

## What happened

<!-- The observed behaviour. -->

## What you expected

<!-- The expected behaviour, and the design section that says so
     (docs/Architecture.md, docs/PolicyTaxonomy.md, docs/MetricsSpec.md). -->

## Reproduction

<!-- Minimal repro. For grading bugs: the run directory, task id, policy id, and the
     trace lines involved. Do not attach secrets or anything containing credentials. -->

```bash
# commands
```

- PolicyBench version / commit:
- Python version:
- OS:
- Backend and model (if a model was involved):

## Is this a determinism failure?

<!-- Replay grading is exactly reproducible (Architecture §15). If two grades of the same
     trace disagree, that is a hard-guarantee violation: say so. -->

- [ ] Re-running `policybench grade` on the same traces gives a different result.
- [ ] A baseline agent violates the expectations in MetricsSpec §7.
- [ ] Other.

## Additional context

<!-- Nothing else? Write "none". -->
