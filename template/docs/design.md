# Design - {{ project_name }}

## Purpose

{{ description or 'What the firmware does, for whom, and what it must never do.' }}

## Hardware

{%- if platform == 'arduino' %}
Board {{ pio_board }} with the Arduino framework.
{%- elif platform == 'avr' %}
MCU {{ avr_mcu }} at {{ avr_clock }} Hz, no Arduino framework.
{%- elif platform == 'esp' %}
Chip {{ esp_chip }}, board {{ esp_board }}, framework {{ esp_framework }}.
{%- elif stm32_toolchain == 'rust' %}
Board {{ stm32_board }}, Rust embedded, target {{ thumb_target }}, uploaded with stm32flash.
{%- else %}
Board {{ pio_board }}, framework {{ stm32_framework }}.
{%- endif %}

## Structure

- `src/` - the firmware; hardware access stays at its edge
- `src/logic.c`{% if platform == 'stm32' and stm32_toolchain == 'rust' %}`logic/`{% endif %} - pure logic, compiled and tested on the host
- `test/host/` - host tests of that logic
{%- if 'simulator' in components %}
- `test/functional/` - tests that boot the firmware in the simulator
{%- endif %}
- `resources/envs/` - the conda environment installers of the toolchain

## Decisions

Record each decision with the alternative it replaced and the reason. A later reader needs the
reason more than the decision.
