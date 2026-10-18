---
description: Build the firmware, upload it to the board and confirm its boot line
---

Build and flash {{ project_name }}.

1. `make build`
2. `make upload PORT=$ARGUMENTS` - when no port is given, list the ports and ask the user:
   `ls /dev/ttyUSB* /dev/ttyACM*`{% if 'device-bridge' in components %}, or `ls $DEVICE_DIR` for a bridge pty{% endif %}
3. Read the console until the line `[BOOT] {{ repo_name }}` appears; do not leave an interactive
   monitor running
4. Report the build size and the first boot line

Stop at the first failure and give the exact error text; do not retry the same command.
