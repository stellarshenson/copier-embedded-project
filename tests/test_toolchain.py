"""Render every scaffold and check its layout; build the AVR branches when the toolchain is present."""

from __future__ import annotations

import os
import shutil
import subprocess

import pytest
from helpers import bake, files

REPO = "board"
ADAPTERS = {
    "src/main.c",
    "src/main.cpp",
    f"src/{REPO}.ino",
    f"src/bin/{REPO}.rs",
}

# Every row of the per-toolchain layout table: the answers, the build file and the one adapter.
CASES = [
    pytest.param(
        {"platform": "arduino", "arduino_board": "uno"},
        "platformio.ini",
        f"src/{REPO}.ino",
        id="arduino-uno",
    ),
    pytest.param(
        {"platform": "arduino", "arduino_board": "nano", "arduino_bootloader": "new"},
        "platformio.ini",
        f"src/{REPO}.ino",
        id="arduino-nano-new",
    ),
    pytest.param(
        {"platform": "avr", "avr_language": "c", "avr_mcu": "atmega328p"},
        "platformio.ini",
        "src/main.c",
        id="avr-c",
    ),
    pytest.param(
        {"platform": "avr", "avr_language": "cpp", "avr_mcu": "atmega328p"},
        "platformio.ini",
        "src/main.cpp",
        id="avr-cpp",
    ),
    pytest.param(
        {"platform": "avr", "avr_language": "rust", "avr_mcu": "atmega328p"},
        "Cargo.toml",
        f"src/bin/{REPO}.rs",
        id="avr-rust",
    ),
    pytest.param(
        {"platform": "esp", "esp_chip": "esp32", "esp_framework": "espidf", "esp_board": "esp32dev"},
        "platformio.ini",
        "src/main.c",
        id="esp32-espidf",
    ),
    pytest.param(
        {
            "platform": "esp",
            "esp_chip": "esp32",
            "esp_framework": "arduino",
            "esp_board": "esp32dev",
        },
        "platformio.ini",
        "src/main.cpp",
        id="esp32-arduino",
    ),
    pytest.param(
        {
            "platform": "esp",
            "esp_chip": "esp8266",
            "esp_framework": "arduino",
            "esp_board": "nodemcuv2",
        },
        "platformio.ini",
        "src/main.cpp",
        id="esp8266-arduino",
    ),
    pytest.param(
        {
            "platform": "esp",
            "esp_chip": "esp8266",
            "esp_framework": "esp8266-rtos-sdk",
            "esp_board": "nodemcuv2",
        },
        "platformio.ini",
        "src/main.c",
        id="esp8266-rtos",
    ),
    pytest.param(
        {"platform": "stm32", "stm32_toolchain": "rust", "stm32_board": "f405rg"},
        "Cargo.toml",
        f"src/bin/{REPO}.rs",
        id="stm32-rust-f405rg",
    ),
    pytest.param(
        {"platform": "stm32", "stm32_toolchain": "rust", "stm32_board": "f103c8"},
        "Cargo.toml",
        f"src/bin/{REPO}.rs",
        id="stm32-rust-f103c8",
    ),
    pytest.param(
        {
            "platform": "stm32",
            "stm32_toolchain": "platformio",
            "stm32_framework": "stm32cube",
            "stm32_board": "f405rg",
        },
        "platformio.ini",
        "src/main.c",
        id="stm32-pio-cube",
    ),
    pytest.param(
        {
            "platform": "stm32",
            "stm32_toolchain": "platformio",
            "stm32_framework": "arduino",
            "stm32_board": "f405rg",
        },
        "platformio.ini",
        "src/main.cpp",
        id="stm32-pio-arduino",
    ),
]

C_CASES = [case for case in CASES if case.id not in {"avr-rust", "stm32-rust-f405rg", "stm32-rust-f103c8"}]
RUST_CASES = [case for case in CASES if case.id in {"avr-rust", "stm32-rust-f405rg", "stm32-rust-f103c8"}]


def read(project, relative: str) -> str:
    return (project / relative).read_text()


@pytest.mark.parametrize("answers,build_file,adapter", CASES)
def test_one_build_root_and_one_adapter(answers, build_file, adapter):
    with bake(answers) as path:
        present = files(path)
        build_files = {name for name in ("platformio.ini", "Cargo.toml") if name in present}
        assert build_files == {build_file}
        assert {name for name in ADAPTERS if name in present} == {adapter}


@pytest.mark.parametrize("answers,build_file,adapter", C_CASES)
def test_c_core_is_one_shared_module(answers, build_file, adapter):
    with bake(answers) as path:
        present = files(path)
        assert {"lib/core/core.c", "lib/core/core.h"} <= present
        core = read(path, "lib/core/core.h")
        assert "core_crc8" in core
        assert "core_ring_push" in core
        assert '#include "core.h"' in read(path, adapter)
        assert not {name for name in present if name.startswith("src/logic")}


@pytest.mark.parametrize("answers,build_file,adapter", RUST_CASES)
def test_rust_core_is_the_package_library(answers, build_file, adapter):
    with bake(answers) as path:
        present = files(path)
        core = read(path, "src/lib.rs")
        assert "#![cfg_attr(not(test), no_std)]" in core
        assert "pub fn crc8(" in core
        assert "pub struct Ring" in core
        cargo = read(path, "Cargo.toml")
        assert 'path = "src/lib.rs"' in cargo
        assert "[[test]]" in cargo
        assert 'name = "core"' in cargo
        assert 'path = "test/host/core.rs"' in cargo
        assert f"use {REPO}::crc8" in read(path, adapter)
        assert "platformio.ini" not in present
        assert "lib/core/core.c" not in present
        assert not {name for name in present if name.startswith("src/logic")}


@pytest.mark.parametrize(
    "language,adapter",
    [("c", "src/main.c"), ("cpp", "src/main.cpp"), ("rust", f"src/bin/{REPO}.rs")],
)
def test_avr_language_selects_one_adapter(language, adapter):
    with bake({"platform": "avr", "avr_language": language, "avr_mcu": "atmega328p"}) as path:
        present = files(path)
        assert adapter in present
        assert not ({name for name in ADAPTERS if name != adapter} & present)
        assert ("Cargo.toml" in present) == (language == "rust")
        assert ("platformio.ini" in present) == (language != "rust")


def test_avr_rust_uses_the_toolchain_the_installer_pins():
    with bake({"platform": "avr", "avr_language": "rust", "avr_mcu": "attiny85"}) as path:
        toolchain = read(path, "rust-toolchain.toml")
        assert 'channel = "nightly-2026-10-06"' in toolchain
        assert "targets" not in toolchain
        cargo_config = read(path, ".cargo/config.toml")
        assert "[target.avr-none]" in cargo_config
        assert "target-cpu=attiny85" in cargo_config
        assert "mmcu=attiny85" in cargo_config
        # A build target or build-std here would send the host tests to the MCU.
        assert "[build]" not in cargo_config
        assert "build-std" not in cargo_config
        assert "-Z build-std=core" in read(path, "Makefile")
        present = files(path)
        assert "memory.x" not in present
        assert "build.rs" not in present


def test_arduino_sketch_and_optional_root_link():
    with bake({"platform": "arduino", "arduino_board": "uno"}) as path:
        sketch = read(path, f"src/{REPO}.ino")
        assert "void setup()" in sketch
        assert "void loop()" in sketch
        assert not (path / f"{REPO}.ino").exists()

    with bake(
        {"platform": "arduino", "arduino_board": "uno", "arduino_sketch_link": "Yes"}
    ) as path:
        link = path / f"{REPO}.ino"
        assert link.is_symlink()
        assert link.resolve() == (path / "src" / f"{REPO}.ino").resolve()


@pytest.mark.parametrize("answers,build_file,adapter", CASES)
def test_every_scaffold_ships_a_library_register(answers, build_file, adapter):
    with bake(answers) as path:
        assert "lib/README.md" in files(path)
        register = read(path, "lib/README.md")
        assert "Library register" in register
        # The register must name the core that this scaffold actually builds.
        if adapter.endswith(".rs"):
            assert "`src/lib.rs`" in register
        else:
            assert "`lib/core/core.c`" in register


def test_arduino_library_register_follows_the_answer():
    with bake({"platform": "arduino", "arduino_board": "uno", "arduino_libraries": "No"}) as path:
        register = read(path, "lib/README.md")
        assert "`core`" in register
        assert "vendor/<name>" not in register
        assert not {name for name in files(path) if name.startswith("lib/vendor/")}

    with bake({"platform": "arduino", "arduino_board": "uno", "arduino_libraries": "Yes"}) as path:
        register = read(path, "lib/README.md")
        assert "`core`" in register
        assert "vendor/<name>" in register
        assert {name for name in files(path) if name.startswith("lib/vendor/")}


@pytest.mark.parametrize(
    "answers,required,forbidden",
    [
        pytest.param(
            {"platform": "arduino", "arduino_board": "nano", "arduino_bootloader": "old"},
            ["platform = atmelavr@5.3.0", "board = nanoatmega328", "framework = arduino",
             "monitor_speed = 9600"],
            [],
            id="arduino-nano-old",
        ),
        pytest.param(
            {"platform": "arduino", "arduino_board": "nano", "arduino_bootloader": "new"},
            ["board = nanoatmega328new"],
            [],
            id="arduino-nano-new",
        ),
        pytest.param(
            {"platform": "avr", "avr_language": "c", "avr_mcu": "atmega328p", "avr_clock": "8000000"},
            ["board = pro8MHzatmega328", "board_build.f_cpu = 8000000L", "upload_protocol = usbasp"],
            ["framework ="],
            id="avr-8mhz",
        ),
        pytest.param(
            {"platform": "avr", "avr_language": "c", "avr_mcu": "atmega32u4",
             "avr_programmer": "arduino-isp"},
            ["board = leonardo", "upload_protocol = arduinoisp"],
            ["framework ="],
            id="avr-leonardo",
        ),
        pytest.param(
            {"platform": "esp", "esp_chip": "esp32", "esp_framework": "espidf",
             "esp_board": "esp32dev"},
            ["platform = espressif32@7.1.3", "board = esp32dev", "framework = espidf",
             "monitor_speed = 115200", "src_dir = main"],
            [],
            id="esp32-espidf",
        ),
        pytest.param(
            {"platform": "esp", "esp_chip": "esp8266", "esp_framework": "esp8266-rtos-sdk",
             "esp_board": "nodemcuv2"},
            ["platform = espressif8266@4.2.1", "board = nodemcuv2",
             "framework = esp8266-rtos-sdk"],
            [],
            id="esp8266-rtos",
        ),
        pytest.param(
            {"platform": "stm32", "stm32_toolchain": "platformio", "stm32_framework": "stm32cube",
             "stm32_board": "f103c8", "stm32_upload": "serial"},
            ["platform = ststm32@20.0.0", "board = bluepill_f103c8", "framework = stm32cube",
             "upload_protocol = serial"],
            [],
            id="stm32-cube-serial",
        ),
        pytest.param(
            {"platform": "stm32", "stm32_toolchain": "platformio", "stm32_framework": "arduino",
             "stm32_board": "f405rg", "stm32_upload": "stlink"},
            ["board = genericSTM32F405RG", "framework = arduino", "upload_protocol = stlink"],
            [],
            id="stm32-arduino-stlink",
        ),
    ],
)
def test_platformio_mappings(answers, required, forbidden):
    with bake(answers) as path:
        ini = read(path, "platformio.ini")
        for text in required:
            assert text in ini
        for text in forbidden:
            assert text not in ini


def test_esp_idf_layout():
    with bake(
        {"platform": "esp", "esp_chip": "esp32", "esp_framework": "espidf", "esp_board": "esp32dev"}
    ) as path:
        present = files(path)
        assert "src/main.c" in present
        main = read(path, "src/main.c")
        assert "void app_main(void)" in main
        assert "[BOOT] board" in main
        assert "vTaskStartScheduler" not in main
        link = path / "main"
        assert link.is_symlink()
        assert os.readlink(link) == "src"
        assert (link / "main.c").resolve() == (path / "src/main.c").resolve()
        ini = read(path, "platformio.ini")
        assert "[platformio]\nsrc_dir = main" in ini
        sdkconfig = read(path, "sdkconfig.defaults")
        assert "CONFIG_ESPTOOLPY_FLASHSIZE_4MB=y" in sdkconfig
        assert "CONFIG_ESP_MAIN_TASK_STACK_SIZE=4096" in sdkconfig


def test_esp8266_rtos_layout():
    with bake(
        {"platform": "esp", "esp_chip": "esp8266", "esp_framework": "esp8266-rtos-sdk",
         "esp_board": "nodemcuv2"}
    ) as path:
        present = files(path)
        main = read(path, "src/main.c")
        assert "void user_init(void)" in main
        assert "[BOOT] board" in main
        assert "vTaskStartScheduler" not in main
        assert "sdkconfig.defaults" in present


def test_stm32cube_layout():
    with bake(
        {"platform": "stm32", "stm32_toolchain": "platformio", "stm32_framework": "stm32cube",
         "stm32_board": "f405rg"}
    ) as path:
        main = read(path, "src/main.c")
        # FreeRTOS owns SysTick, so the starter never starts the HAL time base.
        assert "HAL_NVIC_SetPriorityGrouping(NVIC_PRIORITYGROUP_4)" in main
        assert "HAL_Init()" not in main
        assert "cmsis_os.h" in main
        assert "osKernelStart()" in main
        config = read(path, "src/FreeRTOSConfig.h")
        assert "configTICK_RATE_HZ" in config
        assert "configMAX_SYSCALL_INTERRUPT_PRIORITY" in config
        ini = read(path, "platformio.ini")
        assert "extra_scripts = pre:tools/freertos.py" in ini
        script = read(path, "tools/freertos.py")
        assert "BuildSources" in script
        assert 'portable' in script
        assert "heap_4.c" in script
        assert "cmsis_os.c" in script


def test_stm32_arduino_has_no_freertos_config():
    with bake(
        {"platform": "stm32", "stm32_toolchain": "platformio", "stm32_framework": "arduino",
         "stm32_board": "f405rg"}
    ) as path:
        present = files(path)
        assert "src/FreeRTOSConfig.h" not in present
        assert "src/main.cpp" in present


def test_non_esp_scaffolds_have_no_sdkconfig():
    with bake({"platform": "avr", "avr_language": "cpp", "avr_mcu": "atmega328p"}) as path:
        assert "sdkconfig.defaults" not in files(path)


def test_non_arduino_scaffolds_have_no_vendor_dir():
    with bake({"platform": "esp", "esp_chip": "esp32", "esp_framework": "espidf",
               "esp_board": "esp32dev"}) as path:
        assert not {name for name in files(path) if name.startswith("lib/vendor/")}


@pytest.mark.parametrize(
    "board,flash_kb,ram_kb,thumb_target",
    [
        ("f405rg", "1024", "128", "thumbv7em-none-eabihf"),
        ("f103c8", "64", "20", "thumbv7m-none-eabi"),
        ("f411re", "512", "128", "thumbv7em-none-eabihf"),
        ("l476rg", "1024", "128", "thumbv7em-none-eabihf"),
    ],
)
def test_stm32_rust_memory_and_target(board, flash_kb, ram_kb, thumb_target):
    with bake({"platform": "stm32", "stm32_toolchain": "rust", "stm32_board": board}) as path:
        memory = read(path, "memory.x")
        assert "ORIGIN = 0x08000000" in memory
        assert f"LENGTH = {flash_kb}K" in memory
        assert f"LENGTH = {ram_kb}K" in memory
        toolchain = read(path, "rust-toolchain.toml")
        assert 'channel = "1.99.0"' in toolchain
        assert thumb_target in toolchain
        assert "build.rs" in files(path)


def test_stm32_rust_target_and_host_tests():
    with bake({"platform": "stm32", "stm32_toolchain": "rust", "stm32_board": "f405rg"}) as path:
        cargo_config = read(path, ".cargo/config.toml")
        assert "[target.thumbv7em-none-eabihf]" in cargo_config
        assert 'link-arg=-Tlink.x' in cargo_config
        # The host tests run on the workstation, so no global build target may be set.
        assert "[build]" not in cargo_config
        cargo = read(path, "Cargo.toml")
        assert "test = false" in cargo
        assert 'required-features = ["firmware"]' in cargo
        assert 'path = "test/host/core.rs"' in cargo


def test_toolchain_skill_names_the_run_time_environment_scope():
    with bake({"platform": "arduino"}) as path:
        skill = read(path, ".agents/skills/board-toolchain/SKILL.md")
        assert "ENV_SCOPE=local" in skill
        assert "make create_environment ENV_SCOPE=local" in skill
        assert "global" in skill
        assert "local" in skill
        assert "Ask the user whether the environment should be global or local" in skill
        assert "one large copy on the workstation" in skill
        assert "same large space inside the project folder" in skill

    with bake({"platform": "arduino", "environment_scope": "local"}) as path:
        assert "The project default is `local`" in read(
            path, ".agents/skills/board-toolchain/SKILL.md"
        )


def has_conda_env(name: str) -> bool:
    if shutil.which("conda") is None:
        return False
    result = subprocess.run(["conda", "env", "list"], capture_output=True, text=True)
    return name in result.stdout


@pytest.mark.toolchain
@pytest.mark.parametrize(
    "answers,env_name",
    [
        ({"platform": "arduino"}, "firmware-avr"),
        ({"platform": "avr", "avr_language": "c", "avr_mcu": "atmega328p"}, "firmware-avr"),
        ({"platform": "avr", "avr_language": "cpp", "avr_mcu": "atmega328p"}, "firmware-avr"),
        ({"platform": "avr", "avr_language": "rust", "avr_mcu": "atmega328p"}, "firmware-avr"),
        ({"platform": "stm32", "stm32_toolchain": "rust", "stm32_board": "f405rg"}, "firmware-stm32"),
        (
            {
                "platform": "stm32",
                "stm32_toolchain": "platformio",
                "stm32_framework": "stm32cube",
                "stm32_board": "f405rg",
            },
            "firmware-stm32",
        ),
    ],
    ids=[
        "arduino-uno", "avr-c-328p", "avr-cpp-328p", "avr-rust-328p", "stm32-rust-f405rg",
        "stm32-cube-f405rg",
    ],
)
def test_build_and_host_tests(answers, env_name):
    if not has_conda_env(env_name):
        pytest.skip(f"the {env_name} conda environment is absent")
    with bake(answers) as path:
        build = subprocess.run(["make", "build"], cwd=path, capture_output=True, text=True)
        assert build.returncode == 0, (build.stdout + build.stderr)[-3000:]

        test = subprocess.run(["make", "test"], cwd=path, capture_output=True, text=True)
        assert test.returncode == 0, (test.stdout + test.stderr)[-3000:]


@pytest.mark.toolchain
def test_stm32cube_boots_under_qemu():
    """The STM32Cube starter builds and its one FreeRTOS task prints the boot line under QEMU."""
    if not has_conda_env("firmware-stm32"):
        pytest.skip("the firmware-stm32 conda environment is absent")
    with bake(
        {
            "platform": "stm32",
            "stm32_toolchain": "platformio",
            "stm32_framework": "stm32cube",
            "stm32_board": "f405rg",
        }
    ) as path:
        build = subprocess.run(["make", "build"], cwd=path, capture_output=True, text=True)
        assert build.returncode == 0, (build.stdout + build.stderr)[-3000:]

        simulation = subprocess.run(["make", "sim"], cwd=path, capture_output=True, text=True)
        text = simulation.stdout + simulation.stderr
        assert simulation.returncode == 0, text[-3000:]
        if "Skipping the simulator: qemu-system-arm is not installed" in text:
            pytest.skip("qemu-system-arm is absent from firmware-stm32")
        assert "1 passed" in text, text[-3000:]


@pytest.mark.toolchain
def test_ltspice_circuit_simulates():
    """The opt-in ltspice component runs its op-amp netlist under ngspice in the environment."""
    if not has_conda_env("firmware-avr"):
        pytest.skip("the firmware-avr conda environment is absent")
    probe = subprocess.run(
        ["conda", "run", "-n", "firmware-avr", "ngspice", "--version"],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        pytest.skip("ngspice is absent from firmware-avr")
    components = [
        "notebooks", "resources", "references", "simulator", "agents", "env-installers", "ltspice",
    ]
    with bake(
        {"platform": "avr", "avr_language": "c", "avr_mcu": "atmega328p"}, components=components
    ) as path:
        result = subprocess.run(["make", "ltspice"], cwd=path, capture_output=True, text=True)
        text = result.stdout + result.stderr
        assert result.returncode == 0, text[-3000:]
        assert "1 passed" in text, text[-3000:]


@pytest.mark.toolchain
def test_bare_avr_c_simulates_under_simavr():
    """ACC-TMPL-32: the bare AVR C starter runs its two functional tests under simavr."""
    if not has_conda_env("firmware-avr"):
        pytest.skip("the firmware-avr conda environment is absent")
    with bake({"platform": "avr", "avr_language": "c", "avr_mcu": "atmega328p"}) as path:
        simulation = subprocess.run(["make", "sim"], cwd=path, capture_output=True, text=True)
        text = simulation.stdout + simulation.stderr
        assert simulation.returncode == 0, text[-3000:]
        assert "2 passed" in text, text[-3000:]
        assert "failed" not in text.lower(), text[-3000:]
