# lib

{% if toolchain_language == 'rust' %}
The project libraries. The shared core is the package library in `src/lib.rs`, and the host tests
build it for the workstation.
{% else %}
The project libraries. PlatformIO compiles every folder under `lib/`, and the host tests compile the
core source directly.
{% endif %}

## core

{% if toolchain_language == 'rust' %}
`src/lib.rs` holds the pure logic: no hardware register and no HAL crate. The adapter at
`src/bin/{{ repo_name }}.rs` calls it, and `test/host/core.rs` tests the same library on the host.
Logic that needs a hardware header belongs in the adapter, not here.
{% else %}
`lib/core/core.c` and `lib/core/core.h` hold the pure logic: no hardware register, no Arduino and no
HAL header. The adapter includes `"core.h"`; `test/host/test_core.c` compiles the same source on the
host. Logic that needs a hardware header belongs in the adapter, not here.
{% endif %}

## Library register

| Library | Version | Notes |
|---|---|---|
| `core` | in-tree | shared core, no external dependency |
{%- if arduino_libraries == 'Yes' %}
| vendor/<name> | <version> | add one row per folder under `lib/vendor/` |
{%- endif %}

Pin a library version in this table and keep the full library in the repository, so the firmware
builds alone.
