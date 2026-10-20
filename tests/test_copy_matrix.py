"""The questionnaire asks the platform first and maps every answer to one scaffold."""

from __future__ import annotations

import os
import re
import subprocess

import pytest
import yaml
from helpers import ROOT, bake, text_files
from jinja2 import Environment

CONFIG = yaml.safe_load((ROOT / "copier.yml").read_text())

DERIVED = [
    "project_name",
    "repo_name",
    "author_email",
    "author_name_clean",
    "author_first_name",
    "author_last_name",
    "serial_baud",
    "env_name",
    "env_local",
    "toolchain_language",
    "crate_name",
    "avr_target",
    "avr_cpu",
    "pio_platform",
    "pio_board",
    "pio_framework",
    "pio_upload_protocol",
    "thumb_target",
    "flash_kb",
    "ram_kb",
]

BASE_ANSWERS = {
    "project_name": "board",
    "repo_name": "board",
    "platform": "arduino",
    "arduino_board": "uno",
    "arduino_board_custom": "",
    "arduino_bootloader": "old",
    "arduino_libraries": "No",
    "arduino_sketch_link": "No",
    "avr_language": "c",
    "avr_mcu": "atmega328p",
    "avr_mcu_custom": "",
    "avr_clock": "16000000",
    "avr_programmer": "usbasp",
    "esp_chip": "esp32",
    "esp_framework": "espidf",
    "esp_board": "esp32dev",
    "stm32_toolchain": "rust",
    "stm32_board": "f405rg",
    "stm32_framework": "stm32cube",
    "stm32_upload": "serial",
    "environment_scope": "global",
}


def render(name: str, **overrides: str) -> str:
    context = dict(BASE_ANSWERS)
    context.update(overrides)
    template = Environment().from_string(str(CONFIG[name]["default"]))
    return template.render(**context).strip()


def choices(name: str, **overrides: str) -> list[str]:
    context = dict(BASE_ANSWERS)
    context.update(overrides)
    template = Environment().from_string(str(CONFIG[name]["choices"]))
    return yaml.safe_load(template.render(**context))


def hidden(question: dict) -> bool:
    return question.get("when") is False or question.get("ask") is False


def test_platform_is_the_first_entry_and_question():
    questions = [name for name in CONFIG if not name.startswith("_")]
    assert questions[0] == "platform"
    assert CONFIG["platform"]["choices"] == ["arduino", "avr", "esp", "stm32"]
    assert CONFIG["platform"]["default"] == "arduino"


def test_components_is_the_last_visible_question():
    visible = [
        name
        for name, question in CONFIG.items()
        if not name.startswith("_") and not hidden(question)
    ]
    assert visible[0] == "platform"
    assert visible[-1] == "components"
    assert CONFIG["components"]["multiselect"] is True


@pytest.mark.parametrize(
    "name, expected, default",
    [
        ("arduino_board", ["uno", "nano", "mega2560", "leonardo", "other"], "uno"),
        ("arduino_bootloader", ["old", "new"], "old"),
        ("arduino_libraries", ["No", "Yes"], "No"),
        ("arduino_sketch_link", ["Yes", "No"], "No"),
        ("avr_language", ["c", "cpp", "rust"], "c"),
        ("avr_mcu", ["atmega328p", "atmega32u4", "attiny85", "other"], "atmega328p"),
        ("avr_clock", ["16000000", "8000000"], "16000000"),
        ("avr_programmer", ["usbasp", "arduino-isp"], "usbasp"),
        ("esp_chip", ["esp32", "esp8266"], "esp32"),
        ("stm32_toolchain", ["rust", "platformio"], "rust"),
        ("stm32_board", ["f405rg", "f103c8", "f411re", "l476rg"], "f405rg"),
        ("stm32_framework", ["stm32cube", "arduino"], "stm32cube"),
        ("stm32_upload", ["stlink", "serial"], "{{ 'serial' if stm32_board == 'f405rg' else 'stlink' }}"),
        ("open_source_license", ["Apache-2.0", "MIT", "No license file"], "MIT"),
        ("git_init", ["Yes", "No"], "Yes"),
        ("environment_scope", ["global", "local"], "global"),
        ("host_side", ["No", "Yes"], "No"),
    ],
)
def test_question_choices(name, expected, default):
    assert CONFIG[name]["choices"] == expected
    assert CONFIG[name]["default"] == default


def test_esp_choices_follow_the_chip():
    assert choices("esp_framework", esp_chip="esp32") == ["espidf", "arduino"]
    assert choices("esp_framework", esp_chip="esp8266") == ["arduino", "esp8266-rtos-sdk"]
    assert choices("esp_board", esp_chip="esp32") == ["esp32dev", "esp32doit-devkit-v1"]
    assert choices("esp_board", esp_chip="esp8266") == ["nodemcuv2", "d1_mini"]


def test_dynamic_defaults_follow_the_chip_and_board():
    assert render("esp_framework", esp_chip="esp32") == "espidf"
    assert render("esp_framework", esp_chip="esp8266") == "arduino"
    assert render("esp_board", esp_chip="esp32") == "esp32dev"
    assert render("esp_board", esp_chip="esp8266") == "nodemcuv2"
    assert render("stm32_upload", stm32_board="f405rg") == "serial"
    assert render("stm32_upload", stm32_board="f103c8") == "stlink"


@pytest.mark.parametrize(
    "name, platform",
    [
        ("arduino_board", "arduino"),
        ("arduino_board_custom", "arduino"),
        ("arduino_bootloader", "arduino"),
        ("arduino_libraries", "arduino"),
        ("arduino_sketch_link", "arduino"),
        ("avr_language", "avr"),
        ("avr_mcu", "avr"),
        ("avr_mcu_custom", "avr"),
        ("avr_clock", "avr"),
        ("avr_programmer", "avr"),
        ("esp_chip", "esp"),
        ("esp_framework", "esp"),
        ("esp_board", "esp"),
        ("stm32_toolchain", "stm32"),
        ("stm32_board", "stm32"),
        ("stm32_framework", "stm32"),
        ("stm32_upload", "stm32"),
    ],
)
def test_platform_questions_are_guarded(name, platform):
    assert f"platform == '{platform}'" in CONFIG[name]["when"]


def test_host_module_is_guarded_by_the_host_side_and_asked_before_components():
    assert CONFIG["host_module"]["when"] == "{{ host_side == 'Yes' }}"
    visible = [
        name
        for name, question in CONFIG.items()
        if not name.startswith("_") and not hidden(question)
    ]
    assert visible[-3:] == ["host_side", "host_module", "components"]


def test_derived_answers_are_never_asked():
    for name in DERIVED:
        assert hidden(CONFIG[name]), name
    visible = {
        name
        for name, question in CONFIG.items()
        if not name.startswith("_") and not hidden(question)
    }
    assert visible.isdisjoint(DERIVED)


@pytest.mark.parametrize(
    "overrides, expected",
    [
        (
            {"platform": "arduino", "arduino_board": "uno"},
            {
                "pio_platform": "atmelavr@5.3.0",
                "pio_board": "uno",
                "pio_framework": "arduino",
                "pio_upload_protocol": "",
                "serial_baud": "9600",
                "env_name": "firmware-avr",
                "toolchain_language": "cpp",
            },
        ),
        (
            {"platform": "arduino", "arduino_board": "nano", "arduino_bootloader": "old"},
            {"pio_board": "nanoatmega328"},
        ),
        (
            {"platform": "arduino", "arduino_board": "nano", "arduino_bootloader": "new"},
            {"pio_board": "nanoatmega328new"},
        ),
        ({"platform": "arduino", "arduino_board": "mega2560"}, {"pio_board": "megaatmega2560"}),
        ({"platform": "arduino", "arduino_board": "leonardo"}, {"pio_board": "leonardo"}),
        (
            {"platform": "arduino", "arduino_board": "other", "arduino_board_custom": "my-board"},
            {"pio_board": "my-board"},
        ),
        (
            {"platform": "avr", "avr_language": "c"},
            {
                "pio_platform": "atmelavr@5.3.0",
                "pio_board": "uno",
                "pio_framework": "",
                "pio_upload_protocol": "usbasp",
                "serial_baud": "9600",
                "env_name": "firmware-avr",
                "toolchain_language": "c",
            },
        ),
        (
            {"platform": "avr", "avr_clock": "8000000"},
            {"pio_board": "pro8MHzatmega328"},
        ),
        ({"platform": "avr", "avr_mcu": "atmega32u4"}, {"pio_board": "leonardo"}),
        ({"platform": "avr", "avr_mcu": "attiny85"}, {"pio_board": "attiny85"}),
        (
            {"platform": "avr", "avr_mcu": "other", "avr_mcu_custom": "atmega1284p"},
            {"pio_board": "atmega1284p"},
        ),
        (
            {"platform": "avr", "avr_language": "cpp"},
            {"toolchain_language": "cpp"},
        ),
        (
            {"platform": "avr", "avr_language": "rust"},
            {
                "toolchain_language": "rust",
                "avr_target": "avr-none",
                "avr_cpu": "atmega328p",
                "pio_platform": "",
                "pio_board": "",
                "pio_framework": "",
                "pio_upload_protocol": "",
                "env_name": "firmware-avr",
            },
        ),
        (
            {
                "platform": "avr",
                "avr_language": "rust",
                "avr_mcu": "other",
                "avr_mcu_custom": "atmega1284p",
            },
            {"avr_cpu": "atmega1284p"},
        ),
        (
            {"platform": "avr", "avr_programmer": "arduino-isp"},
            {"pio_upload_protocol": "arduinoisp"},
        ),
        (
            {"platform": "esp", "esp_chip": "esp32", "esp_framework": "espidf"},
            {
                "pio_platform": "espressif32@7.1.3",
                "pio_board": "esp32dev",
                "pio_framework": "espidf",
                "pio_upload_protocol": "",
                "serial_baud": "115200",
                "env_name": "firmware-esp",
                "toolchain_language": "c",
            },
        ),
        (
            {"platform": "esp", "esp_chip": "esp32", "esp_framework": "arduino"},
            {"pio_framework": "arduino", "toolchain_language": "cpp"},
        ),
        (
            {
                "platform": "esp",
                "esp_chip": "esp8266",
                "esp_framework": "arduino",
                "esp_board": "nodemcuv2",
            },
            {
                "pio_platform": "espressif8266@4.2.1",
                "pio_board": "nodemcuv2",
                "pio_framework": "arduino",
                "toolchain_language": "cpp",
            },
        ),
        (
            {
                "platform": "esp",
                "esp_chip": "esp8266",
                "esp_framework": "esp8266-rtos-sdk",
                "esp_board": "d1_mini",
            },
            {"pio_board": "d1_mini", "pio_framework": "esp8266-rtos-sdk", "toolchain_language": "c"},
        ),
        (
            {"platform": "stm32", "stm32_toolchain": "rust", "stm32_board": "f405rg"},
            {
                "pio_platform": "",
                "pio_board": "",
                "pio_framework": "",
                "pio_upload_protocol": "",
                "thumb_target": "thumbv7em-none-eabihf",
                "flash_kb": "1024",
                "ram_kb": "128",
                "serial_baud": "115200",
                "env_name": "firmware-stm32",
                "toolchain_language": "rust",
            },
        ),
        (
            {"platform": "stm32", "stm32_toolchain": "rust", "stm32_board": "f103c8"},
            {"thumb_target": "thumbv7m-none-eabi", "flash_kb": "64", "ram_kb": "20"},
        ),
        (
            {
                "platform": "stm32",
                "stm32_toolchain": "platformio",
                "stm32_framework": "stm32cube",
                "stm32_board": "f405rg",
                "stm32_upload": "serial",
            },
            {
                "pio_platform": "ststm32@20.0.0",
                "pio_board": "genericSTM32F405RG",
                "pio_framework": "stm32cube",
                "pio_upload_protocol": "serial",
                "toolchain_language": "c",
            },
        ),
        (
            {
                "platform": "stm32",
                "stm32_toolchain": "platformio",
                "stm32_framework": "stm32cube",
                "stm32_board": "f103c8",
                "stm32_upload": "stlink",
            },
            {
                "pio_board": "bluepill_f103c8",
                "pio_upload_protocol": "stlink",
                "flash_kb": "64",
                "ram_kb": "20",
            },
        ),
        (
            {
                "platform": "stm32",
                "stm32_toolchain": "platformio",
                "stm32_framework": "arduino",
                "stm32_board": "f411re",
            },
            {
                "pio_board": "nucleo_f411re",
                "pio_framework": "arduino",
                "toolchain_language": "cpp",
                "flash_kb": "512",
                "ram_kb": "128",
            },
        ),
        (
            {
                "platform": "stm32",
                "stm32_toolchain": "platformio",
                "stm32_board": "l476rg",
            },
            {"pio_board": "nucleo_l476rg", "flash_kb": "1024", "ram_kb": "128"},
        ),
        ({"environment_scope": "local"}, {"env_local": "1"}),
        ({"environment_scope": "global"}, {"env_local": ""}),
        ({"project_name": "My Board"}, {"repo_name": "my-board"}),
        ({"repo_name": "my-board"}, {"crate_name": "my_board"}),
    ],
)
def test_derived_values(overrides, expected):
    for name, value in expected.items():
        assert render(name, **overrides) == value, name


SCAFFOLDS = [
    pytest.param(
        {"platform": "arduino", "arduino_board": "uno"},
        "src/board.ino",
        "platformio.ini",
        id="arduino",
    ),
    pytest.param(
        {"platform": "avr", "avr_language": "c"},
        "src/main.c",
        "platformio.ini",
        id="avr-c",
    ),
    pytest.param(
        {"platform": "avr", "avr_language": "cpp"},
        "src/main.cpp",
        "platformio.ini",
        id="avr-cpp",
    ),
    pytest.param(
        {"platform": "avr", "avr_language": "rust"},
        "src/bin/board.rs",
        "Cargo.toml",
        id="avr-rust",
    ),
    pytest.param(
        {"platform": "esp", "esp_chip": "esp32", "esp_framework": "espidf"},
        "src/main.c",
        "platformio.ini",
        id="esp32-espidf",
    ),
    pytest.param(
        {"platform": "esp", "esp_chip": "esp32", "esp_framework": "arduino"},
        "src/main.cpp",
        "platformio.ini",
        id="esp32-arduino",
    ),
    pytest.param(
        {"platform": "esp", "esp_chip": "esp8266", "esp_framework": "arduino"},
        "src/main.cpp",
        "platformio.ini",
        id="esp8266-arduino",
    ),
    pytest.param(
        {"platform": "esp", "esp_chip": "esp8266", "esp_framework": "esp8266-rtos-sdk"},
        "src/main.c",
        "platformio.ini",
        id="esp8266-rtos",
    ),
    pytest.param(
        {"platform": "stm32", "stm32_toolchain": "rust", "stm32_board": "f405rg"},
        "src/bin/board.rs",
        "Cargo.toml",
        id="stm32-rust",
    ),
    pytest.param(
        {
            "platform": "stm32",
            "stm32_toolchain": "platformio",
            "stm32_framework": "stm32cube",
            "stm32_board": "f405rg",
        },
        "src/main.c",
        "platformio.ini",
        id="stm32-cube",
    ),
    pytest.param(
        {
            "platform": "stm32",
            "stm32_toolchain": "platformio",
            "stm32_framework": "arduino",
            "stm32_board": "f405rg",
        },
        "src/main.cpp",
        "platformio.ini",
        id="stm32-arduino",
    ),
]


@pytest.mark.parametrize("answers, adapter, build_file", SCAFFOLDS)
def test_each_platform_renders_one_scaffold(answers, adapter, build_file):
    with bake(answers) as path:
        entry_points = [
            relative
            for relative in (
                "src/main.c",
                "src/main.cpp",
                "src/board.ino",
                "src/bin/board.rs",
            )
            if (path / relative).exists()
        ]
        assert entry_points == [adapter]
        assert (path / build_file).is_file()

        if answers.get("esp_framework") == "espidf":
            main = path / "main"
            assert main.is_symlink()
            assert os.readlink(main) == "src"
            assert main.resolve() == (path / "src").resolve()

        if build_file == "platformio.ini":
            assert not (path / "Cargo.toml").exists()
            assert not (path / "src/lib.rs").exists()
        else:
            assert not (path / "platformio.ini").exists()
            assert (path / "src/lib.rs").is_file()

        for file in text_files(path):
            text = re.sub(r"\$\{\{.*?\}\}", "", file.read_text(errors="replace"))
            for token in ("{{", "}}", "{%", "%}", "{#", "#}"):
                assert token not in text, f"{file.relative_to(path)} holds {token}"


PLATFORMIO = [
    pytest.param(
        {"platform": "arduino", "arduino_board": "uno"},
        {
            "platform": "atmelavr@5.3.0",
            "board": "uno",
            "framework": "arduino",
            "upload": None,
            "baud": "9600",
        },
        id="arduino-uno",
    ),
    pytest.param(
        {"platform": "avr", "avr_mcu": "attiny85", "avr_programmer": "arduino-isp"},
        {
            "platform": "atmelavr@5.3.0",
            "board": "attiny85",
            "framework": None,
            "upload": "arduinoisp",
            "baud": "9600",
        },
        id="avr-attiny85",
    ),
    pytest.param(
        {"platform": "esp", "esp_chip": "esp32", "esp_framework": "espidf"},
        {
            "platform": "espressif32@7.1.3",
            "board": "esp32dev",
            "framework": "espidf",
            "upload": None,
            "baud": "115200",
        },
        id="esp32-espidf",
    ),
    pytest.param(
        {"platform": "esp", "esp_chip": "esp8266", "esp_framework": "arduino"},
        {
            "platform": "espressif8266@4.2.1",
            "board": "nodemcuv2",
            "framework": "arduino",
            "upload": None,
            "baud": "115200",
        },
        id="esp8266-arduino",
    ),
    pytest.param(
        {
            "platform": "stm32",
            "stm32_toolchain": "platformio",
            "stm32_framework": "stm32cube",
            "stm32_board": "f405rg",
            "stm32_upload": "serial",
        },
        {
            "platform": "ststm32@20.0.0",
            "board": "genericSTM32F405RG",
            "framework": "stm32cube",
            "upload": "serial",
            "baud": "115200",
        },
        id="stm32-cube",
    ),
    pytest.param(
        {
            "platform": "stm32",
            "stm32_toolchain": "platformio",
            "stm32_framework": "arduino",
            "stm32_board": "f103c8",
            "stm32_upload": "stlink",
        },
        {
            "platform": "ststm32@20.0.0",
            "board": "bluepill_f103c8",
            "framework": "arduino",
            "upload": "stlink",
            "baud": "115200",
        },
        id="stm32-arduino",
    ),
]


@pytest.mark.parametrize("answers, expected", PLATFORMIO)
def test_platformio_configuration(answers, expected):
    with bake(answers) as path:
        text = (path / "platformio.ini").read_text()
        assert f"platform = {expected['platform']}" in text
        assert f"board = {expected['board']}" in text
        assert f"monitor_speed = {expected['baud']}" in text

        if expected["framework"] is None:
            assert "framework" not in text
        else:
            assert f"framework = {expected['framework']}" in text

        if expected["upload"] is None:
            assert "upload_protocol" not in text
        else:
            assert f"upload_protocol = {expected['upload']}" in text

        assert f"BAUD ?= {expected['baud']}" in (path / "Makefile").read_text()


def test_copier_answers_record_the_visible_answers():
    with bake({"platform": "arduino", "arduino_board": "nano", "arduino_bootloader": "new"}) as path:
        text = (path / ".copier-answers.yml").read_text()
        assert "platform: arduino" in text
        assert "arduino_board: nano" in text
        assert "arduino_bootloader: new" in text
        assert "author_email:" not in text
        assert "pio_board:" not in text


def test_make_help_lists_the_development_targets():
    with bake({"platform": "arduino"}) as path:
        result = subprocess.run(["make", "help"], cwd=path, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        for target in (
            "create_environment",
            "build",
            "upload",
            "monitor",
            "test",
            "sim",
            "clean",
            "help",
        ):
            assert target in result.stdout, result.stdout


@pytest.mark.parametrize("scope", ["global", "local"])
def test_environment_scope_sets_the_makefile_default(scope):
    with bake({"platform": "arduino", "environment_scope": scope}) as path:
        makefile = (path / "Makefile").read_text()
        assert f"ENV_SCOPE ?= {scope}" in makefile
        assert "ifeq ($(ENV_SCOPE),local)" in makefile
        assert "export CONDA_ENVS_PATH := $(PROJECT_DIR)/.conda/envs" in makefile


@pytest.mark.parametrize(
    "license_name, marker",
    [
        ("Apache-2.0", "Apache License"),
        ("MIT", "MIT License"),
    ],
)
def test_license_matches_the_answer(license_name, marker):
    with bake({"platform": "arduino", "open_source_license": license_name}) as path:
        text = (path / "LICENSE").read_text()
        assert marker in text


def test_no_license_answer_writes_no_license_file():
    with bake({"platform": "arduino", "open_source_license": "No license file"}) as path:
        assert not (path / "LICENSE").exists()


def test_git_init_yes_creates_the_main_branch():
    with bake({"platform": "arduino", "git_init": "Yes"}) as path:
        assert (path / ".git").is_dir()
        branch = subprocess.run(
            ["git", "-C", str(path), "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        assert branch == "main"


def test_git_init_no_leaves_no_repository():
    with bake({"platform": "arduino", "git_init": "No"}) as path:
        assert not (path / ".git").exists()


def test_data_and_references_are_components():
    with bake({"platform": "arduino"}, components=["notebooks"]) as path:
        assert not (path / "data").exists()
        assert not (path / "references").exists()

    with bake(
        {"platform": "arduino"},
        components=["notebooks", "data", "references"],
    ) as path:
        assert (path / "data/README.md").is_file()
        assert (path / "references/README.md").is_file()


def test_env_installers_component_selects_the_installer_tree():
    with bake({"platform": "arduino"}, components=["env-installers"]) as path:
        assert (path / "resources/envs/firmware-avr.py").is_file()
        help_text = subprocess.run(
            ["make", "help"], cwd=path, capture_output=True, text=True, check=True
        ).stdout
        assert "create_environment" in help_text

    with bake({"platform": "arduino"}, components=["notebooks"]) as path:
        assert not (path / "resources/envs").exists()
        help_text = subprocess.run(
            ["make", "help"], cwd=path, capture_output=True, text=True, check=True
        ).stdout
        assert "~/.local/lab-utils/envs/firmware-avr.py" in help_text


def test_components_default_matches_the_design():
    question = CONFIG["components"]
    assert question["choices"] == [
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
    assert question["default"] == [
        "notebooks",
        "resources",
        "references",
        "simulator",
        "agents",
        "env-installers",
    ]


def test_default_copy_renders_only_the_default_components():
    with bake({"platform": "arduino"}) as path:
        for present in (
            "notebooks/README.md",
            "resources/README.md",
            "resources/envs/firmware-avr.py",
            "references/README.md",
            ".agents",
        ):
            assert (path / present).exists(), present
        for absent in ("data", "docs", ".github"):
            assert not (path / absent).exists(), absent
        assert "PORT ?= /dev/ttyUSB0" in (path / "Makefile").read_text()


def test_sketch_link_answer_places_a_root_symlink():
    with bake({"platform": "arduino", "arduino_sketch_link": "Yes"}) as path:
        link = path / "board.ino"
        assert link.is_symlink()
        assert os.readlink(link) == "src/board.ino"
        assert link.resolve() == (path / "src/board.ino").resolve()

    with bake({"platform": "arduino", "arduino_sketch_link": "No"}) as path:
        assert (path / "src/board.ino").is_file()
        assert not (path / "board.ino").exists()


def test_arduino_libraries_answer_controls_the_vendor_tree():
    with bake({"platform": "arduino", "arduino_libraries": "Yes"}) as path:
        assert (path / "lib/vendor").is_dir()
        assert (path / "lib/core/core.c").is_file()

    with bake({"platform": "arduino", "arduino_libraries": "No"}) as path:
        assert (path / "lib/core/core.c").is_file()
        assert not (path / "lib/vendor").exists()


def test_stm32_rust_renders_the_app_template_layout():
    with bake({"platform": "stm32", "stm32_toolchain": "rust", "stm32_board": "f103c8"}) as path:
        for present in (
            "Cargo.toml",
            "memory.x",
            ".cargo/config.toml",
            "rust-toolchain.toml",
            "src/lib.rs",
            "src/bin/board.rs",
            "test/host/core.rs",
        ):
            assert (path / present).is_file(), present
        assert not (path / "platformio.ini").exists()
        assert not (path / "src/main.c").exists()
        assert "thumbv7m-none-eabi" in (path / "Cargo.toml").read_text() or "thumbv7m-none-eabi" in (
            path / ".cargo/config.toml"
        ).read_text()


@pytest.mark.parametrize(
    "answers, installer",
    [
        ({"platform": "arduino"}, "firmware-avr.py"),
        ({"platform": "avr"}, "firmware-avr.py"),
        ({"platform": "esp", "esp_chip": "esp32", "esp_framework": "espidf"}, "firmware-esp.py"),
        ({"platform": "stm32", "stm32_toolchain": "rust"}, "firmware-stm32.py"),
        (
            {"platform": "stm32", "stm32_toolchain": "platformio", "stm32_framework": "stm32cube"},
            "firmware-stm32.py",
        ),
    ],
)
def test_each_platform_renders_its_installer(answers, installer):
    with bake(answers) as path:
        envs = path / "resources" / "envs"
        script = envs / installer
        assert script.is_file()
        assert script.stat().st_mode & 0o111
        assert f"./resources/envs/{installer}" in (path / "Makefile").read_text()
        assert sorted(entry.name for entry in envs.glob("firmware-*.py")) == [installer]


def test_copier_answers_omit_hidden_and_skipped_answers():
    with bake({"platform": "avr", "avr_language": "c"}) as path:
        text = (path / ".copier-answers.yml").read_text()
        assert "platform: avr" in text
        assert "avr_language: c" in text
        assert "project_name: board" in text
        assert "repo_name: board" in text
        for hidden in ("author_email:", "author_name_clean:", "pio_board:", "avr_target:"):
            assert hidden not in text, hidden
        for skipped in ("arduino_board:", "esp_chip:", "stm32_toolchain:"):
            assert skipped not in text, skipped


@pytest.mark.parametrize("host_side", ["No", "Yes"])
def test_copier_answers_record_host_module_only_with_the_host_side(host_side):
    with bake({"platform": "arduino", "host_side": host_side}) as path:
        answers = yaml.safe_load((path / ".copier-answers.yml").read_text())
        assert answers["host_side"] == host_side
        if host_side == "Yes":
            assert answers["host_module"] == "board_host"
        else:
            assert "host_module" not in answers
