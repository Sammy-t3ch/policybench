"""Dataset and policy loading (docs/Architecture.md Section 4).

The Dataset Loader "load[s] and validate[s] tasks, resolve[s] ``policy_refs``,
check[s] family consistency" and the Policy Store "load[s] versioned policy JSON,
validate[s] against JSON Schema, hash[es]".
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from policybench.json_schemas import validate_document
from policybench.models.policy import Policy, PolicySet
from policybench.models.task import Dataset


class LoadError(Exception):
    """A file could not be read or did not validate."""

    def __init__(self, path: Path, message: str) -> None:
        self.path = path
        self.message = message
        super().__init__(f"{path}: {message}")


@dataclass(frozen=True)
class DatasetSource:
    """A loaded dataset plus the hashes recorded in the manifest (Section 10)."""

    path: Path
    dataset: Dataset
    sha256: str
    raw: dict[str, Any] = field(repr=False)


@dataclass(frozen=True)
class PolicySource:
    """A loaded policy directory plus its combined hash."""

    directory: Path
    policies: PolicySet
    sha256: str
    version: str


def file_sha256(path: Path) -> str:
    """SHA-256 of a file's bytes; used for manifest hashing."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def combined_sha256(paths: list[Path]) -> str:
    """Order-independent hash of several files, for ``policy_set_hash``."""
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.name):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LoadError(path, "file not found") from exc
    except IsADirectoryError as exc:
        raise LoadError(path, "expected a file, found a directory") from exc
    except json.JSONDecodeError as exc:
        raise LoadError(path, f"invalid JSON at line {exc.lineno} column {exc.colno}: {exc.msg}") from exc


def _validation_message(exc: ValidationError) -> str:
    lines = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error["loc"]) or "<root>"
        lines.append(f"{location}: {error['msg']}")
    return "; ".join(lines)


def load_dataset(path: Path) -> DatasetSource:
    """Load and validate a dataset file.

    Two layers, in order: the committed JSON Schema (strict JSON types, unknown
    keys rejected) and then the Pydantic models (cross-field rules the schema
    cannot express). The schema layer is what keeps ``"5"`` from becoming ``5``.
    """
    raw = _read_json(path)
    if not isinstance(raw, dict):
        raise LoadError(path, "a dataset file must contain a JSON object")
    schema_errors = validate_document("dataset", raw)
    if schema_errors:
        raise LoadError(path, "JSON Schema: " + "; ".join(schema_errors[:5]))
    try:
        dataset = Dataset.model_validate(raw)
    except ValidationError as exc:
        raise LoadError(path, _validation_message(exc)) from exc
    return DatasetSource(path=path, dataset=dataset, sha256=file_sha256(path), raw=raw)


def load_policy_file(path: Path) -> Policy:
    """Load and validate one policy file."""
    raw = _read_json(path)
    if not isinstance(raw, dict):
        raise LoadError(path, "a policy file must contain a JSON object")
    schema_errors = validate_document("policy", raw)
    if schema_errors:
        raise LoadError(path, "JSON Schema: " + "; ".join(schema_errors[:5]))
    try:
        return Policy.model_validate(raw)
    except ValidationError as exc:
        raise LoadError(path, _validation_message(exc)) from exc


def load_policies(directory: Path) -> PolicySource:
    """Load every ``*.json`` policy file in a directory (non-recursive)."""
    if not directory.is_dir():
        raise LoadError(directory, "policies directory not found")
    files = sorted(directory.glob("*.json"))
    if not files:
        raise LoadError(directory, "no policy JSON files found")
    policies = [load_policy_file(path) for path in files]
    try:
        policy_set = PolicySet(policies=policies)
    except ValidationError as exc:
        raise LoadError(directory, _validation_message(exc)) from exc
    versions = {policy.version for policy in policies}
    version = ",".join(str(item) for item in sorted(versions))
    return PolicySource(
        directory=directory,
        policies=policy_set,
        sha256=combined_sha256(files),
        version=version,
    )
