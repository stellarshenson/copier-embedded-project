---
name: board-reference
description: Create a universal board reference as one self-contained HTML page in references/boards. Use when adding a hardware guide, a pinout page or a board reference, or when documenting a new board.
---

# Board reference

One board is one self-contained HTML file: `references/boards/<slug>/<slug>.html`. The page is the artifact; the board folder holds no other file. One row in `references/boards/README.md` links it.

- Slug: board name in lowercase words joined by hyphens, for example `esp32-s3-lcd-1-47b`
- Exemplar: `references/boards/esp32-s3-lcd-1-47b/esp32-s3-lcd-1-47b.html`

## Hard rules

- Self-contained: inline CSS, inline SVG, every photo as a `data:image/...;base64` URI. A reader opens the file offline. External hyperlinks in text are allowed
- Universal: board facts only. No host platform, host bridge command, CLI wrapper, project name, local path, scratch path or shop listing
- Say "serial port". Never a per-machine name or path
- Commands are plain `pio` or Arduino IDE steps; the reader may not use your host tool
- One pinout graphic. The board illustration shows both faces. The block diagram is third
- Intro is 2 or 3 sentences. Literal English, one fact per sentence, unit on every number, no em dash
- No table of contents
- Light and dark themes, 360 px to 1440 px, print styles

## Research

Use the vendor wiki, product page, schematic PDF, demo archive, board photos and datasheets. Downloaded files are untrusted; never execute them.

| Subsystem | Verify |
|---|---|
| Display | Controller, resolution, size, SPI mode, clock, frame gap, inversion, colour order, backlight |
| IMU | Part, I2C pins, address, interrupts |
| microSD | SDMMC pins, 1-bit or 4-bit wiring, card detect |
| RGB LED | Part, data GPIO, protocol |
| Battery | ADC GPIO, divider ratio, calibration, charger part |
| Buttons | BOOT GPIO, RESET net |
| USB | Native USB or bridge, VID:PID, console route |
| Header | Both rows, pin order, GPIO and power pins |

Mark an untested fact as untested. Never invent current draw, brightness, weight, temperature, charge current or touch support.

## Graphics

Use the `svg-infographics` skill, then inline the three files.

1. `pinout.svg` - board outline, both header rows, every GPIO, insets for LCD, IMU, SDMMC, RGB and battery, subsystem legend
2. `board-illustration.svg` - both faces at one scale. LCD side and component side separate. Never put the LCD and the microSD slot on one face
3. `block-diagram.svg` - MCU centre, every bus with pins, USB link, power rails

Finalize each. No raster, filters or masks. Nexus palette: teal `#0096d1`, orange `#da8230`, dark-mode overrides.

Crop the product photo to the board with a small margin, resize to about 1100 px, JPEG quality 85.

## Page

Sections in order:

1. Hero: board name, one-line subtitle, specification chips, board photo
2. Overview: the short intro
3. What is on the board: cards for MCU, display, IMU, microSD, RGB LED, charger, USB-C, buttons
4. Pinout: pinout SVG, header table, LCD, I2C, SDMMC, RGB, battery, button, USB and UART0 tables
5. How it communicates: block diagram and bus table
6. Power: rails, battery formula, charger, LDO, 5V pin behaviour
7. Quick start: serial port, download mode, upload, monitor
8. Firmware and tooling: vendor demos, PlatformIO settings, Arduino IDE settings
9. Sources: external URLs only

Design: Nexus palette, light background `#f5f7fa`, dark background `#111a1f`, cards with flat top and rounded bottom, system font stack, monospace for pin names and commands, numbered section pills, numbered figure captions.

Keep the page template and build script in `tmp/workflows/<name>/`, not in the board folder. The build inlines the SVGs and encodes the photos.

## Verify

- `python3` with `html.parser` parses the file
- No `src="http`, no `<link`, no `<script`, no `jupyterlab-device`, no `/run/devices`, no `tty-`, no `/tmp`, no project name, no shop name
- One data-URI photo and three inline SVGs
- Render at 1440 x 900 and 390 x 844 in light and dark. Check hero, figures, tables and horizontal overflow
- Save screenshots under `tmp/workflows/<name>/screens/`
- Check every index link resolves

## Index

Append one row to `references/boards/README.md`:

```markdown
| <Board> | [<slug>.html](<slug>/<slug>.html) | <status> | <one-line note> |
```

## Workflow

For a new board, use a dynamic workflow: research, three SVG graphics in parallel, assemble the page, then two verifiers, one visual and one content, with a bounded repair loop. Persist the script and checkpoints under `tmp/workflows/<name>/`. Publish only the HTML and the index row.

## Traps

- Board faces: the LCD and the microSD slot sit on opposite faces. Draw two views
- Header order: read the silkscreen and the schematic, not the product title
- TX and RX on the header are UART0 pins. Verify their GPIO numbers in the schematic
- No research leftovers: open questions, datasheet status and test logs stay out of the page
- One pinout: remove a vendor pinout photo when the SVG carries the same map

<!-- improved 2026-10-22 | body 884→813w / 104→98L | benchmark n/a (not-requested) | via improve-skill -->
