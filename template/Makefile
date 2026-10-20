{%- set installer_name = 'firmware-avr' if platform in ['arduino', 'avr'] else 'firmware-' ~ platform -%}
{%- set environment_scope = environment_scope | default('global') -%}
{%- set avr_rust = platform == 'avr' and avr_language | default('c') == 'rust' -%}
{%- set stm32_rust = platform == 'stm32' and stm32_toolchain == 'rust' -%}
{%- set rust = avr_rust or stm32_rust -%}
{%- set simulator = 'simulator' in components -%}
{%- set ltspice = 'ltspice' in components -%}
{%- set installers = 'env-installers' in components -%}
{%- set bridge = 'device-bridge' in components -%}
{%- set eeprom = platform in ['arduino', 'avr'] -%}
{%- set avr_harness = simulator and ((platform == 'arduino' and arduino_board in ['uno', 'nano']) or (platform == 'avr' and avr_mcu in ['atmega328p', 'attiny85'])) -%}
{%- set avr_programmer_id = ('arduinoisp' if avr_programmer == 'arduino-isp' else 'usbasp') if platform == 'avr' else '' -%}
.PHONY: help {% if installers %}create_environment env {% endif %}build upload monitor test host-test{% if host_side == 'Yes' %} host-run host-app-test{% endif %}{% if simulator %} sim{% endif %}{% if ltspice %} ltspice{% endif %}{% if eeprom %} eeprom-backup eeprom-restore{% endif %} increment_version clean

#################################################################################
# GLOBALS                                                                       #
#################################################################################

.DEFAULT_GOAL := help

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
ENV = {{ env_name }}
ENV_RUN = conda run --no-capture-output -n $(ENV)
ENV_SCOPE ?= {{ environment_scope }}
ifeq ($(ENV_SCOPE),local)
export CONDA_ENVS_PATH := $(PROJECT_DIR)/.conda/envs
endif
{% if bridge %}
DEVICE_DIR := $(shell if [ -w /run/devices ]; then echo /run/devices; else echo /tmp/jupyterlab-device-$$(id -u); fi)
PORT ?= $(shell ls $(DEVICE_DIR)/tty-* 2>/dev/null | head -n 1)
STM32_SERIAL_MODE = 8n1
{% else %}
PORT ?= /dev/ttyUSB0
STM32_SERIAL_MODE = 8e1
{% endif %}
BAUD ?= {{ serial_baud }}
HOST_CC = x86_64-conda-linux-gnu-cc
BUILD_DIR = build
{% if avr_harness %}
SIMHARNESS = .pio/simharness/libsimharness.so
{% endif %}

MSG_PREFIX = \033[1m\033[36m>>>\033[0m

#################################################################################
# COMMANDS                                                                      #
#################################################################################

{% if installers %}
## Install the conda environment with the toolchain of this project
create_environment:
	./resources/envs/{{ installer_name }}.py

env: create_environment
{% endif %}

## Build the firmware
build:
{%- if avr_rust %}
	@echo "$(MSG_PREFIX) building with cargo for {{ avr_target }}"
	$(ENV_RUN) cargo build --release --target {{ avr_target }} --features firmware -Z build-std=core
{%- elif stm32_rust %}
	@echo "$(MSG_PREFIX) building with cargo for {{ thumb_target }}"
	$(ENV_RUN) cargo build --release --target {{ thumb_target }} --features firmware
{%- else %}
	@echo "$(MSG_PREFIX) building with PlatformIO"
	$(ENV_RUN) pio run
{%- endif %}

## Upload the firmware to the board on $(PORT)
upload:
{%- if avr_rust %}
	@echo "$(MSG_PREFIX) flashing $(PORT) with avrdude"
	$(ENV_RUN) avrdude -c {{ avr_programmer_id }} -p {{ avr_mcu_custom if avr_mcu == 'other' else avr_mcu }} -P $(PORT) -U flash:w:target/{{ avr_target }}/release/{{ repo_name }}.elf:e
{%- elif stm32_rust %}
	@echo "$(MSG_PREFIX) flashing $(PORT) with stm32flash"
	$(ENV_RUN) cargo objcopy --release --target {{ thumb_target }} --features firmware -- -O binary $(BUILD_DIR)/{{ repo_name }}.bin
	$(ENV_RUN) stm32flash -b $(BAUD) -m $(STM32_SERIAL_MODE) -w $(BUILD_DIR)/{{ repo_name }}.bin -v -g 0x0 $(PORT)
{%- else %}
	@echo "$(MSG_PREFIX) uploading to $(PORT)"
	$(ENV_RUN) pio run -t upload --upload-port $(PORT)
{%- endif %}

## Open the serial console on $(PORT) at $(BAUD) baud
monitor:
{%- if rust %}
	$(ENV_RUN) python -m serial.tools.miniterm $(PORT) $(BAUD)
{%- else %}
	$(ENV_RUN) pio device monitor --port $(PORT) -b $(BAUD)
{%- endif %}

## Run the host unit tests{% if host_side == 'Yes' %} and the host application tests{% endif %}{% if simulator %} and the simulator tests{% endif %}{% if ltspice %} and the circuit test{% endif %}
test: host-test{% if host_side == 'Yes' %} host-app-test{% endif %}{% if simulator %} sim{% endif %}{% if ltspice %} ltspice{% endif %}

host-test:
	@mkdir -p $(BUILD_DIR)
{%- if rust %}
	$(ENV_RUN) cargo test --target-dir $(BUILD_DIR) --lib --test core --target x86_64-unknown-linux-gnu
{%- else %}
	@echo "$(MSG_PREFIX) compiling the host unit tests"
	$(ENV_RUN) $(HOST_CC) -std=c11 -Wall -Wextra -I lib/core lib/core/core.c test/host/test_core.c -o $(BUILD_DIR)/host-test
	$(ENV_RUN) ./$(BUILD_DIR)/host-test
{%- endif %}
{%- if host_side == 'Yes' %}

## Read the boot line from the board on $(PORT) with the host application
host-run:
	$(ENV_RUN) env PYTHONPATH=host/src python -m {{ host_module }} --port $(PORT) --baud $(BAUD)

## Run the host application tests
host-app-test:
	$(ENV_RUN) env PYTHONPATH=host/src pytest host/tests -q
{%- endif %}
{% if simulator %}

{% if avr_harness %}
$(SIMHARNESS): test/harness/simharness.c
	@mkdir -p $(dir $@)
	$(ENV_RUN) sh -c 'S=$$PLATFORMIO_CORE_DIR/packages/tool-simavr; $(HOST_CC) -O2 -Wall -shared -fPIC -I$$S/include/simavr -o $(SIMHARNESS) test/harness/simharness.c -L$$S/lib -lsimavr -Wl,-rpath,$$S/lib'
{% endif %}
## Run the firmware in the simulator
sim: build{% if avr_harness %} $(SIMHARNESS){% endif %}
{%- if platform == 'arduino' %}
{%- if arduino_board in ['uno', 'nano'] %}
	$(ENV_RUN) pytest test/functional -q
{%- elif arduino_board == 'mega2560' %}
	@echo "Skipping the simulator: 256 KB is above simavr's documented 128 KB limit"
{%- elif arduino_board == 'leonardo' %}
	@echo "Skipping the simulator: simavr does not document the ATmega32U4"
{%- else %}
	@echo "Skipping the simulator: simavr supports documented MCUs with at most 128 KB of flash"
{%- endif %}
{%- elif platform == 'avr' %}
{%- if avr_mcu in ['atmega328p', 'attiny85'] %}
	$(ENV_RUN) pytest test/functional -q
{%- elif avr_mcu == 'atmega32u4' %}
	@echo "Skipping the simulator: simavr does not document the ATmega32U4"
{%- else %}
	@echo "Skipping the simulator: simavr supports documented MCUs with at most 128 KB of flash"
{%- endif %}
{%- elif platform == 'esp' %}
{%- if esp_chip == 'esp32' %}
	@$(ENV_RUN) sh -c 'if command -v qemu-system-xtensa >/dev/null 2>&1; then pytest test/functional -q; else echo "Skipping the simulator: qemu-system-xtensa is not installed"; fi'
{%- else %}
	@echo "Skipping the simulator: mainline QEMU has no ESP8266 machine"
{%- endif %}
{%- elif stm32_board == 'f405rg' %}
	@$(ENV_RUN) sh -c 'if command -v qemu-system-arm >/dev/null 2>&1; then pytest test/functional -q; else echo "Skipping the simulator: qemu-system-arm is not installed"; fi'
{%- else %}
	@echo "Skipping the simulator: no QEMU machine for this STM32 board"
{%- endif %}
{% endif %}
{% if ltspice %}

## Simulate the surrounding circuit with LTspice or ngspice
ltspice:
	$(ENV_RUN) pytest simulations -q
{% endif %}
{% if eeprom %}

# Back up the board EEPROM under resources/eeprom/ and print one JSON line
eeprom-backup:
	$(ENV_RUN) python scripts/eeprom_tool.py backup{% if platform == 'arduino' %} --board {{ pio_board }}{% endif %} --port $(PORT){% if platform == 'avr' %} --mcu {{ avr_mcu_custom if avr_mcu == 'other' else avr_mcu }} --programmer {{ avr_programmer_id }}{% endif %}

# Restore an EEPROM image and verify the read-back
eeprom-restore:
	$(ENV_RUN) python scripts/eeprom_tool.py restore{% if platform == 'arduino' %} --board {{ pio_board }}{% endif %} --port $(PORT){% if platform == 'avr' %} --mcu {{ avr_mcu_custom if avr_mcu == 'other' else avr_mcu }} --programmer {{ avr_programmer_id }}{% endif %}
{% endif %}

## Remove build output and caches
clean:
	@echo "$(MSG_PREFIX) removing build output and caches"
	@rm -rf .pio target $(BUILD_DIR) logs tmp .pytest_cache __pycache__
	@find . -type d -name __pycache__ -prune -exec rm -rf {} +

## Increment the patch version in VERSION
increment_version:
	@current=$$(cat VERSION); \
	major=$$(echo $$current | cut -d. -f1); \
	minor=$$(echo $$current | cut -d. -f2); \
	patch=$$(echo $$current | cut -d. -f3); \
	new_patch=$$((patch + 1)); \
	new_version="$$major.$$minor.$$new_patch"; \
	printf '%s\n' "$$new_version" > VERSION; \
	echo "Version bumped: $$current -> $$new_version"

#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

define PRINT_HELP_PYSCRIPT
import sys; \
lines = sys.stdin.read().splitlines(); \
marker = chr(35) * 2 + ' '; \
pairs = [(lines[i + 1].split(':', 1)[0], lines[i][len(marker):]) for i in range(len(lines) - 1) if lines[i].startswith(marker) and ':' in lines[i + 1]]; \
pairs.sort(key=lambda pair: pair[0]); \
print('\nAvailable rules:\n'); \
print('\n'.join('\033[36m{:25}\033[0m{}'.format(*pair) for pair in pairs)); \
print()
endef
export PRINT_HELP_PYSCRIPT

## Print the list of available commands
help:
{%- if not installers %}
	@echo "No environment installer in this project; run ~/.local/lab-utils/envs/{{ installer_name }}.py"
{%- endif %}
	@python3 -c "$${PRINT_HELP_PYSCRIPT}" < $(MAKEFILE_LIST)

# EOF
