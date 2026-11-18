"""Phase 2: the Pydantic models are the single source of truth for the schemas.

Each test name cites the design section or maintainer instruction it enforces.
"""

from __future__ import annotations

import json

import pytest
from pydantic import TypeAdapter, ValidationError

from policybench.json_schemas import SCHEMA_NAMES, load_schema, validate_document
from policybench.loader import load_dataset, load_policies
from policybench.models.base import SCHEMA_VERSION
from policybench.models.condition import (
    MAX_EXPR_DEPTH,
    MAX_EXPR_NODES,
    OPERATOR_TAGS,
    REFERENCE_TAGS,
    expr_limits,
    parse_condition,
)
from policybench.models.policy import Policy, PolicySet
from policybench.models.run import (
    Manifest,
    Mode,
    PolicyVisibility,
    RunConfig,
    RunScore,
)
from policybench.models.task import Dataset, Family, Task
from policybench.models.trace import EventType, TraceEvent
from policybench.schemas_export import build_schema, render

#: model/adapter per committed schema name (see policybench.schemas_export).
ADAPTERS: dict[str, TypeAdapter[object] | type[object]] = {
    "condition": TypeAdapter(object),
    "policy": Policy,
    "task": Task,
    "family": Family,
    "dataset": Dataset,
    "trace_event": TypeAdapter(TraceEvent),
    "run_config": RunConfig,
    "manifest": Manifest,
    "run_score": RunScore,
}


def test_committed_schemas_are_generated_from_the_models() -> None:
    """Phase 2 constraint 1: committed schemas must not drift from the models."""
    from pathlib import Path

    schema_dir = Path(__file__).resolve().parents[1] / "schemas"
    committed = sorted(path.name for path in schema_dir.glob("*.schema.json"))
    assert committed == sorted(f"{name}.schema.json" for name in SCHEMA_NAMES)
    for name in SCHEMA_NAMES:
        path = schema_dir / f"{name}.schema.json"
        assert path.read_text(encoding="utf-8") == render(name), (
            f"{path.name} is out of sync with the models; "
            "run `python -m policybench.schemas_export`"
        )


def test_every_schema_carries_the_schema_version() -> None:
    """Phase 2 constraint 3: every schema carries ``schema_version``."""
    for name in SCHEMA_NAMES:
        schema = build_schema(name)
        assert schema["x-policybench-schema-version"] == SCHEMA_VERSION
        if name == "run_config":
            # RunConfig is also embedded in the manifest; it has no version key of
            # its own (see the PR "needs decision" list).
            continue
        # condition is a bare expression node (no envelope, so no version key:
        # see the PR "needs decision" list). trace_event is a union whose
        # branches each carry the key inside $defs.
        assert schema["x-policybench-schema-version"] == SCHEMA_VERSION
        if name == "condition":
            continue
        if "properties" in schema:
            assert schema["properties"]["schema_version"]["const"] == SCHEMA_VERSION, name
        else:
            assert any(
                branch.get("properties", {}).get("schema_version", {}).get("const")
                == SCHEMA_VERSION
                for branch in schema["$defs"].values()
            ), name


def test_policy_files_carry_id_and_integer_version() -> None:
    """Phase 2 constraint 3: policy files carry ``id`` and an integer ``version``."""
    schema = build_schema("policy")
    assert set(schema["properties"]) >= {"id", "version", "schema_version"}
    assert schema["properties"]["version"]["type"] == "integer"
    policy = Policy.model_validate(
        {
            "schema_version": SCHEMA_VERSION,
            "id": "pay.max_refund",
            "version": 3,
            "applies_to": ["payments.refund"],
            "effect": "deny",
            "priority": 10,
            "when": {"const": True},
        }
    )
    assert policy.version == 3


def test_task_files_carry_dataset_version() -> None:
    """Phase 2 constraint 3: task files carry ``dataset_version``."""
    schema = build_schema("task")
    assert "dataset_version" in schema["required"]
    assert "dataset_version" in build_schema("dataset")["required"]


def test_unknown_keys_are_rejected_everywhere() -> None:
    """PolicyTaxonomy Section 6: unknown keys fail validation at load time."""
    with pytest.raises(ValidationError):
        Policy.model_validate(
            {
                "schema_version": SCHEMA_VERSION,
                "id": "pay.x",
                "version": 1,
                "applies_to": ["payments.refund"],
                "effect": "deny",
                "priority": 1,
                "when": {"const": True},
                "unexpected": "key",
            }
        )


@pytest.mark.parametrize("name", sorted(set(OPERATOR_TAGS) | set(REFERENCE_TAGS)))
def test_every_operator_has_a_valid_and_an_invalid_shape(name: str) -> None:
    """Phase 2 constraint 2: every operator, one valid and one invalid shape."""
    valid = VALID_SHAPES[name]
    parse_condition(valid)

    invalid = INVALID_SHAPES[name]
    with pytest.raises((ValidationError, ValueError, TypeError)):
        parse_condition(invalid)


VALID_SHAPES: dict[str, dict[str, object]] = {
    "and": {"op": "and", "args": [{"const": True}, {"const": False}]},
    "or": {"op": "or", "args": [{"const": True}, {"const": False}]},
    "not": {"op": "not", "arg": {"const": True}},
    "eq": {"op": "eq", "left": {"arg": "amount"}, "right": {"const": 500}},
    "neq": {"op": "neq", "left": {"actor": "role"}, "right": {"const": "agent"}},
    "lt": {"op": "lt", "left": {"arg": "amount"}, "right": {"const": 10}},
    "lte": {"op": "lte", "left": {"arg": "amount"}, "right": {"const": 10}},
    "gt": {"op": "gt", "left": {"arg": "amount"}, "right": {"const": 10}},
    "gte": {"op": "gte", "left": {"arg": "amount"}, "right": {"const": 10}},
    "in": {"op": "in", "left": {"state": "customer.tier"}, "right": {"const": ["gold"]}},
    "not_in": {"op": "not_in", "left": {"state": "customer.tier"}, "right": {"const": ["gold"]}},
    "domain_in": {"op": "domain_in", "left": {"arg": "to"}, "right": {"const": ["example.com"]}},
    "startswith": {"op": "startswith", "left": {"arg": "subject"}, "right": {"const": "[EXT]"}},
    "path_under": {"op": "path_under", "left": {"arg": "path"}, "right": {"const": "/data"}},
    "arg": {"arg": "amount"},
    "state": {"state": "customer.verified"},
    "actor": {"actor": "role"},
    "object": {"object": "sensitivity"},
    "history_has": {"history_has": {"tool": "customer.verify", "where": {"id": "cust_700"}}},
    "history_count": {"history_count": {"tool": "customer.verify", "where": {}}},
    "const": {"const": 500},
}

INVALID_SHAPES: dict[str, dict[str, object]] = {
    "and": {"op": "and", "args": [{"const": True}]},
    "or": {"op": "or", "args": []},
    "not": {"op": "not"},
    "eq": {"op": "eq", "left": {"arg": "amount"}},
    "neq": {"op": "neq", "right": {"const": 1}},
    "lt": {"op": "lt", "left": {"arg": "amount"}, "right": {"const": 1}, "extra": 0},
    "lte": {"op": "lte", "left": {"arg": "amount"}, "right": {"const": 1}, "extra": 0},
    "gt": {"op": "gt", "left": {"arg": "amount"}, "right": {"const": 1}, "extra": 0},
    "gte": {"op": "gte", "left": {"arg": "amount"}, "right": {"const": 1}, "extra": 0},
    "in": {"op": "in", "left": {"state": "customer.tier"}},
    "not_in": {"op": "not_in", "right": {"const": ["gold"]}},
    "domain_in": {"op": "domain_in", "left": {"arg": "to"}, "right": {"const": ["example.com"]}, "x": 1},
    "startswith": {"op": "startswith", "left": {"arg": "subject"}},
    "path_under": {"op": "path_under", "right": {"const": "/data"}},
    "arg": {"arg": 5},
    "state": {"state": ["a"]},
    "actor": {"actor": 1},
    "object": {"object": None},
    "history_has": {"history_has": {"tool": "customer.verify"}},
    "history_count": {"history_count": {"tool": "customer.verify", "where": {}, "limit": 1}},
    "const": {"const": 1, "op": "gt"},
}


def test_unknown_operator_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown operator"):
        parse_condition({"op": "between", "left": {"arg": "a"}, "right": {"const": 1}})


def test_expression_needs_exactly_one_canonical_key() -> None:
    with pytest.raises(ValueError):
        parse_condition({"arg": "amount", "const": 500})
    with pytest.raises(ValueError):
        parse_condition({"amount": 500})


def test_depth_and_node_limits_are_exact() -> None:
    """PolicyTaxonomy Section 6: depth 8 and 64 nodes."""
    deep: dict[str, object] = {"const": 1}
    for _ in range(MAX_EXPR_DEPTH - 1):
        deep = {"op": "not", "arg": deep}
    assert expr_limits(deep) == (MAX_EXPR_DEPTH, MAX_EXPR_DEPTH)
    parse_condition(deep)
    too_deep = {"op": "not", "arg": deep}
    assert expr_limits(too_deep)[0] == MAX_EXPR_DEPTH + 1
    with pytest.raises(ValueError, match="depth"):
        parse_condition(too_deep)

    at_limit = {"op": "and", "args": [{"const": i} for i in range(MAX_EXPR_NODES - 1)]}
    assert expr_limits(at_limit) == (2, MAX_EXPR_NODES)
    parse_condition(at_limit)
    over = {"op": "and", "args": [{"const": i} for i in range(MAX_EXPR_NODES)]}
    with pytest.raises(ValueError, match="nodes"):
        parse_condition(over)


def test_policy_condition_limits_apply_through_the_policy_model() -> None:
    over = {"op": "and", "args": [{"const": i} for i in range(MAX_EXPR_NODES)]}
    with pytest.raises(ValidationError):
        Policy.model_validate(
            {
                "schema_version": SCHEMA_VERSION,
                "id": "pay.big",
                "version": 1,
                "applies_to": ["payments.refund"],
                "effect": "deny",
                "priority": 1,
                "when": over,
            }
        )


def test_allow_is_not_a_policy_effect() -> None:
    """Architecture Section 6.3: "`allow` is the default outcome ... not a rule effect"."""
    with pytest.raises(ValidationError):
        Policy.model_validate(
            {
                "schema_version": SCHEMA_VERSION,
                "id": "pay.x",
                "version": 1,
                "applies_to": ["payments.refund"],
                "effect": "allow",
                "priority": 1,
                "when": {"const": True},
            }
        )


def test_policy_set_rejects_duplicate_ids() -> None:
    rule = {
        "schema_version": SCHEMA_VERSION,
        "id": "pay.dup",
        "version": 1,
        "applies_to": ["payments.refund"],
        "effect": "deny",
        "priority": 1,
        "when": {"const": True},
    }
    with pytest.raises(ValidationError):
        PolicySet(policies=[Policy.model_validate(rule), Policy.model_validate(rule)])


def test_trace_event_includes_invalid_call() -> None:
    """Architecture Section 9 lists `invalid_call` as an event type."""
    assert EventType.INVALID_CALL.value == "invalid_call"
    schema = build_schema("trace_event")
    assert "invalid_call" in json.dumps(schema)
    event: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": "run-1",
        "task_id": "task-1",
        "sample_idx": 0,
        "event_idx": 3,
        "ts_monotonic_ms": 10,
        "type": "invalid_call",
        "payload": {
            "call_id": "c1",
            "tool": "payments.refund",
            "args": {"amount": "700"},
            "errors": ["amount: expected number"],
            "returned_as_tool_error": True,
        },
    }
    assert TypeAdapter(TraceEvent).validate_python(event).type == "invalid_call"


def test_run_config_rejects_visibility_none_with_audit() -> None:
    """Architecture Section 5 + DECISIONS G5."""
    with pytest.raises(ValidationError):
        RunConfig(mode=Mode.AUDIT, policy_visibility=PolicyVisibility.NONE, k=1, max_turns=5)
    RunConfig(mode=Mode.ENFORCE, policy_visibility=PolicyVisibility.NONE, k=1, max_turns=5)


def test_run_score_requires_the_static_recoverable_flag() -> None:
    """Architecture Section 4 + MetricsSpec Section 2."""
    schema = build_schema("run_score")
    assert "recoverable" in schema["required"]


def test_dataset_loader_resolves_shipped_fixtures() -> None:
    """Architecture Section 4: load, validate, resolve policy_refs."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "tests/fixtures"
    dataset = load_dataset(root / "datasets/refund_family.json")
    policies = load_policies(root / "policies")
    assert len(dataset.dataset.tasks) == 9
    referenced = {ref for task in dataset.dataset.tasks for ref in task.policy_refs}
    available = {policy.id for policy in policies.policies.policies}
    assert referenced <= available
    assert dataset.sha256 and policies.sha256


def test_committed_schema_files_are_valid_json_schemas() -> None:
    for name in SCHEMA_NAMES:
        load_schema(name)  # raises if unreadable
    assert validate_document("policy", {"id": "x"})  # non-empty: missing fields
