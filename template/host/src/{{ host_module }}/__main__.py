"""Read the console of the board until the boot line arrives.

python -m {{ host_module }} --port PORT --baud BAUD --timeout SECONDS

The command never prompts and prints one JSON line with the port, whether the boot line arrived
and the line itself. It exits 0 when the boot line arrived and 1 otherwise, with the reason under
"error".
"""

from __future__ import annotations

import argparse
import json

from .serial_client import open_port, read_boot_line

BOOT_LINE = "[BOOT] {{ repo_name }}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="{{ host_module }}", description=__doc__)
    parser.add_argument("--port", required=True, help="serial device of the board")
    parser.add_argument("--baud", type=int, default={{ serial_baud }}, help="console baud rate")
    parser.add_argument("--timeout", type=float, default=10.0, help="seconds to wait")
    args = parser.parse_args(argv)

    result = {"port": args.port, "boot": False, "line": ""}
    try:
        line = read_boot_line(open_port(args.port, args.baud), BOOT_LINE, args.timeout)
    except (ImportError, OSError) as error:
        result["error"] = str(error)
        print(json.dumps(result))
        return 1
    if line is None:
        result["error"] = f"no '{BOOT_LINE}' within {args.timeout} s"
        print(json.dumps(result))
        return 1
    result.update(boot=True, line=line)
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
