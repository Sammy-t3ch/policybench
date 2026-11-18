"""Access to the committed JSON Schemas.

The committed files under ``schemas/`` are generated from the Pydantic models by
``policybench.schemas_export``. Loading them (rather than regenerating at import
time) means the loader validates against exactly what is committed, so a drift
between models and schemas cannot silently pass a load.
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from policybench.schemas_export import SCHEMA_DIR

#: Schema names as committed (``schemas/<name>.schema.json``).
SCHEMA_NAMES = (
    "condition",
    "policy",
    "task",
    "family",
    "dataset",
    "trace_event",
    "run_config",
    "manifest",
    "run_score",
)


def schema_path(name: str, directory: Path | None = None) -> Path:
    return (directory or SCHEMA_DIR) / f"{name}.schema.json"


@cache
def load_schema(name: str, directory: str | None = None) -> dict[str, Any]:
    """Load one committed JSON Schema."""
    path = schema_path(name, Path(directory) if directory else None)
    return json.loads(path.read_text(encoding="utf-8"))


@cache
def validator(name: str, directory: str | None = None) -> Draft202012Validator:
    """A cached Draft 2020-12 validator for one committed schema."""
    schema = load_schema(name, directory)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate_document(name: str, document: Any) -> list[str]:
    """Return JSON Schema errors for a document, as ``path: message`` strings."""
    errors = []
    for error in sorted(validator(name).iter_errors(document), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        errors.append(f"{location}: {error.message}")
    return errors
