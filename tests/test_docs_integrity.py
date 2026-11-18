"""Guards the archival design documents.

The PDFs under docs/design-pdfs/ are the frozen originals; the Markdown files are verbatim
transcriptions of them. This module turns the Phase 0 extraction check into a CI gate:

* the archived PDFs must be byte-identical to what was received;
* every Markdown transcription must exist, and every fenced JSON example in them must parse.

See docs/DECISIONS.md (D-018).
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS = REPO_ROOT / "docs"
PDF_DIR = DOCS / "design-pdfs"

ARCHIVED_PDFS = {
    "Architecture.pdf": "baafa35c7705d980bc8d612549ac67061fcd4dbfd0e584b7ca2b2708c3d8a0ea",
    "Changelog.pdf": "5d6e5079652ecabbc45750ffbd8bb6805fe5b4a3decf18e2f43f68e1b95611c0",
    "Critique.pdf": "f740f61c1f4e6ef74ffd313c966e868a1625695878fa46e7d3a1165778b0db52",
    "MetricsSpec.pdf": "0b6ff5f48b5564a04ad8045a5e026fe79375f3c13e9c042e76ea1eb17feb46c4",
    "PolicyTaxonomy.pdf": "275bd4d4a279410a3aca92d6991f5600e0b52bbe1c84b1b31314c0e217500301",
}

TRANSCRIPTS = (
    "Architecture.md",
    "PolicyTaxonomy.md",
    "MetricsSpec.md",
    "Critique.md",
    "Changelog.md",
)

JSON_BLOCK = re.compile(r"```json\n(?P<body>.*?)```", re.DOTALL)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize("name", sorted(ARCHIVED_PDFS))
def test_archived_pdf_is_byte_identical(name: str) -> None:
    path = PDF_DIR / name
    assert path.is_file(), f"missing archival original: {path}"
    assert _sha256(path) == ARCHIVED_PDFS[name], f"{name} must never be edited"


@pytest.mark.parametrize("name", sorted(ARCHIVED_PDFS))
def test_transcription_exists_for_every_pdf(name: str) -> None:
    transcript = DOCS / name.replace(".pdf", ".md")
    assert transcript.is_file(), f"missing transcription for {name}: {transcript}"
    assert transcript.read_text(encoding="utf-8").strip(), f"{transcript} is empty"


def test_json_examples_parse() -> None:
    blocks = [
        (name, match.group("body"))
        for name in TRANSCRIPTS
        for match in JSON_BLOCK.finditer((DOCS / name).read_text(encoding="utf-8"))
    ]
    # Architecture §6.1 (policy file shape) and PolicyTaxonomy §6 (L4 role-dependent example).
    assert len(blocks) >= 2, "expected at least the two policy JSON examples"
    for name, body in blocks:
        try:
            json.loads(body)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"{name}: JSON example does not parse: {exc}") from exc
