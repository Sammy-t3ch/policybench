"""Generate the committed JSON Schemas from the Pydantic models.

Pydantic models are the single source of truth (Phase 2 constraint 1). This
module writes ``schemas/<name>.schema.json`` for every public schema; a test
(``tests/test_phase2_schemas.py``) fails if the committed files drift from the
models.

Usage::

    python -m policybench.schemas_export            # rewrite the schemas
    python -m policybench.schemas_export --check    # exit 1 on drift
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, TypeAdapter

from policybench.models.base import SCHEMA_VERSION
from policybench.models.condition import Expr
from policybench.models.policy import Policy
from policybench.models.run import Manifest, RunConfig, RunScore
from policybench.models.task import Dataset, Family, Task
from policybench.models.trace import TraceEvent

#: name -> (model or type adapter, description). Order is stable so the files are
#: diffable and the drift test is deterministic.
_SchemaTarget = BaseModel | type[BaseModel] | TypeAdapter[Any]

SCHEMAS: dict[str, tuple[_SchemaTarget, str]] = {
    "condition": (
        TypeAdapter(Expr),
        "Condition expression node (docs/PolicyTaxonomy.md Section 6)",
    ),
    "policy": (Policy, "One policy rule (docs/Architecture.md Section 6.1)"),
    "task": (Task, "One task: a (family, level, variant) cell (docs/PolicyTaxonomy.md Sections 1-5, 7)"),
    "family": (Family, "A matched task family (docs/PolicyTaxonomy.md Section 3)"),
    "dataset": (Dataset, "Dataset envelope (docs/Architecture.md Section 4)"),
    "trace_event": (
        TypeAdapter(TraceEvent),
        "One JSONL trace event (docs/Architecture.md Section 9)",
    ),
    "run_config": (RunConfig, "Run parameters validated before a run (docs/Architecture.md Section 5)"),
    "manifest": (Manifest, "One manifest.json per run (docs/Architecture.md Section 10)"),
    "run_score": (RunScore, "One scores.jsonl row (docs/MetricsSpec.md Section 2)"),
}

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"


def build_schema(name: str) -> dict[str, Any]:
    """Return the JSON Schema for one entry of :data:`SCHEMAS`."""
    target, description = SCHEMAS[name]
    if isinstance(target, TypeAdapter):
        schema = target.json_schema(mode="validation")
    else:
        schema = target.model_json_schema(mode="validation")
    schema["$comment"] = description
    schema["x-policybench-schema-version"] = SCHEMA_VERSION
    return schema


def render(name: str) -> str:
    """Serialise one schema exactly as it is committed."""
    return json.dumps(build_schema(name), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def path_for(name: str) -> Path:
    return SCHEMA_DIR / f"{name}.schema.json"


def write_all() -> list[Path]:
    """Write every schema file; returns the paths written."""
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for name in SCHEMAS:
        path = path_for(name)
        path.write_text(render(name), encoding="utf-8")
        written.append(path)
    return written


def drift() -> dict[str, str]:
    """Return ``{name: reason}`` for every schema that is missing or stale."""
    problems: dict[str, str] = {}
    for name in SCHEMAS:
        path = path_for(name)
        if not path.is_file():
            problems[name] = f"missing file {path}"
        elif path.read_text(encoding="utf-8") != render(name):
            problems[name] = f"{path} is out of sync with the models"
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the committed schemas match the models instead of rewriting them",
    )
    args = parser.parse_args(argv)
    if args.check:
        problems = drift()
        if problems:
            for name, reason in problems.items():
                print(f"drift: {name}: {reason}")
            print("run `python -m policybench.schemas_export` to regenerate")
            return 1
        print(f"schemas in sync ({len(SCHEMAS)} files)")
        return 0
    for path in write_all():
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover - thin CLI wrapper
    raise SystemExit(main())
