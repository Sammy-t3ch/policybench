"""Phase 2: ``policybench validate`` checks and fixture coverage.

Maps to Phase 2 constraint 4 (schema validation, ``policy_refs`` resolution,
family lint, ``recoverable``, ``required_escalation_fields``, visibility/mode
rejection) and constraint 5 (fixtures, including the PolicyTaxonomy Section 3
refund family).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from policybench.json_schemas import SCHEMA_NAMES, validate_document
from policybench.models.condition import parse_condition
from policybench.models.policy import Policy
from policybench.models.run import (
    Feedback,
    Manifest,
    Mode,
    PolicyVisibility,
    RunConfig,
    RunScore,
)
from policybench.models.task import Dataset, Family, Task
from policybench.models.trace import TraceEvent
from policybench.validate import (
    REQUIRED_FAMILY_LABELS,
    CheckCode,
    validate_dataset,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VALID = FIXTURES / "valid"
INVALID = FIXTURES / "invalid"
DATASET = FIXTURES / "datasets/refund_family.json"
POLICIES = FIXTURES / "policies"

MODELS: dict[str, object] = {
    "policy": Policy,
    "task": Task,
    "family": Family,
    "dataset": Dataset,
    "trace_event": TypeAdapter(TraceEvent),
    "run_config": RunConfig,
    "manifest": Manifest,
    "run_score": RunScore,
}


def _accepts(schema: str, document: object) -> bool:
    if validate_document(schema, document):
        return False
    try:
        if schema == "condition":
            parse_condition(document)
        else:
            model = MODELS[schema]
            if isinstance(model, TypeAdapter):
                model.validate_python(document)
            else:  # pragma: no cover - defensive
                model.model_validate(document)  # type: ignore[attr-defined]
        return True
    except (ValidationError, ValueError):
        return False


def test_every_schema_has_at_least_two_valid_and_three_invalid_fixtures() -> None:
    """Phase 2 constraint 5."""
    for name in SCHEMA_NAMES:
        valid = sorted((VALID / name).glob("*.json"))
        invalid = sorted((INVALID / name).glob("*.json"))
        assert len(valid) >= 2, f"{name}: needs at least 2 valid fixtures, has {len(valid)}"
        assert len(invalid) >= 3, f"{name}: needs at least 3 invalid fixtures, has {len(invalid)}"


@pytest.mark.parametrize("path", sorted(VALID.glob("*/*.json")), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_valid_fixtures_are_accepted(path: Path) -> None:
    assert _accepts(path.parent.name, json.loads(path.read_text(encoding="utf-8")))


@pytest.mark.parametrize("path", sorted(INVALID.glob("*/*.json")), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_invalid_fixtures_are_rejected(path: Path) -> None:
    document = json.loads(path.read_text(encoding="utf-8"))
    assert not _accepts(path.parent.name, document), f"{path} was unexpectedly accepted"


def test_refund_family_fixture_is_complete_and_valid() -> None:
    """PolicyTaxonomy Section 3: the refund example at every level, matched."""
    report = validate_dataset(DATASET, POLICIES)
    assert report.ok, [finding.render() for finding in report.errors]
    dataset = json.loads(DATASET.read_text(encoding="utf-8"))
    levels = {task["level"] for task in dataset["tasks"]}
    assert levels == {"L1", "L2", "L3", "L4", "L5"}
    labels = {task["label"] for task in dataset["tasks"]}
    assert "valid" in labels and labels & {"should_refuse", "should_escalate"}
    assert all(task["recoverable"] in (True, False) for task in dataset["tasks"])
    variants = {task["variant"] for task in dataset["tasks"]}
    assert "A1" in variants, "the fixture should include one adversarial variant"


def test_validate_reports_ok_for_the_shipped_dataset() -> None:
    report = validate_dataset(DATASET, POLICIES)
    assert report.ok
    assert report.n_tasks == 9
    assert report.n_policies == len(list(POLICIES.glob("*.json")))


def test_validate_without_policies_directory_warns_but_passes() -> None:
    report = validate_dataset(DATASET)
    assert report.ok
    assert all(finding.code is CheckCode.POLICY_REF_MISSING for finding in report.warnings)


def test_validate_rejects_unresolved_policy_ref(tmp_path: Path) -> None:
    dataset = json.loads(DATASET.read_text(encoding="utf-8"))
    dataset["tasks"][0]["policy_refs"] = ["pay.does_not_exist"]
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps(dataset), encoding="utf-8")
    report = validate_dataset(path, POLICIES)
    assert not report.ok
    assert any(finding.code is CheckCode.POLICY_REF_MISSING for finding in report.errors)


def test_validate_warns_on_unused_policy(tmp_path: Path) -> None:
    policies = tmp_path / "policies"
    shutil.copytree(POLICIES, policies)
    extra = json.loads((POLICIES / "pay.max_refund.json").read_text(encoding="utf-8"))
    extra["id"] = "pay.unused_rule"
    (policies / "pay.unused_rule.json").write_text(json.dumps(extra), encoding="utf-8")
    report = validate_dataset(DATASET, policies)
    assert report.ok
    assert any(finding.code is CheckCode.POLICY_REF_UNUSED for finding in report.warnings)


@pytest.mark.parametrize("name", sorted(path.name for path in (FIXTURES / "invalid_family_lint").glob("*.json")))
def test_family_lint_rejects_incomplete_families(tmp_path: Path, name: str) -> None:
    """Architecture Section 14 item 4: all five levels, valid and prohibited variants."""
    family = json.loads((FIXTURES / "invalid_family_lint" / name).read_text(encoding="utf-8"))
    dataset = json.loads(DATASET.read_text(encoding="utf-8"))
    dataset["families"] = [family]
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps(dataset), encoding="utf-8")
    report = validate_dataset(path, POLICIES)
    assert not report.ok
    codes = {finding.code for finding in report.errors}
    assert codes & {
        CheckCode.FAMILY_MISSING_LEVEL,
        CheckCode.FAMILY_MISSING_LABEL,
        CheckCode.FAMILY_MISSING_PROHIBITED,
    }


def test_family_requires_valid_and_prohibited_members() -> None:
    assert set(REQUIRED_FAMILY_LABELS) == {"valid", "should_escalate"}


def test_validate_rejects_missing_recoverable_at_load(tmp_path: Path) -> None:
    """Architecture Section 4: every task carries the static ``recoverable`` flag."""
    dataset = json.loads(DATASET.read_text(encoding="utf-8"))
    dataset["tasks"][2].pop("recoverable")
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps(dataset), encoding="utf-8")
    report = validate_dataset(path, POLICIES)
    assert not report.ok
    assert any(finding.code is CheckCode.LOAD_ERROR for finding in report.errors)
    assert "recoverable" in report.errors[0].message


def test_validate_rejects_should_escalate_without_required_fields(tmp_path: Path) -> None:
    """Architecture Section 5 / PolicyTaxonomy Section 8."""
    dataset = json.loads(DATASET.read_text(encoding="utf-8"))
    task = next(item for item in dataset["tasks"] if item["label"] == "should_escalate")
    task["required_escalation_fields"] = []
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps(dataset), encoding="utf-8")
    report = validate_dataset(path, POLICIES)
    assert not report.ok
    assert "required_escalation_fields" in report.errors[0].message


def test_validate_rejects_visibility_none_with_audit_mode() -> None:
    """Architecture Section 5 + DECISIONS G5, through the validate entry point.

    ``RunConfig`` itself rejects the combination, so the rejected config is built
    with ``model_construct`` to reach the validator's own check.
    """
    config = RunConfig.model_construct(
        mode=Mode.AUDIT,
        policy_visibility=PolicyVisibility.NONE,
        feedback=Feedback.RULE,
        k=1,
        max_turns=5,
        seed=None,
    )
    report = validate_dataset(DATASET, POLICIES, config)
    assert not report.ok
    assert any(finding.code is CheckCode.RUN_PARAMS for finding in report.errors)


def test_validate_accepts_visibility_none_in_enforce_mode() -> None:
    config = RunConfig(mode=Mode.ENFORCE, policy_visibility=PolicyVisibility.NONE, k=1, max_turns=5)
    report = validate_dataset(DATASET, POLICIES, config)
    assert report.ok


def test_validate_reports_load_errors_for_bad_json(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{ not json", encoding="utf-8")
    report = validate_dataset(path, POLICIES)
    assert not report.ok
    assert report.errors[0].code is CheckCode.LOAD_ERROR


def test_validate_reports_schema_errors_for_unknown_field(tmp_path: Path) -> None:
    dataset = json.loads(DATASET.read_text(encoding="utf-8"))
    dataset["tasks"][0]["surprise"] = True
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps(dataset), encoding="utf-8")
    report = validate_dataset(path, POLICIES)
    assert not report.ok
    assert "surprise" in report.errors[0].message


def test_cli_exit_codes() -> None:
    """Architecture Section 12: ``policybench validate`` exits non-zero on failure."""
    from typer.testing import CliRunner

    from policybench.cli import app

    runner = CliRunner()
    ok = runner.invoke(app, ["validate", str(DATASET), "--policies", str(POLICIES)])
    assert ok.exit_code == 0, ok.output
    assert "OK:" in ok.output

    bad = runner.invoke(
        app,
        [
            "validate",
            str(DATASET),
            "--policies",
            str(POLICIES),
            "--mode",
            "audit",
            "--policy-visibility",
            "none",
        ],
    )
    assert bad.exit_code == 1
    assert "policy_visibility=none" in bad.output


def test_cli_json_output_is_machine_readable() -> None:
    from typer.testing import CliRunner

    from policybench.cli import app

    result = CliRunner().invoke(
        app, ["validate", str(DATASET), "--policies", str(POLICIES), "--json"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["n_tasks"] == 9
    assert payload["findings"] == []
