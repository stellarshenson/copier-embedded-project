# tools

Project tools that run on the host: parsers of the serial output, backup and restore commands,
calibration helpers. A tool is non-interactive, prints one JSON line, and exits non-zero with a
reason on failure, so an agent can run it.
