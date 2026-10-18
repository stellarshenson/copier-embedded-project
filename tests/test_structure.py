"""Every render carries one unified tree, its agent files and its chosen license."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from helpers import bake

REPO = "board"

# The platform branches of ACC-TMPL-11 and ACC-TMPL-14: one per toolchain.
BRANCHES = [
    ("arduino-uno", {"platform": "arduino", "arduino_board": "uno"}),
    ("avr-c", {"platform": "avr", "avr_language": "c", "avr_mcu": "atmega328p"}),
    ("avr-cpp", {"platform": "avr", "avr_language": "cpp", "avr_mcu": "atmega328p"}),
    ("avr-rust", {"platform": "avr", "avr_language": "rust", "avr_mcu": "atmega328p"}),
    ("esp32-espidf", {"platform": "esp", "esp_chip": "esp32", "esp_framework": "espidf"}),
    ("esp32-arduino", {"platform": "esp", "esp_chip": "esp32", "esp_framework": "arduino"}),
    ("esp8266-arduino", {"platform": "esp", "esp_chip": "esp8266", "esp_framework": "arduino"}),
    ("stm32-rust", {"platform": "stm32", "stm32_toolchain": "rust", "stm32_board": "f405rg"}),
    (
        "stm32-platformio-stm32cube",
        {
            "platform": "stm32",
            "stm32_toolchain": "platformio",
            "stm32_framework": "stm32cube",
            "stm32_board": "f405rg",
        },
    ),
]

BRANCH_PARAMS = [pytest.param(answers, id=name) for name, answers in BRANCHES]

ALL_COMPONENTS = [
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
    "device-bridge",
]

TREE_FILES = [
    "Makefile",
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "CHANGELOG.md",
    "VERSION",
    "RELEASING.md",
    ".gitignore",
    ".copier-answers.yml",
]
TREE_DIRS = ["lib", "test/host", "tools"]

# The roots every platform shares, whatever its toolchain (ACC-TMPL-46).
UNIFIED_ROOTS = [
    "Makefile",
    "lib",
    "test/host",
    "test/harness",
    "test/functional",
    "resources",
    "references",
    "docs",
    "tools",
]

# The only top-level names a toolchain may add or swap, from the per-toolchain
# layout table in docs/template-design.md section 3.3.
LAYOUT_VARIATIONS = {
    "src",
    "main",
    "platformio.ini",
    "Cargo.toml",
    "build.rs",
    "memory.x",
    ".cargo",
    "rust-toolchain.toml",
    "sdkconfig.defaults",
}

ADAPTERS = [
    "src/main.c",
    "src/main.cpp",
    f"src/{REPO}.ino",
    f"src/bin/{REPO}.rs",
]


def espidf(answers: dict) -> bool:
    return answers.get("platform") == "esp" and answers.get("esp_framework") == "espidf"


def top_level(project: Path) -> set[str]:
    """The names at the project root, without the git internals."""
    return {entry.name for entry in project.iterdir() if entry.name != ".git"}


def license_named_files(project: Path) -> list[str]:
    """Every file whose name is a license name, whatever its suffix."""
    stems = {"LICENSE", "LICENCE", "COPYING", "UNLICENSE"}
    found = []
    for path in project.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.name.upper().split(".", 1)[0] in stems:
            found.append(str(path.relative_to(project)))
    return sorted(found)


@pytest.mark.parametrize("answers", BRANCH_PARAMS)
def test_unified_top_level_tree(answers):
    """ACC-TMPL-11: the always-rendered tree is present on every platform branch."""
    with bake(answers) as path:
        for relative in TREE_FILES:
            assert (path / relative).is_file(), relative
        for relative in TREE_DIRS:
            assert (path / relative).is_dir(), relative

        assert (path / "src").is_dir(), "src"
        if espidf(answers):
            link = path / "main"
            assert link.is_symlink(), "main"
            assert os.readlink(link) == "src"
            assert (link / "main.c").resolve() == (path / "src/main.c").resolve()
        else:
            assert not (path / "main").exists(), "main"
            assert not (path / "main").is_symlink(), "main"

        host_tests = {entry.name for entry in (path / "test/host").iterdir()}
        assert len(host_tests) == 1, host_tests
        assert host_tests <= {"test_core.c", "core.rs"}, host_tests
        for relative in ("test/harness", "test/functional"):
            assert any((path / relative).iterdir()), relative


@pytest.mark.parametrize("answers", BRANCH_PARAMS)
def test_root_agents_files(answers):
    """ACC-TMPL-14: AGENTS.md explains the project and CLAUDE.md imports it in one line."""
    with bake(answers) as path:
        agents = path / "AGENTS.md"
        assert agents.is_file()
        text = agents.read_text()
        assert "## Structure" in text
        assert "## Commands" in text
        assert "- `tools/`" in text
        for target in ("make help", "make build", "make upload", "make monitor", "make test"):
            assert target in text, target
        assert (path / "CLAUDE.md").read_text().splitlines() == ["@AGENTS.md"]


@pytest.mark.parametrize(
    "license_name, markers, other_marker",
    [
        (
            "Apache-2.0",
            [
                "Apache License",
                "Version 2.0, January 2004",
                "TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION",
            ],
            "MIT License",
        ),
        (
            "MIT",
            ["MIT License", "Permission is hereby granted, free of charge"],
            "Apache License",
        ),
    ],
)
def test_license_answer_selects_the_chosen_license_text(license_name, markers, other_marker):
    """ACC-TMPL-19: the chosen license is the only license-named file and carries its text."""
    answers = {"platform": "arduino", "open_source_license": license_name}
    with bake(answers) as path:
        assert license_named_files(path) == ["LICENSE"]
        text = (path / "LICENSE").read_text()
        for marker in markers:
            assert marker in text, marker
        assert other_marker not in text, other_marker


def test_no_license_answer_writes_no_license_named_file():
    """ACC-TMPL-19: No license file leaves no license-named file in the render."""
    with bake({"platform": "arduino", "open_source_license": "No license file"}) as path:
        assert license_named_files(path) == []


# Every row of the per-toolchain layout table: the answers, the build file, the one
# adapter, the companion build files and the documented variation.
LAYOUTS = [
    pytest.param(
        {"platform": "arduino", "arduino_board": "uno"},
        "platformio.ini",
        f"src/{REPO}.ino",
        (),
        "sketch",
        id="arduino-uno",
    ),
    pytest.param(
        {"platform": "avr", "avr_language": "c", "avr_mcu": "atmega328p"},
        "platformio.ini",
        "src/main.c",
        (),
        None,
        id="avr-c",
    ),
    pytest.param(
        {"platform": "avr", "avr_language": "cpp", "avr_mcu": "atmega328p"},
        "platformio.ini",
        "src/main.cpp",
        (),
        None,
        id="avr-cpp",
    ),
    pytest.param(
        {"platform": "avr", "avr_language": "rust", "avr_mcu": "atmega328p"},
        "Cargo.toml",
        f"src/bin/{REPO}.rs",
        (".cargo/config.toml", "rust-toolchain.toml"),
        "src-bin",
        id="avr-rust",
    ),
    pytest.param(
        {"platform": "esp", "esp_chip": "esp32", "esp_framework": "espidf"},
        "platformio.ini",
        "src/main.c",
        ("sdkconfig.defaults",),
        "main-link",
        id="esp32-espidf",
    ),
    pytest.param(
        {"platform": "esp", "esp_chip": "esp32", "esp_framework": "arduino"},
        "platformio.ini",
        "src/main.cpp",
        (),
        None,
        id="esp32-arduino",
    ),
    pytest.param(
        {"platform": "esp", "esp_chip": "esp8266", "esp_framework": "arduino"},
        "platformio.ini",
        "src/main.cpp",
        (),
        None,
        id="esp8266-arduino",
    ),
    pytest.param(
        {"platform": "stm32", "stm32_toolchain": "rust", "stm32_board": "f405rg"},
        "Cargo.toml",
        f"src/bin/{REPO}.rs",
        ("build.rs", "memory.x", ".cargo/config.toml", "rust-toolchain.toml"),
        "src-bin",
        id="stm32-rust",
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
        ("src/FreeRTOSConfig.h",),
        None,
        id="stm32-platformio-stm32cube",
    ),
]


@pytest.mark.parametrize("answers, build_file, adapter, extra_files, variation", LAYOUTS)
def test_documented_layout_variation(answers, build_file, adapter, extra_files, variation):
    """ACC-TMPL-46: one build root and one adapter, with only the documented variation."""
    with bake(answers) as path:
        build_files = [
            name for name in ("platformio.ini", "Cargo.toml") if (path / name).is_file()
        ]
        assert build_files == [build_file]
        assert [relative for relative in ADAPTERS if (path / relative).is_file()] == [adapter]
        for relative in extra_files:
            assert (path / relative).is_file(), relative

        assert (path / "src").is_dir()
        if variation == "main-link":
            link = path / "main"
            assert link.is_symlink()
            assert os.readlink(link) == "src"
            assert (link / "main.c").resolve() == (path / "src/main.c").resolve()
        else:
            assert not (path / "main").exists()
            assert not (path / "main").is_symlink()

        if variation == "src-bin":
            assert (path / "src/bin").is_dir()
        if variation == "sketch":
            assert not (path / "src/main.cpp").exists()


def test_one_top_level_structure_across_platforms():
    """ACC-TMPL-46: every platform renders the same top level, varying only as documented."""
    trees = {}
    for name, answers in BRANCHES:
        with bake(answers, components=ALL_COMPONENTS) as path:
            for relative in UNIFIED_ROOTS:
                assert (path / relative).exists(), f"{name}: {relative}"
            assert (path / "src").is_dir(), name
            if espidf(answers):
                assert (path / "main").is_symlink(), name
            else:
                assert not (path / "main").exists(), name
                assert not (path / "main").is_symlink(), name
            build_roots = [
                entry for entry in ("platformio.ini", "Cargo.toml") if (path / entry).is_file()
            ]
            assert len(build_roots) == 1, f"{name}: {build_roots}"
            trees[name] = top_level(path)

    base = trees["arduino-uno"]
    for name, tree in trees.items():
        undocumented = (tree ^ base) - LAYOUT_VARIATIONS
        assert not undocumented, f"{name}: undocumented top-level entries {sorted(undocumented)}"
