"""Build and simulate five rendered projects through their own Makefile.

The suite renders one project per toolchain, runs `make build` and then `make sim` inside it, and
reports the stage each case reached. A first run downloads the toolchain packages and the crates,
so the suite is kept out of `make test` and runs through `make test-functional`.

A missing conda environment, toolchain or emulator skips with the exact reason, and the reason
names the stage: `render`, `build` or `sim`.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from helpers import bake

RUN = os.environ.get("RUN_FUNCTIONAL") == "1"

pytestmark = pytest.mark.skipif(
    not RUN,
    reason="run through `make test-functional`; the builds need conda environments and the network",
)

CASES = [
    pytest.param(
        {"platform": "avr", "avr_language": "rust", "avr_mcu": "atmega328p"},
        "firmware-avr",
        id="avr-rust",
    ),
    pytest.param(
        {"platform": "stm32", "stm32_toolchain": "rust", "stm32_board": "f405rg"},
        "firmware-stm32",
        id="stm32-rust",
    ),
    pytest.param(
        {"platform": "arduino", "arduino_board": "uno"},
        "firmware-avr",
        id="arduino-uno",
    ),
    pytest.param(
        {"platform": "esp", "esp_chip": "esp32", "esp_framework": "arduino"},
        "firmware-esp",
        id="esp32-arduino",
    ),
    pytest.param(
        {"platform": "esp", "esp_chip": "esp32", "esp_framework": "espidf"},
        "firmware-esp",
        id="esp32-espidf",
    ),
]

MISSING_TOOLCHAIN = (
    "can't find crate for `core`",
    "error[E0463]",
    "is not installed",
    "may not be installed",
    "unknown target",
    "toolchain '",
)

SKIPPED = re.compile(r"SKIPPED \[\d+\] [^:]+:\d+: (.*)")
SIMULATOR_SKIP = re.compile(r"Skipping the simulator: (.*)")


def environment(name: str) -> None:
    """Skip unless the conda environment of this case exists."""
    conda = shutil.which("conda")
    if conda is None:
        pytest.skip("conda is not installed (stage: render)")
    result = subprocess.run([conda, "env", "list", "--json"], capture_output=True, text=True)
    if result.returncode != 0:
        pytest.skip(f"conda env list failed (stage: render): {result.stderr.strip()}")
    paths = json.loads(result.stdout).get("envs", [])
    if not any(Path(path).name == name for path in paths):
        pytest.skip(
            f"the conda environment {name} is not installed (stage: render); "
            "run make create_environment in the rendered project first"
        )


def make(path: Path, target: str, case: str, timeout: int) -> subprocess.CompletedProcess:
    """Run one Makefile target inside the project and print the stage and its output tail."""
    print(f"[{case}] stage {target}: make {target}", flush=True)
    result = subprocess.run(
        ["make", target], cwd=path, capture_output=True, text=True, timeout=timeout
    )
    tail = (result.stdout + result.stderr).strip()[-3000:]
    print(f"[{case}] stage {target}: exit {result.returncode}\n{tail}", flush=True)
    return result


def missing_toolchain(text: str) -> str | None:
    """The first line that names an absent toolchain or target, or None."""
    for line in text.splitlines():
        if any(signature in line for signature in MISSING_TOOLCHAIN):
            return line.strip()
    return None


@pytest.mark.parametrize("answers, env_name", CASES)
def test_the_project_builds_and_simulates(answers: dict, env_name: str, request):
    """Render, `make build`, `make sim`: each stage passes, skips with its reason or fails."""
    case = request.node.callspec.id
    environment(env_name)

    with bake(answers) as path:
        print(f"[{case}] stage render: {path}", flush=True)

        build = make(path, "build", case, timeout=1800)
        text = build.stdout + build.stderr
        if build.returncode != 0:
            absent = missing_toolchain(text)
            if absent is not None:
                pytest.skip(f"{env_name}: {absent} (stage: build)")
            pytest.fail(f"make build failed (stage: build):\n{text[-3000:]}")

        simulation = make(path, "sim", case, timeout=900)
        text = simulation.stdout + simulation.stderr
        if simulation.returncode != 0:
            pytest.fail(f"make sim failed (stage: sim):\n{text[-3000:]}")

        reasons = SKIPPED.findall(text) + SIMULATOR_SKIP.findall(text)
        if reasons and " passed" not in text:
            pytest.skip("build passed; " + "; ".join(reason.strip() for reason in reasons) + " (stage: sim)")
        if " passed" not in text:
            pytest.fail(f"make sim reported no passing test (stage: sim):\n{text[-3000:]}")
