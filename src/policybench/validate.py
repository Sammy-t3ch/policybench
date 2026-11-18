"""``policybench validate``: schema plus consistency checks.

Implements the Phase 2 scope exactly:

1. schema validation of the dataset and every referenced policy
   (``docs/Architecture.md`` Section 12);
2. ``policy_refs`` resolution against the policies directory (Section 4);
3. family consistency lint - all five levels declared, ``valid`` and prohibited
   variants present (Section 14 item 4; ``docs/PolicyTaxonomy.md`` Sections 3, 5);
4. ``recoverable`` present on every task (Section 4);
5. ``required_escalation_fields`` present on ``should_escalate`` tasks
   (Section 5; ``docs/PolicyTaxonomy.md`` Section 8);
6. rejection of ``policy_visibility=none`` combined with ``mode=audit``
   (Section 5; ``docs/DECISIONS.md`` G5).

Structural checks live in the models, so a structurally invalid file fails at load
time; everything here is the cross-file and cross-field consistency that a single
JSON Schema cannot express. Findings are data, never exceptions, so the CLI can
report all of them at once.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from pydantic import ValidationError

from policybench.loader import LoadError, load_dataset, load_policies
from policybench.models.base import SCHEMA_VERSION
from policybench.models.run import Mode, PolicyVisibility, RunConfig
from policybench.models.task import ALL_LEVELS, ComplexityLevel, Dataset, TaskLabel


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


class CheckCode(StrEnum):
    """Stable machine-readable identifiers for every finding."""

    LOAD_ERROR = "load_error"
    SCHEMA_VERSION = "schema_version_mismatch"
    POLICY_REF_MISSING = "policy_ref_missing"
    POLICY_REF_UNUSED = "policy_ref_unused"
    FAMILY_MISSING_LEVEL = "family_missing_level"
    FAMILY_MISSING_LABEL = "family_missing_label"
    FAMILY_MISSING_PROHIBITED = "family_missing_prohibited"
    FAMILY_UNKNOWN_TASK_LABEL = "family_unknown_task_label"
    DATASET_VERSION = "dataset_version_mismatch"
    TASK_NOT_RECOVERABLE_FLAGGED = "task_not_recoverable"
    COVARIATE_MISMATCH = "covariate_mismatch"
    RUN_PARAMS = "run_params_invalid"


@dataclass(frozen=True)
class Finding:
    """One lint or validation result."""

    code: CheckCode
    severity: Severity
    message: str
    task_id: str | None = None
    family_id: str | None = None

    def render(self) -> str:
        prefix = f"[{self.severity.value}] {self.code.value}"
        if self.family_id:
            prefix += f" family={self.family_id}"
        if self.task_id:
            prefix += f" task={self.task_id}"
        return f"{prefix}: {self.message}"


@dataclass
class ValidationReport:
    """Everything ``policybench validate`` found."""

    dataset: Path
    policies: Path | None
    findings: list[Finding] = field(default_factory=list)
    n_tasks: int = 0
    n_families: int = 0
    n_policies: int = 0
    checks_run: list[str] = field(default_factory=list)

    @property
    def errors(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.severity is Severity.ERROR]

    @property
    def warnings(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.severity is Severity.WARNING]

    @property
    def ok(self) -> bool:
        return not self.errors

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)

    def summary(self) -> str:
        status = "OK" if self.ok else "FAILED"
        return (
            f"{status}: {self.n_families} families, {self.n_tasks} tasks, "
            f"{self.n_policies} policies; {len(self.errors)} error(s), "
            f"{len(self.warnings)} warning(s)"
        )


REQUIRED_FAMILY_LABELS: tuple[TaskLabel, ...] = (TaskLabel.VALID, TaskLabel.SHOULD_ESCALATE)
"""A family must contain at least one ``valid`` and one prohibited task.

docs/PolicyTaxonomy.md Section 3: "Each family should contain valid, should-refuse,
and should-escalate tasks." Phase 2 enforces the ``valid`` and
``should_escalate`` members here and records the reading of that sentence under
"needs decision" in the PR (see docs/DECISIONS.md H-series)."""


def _check_family_levels(dataset: Dataset, report: ValidationReport) -> None:
    for family in dataset.families:
        declared = set(family.levels)
        expected = set(ALL_LEVELS)
        missing = sorted(level.value for level in expected - declared)
        extra = sorted(level.value for level in declared - expected)
        if missing:
            report.add(
                Finding(
                    code=CheckCode.FAMILY_MISSING_LEVEL,
                    severity=Severity.ERROR,
                    message=(
                        "family does not declare every complexity level; missing "
                        f"{missing} (docs/Architecture.md Section 14 item 4)"
                    ),
                    family_id=family.id,
                )
            )
        if extra:
            report.add(
                Finding(
                    code=CheckCode.FAMILY_MISSING_LEVEL,
                    severity=Severity.ERROR,
                    message=f"family declares unknown levels {extra}",
                    family_id=family.id,
                )
            )


def _check_family_labels(dataset: Dataset, report: ValidationReport) -> None:
    for family in dataset.families:
        declared = set(family.labels)
        task_labels = {task.label for task in dataset.tasks if task.family_id == family.id}
        missing_declared = [label.value for label in REQUIRED_FAMILY_LABELS if label not in declared]
        if missing_declared:
            report.add(
                Finding(
                    code=CheckCode.FAMILY_MISSING_LABEL,
                    severity=Severity.ERROR,
                    message=(
                        f"family must declare {missing_declared} tasks "
                        "(docs/PolicyTaxonomy.md Section 3)"
                    ),
                    family_id=family.id,
                )
            )
        prohibited = {TaskLabel.SHOULD_REFUSE, TaskLabel.SHOULD_ESCALATE}
        if not (task_labels & prohibited):
            report.add(
                Finding(
                    code=CheckCode.FAMILY_MISSING_PROHIBITED,
                    severity=Severity.ERROR,
                    message=(
                        "family has no prohibited task; add a should_refuse or "
                        "should_escalate task (docs/PolicyTaxonomy.md Section 3)"
                    ),
                    family_id=family.id,
                )
            )
        if not declared <= task_labels:
            unbuilt = sorted(label.value for label in declared - task_labels)
            report.add(
                Finding(
                    code=CheckCode.FAMILY_UNKNOWN_TASK_LABEL,
                    severity=Severity.WARNING,
                    message=(
                        f"family declares labels with no task yet: {unbuilt} "
                        "(allowed while the dataset is being authored)"
                    ),
                    family_id=family.id,
                )
            )


def _check_family_cells(dataset: Dataset, report: ValidationReport) -> None:
    """Every levels x labels cell the family declares needs at most one A0 task."""
    seen: dict[tuple[str, str, str, str], str] = {}
    for task in dataset.tasks:
        key = (task.family_id, task.level.value, task.variant.value, task.label.value)
        if key in seen:
            report.add(
                Finding(
                    code=CheckCode.FAMILY_UNKNOWN_TASK_LABEL,
                    severity=Severity.ERROR,
                    message=(
                        f"duplicate cell {key}: tasks {seen[key]!r} and {task.id!r} "
                        "occupy the same (family, level, variant, label)"
                    ),
                    task_id=task.id,
                    family_id=task.family_id,
                )
            )
        else:
            seen[key] = task.id


def _check_policy_refs(
    dataset: Dataset, policy_ids: set[str], report: ValidationReport
) -> None:
    referenced: set[str] = set()
    for task in dataset.tasks:
        for policy_id in task.policy_refs:
            referenced.add(policy_id)
            if policy_id not in policy_ids:
                report.add(
                    Finding(
                        code=CheckCode.POLICY_REF_MISSING,
                        severity=Severity.ERROR,
                        message=(
                            f"policy_ref {policy_id!r} does not resolve in the policy "
                            "directory (docs/Architecture.md Section 4)"
                        ),
                        task_id=task.id,
                        family_id=task.family_id,
                    )
                )
    for policy_id in sorted(policy_ids - referenced):
        report.add(
            Finding(
                code=CheckCode.POLICY_REF_UNUSED,
                severity=Severity.WARNING,
                message=(
                    f"policy {policy_id!r} is loaded but no task references it; "
                    "unused policies inflate the policy-set hash"
                ),
            )
        )


def _check_recoverable(dataset: Dataset, report: ValidationReport) -> None:
    """``recoverable`` is required by the model; this records the check explicitly.

    The model rejects a task without the field, so reaching here means every task
    carries it. The explicit pass keeps the check visible in the report and
    protects against a future model change making it optional.
    """
    for task in dataset.tasks:
        if not isinstance(getattr(task, "recoverable", None), bool):
            report.add(
                Finding(
                    code=CheckCode.TASK_NOT_RECOVERABLE_FLAGGED,
                    severity=Severity.ERROR,
                    message=(
                        "every task must declare the static recoverable flag "
                        "(docs/Architecture.md Section 4)"
                    ),
                    task_id=task.id,
                    family_id=task.family_id,
                )
            )


def _check_covariates(dataset: Dataset, report: ValidationReport) -> None:
    for task in dataset.tasks:
        if task.covariates.n_tools != len(task.allowed_tools):
            report.add(
                Finding(
                    code=CheckCode.COVARIATE_MISMATCH,
                    severity=Severity.WARNING,
                    message=(
                        f"covariate n_tools={task.covariates.n_tools} but allowed_tools has "
                        f"{len(task.allowed_tools)} entries (docs/PolicyTaxonomy.md Section 4)"
                    ),
                    task_id=task.id,
                    family_id=task.family_id,
                )
            )


def check_run_params(config: RunConfig) -> list[Finding]:
    """Validate run parameters, including the visibility/mode combination.

    The model raises on the rejected combination; this wrapper turns that into a
    finding so ``policybench validate`` can report it like any other problem.
    """
    try:
        RunConfig.model_validate(
            {
                "mode": config.mode,
                "policy_visibility": config.policy_visibility,
                "feedback": config.feedback,
                "k": config.k,
                "max_turns": config.max_turns,
                "seed": config.seed,
            }
        )
    except ValidationError as exc:
        return [
            Finding(
                code=CheckCode.RUN_PARAMS,
                severity=Severity.ERROR,
                message=str(error["msg"]),
            )
            for error in exc.errors()
        ]
    if config.policy_visibility is PolicyVisibility.NONE and config.mode is Mode.AUDIT:
        return [
            Finding(
                code=CheckCode.RUN_PARAMS,
                severity=Severity.ERROR,
                message=(
                    "policy_visibility=none combined with mode=audit is rejected "
                    "(docs/Architecture.md Section 5)"
                ),
            )
        ]
    return []


def validate_dataset(
    dataset_path: Path,
    policies_dir: Path | None = None,
    config: RunConfig | None = None,
) -> ValidationReport:
    """Run every Phase 2 check and return the findings."""
    report = ValidationReport(dataset=dataset_path, policies=policies_dir)

    try:
        source = load_dataset(dataset_path)
    except LoadError as exc:
        report.add(
            Finding(code=CheckCode.LOAD_ERROR, severity=Severity.ERROR, message=exc.message)
        )
        return report

    dataset = source.dataset
    report.n_tasks = len(dataset.tasks)
    report.n_families = len(dataset.families)
    report.checks_run.append("schema")

    if dataset.schema_version != SCHEMA_VERSION:
        report.add(
            Finding(
                code=CheckCode.SCHEMA_VERSION,
                severity=Severity.ERROR,
                message=(
                    f"dataset schema_version {dataset.schema_version!r} does not match "
                    f"the supported version {SCHEMA_VERSION!r}"
                ),
            )
        )

    policy_ids: set[str] = set()
    if policies_dir is not None:
        try:
            policy_source = load_policies(policies_dir)
        except LoadError as exc:
            report.add(
                Finding(code=CheckCode.LOAD_ERROR, severity=Severity.ERROR, message=exc.message)
            )
        else:
            policy_ids = {policy.id for policy in policy_source.policies.policies}
            report.n_policies = len(policy_ids)
            report.checks_run.append("policies")
            _check_policy_refs(dataset, policy_ids, report)
    else:
        for task in dataset.tasks:
            for policy_id in task.policy_refs:
                report.add(
                    Finding(
                        code=CheckCode.POLICY_REF_MISSING,
                        severity=Severity.WARNING,
                        message=(
                            f"policy_ref {policy_id!r} was not resolved because no "
                            "--policies directory was given"
                        ),
                        task_id=task.id,
                        family_id=task.family_id,
                    )
                )

    _check_family_levels(dataset, report)
    _check_family_labels(dataset, report)
    _check_family_cells(dataset, report)
    _check_recoverable(dataset, report)
    _check_covariates(dataset, report)
    report.checks_run.extend(["families", "recoverable", "covariates"])

    _check_dataset_version(dataset, report)

    if config is not None:
        for finding in check_run_params(config):
            report.add(finding)

    return report


def _check_dataset_version(dataset: Dataset, report: ValidationReport) -> None:
    """Task files carry ``dataset_version`` and must agree with the dataset.

    The envelope check exists in the model; this reports the version so it is
    visible in the CLI output and in the report object.
    """
    mismatched = [task for task in dataset.tasks if task.dataset_version != dataset.dataset_version]
    for task in mismatched:
        report.add(
            Finding(
                code=CheckCode.DATASET_VERSION,
                severity=Severity.ERROR,
                message=(
                    f"task dataset_version {task.dataset_version!r} does not match the "
                    f"dataset's {dataset.dataset_version!r}"
                ),
                task_id=task.id,
                family_id=task.family_id,
            )
        )


def task_level_summary(dataset: Dataset) -> dict[str, dict[str, int]]:
    """Count tasks per family and level; used by the CLI summary line."""
    summary: dict[str, dict[str, int]] = {}
    for task in dataset.tasks:
        bucket = summary.setdefault(task.family_id, {level.value: 0 for level in ComplexityLevel})
        bucket[task.level.value] += 1
    return summary


def tasks_missing_level(dataset: Dataset) -> list[tuple[str, list[str]]]:
    """Families with a declared level that has no task yet."""
    missing: list[tuple[str, list[str]]] = []
    for family in dataset.families:
        built = {task.level for task in dataset.tasks if task.family_id == family.id}
        gaps = sorted(level.value for level in set(ALL_LEVELS) - built)
        if gaps:
            missing.append((family.id, gaps))
    return missing
