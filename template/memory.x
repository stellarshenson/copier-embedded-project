/* Memory of {{ stm32_board }}: the flash and RAM the linker gives the firmware. */
MEMORY
{
  FLASH : ORIGIN = 0x08000000, LENGTH = {{ flash_kb }}K
  RAM : ORIGIN = 0x20000000, LENGTH = {{ ram_kb }}K
}
