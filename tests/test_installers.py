"""The environment installers ship with the template and reach the generated project."""

from __future__ import annotations

import ast
import os
import subprocess

import pytest
from helpers import ROOT, bake

ENVS = ROOT / "template" / "resources" / "envs"
MASTER = ROOT / "envs"

PLATFORM_INSTALLER = {
    "arduino": "firmware-avr.py",
    "avr": "firmware-avr.py",
    "esp": "firmware-esp.py",
    "stm32": "firmware-stm32.py",
}

INSTALLER_CASES = [
    pytest.param({"platform": "arduino"}, "firmware-avr.py", id="arduino"),
    pytest.param({"platform": "avr"}, "firmware-avr.py", id="avr"),
    pytest.param({"platform": "esp"}, "firmware-esp.py", id="esp"),
    pytest.param(
        {"platform": "stm32", "stm32_toolchain": "rust"}, "firmware-stm32.py", id="stm32-rust"
    ),
    pytest.param(
        {"platform": "stm32", "stm32_toolchain": "platformio"},
        "firmware-stm32.py",
        id="stm32-platformio",
    ),
]


@pytest.mark.parametrize(
    "name",
    [
        "firmware-avr.py",
        "firmware-esp.py",
        "firmware-stm32.py",
        "firmware_env.py",
    ],
)
def test_template_copy_matches_the_master(name):
    """envs/ is the master; the template carries a copy of every installer."""
    assert (MASTER / name).is_file(), name
    assert (ENVS / name).read_bytes() == (MASTER / name).read_bytes()


def test_stm32_installer_has_both_toolchains():
    text = (ENVS / "firmware-stm32.py").read_text()
    assert 'STSTM32 = "20.0.0"' in text
    assert "ststm32@" in text
    assert "env.platformio" in text
    assert 'PLATFORMIO = "6.2.0"' in text
    assert 'RUST = "1.99.0"' in text
    assert "thumbv7em-none-eabihf" in text


@pytest.mark.parametrize("path", sorted(ENVS.glob("firmware-*.py")), ids=lambda p: p.name)
def test_installer_parses(path):
    ast.parse(path.read_text())


def test_rendered_project_keeps_only_the_chosen_installer():
    with bake(
        {
            "platform": "stm32",
            "stm32_toolchain": "platformio",
            "stm32_framework": "stm32cube",
            "stm32_board": "f405rg",
        }
    ) as path:
        envs = path / "resources" / "envs"
        assert (envs / "firmware-stm32.py").is_file()
        assert not (envs / "firmware-avr.py").exists()
        assert not (envs / "firmware-esp.py").exists()

    with bake({"platform": "stm32", "stm32_toolchain": "rust"}) as path:
        envs = path / "resources" / "envs"
        assert (envs / "firmware-stm32.py").is_file()

    with bake({"platform": "arduino"}) as path:
        envs = path / "resources" / "envs"
        assert (envs / "firmware-avr.py").is_file()
        assert (envs / "firmware_env.py").is_file()
        assert not (envs / "firmware-esp.py").exists()
        assert not (envs / "firmware-stm32.py").exists()


@pytest.mark.parametrize("answers, installer", INSTALLER_CASES)
def test_the_chosen_installer_is_executable(answers, installer):
    with bake(answers) as path:
        envs = path / "resources" / "envs"
        script = envs / installer
        assert script.is_file()
        assert os.access(script, os.X_OK)
        for other in sorted(envs.glob("firmware-*.py")):
            assert os.access(other, os.X_OK), other


@pytest.mark.parametrize("answers, installer", INSTALLER_CASES)
def test_make_env_runs_the_chosen_installer(answers, installer):
    with bake(answers) as path:
        result = subprocess.run(
            ["make", "-n", "env"], cwd=path, capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr
        assert installer in result.stdout


def test_without_env_installers_make_env_has_no_rule():
    components = ["notebooks", "resources", "simulator", "agents"]
    with bake({"platform": "arduino"}, components=components) as path:
        assert not (path / "resources" / "envs").exists()
        result = subprocess.run(
            ["make", "-n", "env"], cwd=path, capture_output=True, text=True
        )
        assert result.returncode != 0
        assert "No rule to make target" in result.stderr


SCOPE_BLOCK = (
    "ifeq ($(ENV_SCOPE),local)\n"
    "export CONDA_ENVS_PATH := $(PROJECT_DIR)/.conda/envs\n"
    "endif"
)


@pytest.mark.parametrize("scope", ["global", "local"])
def test_environment_scope_sets_the_default_and_keeps_the_installer(scope):
    with bake({"platform": "arduino", "environment_scope": scope}) as path:
        makefile = (path / "Makefile").read_text()
        assert f"ENV_SCOPE ?= {scope}" in makefile
        assert SCOPE_BLOCK in makefile
        result = subprocess.run(
            ["make", "-n", "create_environment"], cwd=path, capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr
        assert PLATFORM_INSTALLER["arduino"] in result.stdout


def test_rendered_gitignore_hides_the_local_environment():
    with bake({"platform": "arduino"}) as path:
        assert ".conda/" in (path / ".gitignore").read_text()
