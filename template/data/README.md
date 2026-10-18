# data

Inputs and derived data of the project. Nothing here is compiled into the firmware.

- `raw/` - untouched captures: serial logs, sensor dumps, register exports; the contents are gitignored
- `processed/` - tables and figures derived from `raw/`, kept when they are small and reproducible

Record here the command that turns `raw/` into `processed/`. Keep a large capture out of git when a
checksum and a download location are enough.
