"""Every platform and every component selection answers make help."""

from __future__ import annotations

import contextlib
import os
import re
import subprocess

import pytest
from helpers import bake

DEFAULT_COMPONENTS = [
    "notebooks",
    "resources",
    "references",
    "simulator",
    "agents",
    "env-installers",
]
COMPONENTS = [
    "notebooks",
    "resources",
    "references",
    "data",
    "simulator",
    "ltspice",
    "docs",
    "ci",
    "agents",
    "env-installers",
]
PLATFORMS = [
    pytest.param({"platform": "arduino", "arduino_board": "uno"}, id="arduino-uno"),
    pytest.param({"platform": "avr", "avr_mcu": "atmega328p"}, id="avr-c-atmega328p"),
    pytest.param(
        {"platform": "avr", "avr_mcu": "atmega328p", "avr_language": "rust"},
        id="avr-rust-atmega328p",
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
        {
            "platform": "stm32",
            "stm32_toolchain": "platformio",
            "stm32_framework": "stm32cube",
            "stm32_board": "f405rg",
        },
        id="stm32-platformio-stm32cube",
    ),
]
LIFECYCLE = {"build", "upload", "monitor", "test", "clean", "help", "increment_version"}
FOLDERS = {
    "ltspice": "simulations",
    "docs": "docs",
    "data": "data",
    "ci": ".github",
    "agents": ".agents",
    "env-installers": "resources/envs",
}
ANSI = re.compile(r"\x1b\[[0-9;]*m")
ARDUINO = {"platform": "arduino", "arduino_board": "uno"}
COMPONENT_CASES = [
    case
    for component in COMPONENTS
    for case in (
        pytest.param(component, True, [component], id=f"{component}-selected"),
        pytest.param(
            component,
            False,
            [item for item in DEFAULT_COMPONENTS if item != component],
            id=f"{component}-absent",
        ),
    )
]


@pytest.fixture(scope="session")
def rendered():
    """One render per distinct answer set, shared by every case that needs it."""
    cache = {}
    stacks = []

    def project(answers, components):
        key = (tuple(sorted(answers.items())), tuple(components))
        if key not in cache:
            stack = contextlib.ExitStack()
            stacks.append(stack)
            cache[key] = stack.enter_context(bake(dict(answers), components=list(components)))
        return cache[key]

    yield project
    for stack in stacks:
        stack.close()


def run_help(project) -> str:
    environment = dict(os.environ)
    for name in ("MAKEFLAGS", "MAKELEVEL", "MFLAGS"):
        environment.pop(name, None)
    result = subprocess.run(
        ["make", "help"], cwd=project, capture_output=True, text=True, env=environment
    )
    assert result.returncode == 0, result.stderr
    return ANSI.sub("", result.stdout)


def help_names(output: str) -> set[str]:
    names = set()
    for line in output.splitlines():
        match = re.match(r"^([a-z_][a-z0-9_-]*)\s{2,}\S", line)
        if match:
            names.add(match.group(1))
    return names


def assert_help(project, answers, selected):
    """help answers, lists the lifecycle and shows only the selected targets and folders."""
    names = help_names(run_help(project))
    expected = set(LIFECYCLE)
    if "env-installers" in selected:
        expected.add("create_environment")
    if "simulator" in selected:
        expected.add("sim")
    if "ltspice" in selected:
        expected.add("ltspice")
    host = answers.get("host_side") == "Yes"
    if host:
        expected.update({"host-run", "host-app-test"})
    assert names == expected, sorted(names)

    makefile = (project / "Makefile").read_text()
    installers = "env-installers" in selected
    assert ("\ncreate_environment:" in makefile) is installers
    assert ("\nenv: create_environment" in makefile) is installers
    assert ("\nsim:" in makefile) is ("simulator" in selected)
    assert ("\nltspice:" in makefile) is ("ltspice" in selected)
    assert ("\nhost-run:" in makefile) is host
    assert ("\nhost-app-test:" in makefile) is host
    eeprom = answers["platform"] in {"arduino", "avr"}
    assert ("\neeprom-backup:" in makefile) is eeprom
    assert ("\neeprom-restore:" in makefile) is eeprom
    assert not {"eeprom-backup", "eeprom-restore"} & names

    for component, folder in FOLDERS.items():
        assert (project / folder).exists() is (component in selected), folder


@pytest.mark.parametrize("answers", PLATFORMS)
def test_platform_help(rendered, answers):
    project = rendered(answers, DEFAULT_COMPONENTS)
    assert_help(project, answers, DEFAULT_COMPONENTS)


@pytest.mark.parametrize("component, present, selected", COMPONENT_CASES)
def test_component_help(rendered, component, present, selected):
    project = rendered(ARDUINO, selected)
    assert_help(project, ARDUINO, selected)
    assert (component in selected) is present


@pytest.mark.parametrize("host_side", ["Yes", "No"])
def test_host_side_help(rendered, host_side):
    answers = {**ARDUINO, "host_side": host_side}
    project = rendered(answers, DEFAULT_COMPONENTS)
    assert_help(project, answers, DEFAULT_COMPONENTS)
