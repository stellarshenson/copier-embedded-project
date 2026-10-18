"""Contracts of the rendered platform branches: the shared core, STM32 upload and environment scope."""

from __future__ import annotations

import os
import subprocess

import pytest
from helpers import bake, files

# Every C and C++ row of the per-toolchain layout table in docs/template-design.md 3.3.
C_CASES = [
    pytest.param({"platform": "arduino", "arduino_board": "uno"}, id="arduino-uno"),
    pytest.param(
        {"platform": "arduino", "arduino_board": "nano", "arduino_bootloader": "new"},
        id="arduino-nano-new",
    ),
    pytest.param(
        {"platform": "avr", "avr_language": "c", "avr_mcu": "atmega328p"}, id="avr-c"
    ),
    pytest.param(
        {"platform": "avr", "avr_language": "cpp", "avr_mcu": "atmega328p"}, id="avr-cpp"
    ),
    pytest.param(
        {
            "platform": "esp",
            "esp_chip": "esp32",
            "esp_framework": "espidf",
            "esp_board": "esp32dev",
        },
        id="esp32-espidf",
    ),
    pytest.param(
        {
            "platform": "esp",
            "esp_chip": "esp32",
            "esp_framework": "arduino",
            "esp_board": "esp32dev",
        },
        id="esp32-arduino",
    ),
    pytest.param(
        {
            "platform": "esp",
            "esp_chip": "esp8266",
            "esp_framework": "arduino",
            "esp_board": "nodemcuv2",
        },
        id="esp8266-arduino",
    ),
    pytest.param(
        {
            "platform": "esp",
            "esp_chip": "esp8266",
            "esp_framework": "esp8266-rtos-sdk",
            "esp_board": "nodemcuv2",
        },
        id="esp8266-rtos",
    ),
    pytest.param(
        {
            "platform": "stm32",
            "stm32_toolchain": "platformio",
            "stm32_framework": "stm32cube",
            "stm32_board": "f405rg",
        },
        id="stm32-pio-cube",
    ),
    pytest.param(
        {
            "platform": "stm32",
            "stm32_toolchain": "platformio",
            "stm32_framework": "arduino",
            "stm32_board": "f405rg",
        },
        id="stm32-pio-arduino",
    ),
]

STM32_PLATFORMIO = {
    "platform": "stm32",
    "stm32_toolchain": "platformio",
    "stm32_framework": "stm32cube",
    "stm32_board": "f405rg",
}

ENVIRONMENTS = [
    pytest.param(
        {"platform": "arduino", "arduino_board": "uno"},
        "firmware-avr",
        "firmware-avr.py",
        id="arduino",
    ),
    pytest.param(
        {"platform": "avr", "avr_language": "c", "avr_mcu": "atmega328p"},
        "firmware-avr",
        "firmware-avr.py",
        id="avr",
    ),
    pytest.param(
        {
            "platform": "esp",
            "esp_chip": "esp32",
            "esp_framework": "espidf",
            "esp_board": "esp32dev",
        },
        "firmware-esp",
        "firmware-esp.py",
        id="esp",
    ),
    pytest.param(
        {"platform": "stm32", "stm32_toolchain": "rust", "stm32_board": "f405rg"},
        "firmware-stm32",
        "firmware-stm32.py",
        id="stm32-rust",
    ),
    pytest.param(
        dict(STM32_PLATFORMIO, stm32_framework="stm32cube"),
        "firmware-stm32",
        "firmware-stm32.py",
        id="stm32-platformio",
    ),
]


def library_table(project) -> tuple[list[str], list[list[str]]]:
    """The header and data rows of the library register table, with the cells stripped."""
    header = []
    rows = []
    for line in (project / "lib" / "README.md").read_text().splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or not cells[0]:
            continue
        if cells[0] == "Library":
            header = cells
            continue
        if set(cells[0]) <= {"-", ":"}:
            continue
        rows.append(cells)
    return header, rows


def exported_conda_envs_path(project) -> str:
    """Run a make target that prints the exported CONDA_ENVS_PATH from its own environment."""
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in {"CONDA_ENVS_PATH", "MAKEFLAGS", "MAKELEVEL", "MFLAGS"}
    }
    result = subprocess.run(
        [
            "make",
            "--eval",
            'print-conda-envs-path: ; @printf "%s" "$$CONDA_ENVS_PATH"',
            "print-conda-envs-path",
        ],
        cwd=project,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


@pytest.mark.parametrize("answers", C_CASES)
def test_every_c_and_cpp_render_keeps_the_shared_core(answers):
    """ACC-TMPL-23: lib/core is always present, independent of arduino_libraries."""
    with bake(answers) as project:
        present = files(project)
        assert {"lib/core/core.c", "lib/core/core.h"} <= present
        assert "lib/README.md" in present
        assert "`lib/core/core.c`" in (project / "lib" / "README.md").read_text()


def test_arduino_libraries_controls_the_vendor_tree_and_its_register_rows():
    """ACC-TMPL-23: Yes adds lib/vendor and versioned rows; No keeps lib/core without vendor."""
    for answer in ("No", "Yes"):
        answers = {"platform": "arduino", "arduino_board": "uno", "arduino_libraries": answer}
        with bake(answers) as project:
            present = files(project)
            assert {"lib/core/core.c", "lib/core/core.h"} <= present
            assert (project / "lib" / "vendor").is_dir() is (answer == "Yes")
            header, rows = library_table(project)
            assert "Library" in header and "Version" in header, header
            version = header.index("Version")
            assert rows, answer
            assert all(len(row) == len(header) and row[0] and row[version] for row in rows), rows
            vendor_rows = [row for row in rows if row[0].startswith("vendor/")]
            assert bool(vendor_rows) is (answer == "Yes"), answer


@pytest.mark.parametrize(
    "answers, protocol",
    [
        pytest.param(dict(STM32_PLATFORMIO, stm32_upload="serial"), "serial", id="serial"),
        pytest.param(dict(STM32_PLATFORMIO, stm32_upload="stlink"), "stlink", id="stlink"),
    ],
)
def test_stm32_upload_selects_the_platformio_protocol(answers, protocol):
    """ACC-TMPL-28: the upload answer sets upload_protocol in platformio.ini."""
    with bake(answers) as project:
        ini = (project / "platformio.ini").read_text()
        assert f"upload_protocol = {protocol}" in ini
        assert ini.count("upload_protocol") == 1


def test_stm32_f405rg_defaults_to_the_serial_upload():
    """ACC-TMPL-28: f405rg defaults to serial."""
    with bake(STM32_PLATFORMIO) as project:
        assert "upload_protocol = serial" in (project / "platformio.ini").read_text()


def test_stm32_serial_upload_is_documented_as_stm32flash():
    """ACC-TMPL-28: the generated AGENTS.md says the serial branch uploads through stm32flash."""
    with bake(dict(STM32_PLATFORMIO, stm32_upload="serial")) as project:
        agents = (project / "AGENTS.md").read_text()
        assert "stm32flash" in agents
        assert "STM32 ROM serial bootloader" in agents


@pytest.mark.parametrize("scope", ["global", "local"])
@pytest.mark.parametrize("answers, env_name, installer", ENVIRONMENTS)
def test_environment_scope_switches_the_export_and_the_installer(
    answers, env_name, installer, scope
):
    """ACC-TMPL-42: the scope switches CONDA_ENVS_PATH; create_environment runs the installer."""
    with bake(dict(answers, environment_scope=scope)) as project:
        text = (project / "Makefile").read_text()
        assert f"ENV = {env_name}" in text
        export = "export CONDA_ENVS_PATH := $(PROJECT_DIR)/.conda/envs"
        assert (export in text) is (scope == "local")
        expected = str(project / ".conda" / "envs") if scope == "local" else ""
        assert exported_conda_envs_path(project) == expected
        result = subprocess.run(
            ["make", "-n", "create_environment"], cwd=project, capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr
        assert f"./resources/envs/{installer}" in result.stdout
