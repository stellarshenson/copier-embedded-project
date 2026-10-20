"""Helpers of the template tests: render a project into a temporary directory."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LAB_ENVS = Path.home() / ".local" / "lab-utils" / "envs"

TEXT_SUFFIXES = {
    ".c", ".h", ".cpp", ".hpp", ".rs", ".toml", ".ini", ".yml", ".yaml", ".md", ".py",
    ".txt", ".json", ".gitignore", ".ipynb",
}

MATRIX = [
    pytest.param({"platform": "arduino", "arduino_board": "uno"}, id="arduino-uno"),
    pytest.param(
        {"platform": "arduino", "arduino_board": "nano", "arduino_bootloader": "new"},
        id="arduino-nano-new",
    ),
    pytest.param({"platform": "avr", "avr_mcu": "atmega328p"}, id="avr-328p"),
    pytest.param({"platform": "avr", "avr_mcu": "attiny85"}, id="avr-attiny85"),
    pytest.param(
        {"platform": "esp", "esp_chip": "esp32", "esp_framework": "espidf"}, id="esp32-espidf"
    ),
    pytest.param(
        {"platform": "esp", "esp_chip": "esp8266", "esp_framework": "arduino"},
        id="esp8266-arduino",
    ),
    pytest.param(
        {"platform": "stm32", "stm32_toolchain": "rust", "stm32_board": "f405rg"}, id="stm32-rust"
    ),
    pytest.param(
        {
            "platform": "stm32",
            "stm32_toolchain": "platformio",
            "stm32_framework": "stm32cube",
            "stm32_board": "f405rg",
        },
        id="stm32-pio",
    ),
]


def copier() -> str:
    """The copier executable, or a skip."""
    beside = Path(sys.executable).parent / "copier"
    if beside.exists():
        return str(beside)
    found = shutil.which("copier")
    if not found:
        pytest.skip("copier is not installed")
    return found


@contextmanager
def bake(answers: dict, components: list[str] | None = None):
    """Render the template into a temporary directory and yield the project path."""
    temp = Path(tempfile.mkdtemp(prefix="ce-test-"))
    destination = temp / answers.get("repo_name", "board")
    # --vcs-ref HEAD renders the working tree; without it copier takes the latest tag.
    command = [
        copier(), "copy", "--trust", "--defaults", "--vcs-ref", "HEAD", str(ROOT), str(destination)
    ]
    for key, value in answers.items():
        command.extend(["-d", f"{key}={value}"])
    if components is not None:
        command.extend(["-d", "components=" + json.dumps(components)])
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    try:
        yield destination
    finally:
        shutil.rmtree(temp)


def files(project: Path) -> set[str]:
    """Every file of the project as a relative path, without the git internals."""
    return {
        str(path.relative_to(project))
        for path in project.rglob("*")
        if path.is_file() and ".git/" not in str(path.relative_to(project)) + "/"
    }


def text_files(project: Path) -> list[Path]:
    """Files that must render as text: the source, the build files, the documents."""
    chosen = []
    for path in project.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix in TEXT_SUFFIXES or path.name in {".gitignore", "Makefile"}:
            chosen.append(path)
    return chosen
