"""The ci component renders the GitHub Actions workflow and only with it."""

from __future__ import annotations

import re

import pytest
import yaml
from helpers import ROOT, bake

COMPONENTS = [
    "notebooks",
    "resources",
    "references",
    "simulator",
    "agents",
    "env-installers",
]
WITH_CI = [*COMPONENTS, "ci"]
EXPRESSION = re.compile(r"\$\{\{.*?\}\}")

CASES = [
    pytest.param(
        {"platform": "arduino", "arduino_board": "uno"},
        ".pio/build/uno",
        id="arduino-uno",
    ),
    pytest.param(
        {"platform": "arduino", "arduino_board": "nano", "arduino_bootloader": "new"},
        ".pio/build/nanoatmega328new",
        id="arduino-nano-new",
    ),
    pytest.param(
        {"platform": "avr", "avr_mcu": "atmega328p"},
        ".pio/build/uno",
        id="avr-328p",
    ),
    pytest.param(
        {"platform": "avr", "avr_mcu": "attiny85"},
        ".pio/build/attiny85",
        id="avr-attiny85",
    ),
    pytest.param(
        {"platform": "avr", "avr_language": "rust", "avr_mcu": "atmega328p"},
        "target/avr-none/release/board",
        id="avr-rust",
    ),
    pytest.param(
        {"platform": "esp", "esp_chip": "esp32", "esp_framework": "espidf"},
        ".pio/build/esp32dev",
        id="esp32-espidf",
    ),
    pytest.param(
        {"platform": "esp", "esp_chip": "esp8266", "esp_framework": "arduino"},
        ".pio/build/nodemcuv2",
        id="esp8266-arduino",
    ),
    pytest.param(
        {"platform": "stm32", "stm32_toolchain": "rust", "stm32_board": "f405rg"},
        "target/thumbv7em-none-eabihf/release/board",
        id="stm32-rust",
    ),
    pytest.param(
        {
            "platform": "stm32",
            "stm32_toolchain": "platformio",
            "stm32_framework": "stm32cube",
            "stm32_board": "f405rg",
        },
        ".pio/build/genericSTM32F405RG",
        id="stm32-pio",
    ),
]


@pytest.mark.parametrize("answers, output", CASES)
def test_ci_builds_tests_and_uploads(answers, output):
    """The build job installs, builds, tests, and uploads the platform output."""
    with bake(answers, components=WITH_CI) as project:
        text = (project / ".github" / "workflows" / "build.yml").read_text()
        for expected in (
            "make env",
            "make build",
            "make test",
            "actions/upload-artifact",
            "path: dist/",
            "actions/cache",
            ".conda/envs",
            "ENV_SCOPE: local",
            output,
        ):
            assert expected in text, expected


def test_ci_release_publishes_on_tags():
    """A v* tag matching VERSION publishes the downloaded firmware artifact."""
    with bake({"platform": "arduino", "arduino_board": "uno"}, components=WITH_CI) as project:
        text = (project / ".github" / "workflows" / "build.yml").read_text()
        for expected in (
            "startsWith(github.ref, 'refs/tags/v')",
            'test "v$(cat VERSION)"',
            "gh release create",
            "contents: write",
            "actions/download-artifact",
            "release-notes.md",
        ):
            assert expected in text, expected


def test_ci_without_env_installers_stops_with_a_reason():
    """Without env-installers the build job explains the missing component and fails."""
    components = [name for name in WITH_CI if name != "env-installers"]
    with bake({"platform": "arduino", "arduino_board": "uno"}, components=components) as project:
        text = (project / ".github" / "workflows" / "build.yml").read_text()
        assert "This project was generated without the env-installers component" in text
        assert "exit 1" in text
        assert "make env" not in text
        steps = yaml.safe_load(text)["jobs"]["build"]["steps"]
        assert not any("make build" in (step.get("run") or "") for step in steps)


def test_ci_absent_without_the_component():
    """A project rendered without ci carries no workflow."""
    with bake({"platform": "arduino", "arduino_board": "uno"}, components=COMPONENTS) as project:
        assert not (project / ".github" / "workflows").exists()


def test_template_repository_ci():
    """The template repository workflow runs the local gates and the AVR toolchain."""
    text = (ROOT / ".github" / "workflows" / "test.yml").read_text()
    for expected in (
        "make setup",
        "make test",
        "make lint",
        "make test-toolchain",
        "./envs/firmware-avr.py",
    ):
        assert expected in text, expected
    assert "make test-functional" not in text


def test_rendered_ci_has_expressions_and_no_jinja():
    """The rendered workflow keeps its GitHub expressions and holds no template syntax."""
    with bake({"platform": "arduino", "arduino_board": "uno"}, components=WITH_CI) as project:
        text = (project / ".github" / "workflows" / "build.yml").read_text()
        assert EXPRESSION.search(text), "the workflow holds no GitHub expression"
        stripped = EXPRESSION.sub("", text)
        for token in ("{{", "}}", "{%", "%}", "{#", "#}"):
            assert token not in stripped, token
