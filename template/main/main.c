/* Starter firmware of {{ repo_name }} on ESP-IDF.
 *
 * app_main() runs after the scheduler starts, so it creates one task and returns; the task prints
 * the boot line on the UART console. Replace the task with the firmware this project is for.
 */
#include <stdio.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "core.h"

static void boot_task(void *argument)
{
    (void)argument;
    printf("[BOOT] {{ repo_name }}\n");

    uint8_t crc = core_crc8((const uint8_t *)"{{ repo_name }}", sizeof("{{ repo_name }}") - 1);
    for (;;) {
        printf("[CRC] %02X\n", crc);
        crc = core_crc8(&crc, 1);
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

void app_main(void)
{
    xTaskCreate(boot_task, "boot", 2048, NULL, 5, NULL);
}
