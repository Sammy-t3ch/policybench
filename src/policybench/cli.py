"""The ``policybench`` command line (docs/Architecture.md Section 12).

Phase 2 implements ``validate`` only. ``run``, ``baseline``, ``grade``,
``report``, ``index`` and ``generate`` are declared V1 commands implemented in
later phases; declaring them now would be a false claim (docs/DECISIONS.md D9).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from policybench.models.run import Feedback, Mode, PolicyVisibility, RunConfig
from policybench.validate import CheckCode, Finding, Severity, validate_dataset

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="PolicyBench: a CLI-first, local-first policy-compliance benchmark.",
)


@app.callback()
def _root() -> None:
    """PolicyBench command group."""


@app.command()
def validate(
    dataset: Annotated[Path, typer.Argument(help="dataset JSON file to validate")],
    policies: Annotated[
        Path | None,
        typer.Option(
            "--policies",
            "-p",
            help="directory of policy JSON files used to resolve policy_refs",
            exists=False,
            file_okay=False,
            dir_okay=True,
        ),
    ] = None,
    mode: Annotated[
        Mode | None,
        typer.Option("--mode", help="run mode to check against the dataset's run parameters"),
    ] = None,
    policy_visibility: Annotated[
        PolicyVisibility | None,
        typer.Option(
            "--policy-visibility",
            help="policy visibility to check (full|summary|none); 'none' is rejected with audit",
        ),
    ] = None,
    feedback: Annotated[
        Feedback,
        typer.Option("--feedback", help="denial feedback level to record in the checked config"),
    ] = Feedback.RULE,
    k: Annotated[int, typer.Option("--k", help="samples per task", min=1)] = 1,
    max_turns: Annotated[int, typer.Option("--max-turns", help="episode turn limit", min=1)] = 20,
    seed: Annotated[int | None, typer.Option("--seed", help="sampling seed")] = None,
    as_json: Annotated[
        bool, typer.Option("--json", help="emit machine-readable JSON instead of text")
    ] = False,
) -> None:
    """Validate a dataset: schema, policy_refs, family lint and run parameters."""
    config: RunConfig | None = None
    config_findings: list[Finding] = []
    if mode is not None:
        try:
            config = RunConfig(
                mode=mode,
                policy_visibility=policy_visibility or PolicyVisibility.FULL,
                feedback=feedback,
                k=k,
                max_turns=max_turns,
                seed=seed,
            )
        except ValidationError as exc:
            for error in exc.errors():
                config_findings.append(
                    Finding(
                        code=CheckCode.RUN_PARAMS,
                        severity=Severity.ERROR,
                        message=str(error["msg"]),
                    )
                )

    report = validate_dataset(dataset, policies, config)
    for finding in config_findings:
        report.add(finding)

    if as_json:
        typer.echo(
            json.dumps(
                {
                    "ok": report.ok,
                    "dataset": str(report.dataset),
                    "policies": str(report.policies) if report.policies else None,
                    "n_families": report.n_families,
                    "n_tasks": report.n_tasks,
                    "n_policies": report.n_policies,
                    "checks_run": report.checks_run,
                    "findings": [
                        {
                            "code": finding.code.value,
                            "severity": finding.severity.value,
                            "message": finding.message,
                            "task_id": finding.task_id,
                            "family_id": finding.family_id,
                        }
                        for finding in report.findings
                    ],
                },
                indent=2,
            )
        )
    else:
        for finding in report.findings:
            typer.echo(finding.render())
        typer.echo(report.summary())

    if not report.ok:
        raise typer.Exit(code=1)


def main(argv: list[str] | None = None) -> int:
    """Entry point used by ``python -m policybench`` and the console script."""
    args = sys.argv[1:] if argv is None else argv
    app(args=args, prog_name="policybench")
    return 0


if __name__ == "__main__":  # pragma: no cover - thin wrapper
    raise SystemExit(main())
