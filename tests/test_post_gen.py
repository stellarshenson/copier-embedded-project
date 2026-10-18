"""post_gen removes files on a fresh copy and leaves them on an update."""

from __future__ import annotations

import importlib.util
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml
from helpers import ROOT

SCRIPT = ROOT / "scripts" / "post_gen.py"
CONFIG_PATH = ROOT / "copier.yml"
REPO = "board"

ALL_COMPONENTS = (
    "notebooks,resources,references,data,simulator,docs,ci,agents,env-installers,device-bridge"
)

# The exact update skip list of docs/template-design.md section 7.2.
REQUIRED_SKIP = {
    "README.md",
    "CHANGELOG.md",
    "AGENTS.md",
    "CLAUDE.md",
    "VERSION",
    "RELEASING.md",
    "docs/README.md",
    "notebooks/README.md",
    "resources/README.md",
    "references/README.md",
    "data/README.md",
    "resources/envs/",
    ".gitignore",
    "pytest.ini",
    "test/",
    "notebooks/",
    "resources/",
    "references/",
    "data/",
    "docs/",
    ".github/",
    ".agents/",
    ".claude/",
}


def load_module():
    spec = importlib.util.spec_from_file_location("post_gen", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_post_gen(
    directory: Path,
    operation: str = "copy",
    platform: str = "arduino",
    components: str = "notebooks",
    **answers: str,
) -> str:
    command = [
        sys.executable,
        str(SCRIPT),
        "--project-name", "board",
        "--repo-name", REPO,
        "--platform", platform,
        "--components", components,
        "--copier-operation", operation,
    ]
    for name, value in answers.items():
        command.extend([f"--{name.replace('_', '-')}", str(value)])
    result = subprocess.run(command, cwd=directory, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return result.stdout


def write(directory: Path, relative: str, content: str = "") -> None:
    path = directory / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def tree_state(directory: Path) -> dict[str, tuple]:
    """Every entry with its content, mode and symlink target."""
    state = {}
    for path in sorted(directory.rglob("*")):
        relative = str(path.relative_to(directory))
        if path.is_symlink():
            state[relative] = ("link", os.readlink(path), stat.S_IMODE(path.lstat().st_mode))
        elif path.is_file():
            state[relative] = ("file", path.read_bytes(), stat.S_IMODE(path.lstat().st_mode))
        else:
            state[relative] = ("dir", None, stat.S_IMODE(path.lstat().st_mode))
    return state


def make_tree(directory: Path) -> None:
    """Every path the unified template renders, whatever the answers."""
    for relative in (
        "src/main.c",
        "src/main.cpp",
        "src/board.ino",
        "src/FreeRTOSConfig.h",
        "src/lib.rs",
        "src/bin/board.rs",
        "Cargo.toml",
        "build.rs",
        "memory.x",
        ".cargo/config.toml",
        "rust-toolchain.toml",
        "sdkconfig.defaults",
        "lib/core/core.c",
        "lib/core/core.h",
        "lib/README.md",
        "lib/vendor/README.md",
        "test/host/test_core.c",
        "test/host/core.rs",
        "test/harness/qemu.py",
        "test/functional/test_boot.py",
        "pytest.ini",
        "notebooks/README.md",
        "resources/README.md",
        "resources/graphics/README.md",
        "resources/external/README.md",
        "resources/envs/firmware-avr.py",
        "references/README.md",
        "data/README.md",
        "docs/README.md",
        ".github/workflows/build.yml",
        ".agents/skills/board-device/SKILL.md",
        ".agents/skills/board-toolchain/SKILL.md",
        ".agents/skills/board-toolchain/references/toolchains.md",
        ".agents/workflows/build-and-flash.md",
        ".claude/CLAUDE.md",
        "LICENSE",
    ):
        write(directory, relative)


def test_fresh_copy_removes_the_unselected_components():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        run_post_gen(directory, components="notebooks")

        assert (directory / "notebooks/README.md").is_file()
        assert (directory / ".claude/CLAUDE.md").is_file()
        for relative in (
            "resources",
            "references",
            "data",
            "docs",
            ".github",
            ".agents",
            ".claude/skills",
            ".claude/commands",
            "test/harness",
            "test/functional",
            "pytest.ini",
        ):
            assert not (directory / relative).exists(), relative


def test_fresh_copy_keeps_every_selected_component():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        run_post_gen(directory, components=ALL_COMPONENTS)

        for relative in (
            "notebooks/README.md",
            "resources/README.md",
            "resources/graphics",
            "resources/external",
            "resources/envs/firmware-avr.py",
            "references/README.md",
            "data/README.md",
            "docs/README.md",
            ".github/workflows/build.yml",
            ".agents/skills/board-device/SKILL.md",
            "test/harness/qemu.py",
            "test/functional/test_boot.py",
            "pytest.ini",
        ):
            assert (directory / relative).exists(), relative


def test_env_installers_survive_without_the_resources_component():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        run_post_gen(directory, components="env-installers")

        assert (directory / "resources/envs/firmware-avr.py").is_file()
        assert not (directory / "resources/README.md").exists()
        assert not (directory / "resources/graphics").exists()


def test_update_removes_nothing():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        before = tree_state(directory)

        output = run_post_gen(
            directory,
            operation="update",
            platform="stm32",
            components="",
            stm32_toolchain="rust",
            open_source_license="No license file",
            git_init="Yes",
        )

        assert tree_state(directory) == before
        assert "would remove" in output
        assert not (directory / ".git").exists()


def test_skip_list_protects_every_user_owned_path():
    config = yaml.safe_load(CONFIG_PATH.read_text())
    skip = set(config["_skip_if_exists"])

    assert REQUIRED_SKIP <= skip
    for template_owned in ("Makefile", "platformio.ini", "Cargo.toml", "src/main.c"):
        assert template_owned not in skip, template_owned


def test_rust_branch_drops_the_c_toolchain():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        run_post_gen(directory, platform="stm32", stm32_toolchain="rust")

        for relative in (
            "Cargo.toml",
            "build.rs",
            "memory.x",
            ".cargo/config.toml",
            "rust-toolchain.toml",
            "src/lib.rs",
            "src/bin/board.rs",
            "test/host/core.rs",
        ):
            assert (directory / relative).exists(), relative
        for relative in (
            "platformio.ini",
            "src/main.c",
            "src/main.cpp",
            "src/FreeRTOSConfig.h",
            "lib/core",
            "test/host/test_core.c",
            "main",
        ):
            assert not (directory / relative).exists(), relative


def test_c_branch_drops_the_rust_toolchain():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        run_post_gen(directory, platform="arduino")

        for relative in (
            "src/board.ino",
            "lib/core/core.c",
            "test/host/test_core.c",
        ):
            assert (directory / relative).exists(), relative
        for relative in (
            "Cargo.toml",
            "build.rs",
            "memory.x",
            ".cargo",
            "rust-toolchain.toml",
            "src/lib.rs",
            "src/bin",
            "test/host/core.rs",
            "src/main.c",
            "src/main.cpp",
            "main",
        ):
            assert not (directory / relative).exists(), relative


def test_avr_rust_has_no_linker_script_or_build_script():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        run_post_gen(directory, platform="avr", avr_language="rust")

        assert (directory / "Cargo.toml").is_file()
        assert (directory / "src/bin/board.rs").is_file()
        assert not (directory / "platformio.ini").exists()
        assert not (directory / "build.rs").exists()
        assert not (directory / "memory.x").exists()
        assert not (directory / "lib/core").exists()


@pytest.mark.parametrize(
    "platform, answers, kept, dropped",
    [
        ("avr", {"avr_language": "c"}, "src/main.c", "src/main.cpp"),
        ("avr", {"avr_language": "cpp"}, "src/main.cpp", "src/main.c"),
        (
            "esp",
            {"esp_framework": "espidf"},
            "src/main.c",
            "src/main.cpp",
        ),
        (
            "esp",
            {"esp_framework": "arduino"},
            "src/main.cpp",
            "src/main.c",
        ),
        (
            "esp",
            {"esp_framework": "esp8266-rtos-sdk"},
            "src/main.c",
            "src/main.cpp",
        ),
        (
            "stm32",
            {"stm32_toolchain": "platformio", "stm32_framework": "stm32cube"},
            "src/main.c",
            "src/main.cpp",
        ),
        (
            "stm32",
            {"stm32_toolchain": "platformio", "stm32_framework": "arduino"},
            "src/main.cpp",
            "src/main.c",
        ),
    ],
)
def test_one_adapter_is_kept(platform, answers, kept, dropped):
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        run_post_gen(directory, platform=platform, **answers)

        assert (directory / kept).is_file()
        assert not (directory / dropped).exists()
        assert not (directory / "src/board.ino").exists()


def test_sdkconfig_defaults_belongs_to_esp_idf():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        run_post_gen(directory, platform="esp", esp_framework="arduino")

        assert not (directory / "sdkconfig.defaults").exists()


def test_stm32cube_keeps_freertos_config():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        run_post_gen(
            directory,
            platform="stm32",
            stm32_toolchain="platformio",
            stm32_framework="stm32cube",
        )

        assert (directory / "src/FreeRTOSConfig.h").is_file()


def test_stm32_arduino_drops_freertos_config():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        run_post_gen(
            directory,
            platform="stm32",
            stm32_toolchain="platformio",
            stm32_framework="arduino",
        )

        assert not (directory / "src/FreeRTOSConfig.h").exists()


def test_arduino_libraries_off_drops_the_vendor_tree():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        run_post_gen(directory, platform="arduino", arduino_libraries="No")

        assert not (directory / "lib/vendor").exists()
        assert (directory / "lib/core/core.c").is_file()


def test_arduino_libraries_on_keeps_the_vendor_tree():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        run_post_gen(directory, platform="arduino", arduino_libraries="Yes")

        assert (directory / "lib/vendor/README.md").is_file()


def test_sketch_link_creates_the_root_symlink():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        run_post_gen(directory, platform="arduino", arduino_sketch_link="Yes")

        link = directory / "board.ino"
        assert link.is_symlink()
        assert os.readlink(link) == "src/board.ino"
        assert link.resolve() == (directory / "src/board.ino").resolve()


def test_sketch_link_off_leaves_the_sketch_in_src():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        run_post_gen(directory, platform="arduino", arduino_sketch_link="No")

        assert (directory / "src/board.ino").is_file()
        assert not (directory / "board.ino").exists()


def test_update_does_not_create_the_sketch_link():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        run_post_gen(directory, operation="update", platform="arduino", arduino_sketch_link="Yes")

        assert not (directory / "board.ino").exists()


def test_esp_idf_keeps_src_and_links_main_to_it():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        run_post_gen(directory, platform="esp", esp_framework="espidf")

        assert (directory / "src/main.c").is_file()
        link = directory / "main"
        assert link.is_symlink()
        assert os.readlink(link) == "src"
        assert link.resolve() == (directory / "src").resolve()


def test_update_does_not_create_the_main_link():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        run_post_gen(
            directory,
            operation="update",
            platform="esp",
            esp_framework="espidf",
        )

        assert not (directory / "main").exists()
        assert not (directory / "main").is_symlink()


@pytest.mark.parametrize("existing", ["file", "directory"])
def test_existing_main_object_makes_create_main_link_leave_it_alone(existing):
    module = load_module()
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        (directory / "src").mkdir()
        (directory / "src/main.c").write_text("void app_main(void) {}\n")
        main = directory / "main"
        if existing == "file":
            main.write_text("user file")
        else:
            main.mkdir()
            (main / "user.c").write_text("user file")

        module.create_main_link(directory)

        assert not main.is_symlink()
        if existing == "file":
            assert main.read_text() == "user file"
        else:
            assert (main / "user.c").read_text() == "user file"


def test_no_license_answer_removes_the_license_file():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        run_post_gen(directory, open_source_license="No license file")

        assert not (directory / "LICENSE").exists()


def test_license_answer_keeps_the_license_file():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        run_post_gen(directory, open_source_license="Apache-2.0")

        assert (directory / "LICENSE").is_file()


@pytest.mark.parametrize("toolchain", ["rust", "platformio"])
def test_stm32_keeps_the_one_installer_for_both_toolchains(toolchain):
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        write(directory, "resources/envs/firmware-stm32.py", "both")
        write(directory, "resources/envs/firmware-stm32-pio.py", "pio")
        run_post_gen(
            directory,
            platform="stm32",
            stm32_toolchain=toolchain,
            components="env-installers",
        )

        installer = directory / "resources/envs" / "firmware-stm32.py"
        assert installer.read_text() == "both"
        assert not (directory / "resources/envs" / "firmware-stm32-pio.py").exists()
        assert installer.stat().st_mode & stat.S_IXUSR


def test_non_stm32_platform_drops_the_stm32_installers():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        write(directory, "resources/envs/firmware-stm32.py", "rust")
        write(directory, "resources/envs/firmware-stm32-pio.py", "pio")
        write(directory, "resources/envs/firmware-esp.py", "esp")
        run_post_gen(directory, platform="arduino", components="env-installers")

        envs = directory / "resources" / "envs"
        assert (envs / "firmware-avr.py").is_file()
        assert not (envs / "firmware-stm32.py").exists()
        assert not (envs / "firmware-stm32-pio.py").exists()
        assert not (envs / "firmware-esp.py").exists()


def test_every_remaining_installer_is_executable():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        run_post_gen(directory, platform="arduino", components="env-installers")

        assert (directory / "resources/envs/firmware-avr.py").stat().st_mode & stat.S_IXUSR


def test_unselected_resources_root_is_removed():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        run_post_gen(directory, components="notebooks")

        assert not (directory / "resources").exists()
        assert (directory / ".claude/CLAUDE.md").is_file()


def test_device_bridge_owns_no_path():
    with tempfile.TemporaryDirectory() as temp:
        first = Path(temp) / "with"
        second = Path(temp) / "without"
        first.mkdir()
        second.mkdir()
        make_tree(first)
        make_tree(second)

        run_post_gen(first, components=ALL_COMPONENTS)
        without = [name for name in ALL_COMPONENTS.split(",") if name != "device-bridge"]
        run_post_gen(second, components=",".join(without))

        assert tree_state(first) == tree_state(second)


def test_existing_sketch_link_is_left_alone():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        link = directory / "board.ino"
        link.write_text("user file")

        run_post_gen(directory, platform="arduino", arduino_sketch_link="Yes")

        assert not link.is_symlink()
        assert link.read_text() == "user file"


def test_agent_links_point_into_the_agents_folder():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        run_post_gen(directory, components="agents")

        skill = directory / ".claude/skills/board-device"
        toolchain = directory / ".claude/skills/board-toolchain"
        commands = directory / ".claude/commands"
        assert skill.is_symlink()
        assert os.readlink(skill) == "../../.agents/skills/board-device"
        assert skill.resolve() == (directory / ".agents/skills/board-device").resolve()
        assert toolchain.is_symlink()
        assert os.readlink(toolchain) == "../../.agents/skills/board-toolchain"
        assert toolchain.resolve() == (directory / ".agents/skills/board-toolchain").resolve()
        assert commands.is_symlink()
        assert os.readlink(commands) == "../.agents/workflows"
        assert commands.resolve() == (directory / ".agents/workflows").resolve()
        assert directory.resolve() in commands.resolve().parents


def test_git_init_yes_creates_a_main_branch():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        run_post_gen(directory, git_init="Yes")

        assert (directory / ".git").is_dir()
        branch = subprocess.run(
            ["git", "-C", str(directory), "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        assert branch == "main"


def test_git_init_no_leaves_no_repository():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        make_tree(directory)
        run_post_gen(directory, git_init="No")

        assert not (directory / ".git").exists()


def test_copier_temp_directory_is_detected():
    module = load_module()
    assert module.is_copier_temp_directory(Path("copier._main.new_copy.abc")) is True
    assert module.is_copier_temp_directory(Path("copier-embedded-project")) is False


def test_normal_directory_is_not_a_copier_temp_directory():
    module = load_module()
    assert module.is_copier_temp_directory(ROOT) is False


def test_copier_temp_directory_is_skipped():
    with tempfile.TemporaryDirectory(prefix="copier._main.new_copy.", dir="/tmp") as temp:
        directory = Path(temp)
        make_tree(directory)
        output = run_post_gen(directory)

        assert output == ""
        assert (directory / "Cargo.toml").exists()
