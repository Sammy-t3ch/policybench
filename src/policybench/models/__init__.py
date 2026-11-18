"""Pydantic models: the single source of truth for every PolicyBench schema.

The JSON Schemas under ``schemas/`` are generated from these models
(``python -m policybench.schemas_export``) and a test fails if they drift.
"""

from policybench.models.base import SCHEMA_VERSION, JsonValue, StrictModel, VersionedModel
from policybench.models.condition import (
    MAX_EXPR_DEPTH,
    MAX_EXPR_NODES,
    Expr,
    expr_limits,
    parse_condition,
)
from policybench.models.policy import Policy, PolicyEffect, PolicySet
from policybench.models.run import (
    Feedback,
    Manifest,
    Mode,
    PolicyVisibility,
    RunConfig,
    RunScore,
)
from policybench.models.task import (
    ALL_LEVELS,
    AdversarialVariant,
    ComplexityCovariates,
    ComplexityLevel,
    Dataset,
    Domain,
    ExpectedResolution,
    Family,
    Injection,
    InjectionChannel,
    ScriptedTurn,
    StateAssertion,
    Task,
    TaskLabel,
    ToolCall,
    TriggerKind,
)
from policybench.models.trace import (
    EventType,
    InvalidCallEvent,
    Termination,
    TraceEvent,
    Verdict,
)

__all__ = [
    "ALL_LEVELS",
    "MAX_EXPR_DEPTH",
    "MAX_EXPR_NODES",
    "SCHEMA_VERSION",
    "AdversarialVariant",
    "ComplexityCovariates",
    "ComplexityLevel",
    "Dataset",
    "Domain",
    "EventType",
    "ExpectedResolution",
    "Expr",
    "Family",
    "Feedback",
    "Injection",
    "InjectionChannel",
    "InvalidCallEvent",
    "JsonValue",
    "Manifest",
    "Mode",
    "Policy",
    "PolicyEffect",
    "PolicySet",
    "PolicyVisibility",
    "RunConfig",
    "RunScore",
    "ScriptedTurn",
    "StateAssertion",
    "StrictModel",
    "Task",
    "TaskLabel",
    "Termination",
    "ToolCall",
    "TraceEvent",
    "TriggerKind",
    "Verdict",
    "VersionedModel",
    "expr_limits",
    "parse_condition",
]
