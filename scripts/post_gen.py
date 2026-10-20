#!/usr/bin/env python3
"""Finish a generated embedded project.

Copier renders one unified project for every platform. This script removes the
parts the answers did not select: the component folders, the host-side package,
the adapters and core of the other toolchains, the unused license and the unused
STM32 installer. On update it removes only the files the update wrote back into
those parts: Copier refuses to update a destination with untracked files, so
every untracked file that git does not ignore came from the update. Tracked and
ignored files stay. This holds only while git status lists untracked files: with
status.showUntrackedFiles=no Copier's check passes, and git ls-files still lists
them, so an untracked file of the user there is removed too.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Each component owns these paths. `device-bridge` owns no path: it only changes
# the files other parts render.
COMPONENT_PATHS = {
    "notebooks": ["notebooks"],
    "resources": ["resources/README.md", "resources/graphics", "resources/external"],
    "references": ["references"],
    "data": ["data"],
    "simulator": ["test/harness", "test/functional", "pytest.ini"],
    "ltspice": ["simulations"],
    "docs": ["docs"],
    "ci": [".github"],
    "agents": [".agents", ".claude/skills", ".claude/commands"],
    "env-installers": ["resources/envs"],
}

# Files that only a Rust project uses.
RUST_ONLY_PATHS = [
    "Cargo.toml",
    "build.rs",
    "memory.x",
    ".cargo",
    "rust-toolchain.toml",
    "src/lib.rs",
    "src/bin",
    "test/host/core.rs",
]

# Files that only a C or C++ project uses.
C_ONLY_PATHS = [
    "platformio.ini",
    "src/main.c",
    "src/main.cpp",
    "src/FreeRTOSConfig.h",
    "lib/core",
    "test/host/test_core.c",
]


def remove(path: Path, written: set[Path] | None) -> None:
    """Remove a file or directory; on update, only the files the update wrote.

    `written` is None on a fresh copy. On update it holds the files the update
    wrote (see `written_files`); those under `path` go, then every directory left
    empty there.
    """
    if not path.exists() and not path.is_symlink():
        return
    if written is not None:
        for file in written:
            if file == path or path in file.parents:
                file.unlink(missing_ok=True)
        if path.is_dir() and not path.is_symlink():
            for directory, _, _ in os.walk(path, topdown=False):
                if not os.listdir(directory):
                    os.rmdir(directory)
        return
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def written_files(root: Path) -> set[Path]:
    """The files an update wrote: untracked and not ignored by git.

    Copier refuses to update a destination that `git status --porcelain` reports
    as dirty, and that includes untracked files, so after an update every such
    file came from the update. This holds only while git status lists untracked
    files: with status.showUntrackedFiles=no Copier's check passes, and the
    listing below still includes them. Without git nothing counts as written.
    """
    try:
        listed = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard", "-z"],
            cwd=root,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        print("post_gen: git is not installed; the update removes nothing")
        return set()
    if listed.returncode != 0:
        print(f"post_gen: {root} is not a git work tree; the update removes nothing")
        return set()
    return {root / name for name in listed.stdout.split("\0") if name}


def create_symlink(link: Path, target: Path) -> None:
    """Create a relative symlink, unless the link already exists."""
    if link.exists() or link.is_symlink():
        return
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(target)


def is_rust(args: argparse.Namespace) -> bool:
    if args.platform == "avr":
        return args.avr_language == "rust"
    if args.platform == "stm32":
        return args.stm32_toolchain == "rust"
    return False


def selected_adapter(args: argparse.Namespace) -> str:
    """Return the one entry point the selected toolchain compiles."""
    if is_rust(args):
        return f"src/bin/{args.repo_name}.rs"
    if args.platform == "arduino":
        return f"src/{args.repo_name}.ino"
    if args.platform == "avr" and args.avr_language == "cpp":
        return "src/main.cpp"
    if args.platform == "esp" and args.esp_framework == "arduino":
        return "src/main.cpp"
    if args.platform == "stm32" and not (
        args.stm32_toolchain == "platformio" and args.stm32_framework == "stm32cube"
    ):
        return "src/main.cpp"
    return "src/main.c"


def remove_components(root: Path, components: list[str], written: set[Path] | None) -> None:
    for name, paths in COMPONENT_PATHS.items():
        if name in components:
            continue
        for relative in paths:
            remove(root / relative, written)
    # resources/ holds two components; when neither is chosen, its last file is gone.
    if "resources" not in components and "env-installers" not in components:
        resources = root / "resources"
        if resources.is_dir() and not any(resources.iterdir()):
            remove(resources, written)


def remove_other_toolchain(
    root: Path, args: argparse.Namespace, written: set[Path] | None
) -> None:
    if is_rust(args):
        for relative in C_ONLY_PATHS:
            remove(root / relative, written)
        # The AVR application has no linker script and no build script.
        if args.platform == "avr":
            remove(root / "build.rs", written)
            remove(root / "memory.x", written)
    else:
        for relative in RUST_ONLY_PATHS:
            remove(root / relative, written)
    # FreeRTOSConfig.h and its build hook belong to the STM32Cube framework only.
    if not (
        args.platform == "stm32"
        and args.stm32_toolchain == "platformio"
        and args.stm32_framework == "stm32cube"
    ):
        remove(root / "src" / "FreeRTOSConfig.h", written)
        remove(root / "scripts" / "freertos.py", written)

    # ESP-IDF and the ESP8266 RTOS SDK own the sdkconfig defaults; the Arduino
    # framework and the other build roots do not read them.
    if not (
        args.platform == "esp"
        and args.esp_framework in ("espidf", "esp8266-rtos-sdk")
    ):
        remove(root / "sdkconfig.defaults", written)
    # Project-local Arduino libraries only exist when the answer asks for them.
    if not (args.platform == "arduino" and args.arduino_libraries == "Yes"):
        remove(root / "lib" / "vendor", written)
    # Only the Arduino and bare AVR Makefile runs the EEPROM tool.
    if args.platform not in ("arduino", "avr"):
        remove(root / "scripts" / "eeprom_tool.py", written)


def keep_one_adapter(root: Path, args: argparse.Namespace, written: set[Path] | None) -> None:
    keep = selected_adapter(args)
    for relative in ("src/main.c", "src/main.cpp"):
        if relative != keep:
            remove(root / relative, written)

    # Only the chosen Arduino sketch stays in src/.
    sketch_dir = root / "src"
    if sketch_dir.is_dir():
        for sketch in sorted(sketch_dir.glob("*.ino")):
            if str(sketch.relative_to(root)) != keep:
                remove(sketch, written)

    # Only the chosen Rust binary stays in src/bin/.
    bin_dir = root / "src" / "bin"
    if bin_dir.is_dir():
        for entry in sorted(bin_dir.iterdir()):
            if str(entry.relative_to(root)) != keep:
                remove(entry, written)

    # Every toolchain compiles src/; main/ is only a compatibility link on ESP-IDF.
    remove(root / "main", written)


def prepare_installers(root: Path, args: argparse.Namespace, written: set[Path] | None) -> None:
    """Keep firmware_env.py and the installer of the selected toolchain; make installers executable."""
    envs = root / "resources" / "envs"
    if not envs.is_dir():
        return

    if args.platform == "stm32":
        chosen = "firmware-stm32.py"
    elif args.platform in ("arduino", "avr"):
        chosen = "firmware-avr.py"
    else:
        chosen = "firmware-esp.py"
    for installer in sorted(envs.glob("firmware-*.py")):
        if installer.name != chosen:
            remove(installer, written)

    if written is None:
        for installer in sorted(envs.glob("firmware*.py")):
            installer.chmod(installer.stat().st_mode | 0o111)


def remove_empty_component_roots(root: Path, update: bool) -> None:
    """Remove a component root whose files all belonged to unselected components."""
    if update:
        return
    for relative in ("resources", ".claude"):
        path = root / relative
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()


def create_sketch_link(root: Path, repo_name: str) -> None:
    link = root / f"{repo_name}.ino"
    target = Path("src") / f"{repo_name}.ino"
    if link.exists() or link.is_symlink():
        return
    if not (root / target).is_file():
        print(f"post_gen: {root / target} is missing; no root sketch link")
        return
    link.symlink_to(target)


def create_main_link(root: Path) -> None:
    """Link main to src for the ESP-IDF build, which expects a component named main."""
    if not (root / "src" / "main.c").is_file():
        print(f"post_gen: {root / 'src' / 'main.c'} is missing; no main link")
        return
    create_symlink(root / "main", Path("src"))


def link_agents(root: Path) -> None:
    """Link every project skill and the command folder into .claude/."""
    skills = root / ".agents" / "skills"
    if skills.is_dir():
        for skill in sorted(skills.iterdir()):
            if skill.is_dir():
                create_symlink(
                    root / ".claude" / "skills" / skill.name,
                    Path("../../.agents/skills") / skill.name,
                )
    workflows = root / ".agents" / "workflows"
    if workflows.is_dir():
        create_symlink(
            root / ".claude" / "commands",
            Path("../.agents/workflows"),
        )


def init_git(root: Path, enabled: str, update: bool) -> None:
    if enabled != "Yes" or update or (root / ".git").exists():
        return
    subprocess.run(
        ["git", "init", "-b", "main", str(root)],
        check=True,
        capture_output=True,
    )


def is_copier_temp_directory(path: Path) -> bool:
    """True for the temporary directory Copier renders into before moving files."""
    return path.name.startswith("copier._main.new_copy.")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--repo-name", required=True)
    parser.add_argument("--platform", required=True, choices=["arduino", "avr", "esp", "stm32"])
    parser.add_argument("--esp-framework", default="")
    parser.add_argument("--avr-language", default="c")
    parser.add_argument("--components", default="")
    parser.add_argument("--stm32-toolchain", default="")
    parser.add_argument("--stm32-framework", default="")
    parser.add_argument("--arduino-libraries", default="No")
    parser.add_argument("--arduino-sketch-link", default="No")
    parser.add_argument("--open-source-license", default="MIT")
    parser.add_argument("--git-init", default="No")
    parser.add_argument("--host-side", default="No")
    parser.add_argument("--copier-operation", default="copy")
    args = parser.parse_args(argv)
    args.components = [name for name in args.components.split(",") if name]
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = Path.cwd()
    if is_copier_temp_directory(root):
        return 0

    update = args.copier_operation == "update"
    written = written_files(root) if update else None
    remove_components(root, args.components, written)
    if args.host_side != "Yes":
        remove(root / "host", written)
    remove_other_toolchain(root, args, written)
    keep_one_adapter(root, args, written)
    if not update and args.platform == "esp" and args.esp_framework == "espidf":
        create_main_link(root)
    prepare_installers(root, args, written)

    if args.open_source_license == "No license file":
        remove(root / "LICENSE", written)
    if not update:
        remove_empty_component_roots(root, update)
        if args.platform == "arduino" and args.arduino_sketch_link == "Yes":
            create_sketch_link(root, args.repo_name)
        if "agents" in args.components:
            link_agents(root)
        init_git(root, args.git_init, update)

    target = f" on {args.platform}"
    if args.platform == "esp" and args.esp_framework:
        target += f" with {args.esp_framework}"
    if args.platform == "stm32" and args.stm32_toolchain == "platformio" and args.stm32_framework:
        target += f" with {args.stm32_framework}"
    print(f"post_gen: {args.project_name} ready{target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
