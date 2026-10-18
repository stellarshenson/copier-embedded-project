#!/usr/bin/env python3
"""Finish a generated embedded project.

Copier renders one unified project for every platform. This script removes the
parts the answers did not select: the component folders, the adapters and core
of the other toolchains, the unused license and the unused STM32 installer. On
update it removes nothing and prints what a fresh copy would have removed.
"""

from __future__ import annotations

import argparse
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
    "ltspice": ["ltspice"],
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


def remove(path: Path, dry_run: bool) -> None:
    """Remove a file or directory; on update, only report what would go."""
    if not path.exists() and not path.is_symlink():
        return
    if dry_run:
        print(f"post_gen: would remove {path}")
        return
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


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
    if args.platform == "esp" and args.esp_framework == "espidf":
        return "main/main.c"
    if args.platform == "avr" and args.avr_language == "cpp":
        return "src/main.cpp"
    if args.platform == "esp" and args.esp_framework == "arduino":
        return "src/main.cpp"
    if args.platform == "stm32" and not (
        args.stm32_toolchain == "platformio" and args.stm32_framework == "stm32cube"
    ):
        return "src/main.cpp"
    return "src/main.c"


def remove_components(root: Path, components: list[str], dry_run: bool) -> None:
    for name, paths in COMPONENT_PATHS.items():
        if name in components:
            continue
        for relative in paths:
            remove(root / relative, dry_run)
    # resources/ holds two components; when neither is chosen, its last file is gone.
    if "resources" not in components and "env-installers" not in components:
        resources = root / "resources"
        if resources.is_dir() and not any(resources.iterdir()):
            remove(resources, dry_run)


def remove_other_toolchain(root: Path, args: argparse.Namespace, dry_run: bool) -> None:
    if is_rust(args):
        for relative in C_ONLY_PATHS:
            remove(root / relative, dry_run)
        # The AVR application has no linker script and no build script.
        if args.platform == "avr":
            remove(root / "build.rs", dry_run)
            remove(root / "memory.x", dry_run)
    else:
        for relative in RUST_ONLY_PATHS:
            remove(root / relative, dry_run)
        # FreeRTOSConfig.h belongs to the STM32Cube framework only.
        if not (
            args.platform == "stm32"
            and args.stm32_toolchain == "platformio"
            and args.stm32_framework == "stm32cube"
        ):
            remove(root / "src" / "FreeRTOSConfig.h", dry_run)
            remove(root / "tools" / "freertos.py", dry_run)

    # ESP-IDF and the ESP8266 RTOS SDK own the sdkconfig defaults; the Arduino
    # framework and the other build roots do not read them.
    if not (
        args.platform == "esp"
        and args.esp_framework in ("espidf", "esp8266-rtos-sdk")
    ):
        remove(root / "sdkconfig.defaults", dry_run)
    # Project-local Arduino libraries only exist when the answer asks for them.
    if not (args.platform == "arduino" and args.arduino_libraries == "Yes"):
        remove(root / "lib" / "vendor", dry_run)


def keep_one_adapter(root: Path, args: argparse.Namespace, dry_run: bool) -> None:
    keep = selected_adapter(args)
    for relative in ("src/main.c", "src/main.cpp"):
        if relative != keep:
            remove(root / relative, dry_run)

    # Only the chosen Arduino sketch stays in src/.
    sketch_dir = root / "src"
    if sketch_dir.is_dir():
        for sketch in sorted(sketch_dir.glob("*.ino")):
            if str(sketch.relative_to(root)) != keep:
                remove(sketch, dry_run)

    # Only the chosen Rust binary stays in src/bin/.
    bin_dir = root / "src" / "bin"
    if bin_dir.is_dir():
        for entry in sorted(bin_dir.iterdir()):
            if str(entry.relative_to(root)) != keep:
                remove(entry, dry_run)

    # ESP-IDF compiles main/, every other toolchain compiles src/.
    if keep.startswith("main/"):
        remove(root / "src", dry_run)
    else:
        remove(root / "main", dry_run)


def prepare_installers(root: Path, args: argparse.Namespace, dry_run: bool) -> None:
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
            remove(installer, dry_run)

    if not dry_run:
        for installer in sorted(envs.glob("firmware*.py")):
            installer.chmod(installer.stat().st_mode | 0o111)


def remove_empty_component_roots(root: Path, dry_run: bool) -> None:
    """Remove a component root whose files all belonged to unselected components."""
    if dry_run:
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


def init_git(root: Path, enabled: str, dry_run: bool) -> None:
    if enabled != "Yes" or dry_run or (root / ".git").exists():
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
    parser.add_argument("--author-name", default="")
    parser.add_argument("--description", default="")
    parser.add_argument("--platform", required=True, choices=["arduino", "avr", "esp", "stm32"])
    parser.add_argument("--esp-chip", default="")
    parser.add_argument("--esp-framework", default="")
    parser.add_argument("--avr-language", default="c")
    parser.add_argument("--components", default="")
    parser.add_argument("--stm32-toolchain", default="")
    parser.add_argument("--stm32-framework", default="")
    parser.add_argument("--arduino-libraries", default="No")
    parser.add_argument("--arduino-sketch-link", default="No")
    parser.add_argument("--open-source-license", default="MIT")
    parser.add_argument("--git-init", default="No")
    parser.add_argument("--copier-operation", default="copy")
    args = parser.parse_args(argv)
    args.components = [name for name in args.components.split(",") if name]
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = Path.cwd()
    if is_copier_temp_directory(root):
        return 0

    dry_run = args.copier_operation == "update"
    remove_components(root, args.components, dry_run)
    remove_other_toolchain(root, args, dry_run)
    keep_one_adapter(root, args, dry_run)
    prepare_installers(root, args, dry_run)

    if args.open_source_license == "No license file":
        remove(root / "LICENSE", dry_run)
    if not dry_run:
        remove_empty_component_roots(root, dry_run)
        if args.platform == "arduino" and args.arduino_sketch_link == "Yes":
            create_sketch_link(root, args.repo_name)
        if "agents" in args.components:
            link_agents(root)
        init_git(root, args.git_init, dry_run)

    target = f" on {args.platform}"
    if args.platform == "esp" and args.esp_framework:
        target += f" with {args.esp_framework}"
    if args.platform == "stm32" and args.stm32_framework:
        target += f" with {args.stm32_framework}"
    print(f"post_gen: {args.project_name} ready{target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
