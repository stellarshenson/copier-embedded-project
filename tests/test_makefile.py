"""The generated Makefile carries the lifecycle of its platform and components."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from helpers import MATRIX, bake

DEFAULT = [
    "notebooks",
    "resources",
    "references",
    "simulator",
    "agents",
    "env-installers",
]
MINIMAL = ["notebooks"]
ANSI = re.compile(r"\x1b\[[0-9;]*m")
LIFECYCLE = {
    "create_environment",
    "build",
    "upload",
    "monitor",
    "test",
    "sim",
    "clean",
    "help",
    "increment_version",
}


def makefile(project) -> str:
    return (project / "Makefile").read_text()


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


def recipe_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.startswith("\t")]


def dry_run(project, target: str) -> str:
    result = subprocess.run(
        ["make", "-n", target], cwd=project, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


@pytest.mark.parametrize("answers", MATRIX)
def test_help_renders_for_every_branch(answers):
    with bake(answers, components=DEFAULT) as project:
        output = run_help(project)
        assert help_names(output) == LIFECYCLE


def test_help_lists_the_lifecycle_targets_with_descriptions():
    with bake({"platform": "arduino", "arduino_board": "uno"}, components=DEFAULT) as project:
        output = run_help(project)
        names = help_names(output)
        assert names == LIFECYCLE
        for line in output.splitlines():
            if line.split()[:1] and line.split()[0] in LIFECYCLE:
                assert len(line.split()) > 1, line
        assert "Install the conda environment" in output
        assert "Build the firmware" in output
        assert "Upload the firmware" in output
        assert "Open the serial console" in output
        assert "host unit tests" in output
        assert "firmware in the simulator" in output
        assert "build output" in output
        assert "available commands" in output
        assert "host-test" not in output
        assert "eeprom-backup" not in output
        assert "eeprom-restore" not in output


@pytest.mark.parametrize(
    "platform, installer",
    [
        ("arduino", "firmware-avr.py"),
        ("avr", "firmware-avr.py"),
        ("esp", "firmware-esp.py"),
        ("stm32", "firmware-stm32.py"),
    ],
)
def test_help_names_the_lab_installer_without_env_installers(platform, installer):
    answers = {"platform": platform}
    with bake(answers, components=MINIMAL) as project:
        output = run_help(project)
        assert f"~/.local/lab-utils/envs/{installer}" in output
        assert help_names(output) == LIFECYCLE - {"create_environment", "sim"}
        assert "create_environment" not in makefile(project)


def test_create_environment_runs_the_platform_installer():
    answers = {"platform": "stm32", "stm32_toolchain": "rust", "stm32_board": "f405rg"}
    with bake(answers, components=DEFAULT) as project:
        text = makefile(project)
        assert "create_environment:" in text
        assert "./resources/envs/firmware-stm32.py" in text
        assert "env: create_environment" in text
        assert "firmware-stm32.py" in dry_run(project, "create_environment")
        assert "create_environment" in help_names(run_help(project))


@pytest.mark.parametrize("scope, local", [("global", False), ("local", True)])
def test_environment_scope_selects_the_conda_root(scope, local):
    answers = {"platform": "arduino", "environment_scope": scope}
    with bake(answers, components=DEFAULT) as project:
        text = makefile(project)
        line = "export CONDA_ENVS_PATH := $(PROJECT_DIR)/.conda/envs"
        assert (line in text) is local
        assert "firmware-avr.py" in dry_run(project, "create_environment")


def test_upload_and_monitor_take_port_and_baud():
    with bake({"platform": "arduino", "arduino_board": "uno"}, components=DEFAULT) as project:
        text = makefile(project)
        assert "PORT ?= /dev/ttyUSB0" in text
        assert re.search(r"^BAUD \?= \d+$", text, re.MULTILINE)
        assert "pio run -t upload --upload-port $(PORT)" in text
        assert "pio device monitor --port $(PORT) -b $(BAUD)" in text


def test_ltspice_target_is_opt_in():
    with bake({"platform": "arduino"}, components=DEFAULT + ["ltspice"]) as project:
        assert "ltspice" in help_names(run_help(project))
        test_line = next(
            line for line in makefile(project).splitlines() if line.startswith("test:")
        )
        assert "ltspice" in test_line

    with bake({"platform": "arduino"}, components=DEFAULT) as project:
        assert "ltspice" not in help_names(run_help(project))


@pytest.mark.parametrize("answers", MATRIX)
def test_every_toolchain_command_runs_inside_the_environment(answers):
    with bake(answers, components=DEFAULT) as project:
        for line in recipe_lines(makefile(project)):
            recipe = line.lstrip("\t@")
            if (
                "$(ENV_RUN)" in recipe
                or recipe.startswith("echo ")
                or "resources/envs/" in recipe
            ):
                continue
            for tool in ("pio", "cargo", "avrdude", "stm32flash", "pytest", "miniterm"):
                assert not re.search(rf"(?<![\w.]){tool}\b", recipe), line


@pytest.mark.parametrize(
    "answers",
    [
        {"platform": "arduino", "arduino_board": "uno"},
        {"platform": "avr", "avr_mcu": "atmega328p", "avr_language": "c"},
        {"platform": "esp", "esp_chip": "esp32", "esp_framework": "espidf"},
        {
            "platform": "stm32",
            "stm32_toolchain": "platformio",
            "stm32_framework": "stm32cube",
            "stm32_board": "f405rg",
        },
    ],
)
def test_platformio_branches_call_pio(answers):
    with bake(answers, components=DEFAULT) as project:
        text = makefile(project)
        assert "$(ENV_RUN) pio run" in text
        assert "$(ENV_RUN) pio run -t upload --upload-port $(PORT)" in text
        assert "$(ENV_RUN) pio device monitor --port $(PORT) -b $(BAUD)" in text
        assert "cargo" not in text


def test_bare_avr_rust_calls_cargo_and_avrdude():
    answers = {"platform": "avr", "avr_mcu": "atmega328p", "avr_language": "rust"}
    with bake(answers, components=DEFAULT) as project:
        text = makefile(project)
        assert "$(ENV_RUN) cargo build --release --target avr-none" in text
        assert "$(ENV_RUN) avrdude -c usbasp -p atmega328p -P $(PORT)" in text
        assert "-U flash:w:target/avr-none/release/board.elf:e" in text
        assert "python -m serial.tools.miniterm $(PORT) $(BAUD)" in text
        assert "$(ENV_RUN) pio run" not in text


def test_stm32_rust_uses_stm32flash():
    answers = {"platform": "stm32", "stm32_toolchain": "rust", "stm32_board": "f103c8"}
    with bake(answers, components=DEFAULT) as project:
        text = makefile(project)
        assert "$(ENV_RUN) cargo build --release --target thumbv7m-none-eabi" in text
        assert "cargo objcopy --release --target thumbv7m-none-eabi" in text
        assert "stm32flash -b $(BAUD) -m $(STM32_SERIAL_MODE)" in text
        assert "-w $(BUILD_DIR)/board.bin -v -g 0x0 $(PORT)" in text
        assert "STM32_SERIAL_MODE = 8e1" in text


def test_device_bridge_selects_the_pty_and_eight_n_one():
    answers = {"platform": "stm32", "stm32_toolchain": "rust", "stm32_board": "f103c8"}
    with bake(answers, components=DEFAULT + ["device-bridge"]) as project:
        text = makefile(project)
        assert "DEVICE_DIR" in text
        assert "/run/devices" in text
        assert "/tmp/jupyterlab-device-" in text
        assert "tty-*" in text
        assert "PORT ?= " in text
        assert "STM32_SERIAL_MODE = 8n1" in text


def test_host_tests_compile_the_shared_core():
    with bake({"platform": "arduino", "arduino_board": "uno"}, components=DEFAULT) as project:
        text = makefile(project)
        assert "$(HOST_CC)" in text
        assert "lib/core/core.c" in text
        assert "test/host/test_core.c" in text
        assert "$(ENV_RUN) ./$(BUILD_DIR)/host-test" in text


def test_host_tests_run_cargo_for_rust():
    answers = {"platform": "avr", "avr_mcu": "atmega328p", "avr_language": "rust"}
    with bake(answers, components=DEFAULT) as project:
        assert "$(ENV_RUN) cargo test" in makefile(project)


def test_test_target_and_sim_follow_the_simulator_component():
    with bake({"platform": "arduino", "arduino_board": "uno"}, components=DEFAULT) as project:
        text = makefile(project)
        assert "test: host-test sim" in text
        assert "sim: build $(SIMHARNESS)" in text
        assert "pytest test/functional -q" in text
    with bake({"platform": "arduino", "arduino_board": "uno"}, components=MINIMAL) as project:
        text = makefile(project)
        assert "test: host-test" in text
        assert "\nsim:" not in text
        assert "pytest test/functional" not in text


def test_simavr_branches_build_the_harness():
    with bake({"platform": "arduino", "arduino_board": "uno"}, components=DEFAULT) as project:
        text = makefile(project)
        assert "SIMHARNESS = .pio/simharness/libsimharness.so" in text
        assert "$(SIMHARNESS): test/harness/simharness.c" in text
        assert "-lsimavr" in text
        assert "$(ENV_RUN) sh -c" in text
    answers = {"platform": "esp", "esp_chip": "esp32", "esp_framework": "espidf"}
    with bake(answers, components=DEFAULT) as project:
        text = makefile(project)
        assert "SIMHARNESS" not in text
        assert "sim: build\n" in text
        assert "qemu-system-xtensa" in text


@pytest.mark.parametrize(
    "answers",
    [
        {"platform": "arduino", "arduino_board": "uno"},
        {"platform": "avr", "avr_mcu": "atmega328p", "avr_language": "c"},
    ],
)
def test_eeprom_targets_exist_for_arduino_and_bare_avr(answers):
    with bake(answers, components=DEFAULT) as project:
        text = makefile(project)
        assert "\neeprom-backup:" in text
        assert "\neeprom-restore:" in text
        assert "tools/eeprom_tool.py backup" in text
        assert "tools/eeprom_tool.py restore" in text
        assert "resources/eeprom/" in text
        assert "eeprom-backup" not in run_help(project)
        assert "eeprom-restore" not in run_help(project)


@pytest.mark.parametrize(
    "answers",
    [
        {"platform": "esp", "esp_chip": "esp32", "esp_framework": "espidf"},
        {"platform": "stm32", "stm32_toolchain": "rust", "stm32_board": "f103c8"},
    ],
)
def test_eeprom_targets_are_absent_outside_avr(answers):
    with bake(answers, components=DEFAULT) as project:
        text = makefile(project)
        assert "eeprom" not in text
        assert "tools/eeprom_tool.py" not in text


@pytest.mark.parametrize("answers", MATRIX)
def test_no_erase_target(answers):
    with bake(answers, components=DEFAULT) as project:
        text = makefile(project)
        assert "\nerase:" not in text
        assert "pio run -t erase" not in text


def test_clean_keeps_the_environment_and_the_eeprom_images():
    with bake({"platform": "arduino", "arduino_board": "uno"}, components=DEFAULT) as project:
        text = makefile(project)
        clean = text.split("\nclean:", 1)[1].split("\n\n", 1)[0]
        assert ".conda" not in clean
        assert "resources/eeprom" not in clean


def test_bare_avr_arduino_isp_maps_to_arduinoisp():
    answers = {
        "platform": "avr",
        "avr_mcu": "attiny85",
        "avr_language": "rust",
        "avr_programmer": "arduino-isp",
    }
    with bake(answers, components=DEFAULT) as project:
        text = makefile(project)
        assert "$(ENV_RUN) avrdude -c arduinoisp -p attiny85 -P $(PORT)" in text
        assert "tools/eeprom_tool.py backup --port $(PORT) --mcu attiny85" in text
        assert "--programmer arduinoisp" in text


def test_arduino_eeprom_targets_name_the_board_and_no_programmer():
    with bake({"platform": "arduino", "arduino_board": "nano"}, components=DEFAULT) as project:
        text = makefile(project)
        assert "tools/eeprom_tool.py backup --board nanoatmega328 --port $(PORT)" in text
        assert "tools/eeprom_tool.py restore --board nanoatmega328 --port $(PORT)" in text
        eeprom = text.split("\neeprom-backup:", 1)[1]
        assert "--programmer" not in eeprom


@pytest.mark.parametrize(
    "answers, reason",
    [
        (
            {"platform": "arduino", "arduino_board": "mega2560"},
            "256 KB is above simavr's documented 128 KB limit",
        ),
        (
            {"platform": "arduino", "arduino_board": "leonardo"},
            "simavr does not document the ATmega32U4",
        ),
        (
            {"platform": "avr", "avr_mcu": "atmega32u4"},
            "simavr does not document the ATmega32U4",
        ),
        (
            {"platform": "esp", "esp_chip": "esp8266", "esp_framework": "arduino"},
            "mainline QEMU has no ESP8266 machine",
        ),
        (
            {
                "platform": "stm32",
                "stm32_toolchain": "rust",
                "stm32_board": "f103c8",
            },
            "no QEMU machine for this STM32 board",
        ),
    ],
)
def test_sim_skips_with_a_written_reason(answers, reason):
    with bake(answers, components=DEFAULT) as project:
        sim = makefile(project).split("\nsim:", 1)[1].split("\n\n", 1)[0]
        assert reason in sim
        assert "pytest" not in sim


@pytest.mark.parametrize(
    "answers, binary",
    [
        (
            {"platform": "esp", "esp_chip": "esp32", "esp_framework": "espidf"},
            "qemu-system-xtensa",
        ),
        (
            {"platform": "stm32", "stm32_toolchain": "rust", "stm32_board": "f405rg"},
            "qemu-system-arm",
        ),
    ],
)
def test_qemu_sim_probes_the_binary_before_it_runs_pytest(answers, binary):
    with bake(answers, components=DEFAULT) as project:
        sim = makefile(project).split("\nsim:", 1)[1].split("\n\n", 1)[0]
        assert f"command -v {binary}" in sim
        assert f"Skipping the simulator: {binary} is not installed" in sim
        assert "pytest test/functional -q" in sim


FAKE_AVRDUDE = '''#!/usr/bin/env python3
import os
import sys

args = sys.argv[1:]
state = os.environ["FAKE_AVRDUDE_STATE"]
action = kind = path = None
for index, value in enumerate(args):
    if value == "-U":
        action, _, rest = args[index + 1].partition(":")
        kind, _, target = rest.partition(":")
        path = target.rsplit(":", 1)[0]
if action != "eeprom":
    sys.exit(2)
if kind == "r":
    data = open(state, "rb").read() if os.path.exists(state) else b"\\x00\\x01\\x02\\x03"
    if os.environ.get("FAKE_AVRDUDE_MISMATCH") and "readback" in path:
        data = b"\\xff" * len(data)
    open(path, "wb").write(data)
else:
    open(state, "wb").write(open(path, "rb").read())
'''


def fake_avrdude(project):
    """Put a fake avrdude on PATH and return the environment and the device state path."""
    binary = project.parent / "fakebin"
    binary.mkdir()
    tool = binary / "avrdude"
    tool.write_text(FAKE_AVRDUDE)
    tool.chmod(0o755)
    state = project.parent / "device-eeprom.bin"
    environment = dict(os.environ)
    environment["PATH"] = f"{binary}:{environment['PATH']}"
    environment["FAKE_AVRDUDE_STATE"] = str(state)
    return environment, state


def run_eeprom(project, environment, *arguments):
    result = subprocess.run(
        [sys.executable, str(project / "tools" / "eeprom_tool.py"), *arguments],
        cwd=project,
        capture_output=True,
        text=True,
        env=environment,
    )
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 1, result.stdout + result.stderr
    return result, json.loads(lines[0])


def test_eeprom_tool_backs_up_and_restores_with_verification():
    with bake({"platform": "arduino", "arduino_board": "uno"}, components=DEFAULT) as project:
        environment, state = fake_avrdude(project)
        result, payload = run_eeprom(
            project, environment, "backup", "--board", "uno", "--port", "/dev/fake"
        )
        assert result.returncode == 0, result.stderr
        assert payload["ok"] is True
        assert payload["bytes"] == 4
        image = Path(payload["file"])
        assert image.parent == project / "resources" / "eeprom"
        assert image.read_bytes() == b"\x00\x01\x02\x03"

        result, payload = run_eeprom(
            project, environment, "restore", "--board", "uno", "--port", "/dev/fake"
        )
        assert result.returncode == 0, result.stderr
        assert payload["ok"] is True
        assert payload["verified"] is True
        assert payload["bytes"] == 4
        assert state.read_bytes() == b"\x00\x01\x02\x03"


def test_eeprom_tool_fails_when_the_read_back_differs():
    with bake({"platform": "arduino", "arduino_board": "uno"}, components=DEFAULT) as project:
        environment, _ = fake_avrdude(project)
        run_eeprom(project, environment, "backup", "--board", "uno")
        environment["FAKE_AVRDUDE_MISMATCH"] = "1"
        result, payload = run_eeprom(project, environment, "restore", "--board", "uno")
        assert result.returncode == 1
        assert payload["ok"] is False
        assert "read-back does not match" in payload["error"]


def test_eeprom_tool_reports_an_unknown_board_without_avrdude():
    with bake({"platform": "arduino", "arduino_board": "uno"}, components=DEFAULT) as project:
        result, payload = run_eeprom(project, None, "backup", "--board", "mystery")
        assert result.returncode == 1
        assert payload["ok"] is False
        assert "unknown board" in payload["error"]
