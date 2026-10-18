---
name: {{ repo_name }}-toolchain
description: Manage the conda environment {{ env_name }} of {{ project_name }} and run the tools it carries - builds, simulators, ngspice and LTspice circuit simulation. Use when a toolchain program is missing, the environment must be installed, checked or repaired, or a simulator or circuit run must be started.
---
{% set installer_name = 'firmware-avr' if platform in ['arduino', 'avr'] else 'firmware-' ~ platform -%}
{%- set has_installers = 'env-installers' in components -%}
{%- set has_simulator = 'simulator' in components -%}
{%- set has_ltspice = 'ltspice' in components -%}
{%- set local = (environment_scope | default('global')) == 'local' -%}

# {{ project_name }} toolchain skill

The project builds, uploads and simulates inside one conda environment. Run every command below from
the project root. The Makefile enters the environment with `conda run`; never activate it by hand.
Board facts and upload commands are in the `{{ repo_name }}-device` skill.

## First run, in order

1. `make help` - list the targets. Stop and report if `make` or the expected target is missing.
2. {% if has_installers %}`make create_environment`{% else %}`~/.local/lab-utils/envs/{{ installer_name }}.py`{% endif %} - install `{{ env_name }}`. Ask the user first. The installer ends with a tool table; every tool must show a version.
3. `make build` - build the firmware. On failure read the first error line, not the last.
4. `make test` - run the host tests. All must pass.
{% set step = 5 -%}
{% if has_simulator -%}
{{ step }}. `make sim` - run the simulator tests. A skipped test is not a pass; read the printed reason.
{% set step = step + 1 -%}
{% endif -%}
{{ step }}. Only after the earlier steps pass: `make upload PORT=<port>`, then the read loop in the `{{ repo_name }}-device` skill.

## Environment

- Name: `{{ env_name }}`
- Installer: {% if has_installers %}`resources/envs/{{ installer_name }}.py`{% else %}`~/.local/lab-utils/envs/{{ installer_name }}.py`{% endif %}
- Scope: {% if local %}local - the environment lives under `.conda/envs/{{ env_name }}` in the project{% else %}global - the environment lives in the conda root{% endif %}
- Form: a `uv` script with its own shebang; run it as a program, never with `python`
- Needs: `uv`, x86-64 Linux, internet, and conda at `/opt/conda/bin/conda` or in `CONDA_CMD`
- Idempotent: every finished stage leaves a marker in `<prefix>/.firmware-env/`; a rerun installs only the missing stages, and a listed environment without its conda stage marker is recreated
- Full output: `~/.local/{{ env_name }}.out`

Read `references/toolchains.md` when the installer fails or a tool reports an unexpected version.

## Commands

| Task | Command |
|---|---|
| Install or repair | {% if has_installers %}`make create_environment`{% else %}`~/.local/lab-utils/envs/{{ installer_name }}.py`{% endif %} |
| Verify the environment | `make build`, then `make test` |
| Confirm one tool | `conda run -n {{ env_name }} <tool> --version` |
| Show the environment prefix | `conda run -n {{ env_name }} python -c "import sys; print(sys.prefix)"` |
| Read the installer log | `tail -50 ~/.local/{{ env_name }}.out` |
| Remove the environment | {% if local %}`conda env remove -p .conda/envs/{{ env_name }}`{% else %}`conda env remove -n {{ env_name }}`{% endif %} |

## Rules

- Ask the user before running an installer or removing an environment. Both change the workstation.
- Do not install a missing tool with `apt`, `pip`, `cargo install` or `rustup`; the installer owns
  every tool, and a second copy on the PATH is the usual cause of a version mismatch.
- Do not edit the installer in this project. The master lives in `envs/` of the template repository;
  report a faulty stage there.
- Build, upload and test through the make targets. They enter the environment for you.
- A stage that fails leaves its marker unwritten. Rerun the installer before you investigate.

{% if has_simulator %}
## Simulator

1. `make sim`.
2. All tests must pass. A skipped test prints its reason; read it before you report the result.
3. The test-capability table in `README.md` names the emulator for this board. A board marked
   `HIL only` has no emulator; run the test on hardware.
4. Confirm the emulator program: {% if platform == 'esp' %}`conda run -n {{ env_name }} qemu-system-xtensa --version`{% elif platform == 'stm32' %}`conda run -n {{ env_name }} qemu-system-arm --version`{% else %}simavr is the PlatformIO package `tool-simavr`, used by `test/harness`{% endif %}.
{% endif %}
{% if has_ltspice %}
## Run LTspice

1. `make ltspice`.
2. Read the single JSON line it prints:
   - `"ok": true` - the circuit passed; stop.
   - `"ran": false` - neither LTspice nor ngspice is installed; run
     {% if has_installers %}`make create_environment`{% else %}the installer{% endif %}, then repeat step 1.
   - `"ok": false` - the gain is wrong; `vhigh` must be 5 V and `vlow` 0 V, each within 0.05 V.
3. Read the simulator output: `cat ltspice/circuit.log`.
4. Run a simulator by hand only to inspect it: `ltspice -b ltspice/circuit.cir` when LTspice is on
   the PATH, otherwise `ngspice -b ltspice/circuit.cir`.

The netlist models the ATtiny84 pin as a 0-5 V pulse at 1 kHz, divided to 2.5 V and amplified by a
non-inverting op-amp with gain 2. The firmware is not co-simulated: the pin is the voltage source the
firmware produces.
{% endif %}

## Failure modes

| Symptom | Cause | Action |
|---|---|---|
| `conda: command not found` | conda is not at `/opt/conda/bin/conda` | set `CONDA_CMD` to the conda binary and rerun |
| The installer stops mid-stage | network or a failed download | rerun; completed stages are skipped, the log names the failed command |
| The environment exists but a tool is missing | an interrupted stage | rerun the installer; the conda stage recreates an incomplete environment |
| `pio`, `cargo` or `avrdude` not found in a shell | the shell is not inside the environment | use `make`, or `conda run -n {{ env_name }}` |
{% if has_simulator %}
| `make sim` skips | the emulator is absent or the board has none | read the reason; rerun the installer when it names a missing program |
{% endif %}
{% if has_ltspice %}
| `make ltspice` skips | neither LTspice nor ngspice is on the PATH | rerun the installer, which carries ngspice |
{% endif %}
