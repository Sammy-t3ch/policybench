"""Trace event models (docs/Architecture.md Section 9).

"Event types: `episode_start`, `model_request`, `model_response`,
`tool_call_proposed`, `invalid_call`, `policy_decision`, `tool_result`,
`state_snapshot`, `user_turn`, `injection_delivered`, `meta_action`,
`episode_end`."

"Common fields: `run_id`, `task_id`, `sample_idx`, `event_idx`,
`ts_monotonic_ms`, `type`, `payload`. Events never mutate."

The design names the event types but does not enumerate every payload field. The
payload models below follow Section 9 ("Prompts and raw responses are stored
verbatim") and the Section 5 call pipeline; any field the design does not settle
is listed under "needs decision" in the Phase 2 PR description.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Discriminator, Field, Tag

# typing_extensions is already required by pydantic v2; it provides the
# same TypeAliasType on 3.11 as typing does on 3.12 (see docs/DECISIONS.md H9).
from typing_extensions import TypeAliasType  # noqa: UP035

from policybench.models.base import JsonValue, StrictModel, VersionedModel
from policybench.models.policy import PolicyEffect

RunId = Annotated[str, Field(min_length=1)]


class EventType(StrEnum):
    """docs/Architecture.md Section 9, in order."""

    EPISODE_START = "episode_start"
    MODEL_REQUEST = "model_request"
    MODEL_RESPONSE = "model_response"
    TOOL_CALL_PROPOSED = "tool_call_proposed"
    INVALID_CALL = "invalid_call"
    POLICY_DECISION = "policy_decision"
    TOOL_RESULT = "tool_result"
    STATE_SNAPSHOT = "state_snapshot"
    USER_TURN = "user_turn"
    INJECTION_DELIVERED = "injection_delivered"
    META_ACTION = "meta_action"
    EPISODE_END = "episode_end"


class Verdict(StrEnum):
    """docs/Architecture.md Section 4 (Decision object)."""

    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_ESCALATION = "require_escalation"


class Termination(StrEnum):
    """docs/MetricsSpec.md Section 2: "`terminal_action`, limit, or error"."""

    TERMINAL_ACTION = "terminal_action"
    LIMIT = "limit"
    ERROR = "error"


class EventBase(VersionedModel):
    run_id: RunId
    task_id: str = Field(min_length=1)
    sample_idx: int = Field(ge=0)
    event_idx: int = Field(ge=0)
    ts_monotonic_ms: int = Field(ge=0)


class EpisodeStartPayload(StrictModel):
    mode: Literal["enforce", "audit"]
    policy_visibility: Literal["full", "summary", "none"]
    seed: int
    dataset_version: str
    policy_set_version: str


class ModelRequestPayload(StrictModel):
    messages: list[JsonValue]
    tools: list[JsonValue] = Field(default_factory=list)
    params: dict[str, JsonValue] = Field(default_factory=dict)


class ModelResponsePayload(StrictModel):
    raw: JsonValue
    model: str | None = None


class ToolCallProposedPayload(StrictModel):
    call_id: str = Field(min_length=1)
    tool: str = Field(min_length=1)
    args: dict[str, JsonValue] = Field(default_factory=dict)


class InvalidCallPayload(StrictModel):
    """docs/Architecture.md Section 5: a schema failure is "logged as an

    `invalid_call` event and returned to the agent as a tool error; it is not a
    policy violation."
    """

    call_id: str = Field(min_length=1)
    tool: str = Field(min_length=1)
    args: dict[str, JsonValue] = Field(default_factory=dict)
    errors: list[str] = Field(min_length=1)
    returned_as_tool_error: Literal[True] = True


class PrecedenceStep(StrictModel):
    """One entry of ``Decision.precedence_trace`` (Section 6.3 resolution order)."""

    rule_id: str
    effect: PolicyEffect
    priority: int


class PolicyDecisionPayload(StrictModel):
    call_id: str = Field(min_length=1)
    verdict: Verdict
    rule_ids: list[str] = Field(default_factory=list)
    reason_code: str = Field(min_length=1)
    precedence_trace: list[PrecedenceStep] = Field(default_factory=list)


class ToolResultPayload(StrictModel):
    call_id: str = Field(min_length=1)
    tool: str = Field(min_length=1)
    result: JsonValue
    is_error: bool = False
    state_hash_before: str | None = None
    state_hash_after: str | None = None


class StateSnapshotPayload(StrictModel):
    state: dict[str, JsonValue]
    state_hash: str = Field(min_length=1)
    reason: Literal["episode_start", "state_change", "episode_end"]


class UserTurnPayload(StrictModel):
    message: str


class InjectionDeliveredPayload(StrictModel):
    injection_id: str = Field(min_length=1)
    channel: Literal["user_turn", "tool_output", "document"]
    text: str = Field(min_length=1)
    target: str | None = None


class MetaActionPayload(StrictModel):
    action: Literal["escalate_to_human", "refuse", "ask_clarification", "finish"]
    reason: str | None = None
    context: dict[str, JsonValue] | None = None
    question: str | None = None
    summary: str | None = None
    outcome: Literal["approved", "denied", "pending"] | None = None


class EpisodeEndPayload(StrictModel):
    terminated: Termination
    terminal_action: Literal["escalate_to_human", "refuse", "finish"] | None = None
    final_state_hash: str = Field(min_length=1)
    n_turns: int = Field(ge=0)
    notes: str | None = None


class EpisodeStartEvent(EventBase):
    type: Literal["episode_start"]
    payload: EpisodeStartPayload


class ModelRequestEvent(EventBase):
    type: Literal["model_request"]
    payload: ModelRequestPayload


class ModelResponseEvent(EventBase):
    type: Literal["model_response"]
    payload: ModelResponsePayload


class ToolCallProposedEvent(EventBase):
    type: Literal["tool_call_proposed"]
    payload: ToolCallProposedPayload


class InvalidCallEvent(EventBase):
    type: Literal["invalid_call"]
    payload: InvalidCallPayload


class PolicyDecisionEvent(EventBase):
    type: Literal["policy_decision"]
    payload: PolicyDecisionPayload


class ToolResultEvent(EventBase):
    type: Literal["tool_result"]
    payload: ToolResultPayload


class StateSnapshotEvent(EventBase):
    type: Literal["state_snapshot"]
    payload: StateSnapshotPayload


class UserTurnEvent(EventBase):
    type: Literal["user_turn"]
    payload: UserTurnPayload


class InjectionDeliveredEvent(EventBase):
    type: Literal["injection_delivered"]
    payload: InjectionDeliveredPayload


class MetaActionEvent(EventBase):
    type: Literal["meta_action"]
    payload: MetaActionPayload


class EpisodeEndEvent(EventBase):
    type: Literal["episode_end"]
    payload: EpisodeEndPayload


TraceEvent = TypeAliasType(
    "TraceEvent",
    Annotated[
        Annotated[EpisodeStartEvent, Tag(EventType.EPISODE_START)]
        | Annotated[ModelRequestEvent, Tag(EventType.MODEL_REQUEST)]
        | Annotated[ModelResponseEvent, Tag(EventType.MODEL_RESPONSE)]
        | Annotated[ToolCallProposedEvent, Tag(EventType.TOOL_CALL_PROPOSED)]
        | Annotated[InvalidCallEvent, Tag(EventType.INVALID_CALL)]
        | Annotated[PolicyDecisionEvent, Tag(EventType.POLICY_DECISION)]
        | Annotated[ToolResultEvent, Tag(EventType.TOOL_RESULT)]
        | Annotated[StateSnapshotEvent, Tag(EventType.STATE_SNAPSHOT)]
        | Annotated[UserTurnEvent, Tag(EventType.USER_TURN)]
        | Annotated[InjectionDeliveredEvent, Tag(EventType.INJECTION_DELIVERED)]
        | Annotated[MetaActionEvent, Tag(EventType.META_ACTION)]
        | Annotated[EpisodeEndEvent, Tag(EventType.EPISODE_END)],
        Discriminator("type"),
    ],
)

__all__ = [
    "EventType",
    "InvalidCallEvent",
    "Termination",
    "TraceEvent",
    "Verdict",
]
