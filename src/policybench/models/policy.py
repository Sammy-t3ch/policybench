"""Policy models (docs/Architecture.md Section 6.1)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import Field, model_validator

from policybench.models.base import StrictModel, VersionedModel
from policybench.models.condition import Expr, check_limits


class PolicyEffect(StrEnum):
    """docs/Architecture.md Section 6.1: "Effects: `deny`, `require_escalation`,

    `require_prior`". ``allow`` is the no-rule default, not an effect
    (Section 6.3).
    """

    DENY = "deny"
    REQUIRE_ESCALATION = "require_escalation"
    REQUIRE_PRIOR = "require_prior"


POLICY_ID_PATTERN = r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$"


class Policy(VersionedModel):
    """One policy file.

    ``docs/Architecture.md`` Section 6.1 gives the shape; ``id`` and the integer
    ``version`` are required by the maintainer's Phase 2 instructions.
    """

    id: str = Field(pattern=POLICY_ID_PATTERN, min_length=1)
    version: int = Field(ge=1)
    description: str | None = None
    applies_to: list[str] = Field(min_length=1)
    effect: PolicyEffect
    priority: int = Field(ge=0)
    when: Expr

    @model_validator(mode="before")
    @classmethod
    def _condition_limits(cls, data: Any) -> Any:
        if isinstance(data, dict) and "when" in data:
            check_limits(data["when"])
        return data


class PolicySet(StrictModel):
    """A validated collection of policy rules, as loaded from a policies directory."""

    policies: list[Policy]

    @model_validator(mode="after")
    def _unique_ids(self) -> PolicySet:
        seen: dict[str, int] = {}
        for policy in self.policies:
            if policy.id in seen:
                raise ValueError(
                    f"duplicate policy id {policy.id!r} "
                    f"(versions {seen[policy.id]} and {policy.version})"
                )
            seen[policy.id] = policy.version
        return self

    def by_id(self, policy_id: str) -> Policy | None:
        for policy in self.policies:
            if policy.id == policy_id:
                return policy
        return None
