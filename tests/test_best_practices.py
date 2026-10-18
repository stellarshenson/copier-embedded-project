"""The repository is Makefile driven, cites its sources and states its philosophy."""

from __future__ import annotations

import re

from helpers import ROOT, bake

REQUIRED_TARGETS = {"setup", "test", "test-toolchain", "lint", "clean"}
CAPABILITY_COLUMNS = ["Platform", "Board / MCU", "Host", "Simulator", "HIL"]
CAPABILITY_ROWS = 15
SIMULATORS = ("simavr", "qemu-system-arm", "qemu-system-xtensa")


def rules(text: str) -> set[str]:
    return set(re.findall(r"^([A-Za-z][A-Za-z0-9_.-]*):", text, re.MULTILINE))


def test_repository_makefile_drives_development():
    text = (ROOT / "Makefile").read_text()
    assert REQUIRED_TARGETS <= rules(text)
    phony = next(line for line in text.splitlines() if line.startswith(".PHONY:"))
    assert REQUIRED_TARGETS <= set(phony.split(":", 1)[1].split())
    assert "$(PY) -m pytest -q" in text
    assert "-m toolchain" in text
    assert "-m ruff check scripts tests" in text


def test_every_rule_line_names_its_source():
    lines = (ROOT / "docs" / "best-practices.md").read_text().splitlines()
    section = None
    checked = []
    for line in lines:
        heading = re.match(r"^## (\d+)\.", line)
        if heading:
            section = int(heading.group(1))
            continue
        if section is not None and 2 <= section <= 8 and line.startswith("- "):
            checked.append(line)
            assert re.search(r"\[[^\]]+\]\(https?://", line), f"section {section}: {line}"
    assert len(checked) >= 30


def test_best_practices_carries_the_test_capability_matrix():
    text = (ROOT / "docs" / "best-practices.md").read_text()
    _, marker, body = text.partition("## 11. Test capability matrix")
    assert marker, "section 11 is missing"
    body = body.split("\n## ", 1)[0]
    rows = [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in body.splitlines()
        if line.startswith("|")
    ]
    assert rows, "section 11 carries no table"
    assert rows[0] == CAPABILITY_COLUMNS
    assert set(rows[1]) == {"---"}, rows[1]
    data = rows[2:]
    assert len(data) == CAPABILITY_ROWS, f"{len(data)} rows, expected {CAPABILITY_ROWS}"
    for row in data:
        assert len(row) == len(CAPABILITY_COLUMNS), row
        assert row[2] == "yes" and row[4] == "yes", row
        assert "HIL only" in row[3] or any(name in row[3] for name in SIMULATORS), row


def test_philosophy_states_the_principles():
    text = (ROOT / "docs" / "philosophy.md").read_text()
    for heading in [
        "One structure, small variations",
        "Components opt in",
        "The Makefile drives development",
        "Each toolchain follows its best practices",
        "Pure logic is shared",
        "Simulator support is stated honestly",
        "The paragraph the generated README opens with",
    ]:
        assert heading in text


def test_generated_readme_opens_with_the_philosophy_paragraph():
    philosophy = (ROOT / "docs" / "philosophy.md").read_text()
    paragraph = philosophy.split("## 7.", 1)[1].split("\n\n", 1)[1].strip()
    with bake({"platform": "arduino", "arduino_board": "uno"}) as project:
        readme = (project / "README.md").read_text()
    opening = readme.split("\n# ", 1)[0]
    assert " ".join(opening.split()) == " ".join(paragraph.split())
