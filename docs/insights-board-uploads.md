# Board upload notes

Board-specific behaviour seen while testing the device bridge with real boards, and what a generated project should carry.

## ESP32 with native USB (C3, S3, C6)

- The USB Serial/JTAG peripheral (303a:1001) ignores the DTR/RTS reset esptool performs by default; an upload started that way fails with `No serial data received`
- Working form on the bridge: the port's on-open action enters the bootloader and esptool runs with no reset (`--before=no_reset`); with the shim, esptool's own reset reaches the browser and the write verifies
- PlatformIO's bundled esptool 4.11 spells the value with an underscore (`no_reset`); standalone esptool 5.6 spells it with a hyphen (`no-reset`)
- In `platformio.ini` give each flag its own line: `upload_flags = --before=no_reset --after=watchdog_reset` on one line reaches esptool as a single argument and is rejected
- ESP-IDF puts the console on UART0 by default; a board whose only bridged port is USB Serial/JTAG needs `CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=y` in `sdkconfig.defaults`
- The no-reset upload was proven on an ESP32-C3 and its output observed after a power cycle: three images written, each hash verified, and the monitor read `DEVICE-BRIDGE BOARD TEST boot=1` to `39` (ACC-BOARD-186 closed)
- After a verified upload the C3 can stay in ROM download (`boot:0x4 (DOWNLOAD(USB/UART0/1))`, `waiting for download`)
- The USB-JTAG maps DTR to the IO0 boot strap
- The post-upload reset did not leave download in the observed run, so a replug or the RESET button is the reliable step before reading the monitor
- The USB Serial/JTAG peripheral exists on the C3, S3, C6 and P4 only
- A classic ESP32 board with a CP210x or CH340 does not follow this recipe
- A stale `.pio/build` after a framework change fails with `Multiple ways to build the same target`; `pio run -t clean` fixes it. The first ESP-IDF build downloads ESP-IDF Python tooling (esp-idf-kconfig, esp-pylib, idf-component-manager) and needs network

## STM32 serial bootloader

- The ROM bootloader speaks 8E1 and autobauds on the sync byte; stm32flash 0.7 defaults to 57600 8E1
- On the bridge the parity comes from the STM32 bootloader set (115200 8E1); run stm32flash with `-b 115200 -m 8n1`
- A Nucleo-L152RE does not enter the bootloader through its ST-Link VCP even with BOOT0 high
- The VCP is wired to USART2 PA2/PA3, while the STM32L1 bootloader uses USART2 on the remapped PD5/PD6 (absent on the 64-pin package) or USART1 PA9/PA10
- stm32flash ends `Failed to init device, timeout`
- A USB-UART adapter on PA9/PA10 is required
- The criterion was rejected for this reason
- BOOT0 on a Nucleo-64 is not a jumper
- CN7 pin 5 is VDD and pin 7 is BOOT0
- A shunt across pins 5 and 7 sets BOOT0 high
- Spare shunts sit on CN11/CN12 on the bottom side
- Pin 1 is the square pad at the USB end

## Arduino

- The Nano question maps the old bootloader to `nanoatmega328` and the new one to `nanoatmega328new`; PlatformIO's board definitions carry the matching upload speed, 57600 and 115200
- The Arduino upload set is 115200 8N1 with a DTR pulse on open; an Uno and a Mega use it unchanged
- Not yet exercised on hardware in this project; ACC-BOARD-98 and ACC-BOARD-99 cover it
