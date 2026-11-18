"""Phase 0 repository and package smoke tests."""

import json
import re
from pathlib import Path

from typer.testing import CliRunner

import policybench
from policybench.cli import app

REPO_ROOT = Path(__file__).resolve().parents[1]

DESIGN_DOC_STEMS = (
    "Architecture",
    "PolicyTaxonomy",
    "MetricsSpec",
    "Critique",
    "Changelog",
)

SCAFFOLD_DIRS = (
    "datasets",
    "policies",
    "runners",
    "evaluators",
    "metrics",
    "tools",
    "traces/fixtures",
    "reports/fixtures",
    "reports/samples",
    "tests",
    "docs",
    "docs/design-pdfs",
    "src/policybench",
)


def test_cli_version() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert policybench.__version__ in result.stdout


def test_scaffold_layout_exists() -> None:
    for rel_path in SCAFFOLD_DIRS:
        assert (REPO_ROOT / rel_path).is_dir(), f"Missing directory: {rel_path}"


def test_design_pdfs_and_markdown_present() -> None:
    for stem in DESIGN_DOC_STEMS:
        pdf_path = REPO_ROOT / "docs" / "design-pdfs" / f"{stem}.pdf"
        md_path = REPO_ROOT / "docs" / f"{stem}.md"
        assert pdf_path.is_file() and pdf_path.stat().st_size > 0
        assert md_path.is_file() and md_path.stat().st_size > 0


def test_design_markdown_json_blocks_parse() -> None:
    json_fence = re.compile(r"```json\n(.*?)\n```", re.DOTALL)
    total_blocks = 0
    for stem in DESIGN_DOC_STEMS:
        content = (REPO_ROOT / "docs" / f"{stem}.md").read_text(encoding="utf-8")
        for block in json_fence.findall(content):
            parsed = json.loads(block)
            assert isinstance(parsed, dict)
            total_blocks += 1
    assert total_blocks >= 2
