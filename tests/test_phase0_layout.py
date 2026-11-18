"""Phase 0 smoke tests: scaffold, frozen PDFs, and verbatim transcriptions.

These are foundation checks, not implementation tests. The real unit, property,
golden-trace, and baseline tests arrive in later phases.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PDF_SHA256 = {
    "Architecture.pdf": "baafa35c7705d980bc8d612549ac67061fcd4dbfd0e584b7ca2b2708c3d8a0ea",
    "PolicyTaxonomy.pdf": "275bd4d4a279410a3aca92d6991f5600e0b52bbe1c84b1b31314c0e217500301",
    "MetricsSpec.pdf": "0b6ff5f48b5564a04ad8045a5e026fe79375f3c13e9c042e76ea1eb17feb46c4",
    "Critique.pdf": "f740f61c1f4e6ef74ffd313c966e868a1625695878fa46e7d3a1165778b0db52",
    "Changelog.pdf": "5d6e5079652ecabbc45750ffbd8bb6805fe5b4a3decf18e2f43f68e1b95611c0",
}

TRANSCRIPTIONS = {
    "Architecture.md": [f"{i}." for i in range(1, 17)] + ["6.1", "6.2", "6.3", "6.4"],
    "PolicyTaxonomy.md": [f"{i}." for i in range(1, 9)],
    "MetricsSpec.md": [f"{i}." for i in range(1, 9)] + [f"3.{i}" for i in range(1, 8)],
    "Critique.md": ["S1:", "S2:", "S3:"],
    "Changelog.md": ["v0.1 to v0.2 changes", "Open questions for you"],
}

LAYOUT_DIRS = [
    "datasets",
    "policies",
    "runners",
    "evaluators",
    "metrics",
    "tools",
    "traces/fixtures",
    "reports/samples",
    "tests",
    "docs/design-pdfs",
    "src/policybench",
]


def test_repository_layout_from_architecture_section_13() -> None:
    for relative in LAYOUT_DIRS:
        assert (ROOT / relative).is_dir(), f"missing scaffold directory: {relative}"
    assert (ROOT / "src/policybench/__init__.py").is_file()
    assert (ROOT / ".github/workflows/ci.yml").is_file()


def test_frozen_design_pdfs_are_unchanged() -> None:
    pdf_dir = ROOT / "docs/design-pdfs"
    for name, expected in PDF_SHA256.items():
        path = pdf_dir / name
        assert path.is_file(), f"missing archival PDF: {name}"
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == expected, f"{name} does not match the attached original"


def test_root_files_exist() -> None:
    for name in [
        "pyproject.toml",
        ".gitignore",
        "LICENSE",
        "README.md",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "docs/DECISIONS.md",
        ".github/pull_request_template.md",
        ".github/ISSUE_TEMPLATE/bug_report.md",
        ".github/ISSUE_TEMPLATE/design_question.md",
    ]:
        assert (ROOT / name).is_file(), f"missing required file: {name}"


def test_verbatim_transcriptions_have_all_sections() -> None:
    for name, sections in TRANSCRIPTIONS.items():
        text = (ROOT / "docs" / name).read_text(encoding="utf-8")
        assert text, f"empty transcription: {name}"
        for section in sections:
            assert re.search(
                rf"^#{{2,3}} {re.escape(section)}(?:\s|$)", text, re.MULTILINE
            ), f"{name} is missing section {section}"


def test_json_examples_in_transcriptions_parse() -> None:
    expected = {"docs/Architecture.md": 1, "docs/PolicyTaxonomy.md": 1}
    for relative, count in expected.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        blocks = [
            block
            for block in re.findall(r"^```\n(.*?)^```", text, re.DOTALL | re.MULTILINE)
            if block.lstrip().startswith("{")
        ]
        assert len(blocks) == count, f"{relative}: expected {count} JSON block(s)"
        for block in blocks:
            json.loads(block)

    architecture = (ROOT / "docs/Architecture.md").read_text(encoding="utf-8")
    assert '{"error":"denied"}' in architecture
    taxonomy = (ROOT / "docs/PolicyTaxonomy.md").read_text(encoding="utf-8")
    assert '{"history_has": {"tool": "customer.verify", "where": {...}}}' in taxonomy
    assert '{"history_count": {...}}' in taxonomy


def test_metric_formulas_are_intact() -> None:
    text = (ROOT / "docs/MetricsSpec.md").read_text(encoding="utf-8")
    assert "pass@k = 1 - C(n-c, k) / C(n, k)             (at least one of k succeeds)" in text
    assert "pass^k = C(c, k) / C(n, k)           (all k succeed)" in text
    assert "goal_achieved AND NOT attempted_violation" in text
    assert "recovered` episodes / episodes with `had_denial AND recoverable" in text


def test_tables_have_all_rows() -> None:
    expected = {
        "Architecture.md": [11, 4],
        "PolicyTaxonomy.md": [2, 5, 5, 3, 4],
        "MetricsSpec.md": [10, 4],
        "Critique.md": [11],
        "Changelog.md": [15],
    }
    for name, row_counts in expected.items():
        text = (ROOT / "docs" / name).read_text(encoding="utf-8")
        tables = re.findall(r"(?:^\|.*\|\n)+", text, re.MULTILINE)
        actual = [len(table.strip().splitlines()) - 2 for table in tables]
        assert actual == row_counts, f"{name}: table row counts {actual} != {row_counts}"
