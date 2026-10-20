"""The opt-in host side: a Python package under host/ that talks to the board over serial."""

from __future__ import annotations

import ctypes
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time

import pytest
import yaml
from helpers import MATRIX, ROOT, bake, copier, text_files

CONFIG = yaml.safe_load((ROOT / "copier.yml").read_text())
WEATHER_STATION = {
    "platform": "avr",
    "avr_language": "c",
    "repo_name": "weather-station",
    "host_side": "Yes",
}
BOOT_LINE = "[BOOT] weather-station"
HOST_TEXT = ("host-run", "host-app-test", "host_module", "host/src")
ANSI = re.compile(r"\x1b\[[0-9;]*m")


@pytest.fixture(scope="module")
def weather_station():
    """One AVR C render of weather-station with the host side, shared by the tests below."""
    with bake(WEATHER_STATION) as path:
        yield path


def host_env() -> dict[str, str]:
    return {**os.environ, "PYTHONPATH": "host/src"}


def run_host_tests(project) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "pytest", "host/tests", "-q"],
        cwd=project,
        env=host_env(),
        capture_output=True,
        text=True,
    )


def test_host_side_no_renders_no_host_package():
    components = CONFIG["components"]["choices"]
    with bake({"platform": "avr", "host_side": "No"}, components=components) as path:
        assert not (path / "host").exists()
        for file in text_files(path):
            text = file.read_text(errors="replace")
            for token in HOST_TEXT:
                assert token not in text, f"{file.relative_to(path)} holds {token}"


def test_host_side_yes_renders_the_package(weather_station):
    host = weather_station / "host"
    for name in ("__init__.py", "__main__.py", "serial_client.py", "protocol.py"):
        assert (host / "src/weatherstation_host" / name).is_file(), name
    assert (host / "tests/test_serial_client.py").is_file()
    assert (host / "tests/test_protocol.py").is_file()
    pyproject = (host / "pyproject.toml").read_text()
    assert 'name = "weather-station-host"' in pyproject
    assert 'dependencies = ["pyserial"]' in pyproject


def test_rendered_host_tests_pass(weather_station):
    result = run_host_tests(weather_station)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("answers", MATRIX)
def test_host_package_stays_out_of_the_build_inputs(answers):
    with bake({**answers, "host_side": "Yes"}) as path:
        assert (path / "host/src/board_host/__main__.py").is_file()
        inputs = [path / "platformio.ini", path / "Cargo.toml"]
        inputs += (path / "src").rglob("*")
        inputs = [file for file in inputs if file.is_file()]
        for file in inputs:
            # test/host/ is the host test of the core, not the host package.
            text = file.read_text().replace("test/host/", "")
            assert "host/" not in text, file.relative_to(path)
            assert "board_host" not in text, file.relative_to(path)


def test_protocol_crc8_mirrors_core_crc8(weather_station, tmp_path):
    compiler = shutil.which("cc") or shutil.which("gcc")
    if not compiler:
        pytest.skip("no C compiler (cc or gcc) to build lib/core/core.c as a shared library")
    library = tmp_path / "libcore.so"
    subprocess.run(
        [compiler, "-shared", "-fPIC", "-I", "lib/core", "lib/core/core.c", "-o", str(library)],
        cwd=weather_station,
        check=True,
    )
    core = ctypes.CDLL(str(library))
    core.core_crc8.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
    core.core_crc8.restype = ctypes.c_uint8
    spec = importlib.util.spec_from_file_location(
        "protocol", weather_station / "host/src/weatherstation_host/protocol.py"
    )
    protocol = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(protocol)

    for data in (b"", b"123456789", BOOT_LINE.encode(), bytes(range(256))):
        assert protocol.crc8(data) == core.core_crc8(data, len(data)), data


def test_cli_reads_the_boot_line_from_a_pty(weather_station):
    check = subprocess.run([sys.executable, "-c", "import serial"], capture_output=True)
    if check.returncode != 0:
        pytest.skip(f"pyserial is not importable by {sys.executable}, which runs the host CLI")
    master, slave = os.openpty()
    port = os.ttyname(slave)
    process = subprocess.Popen(
        [sys.executable, "-m", "weatherstation_host", "--port", port, "--timeout", "5"],
        cwd=weather_station,
        env=host_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        # pyserial empties the input buffer when it opens the port, so the line repeats until
        # the command exits.
        deadline = time.monotonic() + 15
        while process.poll() is None and time.monotonic() < deadline:
            os.write(master, f"{BOOT_LINE}\n".encode())
            time.sleep(0.2)
        stdout, stderr = process.communicate(timeout=5)
    finally:
        process.kill()
        os.close(master)
        os.close(slave)

    assert process.returncode == 0, stdout + stderr
    lines = stdout.splitlines()
    assert len(lines) == 1, stdout
    assert json.loads(lines[0]) == {"port": port, "boot": True, "line": BOOT_LINE}


def test_host_module_is_asked_only_with_the_host_side():
    assert "host_side == 'Yes'" in CONFIG["host_module"]["when"]


def test_host_module_default_is_the_repo_name_without_hyphens(weather_station):
    assert (weather_station / "host/src/weatherstation_host").is_dir()
    with bake({"platform": "avr", "host_side": "Yes"}) as path:
        assert [entry.name for entry in (path / "host/src").iterdir()] == ["board_host"]


def test_host_module_answer_names_the_package():
    with bake({**WEATHER_STATION, "host_module": "probe"}) as path:
        assert [entry.name for entry in (path / "host/src").iterdir()] == ["probe"]
        result = run_host_tests(path)
        assert result.returncode == 0, result.stdout + result.stderr
        cli = subprocess.run(
            [sys.executable, "-m", "probe", "--help"],
            cwd=path,
            env=host_env(),
            capture_output=True,
            text=True,
        )
        assert cli.returncode == 0, cli.stderr
        assert ANSI.sub("", cli.stdout).startswith("usage: probe ")


@pytest.mark.parametrize("module", ["bad-name", "1probe"])
def test_host_module_must_be_a_python_identifier(module, tmp_path):
    result = subprocess.run(
        [
            copier(), "copy", "--trust", "--defaults", "--vcs-ref", "HEAD",
            "-d", "platform=avr", "-d", "host_side=Yes", "-d", f"host_module={module}",
            str(ROOT), str(tmp_path / "board"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "host_module must be a Python identifier" in ANSI.sub("", result.stderr)


def test_host_side_no_ignores_a_host_module_answer():
    with bake({"platform": "avr", "host_side": "No", "host_module": "probe"}) as path:
        assert not (path / "host").exists()
        answers = yaml.safe_load((path / ".copier-answers.yml").read_text())
        assert answers["host_side"] == "No"
        assert "host_module" not in answers
