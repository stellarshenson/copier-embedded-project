# Device bridge notes for generated projects

The lab's device bridge gives container programs a pty for a board granted in the browser. A generated project uploads and monitors through that pty with the same commands it uses for a real serial port.

## Port

- One pty per attached port, named `tty-<vid>-<pid>` in hex: `tty-0483-374b` for an ST-Link, `tty-303a-1001` for an ESP32-C3 USB Serial/JTAG
- Directory: `/run/devices` when writable, else `/tmp/jupyterlab-device-<uid>`
- The generated `Makefile` keeps `PORT ?=` and passes it to pio, avrdude and stm32flash; set it once per board
- `jupyterlab-device monitor read <device>` prints the recent output of a port without holding it

## Settings record

- One record per port holds baud rate, data bits, parity, stop bits and the action on open; the browser opens the Web Serial port with these values
- The wire settings are the record's, not the tool's: a change the tool makes to the pty termios does not reach the board
- System sets relevant to the template:
  - Default: 115200 8N1, restores the built-in values
  - Monitor: 115200 8N1
  - Arduino upload: 115200 8N1, DTR pulse on open
  - Arduino as ISP: 19200 8N1
  - STM32 bootloader: 115200 8E1
  - ESP upload: 115200 8N1, bootloader entry on open

## Parity

- Every pty on this host refuses `PARENB`: `tcsetattr` with even parity returns EINVAL, on a fresh pty as well as on the bridge pty, so the bridge is not the cause
- A tool that asks the port for even parity fails at open; the wire parity still comes from the record
- stm32flash 0.7 avoids it with `-m 8n1`, and takes the baud with `-b`; its defaults are 57600 and `8e1`
- The alternative is `jupyterlab-device run -- CMD`: the preload shim passes the tool's baud, parity, DTR and RTS to the bridge and keeps them off the pty

## Applied in the template

- The STM32 Rust upload runs `stm32flash` with `-b $(BAUD) -m $(STM32_SERIAL_MODE)`: 8e1 by default, and `STM32_SERIAL_MODE=8n1` in `.env` for the bridge pty
- `.env.example` names a bridge pty as one possible `PORT` and the 8n1 rule for a port that refuses parity
