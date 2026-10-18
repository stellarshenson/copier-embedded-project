"""Run the surrounding-circuit netlist with LTspice or ngspice and check the op-amp gain.

The ATtiny84 pin is modeled as a 0-5 V pulse at 1 kHz; the firmware is not co-simulated. The
non-inverting amplifier has gain 2, so the output swings 0 V to 5 V. The script prints one JSON
line and exits 0 when no simulator is installed or the gain is right, and 1 when the gain is wrong.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NETLIST = ROOT / "circuit.cir"
LOG = ROOT / "circuit.log"
MEASUREMENT = re.compile(r"\b(vhigh|vlow)\s*=\s*([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)")
LTSPICE = ("XVIIx64.exe", "LTspiceXVII.exe", "LTspice.exe", "LTspice", "ltspice", "LTspiceXVII")


def simulator() -> list[str] | None:
    """The command that runs the netlist: LTspice first, ngspice second."""
    for name in LTSPICE:
        found = shutil.which(name)
        if found:
            return [found, "-b", str(NETLIST)]
    found = shutil.which("ngspice")
    if found:
        return [found, "-b", str(NETLIST)]
    return None


def measurements(text: str) -> dict[str, float]:
    return {name.lower(): float(value) for name, value in MEASUREMENT.findall(text)}


def main() -> int:
    command = simulator()
    if command is None:
        print(json.dumps({"ran": False, "reason": "LTspice and ngspice are not installed"}))
        return 0

    LOG.unlink(missing_ok=True)
    result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    text = result.stdout + result.stderr
    if LOG.is_file():
        text += LOG.read_text(errors="replace")
    values = measurements(text)
    high, low = values.get("vhigh"), values.get("vlow")
    ok = (
        result.returncode == 0
        and high is not None
        and low is not None
        and abs(high - 5.0) <= 0.05
        and abs(low) <= 0.05
    )
    print(
        json.dumps(
            {
                "ran": True,
                "command": command,
                "vhigh": high,
                "vlow": low,
                "ok": ok,
            }
        )
    )
    if not ok:
        print(text[-2000:], file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
