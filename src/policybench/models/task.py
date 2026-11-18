"""Task, family and dataset models.

Quoted sources:

* ``docs/PolicyTaxonomy.md`` Section 1 - a task is a cell (family, level,
  variant); Section 3 - matched families; Section 4 - complexity covariates;
  Section 5 - validity labels; Section 7 - adversarial variants.
* ``docs/Architecture.md`` Section 4 - the static task field ``recoverable``;
  Section 5 - ``allowed_tools``, ``required_escalation_fields``; Section 6.3 -
  ``expected_resolution``; Section 8 - ``scripted_turns`` and ``injections``.
* ``docs/Critique.md`` item 3 - independent ``forbidden_calls``, final-state
  assertions and a hand-written oracle path per task.
* ``docs/MetricsSpec.md`` Section 1 - episodes run against a task.
"""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

from policybench.models.base import JsonValue, StrictModel, VersionedModel

#: Domain tools are dotted (``payments.refund``); the four always-available meta
#: tools are single-segment (``refuse``, ``finish``, ``escalate_to_human``,
#: ``ask_clarification``) per docs/Architecture.md Section 5.
TOOL_NAME_PATTERN = r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$|^(refuse|finish|escalate_to_human|ask_clarification)$"
TASK_ID_PATTERN = r"^[a-z0-9][a-z0-9_.\-]*$"

ToolName = Annotated[str, StringConstraints(pattern=TOOL_NAME_PATTERN)]
TaskId = Annotated[str, StringConstraints(pattern=TASK_ID_PATTERN, max_length=128)]


class ComplexityLevel(StrEnum):
    """docs/PolicyTaxonomy.md Section 2: canonical identifiers L1-L5."""

    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"
    L5 = "L5"


ALL_LEVELS: tuple[ComplexityLevel, ...] = (
    ComplexityLevel.L1,
    ComplexityLevel.L2,
    ComplexityLevel.L3,
    ComplexityLevel.L4,
    ComplexityLevel.L5,
)
"""docs/Architecture.md Section 14 item 4: "Every family has all levels declared"."""


class AdversarialVariant(StrEnum):
    """docs/PolicyTaxonomy.md Section 1: A0 none, A1 user-turn injection,

    A2 tool-output injection, A3 social engineering or authority claim,
    A4 multi-turn pressure.
    """

    A0 = "A0"
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"


class TaskLabel(StrEnum):
    """docs/PolicyTaxonomy.md Section 5: exactly one label per task."""

    VALID = "valid"
    SHOULD_REFUSE = "should_refuse"
    SHOULD_ESCALATE = "should_escalate"


class Domain(StrEnum):
    """docs/PolicyTaxonomy.md Section 8: "Domains in V1: payments, email, database,

    calendar, tickets, filesystem."
    """

    PAYMENTS = "payments"
    EMAIL = "email"
    DATABASE = "database"
    CALENDAR = "calendar"
    TICKETS = "tickets"
    FILESYSTEM = "filesystem"


class TriggerKind(StrEnum):
    """docs/Architecture.md Section 8: "A trigger is `start`, `after_tool:<name>`,

    `on_clarification:<key>`, or `on_denial`."
    """

    START = "start"
    AFTER_TOOL = "after_tool"
    ON_CLARIFICATION = "on_clarification"
    ON_DENIAL = "on_denial"


class InjectionChannel(StrEnum):
    """docs/Architecture.md Section 8: "each with a `channel`: `user_turn`,

    `tool_output` ... or `document`".
    """

    USER_TURN = "user_turn"
    TOOL_OUTPUT = "tool_output"
    DOCUMENT = "document"


class ExpectedResolution(StrEnum):
    """docs/Architecture.md Section 6.3: "the task specifies `expected_resolution`

    (for example, `escalate`)". The terminal action names follow Section 5.
    """

    ESCALATE = "escalate"
    REFUSE = "refuse"
    FINISH = "finish"


class StateAssertion(StrictModel):
    """A final-state assertion checked by the grader.

    ``docs/MetricsSpec.md`` Section 2 refers to a final-state assertion marked
    ``forbidden_state``; ``docs/Architecture.md`` Section 7 exposes
    ``assert_state(path, predicate)``. The predicate vocabulary is not specified
    in the design - see the PR "needs decision" list.
    """

    path: str = Field(min_length=1)
    predicate: Literal["eq", "neq", "in", "not_in", "exists", "not_exists", "lt", "gt"]
    value: JsonValue = None
    forbidden_state: bool = False
    description: str | None = None


class ScriptedTurn(StrictModel):
    """One (trigger, message) pair from docs/Architecture.md Section 8."""

    trigger: TriggerKind
    target: str | None = None
    message: str = Field(min_length=1)

    @model_validator(mode="after")
    def _target_matches_trigger(self) -> ScriptedTurn:
        needs_target = self.trigger in (TriggerKind.AFTER_TOOL, TriggerKind.ON_CLARIFICATION)
        if needs_target and not self.target:
            raise ValueError(
                f"trigger {self.trigger.value!r} requires a target "
                "(`after_tool:<name>` / `on_clarification:<key>`)"
            )
        if not needs_target and self.target is not None:
            raise ValueError(f"trigger {self.trigger.value!r} does not take a target")
        return self


class Injection(StrictModel):
    """A fixed adversarial injection (docs/Architecture.md Section 8)."""

    id: str = Field(min_length=1)
    channel: InjectionChannel
    target: str | None = None
    text: str = Field(min_length=1)

    @model_validator(mode="after")
    def _target_rules(self) -> Injection:
        if self.channel is InjectionChannel.TOOL_OUTPUT and not self.target:
            raise ValueError("channel 'tool_output' requires the named tool it is appended to")
        if self.channel is not InjectionChannel.TOOL_OUTPUT and self.target is not None:
            raise ValueError(f"channel {self.channel.value!r} does not take a target")
        return self


class ToolCall(StrictModel):
    """A deterministic tool-call step; used for oracle paths and forbidden calls."""

    tool: ToolName
    args: dict[str, JsonValue] = Field(default_factory=dict)


class ComplexityCovariates(StrictModel):
    """docs/PolicyTaxonomy.md Section 4, recorded per task.

    The design lists the six covariates but does not say whether they are authored
    or computed. Phase 2 records them as authored values; computing them from the
    policy set is a later-phase question (see the PR "needs decision" list).
    """

    rule_count: int = Field(ge=0)
    active_rules: int = Field(ge=0)
    precondition_depth: int = Field(ge=0)
    n_tools: int = Field(ge=0)
    n_roles: int = Field(ge=0)
    conflict_count: int = Field(ge=0)


class Task(VersionedModel):
    """One task: a cell (family, level, variant) per docs/PolicyTaxonomy.md Section 1."""

    dataset_version: str = Field(min_length=1)
    id: TaskId
    family_id: str = Field(min_length=1)
    level: ComplexityLevel
    variant: AdversarialVariant
    domain: Domain
    label: TaskLabel
    description: str | None = None

    allowed_tools: list[ToolName] = Field(min_length=1)
    policy_refs: list[str] = Field(default_factory=list)
    required_escalation_fields: list[str] = Field(default_factory=list)
    expected_resolution: ExpectedResolution | None = None

    recoverable: bool
    """docs/Architecture.md Section 4: static task-level field, copied into the

    per-episode output flag by the Evaluator."""

    covariates: ComplexityCovariates

    initial_state: dict[str, JsonValue] = Field(default_factory=dict)
    scripted_turns: list[ScriptedTurn] = Field(default_factory=list)
    injections: list[Injection] = Field(default_factory=list)

    forbidden_calls: list[ToolCall] = Field(default_factory=list)
    final_state_assertions: list[StateAssertion] = Field(default_factory=list)
    oracle_path: list[ToolCall] = Field(default_factory=list)

    max_turns: int = Field(ge=1)
    notes: str | None = None

    @model_validator(mode="after")
    def _label_rules(self) -> Task:
        if self.label is TaskLabel.SHOULD_ESCALATE and not self.required_escalation_fields:
            raise ValueError(
                "should_escalate tasks must declare at least one entry in "
                "required_escalation_fields (docs/Architecture.md Section 5, "
                "docs/PolicyTaxonomy.md Section 8)"
            )
        if self.label is not TaskLabel.SHOULD_ESCALATE and self.required_escalation_fields:
            raise ValueError(
                "required_escalation_fields is declared on should_escalate tasks "
                "(docs/PolicyTaxonomy.md Section 8)"
            )
        if self.variant is AdversarialVariant.A0 and self.injections:
            raise ValueError("adversarial injections require variant A1-A4, not A0")
        if self.variant is not AdversarialVariant.A0 and not self.injections:
            raise ValueError(
                "variant A1-A4 requires at least one fixed injection "
                "(docs/Architecture.md Section 8)"
            )
        if (self.level is ComplexityLevel.L5) != (self.expected_resolution is not None):
            raise ValueError(
                "expected_resolution is specified by L5 tasks, and only by them "
                "(docs/Architecture.md Section 6.3)"
            )
        return self

    @model_validator(mode="after")
    def _unique_lists(self) -> Task:
        if len(set(self.allowed_tools)) != len(self.allowed_tools):
            raise ValueError("allowed_tools contains duplicates")
        if len(set(self.policy_refs)) != len(self.policy_refs):
            raise ValueError("policy_refs contains duplicates")
        if len(set(self.required_escalation_fields)) != len(self.required_escalation_fields):
            raise ValueError("required_escalation_fields contains duplicates")
        return self


class Family(VersionedModel):
    """A matched task family (docs/PolicyTaxonomy.md Section 3).

    The levels and task labels a family must contain are members of the set
    ``{valid, should_refuse, should_escalate}``; ``policybench validate`` lints
    both (docs/Architecture.md Section 14 item 4, Section 12).
    """

    id: str = Field(min_length=1)
    domain: Domain
    intent: str = Field(min_length=1)
    levels: list[ComplexityLevel] = Field(min_length=1)
    labels: list[TaskLabel] = Field(min_length=1)
    description: str | None = None

    @model_validator(mode="after")
    def _no_duplicates(self) -> Family:
        if len(set(self.levels)) != len(self.levels):
            raise ValueError("levels contains duplicates")
        if len(set(self.labels)) != len(self.labels):
            raise ValueError("labels contains duplicates")
        return self


class Dataset(VersionedModel):
    """The dataset envelope loaded by the Dataset Loader.

    docs/Architecture.md Section 4: "Load and validate tasks, resolve
    ``policy_refs``, check family consistency". One file holds the families and
    their tasks; ``policybench validate`` resolves ``policy_refs`` against
    ``--policies DIR``.
    """

    dataset_version: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str | None = None
    families: list[Family] = Field(min_length=1)
    tasks: list[Task] = Field(min_length=1)

    @model_validator(mode="after")
    def _referential_integrity(self) -> Dataset:
        family_ids = [family.id for family in self.families]
        if len(set(family_ids)) != len(family_ids):
            raise ValueError("dataset families contain duplicate ids")
        task_ids = [task.id for task in self.tasks]
        duplicates = {task_id for task_id in task_ids if task_ids.count(task_id) > 1}
        if duplicates:
            raise ValueError(f"dataset tasks contain duplicate ids: {sorted(duplicates)}")
        known = set(family_ids)
        orphans = sorted({task.family_id for task in self.tasks} - known)
        if orphans:
            raise ValueError(f"tasks reference unknown families: {orphans}")
        for task in self.tasks:
            if task.dataset_version != self.dataset_version:
                raise ValueError(
                    f"task {task.id!r} has dataset_version {task.dataset_version!r}, "
                    f"but the dataset declares {self.dataset_version!r}"
                )
        return self

    def family_of(self, task: Task) -> Family:
        for family in self.families:
            if family.id == task.family_id:
                return family
        raise KeyError(task.family_id)

    def cell(self, family_id: str, level: ComplexityLevel, variant: AdversarialVariant) -> Task:
        for task in self.tasks:
            if (task.family_id, task.level, task.variant) == (family_id, level, variant):
                return task
        raise KeyError((family_id, level, variant))


def is_valid_family_id(value: str) -> bool:
    """Family ids follow the task-id character set in this Phase 2 schema."""
    return re.fullmatch(TASK_ID_PATTERN, value) is not None
