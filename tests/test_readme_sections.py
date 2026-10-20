"""The generated README and CHANGELOG document the project and its simulator."""

from __future__ import annotations

import re

import pytest
from helpers import bake

COMPONENTS = [
    "notebooks",
    "resources",
    "references",
    "simulator",
    "agents",
    "env-installers",
]

README_MATRIX = [
    pytest.param({"platform": "arduino", "arduino_board": "uno"}, id="arduino-uno"),
    pytest.param(
        {"platform": "avr", "avr_language": "c", "avr_mcu": "atmega328p"},
        id="avr-c",
    ),
    pytest.param(
        {"platform": "esp", "esp_chip": "esp32", "esp_framework": "espidf"},
        id="esp32-espidf",
    ),
    pytest.param(
        {"platform": "esp", "esp_chip": "esp32", "esp_framework": "arduino"},
        id="esp32-arduino",
    ),
    pytest.param(
        {"platform": "esp", "esp_chip": "esp8266", "esp_framework": "arduino"},
        id="esp8266-arduino",
    ),
    pytest.param(
        {"platform": "stm32", "stm32_toolchain": "rust", "stm32_board": "f405rg"},
        id="stm32-rust-f405rg",
    ),
    pytest.param(
        {"platform": "stm32", "stm32_toolchain": "rust", "stm32_board": "f103c8"},
        id="stm32-rust-f103c8",
    ),
    pytest.param(
        {
            "platform": "stm32",
            "stm32_toolchain": "platformio",
            "stm32_framework": "stm32cube",
            "stm32_board": "f405rg",
        },
        id="stm32-platformio-stm32cube",
    ),
]

MAKE_TARGETS = (
    "make create_environment",
    "make build",
    "make upload",
    "make monitor",
    "make test",
    "make sim",
    "make clean",
)

SIMULATOR_LIMITS = [
    pytest.param(
        {"platform": "arduino", "arduino_board": "uno"},
        ("simavr", "128 KB", "does not model"),
        (),
        "upload to the board and observe the boot line",
        id="arduino-uno",
    ),
    pytest.param(
        {"platform": "avr", "avr_language": "c", "avr_mcu": "atmega328p"},
        ("simavr", "128 KB", "does not model"),
        (),
        "upload to the board and observe the boot line",
        id="avr-c",
    ),
    pytest.param(
        {"platform": "esp", "esp_chip": "esp32", "esp_framework": "espidf"},
        ("Espressif QEMU fork", "does not model the radio"),
        (),
        "use the board for radio and timing cases",
        id="esp32-espidf",
    ),
    pytest.param(
        {"platform": "esp", "esp_chip": "esp32", "esp_framework": "arduino"},
        ("Espressif QEMU fork", "does not model the radio"),
        (),
        "upload to the board and observe the boot line",
        id="esp32-arduino",
    ),
    pytest.param(
        {"platform": "esp", "esp_chip": "esp8266", "esp_framework": "arduino"},
        ("No supported emulator", "no ESP8266 machine"),
        (),
        "upload to the board and observe the boot line",
        id="esp8266-arduino",
    ),
    pytest.param(
        {"platform": "stm32", "stm32_toolchain": "rust", "stm32_board": "f405rg"},
        ("QEMU", "not the board circuit"),
        ("netduinoplus2",),
        "use the board for the circuit and timing",
        id="stm32-rust-f405rg",
    ),
    pytest.param(
        {"platform": "stm32", "stm32_toolchain": "rust", "stm32_board": "f103c8"},
        ("No supported emulator", "QEMU has no machine"),
        (),
        "upload to the board and observe the boot line",
        id="stm32-rust-f103c8",
    ),
    pytest.param(
        {
            "platform": "stm32",
            "stm32_toolchain": "platformio",
            "stm32_framework": "stm32cube",
            "stm32_board": "f405rg",
        },
        ("QEMU", "not the board circuit"),
        ("netduinoplus2",),
        "use the board for the circuit and timing",
        id="stm32-platformio-stm32cube",
    ),
]


def section(text: str, heading: str) -> str:
    """The body of one level-two README section."""
    marker = f"## {heading}"
    assert marker in text, marker
    return text.split(marker, 1)[1].split("\n## ", 1)[0]


def table(text: str) -> list[list[str]]:
    """The rows of the first markdown table in the text, with the cells stripped."""
    rows = []
    for line in text.splitlines():
        if line.startswith("|"):
            rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return rows


def expected_simulator(answers: dict) -> str:
    """The Simulator cell the capability matrix carries for a branch (ACC-TMPL-45)."""
    if answers["platform"] in ("arduino", "avr"):
        return "simavr"
    if answers["platform"] == "esp":
        return "Espressif QEMU fork" if answers.get("esp_chip") == "esp32" else "HIL only"
    return "QEMU `netduinoplus2`" if answers.get("stm32_board") == "f405rg" else "HIL only"


def device_skill(project) -> str:
    """The device skill of the generated project."""
    paths = list((project / ".agents" / "skills").glob("*-device/SKILL.md"))
    assert len(paths) == 1, paths
    return paths[0].read_text()


@pytest.mark.parametrize("answers", README_MATRIX)
def test_readme_and_device_skill_route_every_command_through_make(answers):
    with bake(answers, components=COMPONENTS) as project:
        readme = (project / "README.md").read_text()
        skill = device_skill(project)
        for text in (readme, skill):
            for target in MAKE_TARGETS:
                assert target in text, target
            assert "pio run" not in text
            assert "cargo build" not in text
        if answers.get("stm32_toolchain") == "rust":
            console = [line for line in skill.splitlines() if "Console" in line]
            assert any(
                re.match(r"- Console: \d+ baud, 8N1\b", line) for line in console
            ) and not any(re.search(r"Console[^;|]*8E1", line) for line in console), console


@pytest.mark.parametrize(
    "answers, section_markers, readme_markers, workaround", SIMULATOR_LIMITS
)
def test_simulator_limits_name_the_emulator_and_a_limit(
    answers, section_markers, readme_markers, workaround
):
    with bake(answers, components=COMPONENTS) as project:
        readme = (project / "README.md").read_text()
        limits = section(readme, "Simulator limits")
        for marker in section_markers:
            assert marker in limits, marker
        assert workaround in limits, workaround
        for marker in readme_markers:
            assert marker in readme, marker


@pytest.mark.parametrize("answers", README_MATRIX)
def test_readme_documents_the_folder_structure_and_targets(answers):
    with bake(answers, components=COMPONENTS) as project:
        readme = (project / "README.md").read_text()
        assert "## Folder structure" in readme
        assert "## Targets" in readme
        structure = section(readme, "Folder structure")
        targets = section(readme, "Targets")
        assert "├── src/" in structure
        if answers.get("esp_framework") == "espidf":
            assert "├── main -> src" in structure
        else:
            assert "main -> src" not in structure
        assert "`main -> src` compatibility symlink" in readme
        assert "├── lib/" in structure
        assert "├── test/" in structure
        assert re.search(r"^\| `make build` \| build the firmware \|$", targets, re.MULTILINE)
        assert re.search(
            r"^\| `make env` \| alias for `make create_environment` \|$", targets, re.MULTILINE
        )
        assert (
            "| Host, simulator and functional tests | `test/host/`, `test/harness/`, "
            "`test/functional/` |"
        ) in readme
        capability = section(readme, "Test capability")
        for tier in ("Host", "Simulator", "HIL"):
            assert f"| {tier} |" in capability, tier


@pytest.mark.parametrize("answers", README_MATRIX)
def test_readme_states_the_test_capability_for_its_board(answers):
    """ACC-TMPL-45: the README states host, simulator and HIL for this board."""
    with bake(answers, components=COMPONENTS) as project:
        readme = (project / "README.md").read_text()
        rows = table(section(readme, "Test capability"))
        assert rows[0] == ["Tier", "Command", "This board"], rows[0]
        tiers = {row[0]: row for row in rows[2:] if len(row) == 3}
        assert set(tiers) == {"Host", "Simulator", "HIL"}, sorted(tiers)
        assert tiers["Host"][2].startswith("yes"), tiers["Host"]
        assert expected_simulator(answers) in tiers["Simulator"][2], tiers["Simulator"]
        assert tiers["HIL"][2].startswith("yes"), tiers["HIL"]


@pytest.mark.parametrize("answers", README_MATRIX)
def test_changelog_follows_keep_a_changelog(answers):
    with bake(answers, components=COMPONENTS) as project:
        changelog = project / "CHANGELOG.md"
        assert changelog.is_file()
        text = changelog.read_text()
        assert text.startswith("# Changelog")
        assert "Keep a Changelog" in text
        assert "keepachangelog.com" in text
        assert "## [Unreleased]" in text
