"""Functional test of the surrounding circuit: the ATtiny84 pin drives an op-amp with gain 2.

The test skips with the reason when neither LTspice nor ngspice is installed; the analog circuit
cannot be checked without a SPICE simulator.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent


def test_the_opamp_follows_the_attiny84_pin():
    result = subprocess.run(
        [sys.executable, str(ROOT / "run.py")], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout.splitlines()[-1])
    if not report["ran"]:
        pytest.skip(report["reason"])
    assert report["ok"], report
