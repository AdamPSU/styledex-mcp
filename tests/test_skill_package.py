from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "copycat" / "skills" / "copycat"


def test_copycat_skill_is_vendored_with_required_metadata() -> None:
    skill = SKILL_DIR / "SKILL.md"

    text = skill.read_text()

    assert text.startswith("---\n")
    assert "name: copycat" in text
    assert "description: Captures website design style" in text
    assert "# Copycat" in text


def test_copycat_skill_reference_docs_are_vendored() -> None:
    text = (SKILL_DIR / "SKILL.md").read_text()
    references = sorted(set(re.findall(r"@references/([A-Za-z0-9_-]+\.md)", text)))

    assert references == [
        "apply-guidelines.md",
        "capture-guidelines.md",
        "design-md-guidelines.md",
        "legal-boundaries.md",
        "playwright.md",
    ]
    for reference in references:
        assert (SKILL_DIR / "references" / reference).is_file()


def test_copycat_skill_is_available_as_package_resource() -> None:
    assert SKILL_DIR.is_relative_to(ROOT / "copycat")
    assert (files("copycat") / "skills" / "copycat" / "SKILL.md").is_file()
