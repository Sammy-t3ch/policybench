"""Condition language models.

Encodes the operator table in ``docs/PolicyTaxonomy.md`` Section 6 exactly as
mirrored in ``docs/Architecture.md`` Section 6.2:

* ``and`` / ``or``: ``{"op": ..., "args": [expr, ...]}`` with 2 or more args.
* ``not``: ``{"op": "not", "arg": expr}``.
* ``eq``, ``neq``, ``lt``, ``lte``, ``gt``, ``gte``, ``in``, ``not_in``,
  ``domain_in``, ``startswith``, ``path_under``: ``{"op", "left", "right"}``.
* ``history_has`` / ``history_count``: ``{"<key>": {"tool": <name>,
  "where": {<field>: <const>, ...}}}``.
* Reference nodes: ``{"arg": ...}``, ``{"state": ...}``, ``{"actor": ...}``,
  ``{"object": ...}``, ``{"const": ...}``, and the two history keys above.

Unknown operators and unknown keys are rejected at load time. Maximum expression
depth is 8 and maximum nodes is 64; both are checked here so ``policybench
validate`` reports them as schema errors instead of runtime ones.

Runtime *type* rules (identical types for ``eq``/``neq``, numbers for
comparisons, a list on the right of ``in``, and so on) belong to the engine in
Phase 3. This module enforces shape, arity and the structural limits — everything
a load-time schema can decide without argument values.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Discriminator, Tag, TypeAdapter, model_validator

# typing_extensions is already required by pydantic v2; it provides the
# same TypeAliasType on 3.11 as typing does on 3.12 (see docs/DECISIONS.md H9).
from typing_extensions import TypeAliasType  # noqa: UP035

# TypeAliasType gives the recursive union a real name, which Pydantic needs to
# emit a stable "$defs/Expr" reference.
from policybench.models.base import JsonValue, StrictModel

#: docs/PolicyTaxonomy.md Section 6: "Maximum expression depth is 8."
MAX_EXPR_DEPTH = 8
#: docs/PolicyTaxonomy.md Section 6: "Maximum nodes is 64."
MAX_EXPR_NODES = 64
#: docs/PolicyTaxonomy.md Section 6: "'args' has 2 or more expressions."
MIN_BOOLEAN_ARGS = 2

#: Operators from the Section 6 table, in table order.
OPERATOR_TAGS: tuple[str, ...] = (
    "and",
    "or",
    "not",
    "eq",
    "neq",
    "lt",
    "lte",
    "gt",
    "gte",
    "in",
    "not_in",
    "domain_in",
    "startswith",
    "path_under",
)
#: Canonical reference keys from Section 6 ("Reference nodes").
REFERENCE_TAGS: tuple[str, ...] = (
    "arg",
    "state",
    "actor",
    "object",
    "history_has",
    "history_count",
    "const",
)


class _Node(StrictModel):
    """Marker base class for every expression node."""


class AndExpr(_Node):
    op: Literal["and"]
    args: list[Expr]

    @model_validator(mode="after")
    def _arity(self) -> AndExpr:
        if len(self.args) < MIN_BOOLEAN_ARGS:
            raise ValueError(
                f"'and' requires at least {MIN_BOOLEAN_ARGS} args "
                f"(docs/PolicyTaxonomy.md Section 6); got {len(self.args)}"
            )
        return self


class OrExpr(_Node):
    op: Literal["or"]
    args: list[Expr]

    @model_validator(mode="after")
    def _arity(self) -> OrExpr:
        if len(self.args) < MIN_BOOLEAN_ARGS:
            raise ValueError(
                f"'or' requires at least {MIN_BOOLEAN_ARGS} args "
                f"(docs/PolicyTaxonomy.md Section 6); got {len(self.args)}"
            )
        return self


class NotExpr(_Node):
    op: Literal["not"]
    arg: Expr


class EqExpr(_Node):
    op: Literal["eq"]
    left: Expr
    right: Expr


class NeqExpr(_Node):
    op: Literal["neq"]
    left: Expr
    right: Expr


class LtExpr(_Node):
    op: Literal["lt"]
    left: Expr
    right: Expr


class LteExpr(_Node):
    op: Literal["lte"]
    left: Expr
    right: Expr


class GtExpr(_Node):
    op: Literal["gt"]
    left: Expr
    right: Expr


class GteExpr(_Node):
    op: Literal["gte"]
    left: Expr
    right: Expr


class InExpr(_Node):
    op: Literal["in"]
    left: Expr
    right: Expr


class NotInExpr(_Node):
    op: Literal["not_in"]
    left: Expr
    right: Expr


class DomainInExpr(_Node):
    op: Literal["domain_in"]
    left: Expr
    right: Expr


class StartswithExpr(_Node):
    op: Literal["startswith"]
    left: Expr
    right: Expr


class PathUnderExpr(_Node):
    op: Literal["path_under"]
    left: Expr
    right: Expr


class HistoryQuery(StrictModel):
    """Inner object of ``history_has`` / ``history_count``.

    ``where`` maps field names to constants; every entry must match by equality
    (docs/PolicyTaxonomy.md Section 6).
    """

    tool: str
    where: dict[str, JsonValue]


class HistoryHasExpr(_Node):
    history_has: HistoryQuery


class HistoryCountExpr(_Node):
    history_count: HistoryQuery


class ArgRef(_Node):
    arg: str


class StateRef(_Node):
    state: str


class ActorRef(_Node):
    actor: str


class ObjectRef(_Node):
    object: str


class ConstRef(_Node):
    const: Any


def expr_kind(value: Any) -> str:
    """Discriminator: which canonical node an expression object is.

    Operator nodes carry ``"op": <operator>``; reference nodes carry exactly one
    canonical reference key. Non-objects, unknown operators, unknown keys, and
    objects that mix an operator with a reference key are rejected.
    """
    if not isinstance(value, dict):
        raise TypeError(
            "a condition expression must be a JSON object (docs/PolicyTaxonomy.md Section 6)"
        )
    if "op" in value:
        op = value["op"]
        if op not in OPERATOR_TAGS:
            raise ValueError(
                f"unknown operator {op!r}; expected one of {list(OPERATOR_TAGS)} "
                "(docs/PolicyTaxonomy.md Section 6)"
            )
        return str(op)
    present_refs = [key for key in REFERENCE_TAGS if key in value]
    if not present_refs:
        raise ValueError(
            "unknown condition expression; expected an object with an 'op' key or one of "
            f"{list(REFERENCE_TAGS)} (docs/PolicyTaxonomy.md Section 6)"
        )
    if len(present_refs) > 1:
        raise ValueError(
            f"a reference node carries exactly one canonical key; found {present_refs} "
            "(docs/PolicyTaxonomy.md Section 6)"
        )
    return present_refs[0]


Expr = TypeAliasType(
    "Expr",
    Annotated[
        Annotated[AndExpr, Tag("and")] | Annotated[OrExpr, Tag("or")] | Annotated[NotExpr, Tag("not")] | Annotated[EqExpr, Tag("eq")] | Annotated[NeqExpr, Tag("neq")] | Annotated[LtExpr, Tag("lt")] | Annotated[LteExpr, Tag("lte")] | Annotated[GtExpr, Tag("gt")] | Annotated[GteExpr, Tag("gte")] | Annotated[InExpr, Tag("in")] | Annotated[NotInExpr, Tag("not_in")] | Annotated[DomainInExpr, Tag("domain_in")] | Annotated[StartswithExpr, Tag("startswith")] | Annotated[PathUnderExpr, Tag("path_under")] | Annotated[ArgRef, Tag("arg")] | Annotated[StateRef, Tag("state")] | Annotated[ActorRef, Tag("actor")] | Annotated[ObjectRef, Tag("object")] | Annotated[HistoryHasExpr, Tag("history_has")] | Annotated[HistoryCountExpr, Tag("history_count")] | Annotated[ConstRef, Tag("const")],
        Discriminator(expr_kind),
    ],
)

EXPR_ADAPTER: TypeAdapter[Any] = TypeAdapter(Expr)


def _children(value: Any) -> list[Any]:
    """Direct child expression nodes of a raw expression object."""
    if not isinstance(value, dict):
        return []
    if value.get("op") in ("and", "or"):
        args = value.get("args")
        return list(args) if isinstance(args, list) else []
    if value.get("op") == "not":
        return [value["arg"]] if "arg" in value else []
    return [value[side] for side in ("left", "right") if side in value]


def expr_limits(value: Any) -> tuple[int, int]:
    """Return ``(depth, nodes)`` for a raw expression tree.

    The root counts as one node at depth 1: the plain reading of "Maximum
    expression depth is 8. Maximum nodes is 64."
    """
    children = _children(value)
    if not children:
        return (1, 1)
    size = [expr_limits(child) for child in children]
    return (1 + max(depth for depth, _ in size), 1 + sum(nodes for _, nodes in size))


def check_limits(value: Any) -> None:
    """Raise ``ValueError`` if a raw expression tree exceeds the Section 6 limits."""
    depth, nodes = expr_limits(value)
    if depth > MAX_EXPR_DEPTH:
        raise ValueError(
            f"condition depth {depth} exceeds the maximum of {MAX_EXPR_DEPTH} "
            "(docs/PolicyTaxonomy.md Section 6)"
        )
    if nodes > MAX_EXPR_NODES:
        raise ValueError(
            f"condition has {nodes} nodes, exceeding the maximum of {MAX_EXPR_NODES} "
            "(docs/PolicyTaxonomy.md Section 6)"
        )


def parse_condition(raw: Any) -> Any:
    """Validate a raw expression object against the operator table and the limits."""
    check_limits(raw)
    return EXPR_ADAPTER.validate_python(raw)


for _node_model in (
    AndExpr,
    OrExpr,
    NotExpr,
    EqExpr,
    NeqExpr,
    LtExpr,
    LteExpr,
    GtExpr,
    GteExpr,
    InExpr,
    NotInExpr,
    DomainInExpr,
    StartswithExpr,
    PathUnderExpr,
    HistoryHasExpr,
    HistoryCountExpr,
):
    _node_model.model_rebuild()

__all__ = [
    "EXPR_ADAPTER",
    "MAX_EXPR_DEPTH",
    "MAX_EXPR_NODES",
    "MIN_BOOLEAN_ARGS",
    "OPERATOR_TAGS",
    "REFERENCE_TAGS",
    "Expr",
    "check_limits",
    "expr_kind",
    "expr_limits",
    "parse_condition",
]
