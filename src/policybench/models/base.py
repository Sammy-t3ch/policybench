"""Base model configuration and the shared schema-version field.

Every Phase 2 schema carries ``schema_version`` (maintainer instruction for
Phase 2; ``docs/DECISIONS.md`` records the choice). ``docs/Architecture.md``
does not specify the value, so it is a module constant, not a per-file edit.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

# typing_extensions is already required by pydantic v2; it provides the
# same TypeAliasType on 3.11 as typing does on 3.12 (see docs/DECISIONS.md H9).
from typing_extensions import TypeAliasType  # noqa: UP035

#: Version of the *schemas* in this package. Bumped whenever a model change
#: would make previously valid documents invalid (see docs/DECISIONS.md, H-series).
SCHEMA_VERSION = "1.0"

SchemaVersion = Literal["1.0"]

#: JSON values permitted inside free-form payloads and task state. Kept to the
#: JSON data model (docs/Architecture.md Section 7: state is a plain
#: JSON-serializable dict). Named recursive alias so Pydantic can resolve it.
JsonValue = TypeAliasType(
    "JsonValue",
    "str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]",  # type: ignore[misc]
)


class StrictModel(BaseModel):
    """Project-wide Pydantic configuration.

    ``extra="forbid"`` rejects unknown keys at load time (Phase 2 constraint 2,
    quoted from PolicyTaxonomy.md Section 6: "Unknown operators fail JSON Schema
    validation at load time").

    Type coercion is prevented at the *document* boundary instead of with
    ``strict=True``: ``strict=True`` refuses a JSON string for an enum member, which
    would make every policy file unloadable. The loader validates raw documents
    against the committed JSON Schema (whose types are strict) before Pydantic
    builds the objects, so ``"5"`` still cannot become ``5``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)


class VersionedModel(StrictModel):
    """Base class for every committed schema: always carries ``schema_version``."""

    schema_version: SchemaVersion = "1.0"


def json_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Return the JSON Schema generated from a Pydantic model (single source of truth)."""
    return model.model_json_schema(mode="validation")
