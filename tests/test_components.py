"""The multiselect components add and remove exactly their folders and content."""

from __future__ import annotations

import subprocess

import pytest
from helpers import bake

DEFAULT_COMPONENTS = [
    "notebooks",
    "resources",
    "references",
    "simulator",
    "agents",
    "env-installers",
]

ALL_COMPONENTS = DEFAULT_COMPONENTS + [
    "data",
    "ltspice",
    "docs",
    "ci",
]


def test_ltspice_component_renders_the_circuit():
    with bake({"platform": "arduino"}, components=DEFAULT_COMPONENTS + ["ltspice"]) as path:
        for present in (
            "simulations/README.md",
            "simulations/circuit.cir",
            "simulations/run.py",
            "simulations/test_circuit.py",
        ):
            assert (path / present).is_file(), present
        netlist = (path / "simulations" / "circuit.cir").read_text()
        assert "PULSE(0 5 0 1u 1u 500u 1000u)" in netlist
        assert ".meas tran vhigh" in netlist
        makefile = (path / "Makefile").read_text()
        assert "\nltspice:" in makefile
        test_line = next(line for line in makefile.splitlines() if line.startswith("test:"))
        assert "ltspice" in test_line

    with bake({"platform": "arduino"}) as path:
        assert not (path / "simulations").exists()
        assert "\nltspice:" not in (path / "Makefile").read_text()


def test_default_components():
    with bake({"platform": "arduino"}) as path:
        assert (path / "notebooks/README.md").is_file()
        assert (path / "resources/README.md").is_file()
        assert (path / "references/README.md").is_file()
        assert (path / "test/harness").is_dir()
        assert (path / "test/functional").is_dir()
        assert (path / ".agents/skills/board-device/SKILL.md").is_file()
        assert (path / "resources/envs/firmware-avr.py").is_file()
        assert not (path / "data").exists()
        assert not (path / "docs").exists()
        assert not (path / ".github").exists()
        skill = (path / ".agents/skills/board-device/SKILL.md").read_text()
        assert "jupyterlab-device" not in skill


def test_minimal_components():
    with bake({"platform": "arduino"}, components=["notebooks"]) as path:
        assert (path / "notebooks/README.md").is_file()
        assert (path / "notebooks/telemetry-exploration.ipynb").is_file()
        assert not (path / "test/harness").exists()
        assert not (path / "test/functional").exists()
        assert not (path / ".agents").exists()
        assert not (path / ".claude").exists()
        assert not (path / "references").exists()
        assert not (path / "data").exists()
        assert not (path / "resources").exists()
        makefile = (path / "Makefile").read_text()
        assert "\nsim:" not in makefile
        result = subprocess.run(["make", "help"], cwd=path, capture_output=True, text=True)
        assert "Run the firmware in the simulator" not in result.stdout


def test_all_components():
    with bake({"platform": "arduino"}, components=ALL_COMPONENTS) as path:
        assert (path / "docs/README.md").is_file()
        assert (path / "docs/design.md").is_file()
        assert (path / ".github/workflows/build.yml").is_file()
        assert (path / ".agents/workflows").is_dir()
        assert (path / "resources/graphics").is_dir()
        assert (path / "resources/external").is_dir()
        assert (path / "references/datasheets").is_dir()
        assert (path / "references/notes").is_dir()
        assert (path / "data/README.md").is_file()
        assert (path / "resources/envs/firmware-avr.py").is_file()


def test_agents_master_layout():
    with bake({"platform": "arduino"}) as path:
        skill = path / ".claude/skills/board-device"
        toolchain = path / ".claude/skills/board-toolchain"
        commands = path / ".claude/commands"
        assert skill.is_symlink()
        assert skill.resolve() == (path / ".agents/skills/board-device").resolve()
        assert toolchain.is_symlink()
        assert toolchain.resolve() == (path / ".agents/skills/board-toolchain").resolve()
        assert commands.is_symlink()
        assert commands.resolve() == (path / ".agents/workflows").resolve()
        assert (path / ".agents/skills/board-device/SKILL.md").is_file()
        assert (path / ".agents/skills/board-toolchain/SKILL.md").is_file()
        assert (path / ".agents/skills/board-toolchain/references/toolchains.md").is_file()

    without = [item for item in DEFAULT_COMPONENTS if item != "agents"]
    with bake({"platform": "arduino"}, components=without) as path:
        assert not (path / ".agents").exists()
        assert not (path / ".claude").exists()


def test_toolchain_skill_adds_ltspice_only_when_selected():
    with bake({"platform": "arduino"}, components=DEFAULT_COMPONENTS + ["ltspice"]) as path:
        text = (path / ".agents/skills/board-toolchain/SKILL.md").read_text()
        assert "## Run LTspice" in text

    with bake({"platform": "arduino"}) as path:
        text = (path / ".agents/skills/board-toolchain/SKILL.md").read_text()
        assert "## Run LTspice" not in text


def test_data_component():
    onto = [item for item in DEFAULT_COMPONENTS if item != "data"]
    with bake({"platform": "arduino"}, components=onto + ["data"]) as path:
        readme = (path / "data/README.md").read_text()
        assert "raw/" in readme
        assert "processed/" in readme
        assert "gitignored" in readme
        assert (path / "data/raw").is_dir()
        assert (path / "data/processed").is_dir()
        assert (path / "data/raw/.gitignore").is_file()

    with bake({"platform": "arduino"}, components=onto) as path:
        assert not (path / "data").exists()


def test_references_component():
    with bake({"platform": "arduino"}) as path:
        readme = (path / "references/README.md").read_text()
        assert "datasheets/" in readme
        assert "notes/" in readme
        assert (path / "references/datasheets").is_dir()
        assert (path / "references/notes").is_dir()

    without = [item for item in DEFAULT_COMPONENTS if item != "references"]
    with bake({"platform": "arduino"}, components=without) as path:
        assert not (path / "references").exists()


def test_resources_readme_purposes():
    with bake({"platform": "arduino"}) as path:
        readme = (path / "resources/README.md").read_text()
        assert "graphics/" in readme
        assert "Project binaries" in readme
        assert "make eeprom-backup" in readme
        assert "envs/" in readme


def test_resources_and_env_installers_are_separate():
    with bake({"platform": "arduino"}, components=["env-installers"]) as path:
        assert (path / "resources/envs/firmware-avr.py").is_file()
        assert not (path / "resources/README.md").exists()
        assert not (path / "resources/graphics").exists()
        assert not (path / "resources/external").exists()


def test_notebooks_readme_names_the_starter():
    with bake({"platform": "arduino"}) as path:
        readme = (path / "notebooks/README.md").read_text()
        assert "telemetry-exploration.ipynb" in readme
        assert "notebooks/cache/" in readme


def test_docs_component_renders_both_trackers():
    with bake({"platform": "arduino"}, components=DEFAULT_COMPONENTS + ["docs"]) as path:
        acc = path / "docs/acc-crit-board.md"
        defects = path / "docs/defects-board.md"
        assert acc.is_file()
        assert defects.is_file()
        acc_text = acc.read_text()
        defects_text = defects.read_text()
        assert acc_text.startswith("# Acceptance criteria - board")
        assert defects_text.startswith("# Defects - board")
        assert "## Authors" in acc_text
        assert "## Authors" in defects_text
        assert "ACC-BOOT-1" in acc_text
        assert "ACC-LOGIC-2" in acc_text
        assert "## Boot `BOOT`" in defects_text

    with bake({"platform": "arduino"}) as path:
        assert not (path / "docs/acc-crit-board.md").exists()
        assert not (path / "docs/defects-board.md").exists()


def test_device_skill_covers_the_board():
    with bake({"platform": "arduino"}) as path:
        text = (path / ".agents/skills/board-device/SKILL.md").read_text()
        for heading in (
            "## Board facts",
            "## Port discovery",
            "## Environment",
            "## Build and upload",
            "## Non-interactive console",
            "## Commands",
            "## Troubleshooting",
        ):
            assert heading in text, heading
        assert "`make create_environment`" in text
        assert "`make build`" in text
        assert "`make upload PORT=<port>`" in text
        assert "[BOOT] board" in text
        assert "| Symptom | Cause | Action |" in text
        assert "simavr" in text


def test_device_skill_covers_bare_avr_rust():
    with bake({"platform": "avr", "avr_language": "rust", "avr_mcu": "atmega328p"}) as path:
        text = (path / ".agents/skills/board-device/SKILL.md").read_text()
        assert "bare AVR with Cargo and avrdude" in text
        assert "ISP through `avrdude -c " in text
        assert "Upload:  programmer" not in text
        assert "`make upload PORT=<port>`" in text


DEVICE_SECTIONS = [
    "Identity",
    "Connection",
    "Device protocol",
    "Device code",
    "Host protocol",
    "Host code",
    "Traps and recovery",
    "Observed and untested",
    "Sources",
]


def test_acc_tmpl_56_devref_readme_names_the_format_and_the_file_naming():
    """ACC-TMPL-56-DEVREF-README: devices/README.md names the nine sections in order."""
    with bake({"platform": "arduino"}) as path:
        readme = (path / "references/devices/README.md").read_text()
        assert "references/devices/<device>.md" in readme
        assert "references/datasheets/" in readme
        assert "jupyterlab-device-bridge-extension" in readme
        positions = [readme.find(f"| {section} |") for section in DEVICE_SECTIONS]
        assert -1 not in positions, positions
        assert positions == sorted(positions), positions
        listing = (path / "references/README.md").read_text()
        assert "- `devices/` - " in listing
        assert not any(path.rglob("turmo-usb-monitor.md"))


def test_acc_tmpl_58_devref_absent_without_references():
    """ACC-TMPL-58-DEVREF-ABSENT: no device reference without the references component."""
    without = [item for item in DEFAULT_COMPONENTS if item != "references"]
    with bake({"platform": "arduino"}, components=without) as path:
        assert not (path / "references").exists()


SIMULATIONS = {"README.md", "circuit.cir", "run.py", "test_circuit.py"}


@pytest.mark.parametrize(
    "answers",
    [
        pytest.param({"platform": "arduino"}, id="arduino"),
        pytest.param({"platform": "esp"}, id="esp"),
        pytest.param({"platform": "stm32"}, id="stm32"),
    ],
)
def test_acc_tmpl_65_sims_circuit_simulations_live_in_simulations(answers):
    """ACC-TMPL-65-SIMS: the ltspice component renders simulations/; no file names ltspice/."""
    with bake(answers, components=ALL_COMPONENTS) as path:
        assert {entry.name for entry in (path / "simulations").iterdir()} == SIMULATIONS
        assert "pytest simulations -q" in (path / "Makefile").read_text()
        skill = (path / ".agents/skills/board-toolchain/SKILL.md").read_text()
        assert "python simulations/run.py" in skill
        named_ltspice = []
        mentions = []
        for entry in path.rglob("*"):
            relative = entry.relative_to(path)
            if ".git" in relative.parts:
                continue
            if entry.name == "ltspice":
                named_ltspice.append(str(relative))
            if entry.is_file() and "ltspice/" in entry.read_text(errors="ignore"):
                mentions.append(str(relative))
        assert named_ltspice == []
        assert mentions == []


def test_acc_tmpl_65_sims_absent_without_the_ltspice_component():
    """ACC-TMPL-65-SIMS: without the ltspice component neither simulations/ nor ltspice/ exists."""
    without = [item for item in ALL_COMPONENTS if item != "ltspice"]
    with bake({"platform": "arduino"}, components=without) as path:
        assert not (path / "simulations").exists()
        assert not (path / "ltspice").exists()
