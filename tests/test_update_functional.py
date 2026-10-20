"""Update a project rendered at v1.0.16 to the working tree with a real copier update.

The test renders the project at the v1.0.16 tag, commits it, removes and edits starter files under
folders of _skip_if_exists, commits again and runs copier update. It needs no toolchain, and it
runs through `make test-functional` with the builds.
"""

from __future__ import annotations

import json
import os
import subprocess

import pytest
from helpers import ROOT, copier

RUN = os.environ.get("RUN_FUNCTIONAL") == "1"

pytestmark = pytest.mark.skipif(
    not RUN,
    reason="run through `make test-functional`; the test runs a real copier copy and update",
)

OLD_TAG = "v1.0.16"

ANSWERS = {"platform": "esp", "host_side": "Yes"}
COMPONENTS = [
    "notebooks", "resources", "references", "data", "simulator", "docs", "agents",
    "env-installers",
]

# The starter files DEF-POST-9-UPDATE-STARTER names; each one is under a folder of _skip_if_exists.
REMOVED = (
    "docs/design.md",
    "host/tests/test_protocol.py",
    "host/tests/test_serial_client.py",
    "notebooks/README.md",
    "notebooks/telemetry-exploration.ipynb",
    "references/schematics/.gitkeep",
    "resources/graphics/.gitkeep",
    "test/functional/test_qemu.py",
    "test/harness/board.py",
    "test/harness/qemu.py",
    "test/host/test_core.c",
)
EDITED = "test/harness/sim.py"


def git(project, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.com", *args],
        cwd=project, check=True, capture_output=True,
    )


def test_real_update_writes_back_no_starter_file_the_project_removed(tmp_path):
    """DEF-POST-9-UPDATE-STARTER: copier update writes back no starter file the project removed."""
    tag = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/tags/{OLD_TAG}"],
        cwd=ROOT, capture_output=True,
    )
    if tag.returncode != 0:
        pytest.skip(
            f"the template checkout has no {OLD_TAG} tag, which the update starts from; "
            "a shallow clone has no tags"
        )
    project = tmp_path / "board"
    command = [
        copier(), "copy", "--trust", "--defaults", "--vcs-ref", OLD_TAG, str(ROOT), str(project)
    ]
    for key, value in ANSWERS.items():
        command.extend(["-d", f"{key}={value}"])
    command.extend(["-d", "components=" + json.dumps(COMPONENTS)])
    copy = subprocess.run(command, capture_output=True, text=True)
    assert copy.returncode == 0, copy.stderr

    git(project, "init", "-q")
    git(project, "add", "-A")
    git(project, "commit", "-q", "-m", "copy")
    git(project, "rm", "-q", *REMOVED)
    with (project / EDITED).open("a") as handle:
        handle.write("# edited by the project\n")
    edited = (project / EDITED).read_text()
    git(project, "commit", "-q", "-am", "remove and edit starter files")

    # --vcs-ref HEAD renders the working tree; copier includes its uncommitted changes.
    update = subprocess.run(
        [copier(), "update", "--trust", "--defaults", "--vcs-ref", "HEAD"],
        cwd=project, capture_output=True, text=True,
    )

    assert update.returncode == 0, update.stderr
    written_back = [relative for relative in REMOVED if (project / relative).exists()]
    assert written_back == [], f"written back: {written_back}\n{update.stdout[-2000:]}"
    assert (project / EDITED).read_text() == edited
    assert list(project.rglob("*.rej")) == []
