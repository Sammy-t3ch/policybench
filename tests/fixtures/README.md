# Phase 2 fixtures

Layout follows the maintainer's Phase 2 constraint 5: at least two valid and
three invalid examples per schema under `tests/fixtures/`, including one complete
matched family — the refund example from `docs/PolicyTaxonomy.md` Section 3.

| Path | Contents |
| --- | --- |
| `policies/*.json` | Valid policy files (one rule each) used by `policybench validate --policies`. |
| `datasets/refund_family.json` | The complete matched refund family: 5 levels x (valid, should_escalate/should_refuse), A0, plus an A1 variant. Every task carries `recoverable` and an oracle path. |
| `valid/<schema>/*.json` | Valid single-document examples per schema. |
| `invalid/<schema>/*.json` | Invalid single-document examples per schema, each rejected for a *named* reason. |

Every file here is data, not code. Fixtures are checked by
`tests/test_phase2_fixtures.py` and consumed by `tests/test_phase2_validate.py`.
