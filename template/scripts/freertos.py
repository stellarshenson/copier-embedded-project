"""Compile the FreeRTOS kernel and CMSIS-RTOS wrapper that ship inside the STM32Cube framework.

PlatformIO's stm32cube builder adds the HAL and CMSIS; it does not compile the FreeRTOS middleware
under Middlewares/Third_Party. This pre-script adds the include paths and the kernel, port, heap and
CMSIS-RTOS sources of the framework package that the project already pins.
"""

Import("env")

import os
from pathlib import Path

platform = env.PioPlatform()
board = env.BoardConfig()
mcu = board.get("build.mcu", "")
package = platform.get_package_dir(f"framework-stm32cube{mcu[5:7].lower()}")
source = Path(package) / "Middlewares" / "Third_Party" / "FreeRTOS" / "Source"
if not source.is_dir():
    raise SystemExit(f"FreeRTOS middleware not found in {package}")

cpu = board.get("build.cpu", "")
ports = {
    "cortex-m0": "ARM_CM0",
    "cortex-m0plus": "ARM_CM0",
    "cortex-m3": "ARM_CM3",
    "cortex-m4": "ARM_CM4F",
    "cortex-m7": "ARM_CM7/r0p1",
}
port = ports.get(cpu)
if port is None:
    raise SystemExit(f"no FreeRTOS port for {cpu}")
port_dir = source / "portable" / "GCC" / port
if not port_dir.is_dir():
    raise SystemExit(f"no FreeRTOS port directory {port_dir}")

# The M4 cores of the supported boards carry an FPU; the board files do not set the float ABI,
# so the script sets it for the compile and the link, or the FPU context switch fails to link.
fpu_flags = ["-mfpu=fpv4-sp-d16", "-mfloat-abi=hard"] if cpu == "cortex-m4" else []
env.Append(CCFLAGS=fpu_flags, LINKFLAGS=fpu_flags)
env.Append(
    CPPPATH=[
        os.path.join("$PROJECT_DIR", "src"),
        str(source / "include"),
        str(source / "CMSIS_RTOS"),
        str(port_dir),
    ]
)
kernel = ["tasks.c", "queue.c", "list.c", "timers.c", "event_groups.c", "stream_buffer.c", "croutine.c"]
env.BuildSources(
    os.path.join("$BUILD_DIR", "freertos"),
    str(source),
    " ".join(f"+<{name}>" for name in kernel),
)
env.BuildSources(os.path.join("$BUILD_DIR", "freertos_port"), str(port_dir), "+<port.c>")
env.BuildSources(
    os.path.join("$BUILD_DIR", "freertos_heap"), str(source / "portable" / "MemMang"), "+<heap_4.c>"
)
env.BuildSources(os.path.join("$BUILD_DIR", "freertos_cmsis"), str(source / "CMSIS_RTOS"), "+<cmsis_os.c>")
