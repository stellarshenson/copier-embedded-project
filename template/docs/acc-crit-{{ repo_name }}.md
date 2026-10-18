# Acceptance criteria - {{ project_name }}

Behaviour the firmware must show, one item per line. This file is the store; `pm-tools` is the
only way in, and every closed item names the test that proved it.

## Authors

- `@kj` Konrad Jelen

## Boot `BOOT`

The board starts and reports itself.

- [ ] `ACC-BOOT-1` **Boot line** - HIGH; the firmware prints `[BOOT] {{ repo_name }}` on its serial console once at startup
  - test: run the firmware in the simulator; assert the line on the serial output
  - test-tags: FUNCTIONAL
  - mechanism: {% now 'utc', '%Y-%m-%dT%H:%M:%SZ' %} @kj the starter initializes the console and prints the line before its loop
  - log: {% now 'utc', '%Y-%m-%dT%H:%M:%SZ' %} @kj added

## Logic `LOGIC`

Pure logic, compiled and tested on the host.

- [ ] `ACC-LOGIC-2` **CRC-8 check value** - MEDIUM; the CRC-8 of `123456789` is `0xF4` and of an empty buffer is `0x00`
  - test: host unit test of the logic module
  - test-tags: UNIT
  - mechanism: {% now 'utc', '%Y-%m-%dT%H:%M:%SZ' %} @kj polynomial 0x07, initial value 0x00
  - log: {% now 'utc', '%Y-%m-%dT%H:%M:%SZ' %} @kj added
