"""Every generated project carries the release procedure and its version."""

from __future__ import annotations

import os
import re
import subprocess

import yaml
from helpers import ROOT, bake

ARDUINO = {"platform": "arduino", "arduino_board": "uno"}
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def run_make(project, target: str) -> subprocess.CompletedProcess:
    environment = dict(os.environ)
    for name in ("MAKEFLAGS", "MAKELEVEL", "MFLAGS"):
        environment.pop(name, None)
    return subprocess.run(
        ["make", target], cwd=project, capture_output=True, text=True, env=environment
    )


def help_names(output: str) -> set[str]:
    names = set()
    for line in output.splitlines():
        match = re.match(r"^([a-z_][a-z0-9_-]*)\s{2,}\S", line)
        if match:
            names.add(match.group(1))
    return names


def announces_approval(text: str) -> bool:
    """Every release action shares a paragraph with an approval requirement."""
    blocks = re.split(r"\n\s*\n", text.lower())
    return all(
        any("approval" in block and action in block for block in blocks)
        for action in ("commit", "tag", "push")
    )


def test_release_files_render():
    """A fresh project carries VERSION, RELEASING.md and the CHANGELOG headings."""
    with bake(ARDUINO) as project:
        assert (project / "VERSION").read_text().strip() == "0.1.0"
        assert (project / "RELEASING.md").is_file()
        changelog = (project / "CHANGELOG.md").read_text()
        assert "## [Unreleased]" in changelog
        assert "## [0.1.0]" in changelog


def test_help_lists_increment_version():
    """make help lists the release target beside the lifecycle targets."""
    with bake(ARDUINO) as project:
        result = run_make(project, "help")
        assert result.returncode == 0, result.stderr
        assert "increment_version" in help_names(ANSI.sub("", result.stdout))


def test_increment_version_bumps_the_patch():
    """make increment_version moves VERSION from 0.1.0 to 0.1.1 and names both."""
    with bake(ARDUINO) as project:
        result = run_make(project, "increment_version")
        assert result.returncode == 0, result.stderr
        assert (project / "VERSION").read_text().strip() == "0.1.1"
        assert "Version bumped" in result.stdout
        assert "0.1.0" in result.stdout
        assert "0.1.1" in result.stdout


def test_release_workflow_ships_with_the_agents_component():
    """The agents component carries the release command with its safeguards."""
    with bake(ARDUINO, components=["agents"]) as project:
        workflow = project / ".agents" / "workflows" / "release.md"
        assert workflow.is_file()
        body = workflow.read_text()
        assert "make increment_version" in body
        assert "v<version>" in body
        assert announces_approval(body)


def test_release_workflow_is_absent_without_the_agents_component():
    """Without the agents component the project has no release command."""
    with bake(ARDUINO, components=["notebooks"]) as project:
        assert not (project / ".agents" / "workflows" / "release.md").exists()


def test_update_skip_list_protects_the_release_files():
    """copier update keeps the project's version and release notes."""
    config = yaml.safe_load((ROOT / "copier.yml").read_text())
    skip = set(config["_skip_if_exists"])
    assert {"VERSION", "RELEASING.md"} <= skip
