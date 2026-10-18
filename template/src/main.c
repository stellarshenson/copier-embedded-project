{% if platform == 'avr' and avr_language == 'c' %}
/* Starter firmware of {{ repo_name }} on bare AVR in C.
 *
 * The starter proves the toolchain, the upload and the serial console: it prints one boot line and
 * keeps the board alive. Replace the loop with the firmware this project is for.
 */
#include <avr/io.h>
#include <util/delay.h>

#include "core.h"

{% if avr_mcu == 'attiny85' %}
/* The ATtiny85 has no UART, so this starter only blinks and exercises the core module. */
int main(void)
{
    DDRB |= (1 << PB1);
    uint8_t crc = core_crc8((const uint8_t *)"{{ repo_name }}", sizeof("{{ repo_name }}") - 1);
    for (;;) {
        PORTB ^= (1 << PB1);
        crc = core_crc8(&crc, 1);
        _delay_ms(500);
    }
}
{% else %}
#define BAUD {{ serial_baud }}UL
#define UBRR_VALUE ((F_CPU / (16UL * BAUD)) - 1)

{% if avr_mcu == 'atmega32u4' %}
/* The ATmega32U4 (Leonardo) routes its console to USART1 and its LED to PC7. */
#define UBRR_H UBRR1H
#define UBRR_L UBRR1L
#define UCSR_B UCSR1B
#define UCSR_C UCSR1C
#define UCSR_A UCSR1A
#define UDR UDR1
#define TX_ENABLE_BIT TXEN1
#define UDRE_BIT UDRE1
#define UCSZ_1 UCSZ11
#define UCSZ_0 UCSZ10
#define LED_DDR DDRC
#define LED_PORT PORTC
#define LED_BIT PC7
{% else %}
/* The ATmega328P and other AVR boards route their console to USART0 and their LED to PB5. */
#define UBRR_H UBRR0H
#define UBRR_L UBRR0L
#define UCSR_B UCSR0B
#define UCSR_C UCSR0C
#define UCSR_A UCSR0A
#define UDR UDR0
#define TX_ENABLE_BIT TXEN0
#define UDRE_BIT UDRE0
#define UCSZ_1 UCSZ01
#define UCSZ_0 UCSZ00
#define LED_DDR DDRB
#define LED_PORT PORTB
#define LED_BIT PB5
{% endif %}

static void uart_init(void)
{
    UBRR_H = (uint8_t)(UBRR_VALUE >> 8);
    UBRR_L = (uint8_t)UBRR_VALUE;
    UCSR_B = (1 << TX_ENABLE_BIT);
    UCSR_C = (1 << UCSZ_1) | (1 << UCSZ_0);
}

static void uart_putc(char c)
{
    while (!(UCSR_A & (1 << UDRE_BIT))) {
    }
    UDR = (uint8_t)c;
}

static void uart_puts(const char *text)
{
    while (*text) {
        uart_putc(*text++);
    }
}

static void uart_puthex(uint8_t value)
{
    static const char digits[] = "0123456789ABCDEF";
    uart_putc(digits[value >> 4]);
    uart_putc(digits[value & 0x0F]);
}

int main(void)
{
    uart_init();
    uart_puts("[BOOT] {{ repo_name }}\r\n");

    LED_DDR |= (1 << LED_BIT);
    uint8_t crc = core_crc8((const uint8_t *)"{{ repo_name }}", sizeof("{{ repo_name }}") - 1);
    for (;;) {
        LED_PORT ^= (1 << LED_BIT);
        uart_puts("[CRC] ");
        uart_puthex(crc);
        uart_puts("\r\n");
        crc = core_crc8(&crc, 1);
        _delay_ms(1000);
    }
}
{% endif %}
{% elif platform == 'esp' and esp_framework == 'esp8266-rtos-sdk' %}
/* Starter firmware of {{ repo_name }} on the ESP8266 RTOS SDK.
 *
 * The SDK calls user_init() after its own startup and the scheduler already runs; the starter
 * creates one task that prints the boot line. Replace the task with the firmware this project is
 * for.
 */
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "espressif/esp_common.h"
#include "espressif/esp_libc.h"

#include "core.h"

/* The SDK reserves the last sectors for RF calibration data and asks the application which sector
 * to use; the answer depends on the flash size of the board. */
uint32_t user_rf_cal_sector_set(void)
{
    uint32_t sector;

    switch (system_get_flash_size_map()) {
    case FLASH_SIZE_4M_MAP_256_256:
        sector = 128 - 5;
        break;
    case FLASH_SIZE_8M_MAP_512_512:
        sector = 256 - 5;
        break;
    case FLASH_SIZE_16M_MAP_512_512:
    case FLASH_SIZE_16M_MAP_1024_1024:
        sector = 512 - 5;
        break;
    case FLASH_SIZE_32M_MAP_512_512:
    case FLASH_SIZE_32M_MAP_1024_1024:
        sector = 1024 - 5;
        break;
    case FLASH_SIZE_64M_MAP_1024_1024:
        sector = 2048 - 5;
        break;
    case FLASH_SIZE_128M_MAP_1024_1024:
        sector = 4096 - 5;
        break;
    default:
        sector = 0;
        break;
    }
    return sector;
}

static void loop_task(void *argument)
{
    (void)argument;
    os_printf("[BOOT] {{ repo_name }}\n");
    uint8_t crc = core_crc8((const uint8_t *)"{{ repo_name }}", sizeof("{{ repo_name }}") - 1);
    for (;;) {
        os_printf("[CRC] %02X\n", crc);
        crc = core_crc8(&crc, 1);
        vTaskDelay(1000 / portTICK_RATE_MS);
    }
}

void user_init(void)
{
    xTaskCreate(loop_task, "loop", 256, NULL, 2, NULL);
}
{% elif platform == 'stm32' and stm32_toolchain == 'platformio' and stm32_framework == 'stm32cube' %}
/* Starter firmware of {{ repo_name }} on STM32Cube with FreeRTOS.
 *
 * FreeRTOS owns SysTick, so the starter groups the NVIC priorities instead of starting the HAL
 * time base, then opens the console UART and creates one CMSIS-RTOS task that prints the boot
 * line. Replace the task with the firmware this project is for.
 */
{% if stm32_board in ['f405rg', 'f411re'] %}
#include "stm32f4xx_hal.h"
{% elif stm32_board == 'f103c8' %}
#include "stm32f1xx_hal.h"
{% else %}
#include "stm32l4xx_hal.h"
{% endif %}
#include "cmsis_os.h"

#include <string.h>

#include "core.h"

static UART_HandleTypeDef console;

static void console_init(void)
{
    GPIO_InitTypeDef gpio = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
{% if stm32_board == 'f103c8' %}
    __HAL_RCC_USART1_CLK_ENABLE();
    gpio.Pin = GPIO_PIN_9;
{% else %}
    __HAL_RCC_USART2_CLK_ENABLE();
    gpio.Pin = GPIO_PIN_2;
    gpio.Alternate = GPIO_AF7_USART2;
{% endif %}
    gpio.Mode = GPIO_MODE_AF_PP;
    gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &gpio);

{% if stm32_board == 'f103c8' %}
    console.Instance = USART1;
{% else %}
    console.Instance = USART2;
{% endif %}
    console.Init.BaudRate = {{ serial_baud }};
    console.Init.WordLength = UART_WORDLENGTH_8B;
    console.Init.StopBits = UART_STOPBITS_1;
    console.Init.Parity = UART_PARITY_NONE;
    console.Init.Mode = UART_MODE_TX;
    console.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    console.Init.OverSampling = UART_OVERSAMPLING_16;
    HAL_UART_Init(&console);
}

static void boot_print(const char *text)
{
    HAL_UART_Transmit(&console, (uint8_t *)text, (uint16_t)strlen(text), HAL_MAX_DELAY);
}

static void boot_task(void const *argument)
{
    (void)argument;
    boot_print("[BOOT] {{ repo_name }}\r\n");
    uint8_t crc = core_crc8((const uint8_t *)"{{ repo_name }}", sizeof("{{ repo_name }}") - 1);
    for (;;) {
        crc = core_crc8(&crc, 1);
        osDelay(1000);
    }
}

int main(void)
{
    /* FreeRTOS owns SysTick, and a HAL time base would claim it before the scheduler starts.
     * The starter keeps the reset clock (HSI, no flash wait states) and groups the NVIC
     * priorities as FreeRTOS expects; the HAL still drives the console. */
    HAL_NVIC_SetPriorityGrouping(NVIC_PRIORITYGROUP_4);
    console_init();

    osThreadDef(boot, boot_task, osPriorityNormal, 0, 256);
    osThreadCreate(osThread(boot), NULL);
    osKernelStart();

    for (;;) {
    }
}
{% else %}
/* This adapter belongs to another scaffold; post_gen removes the file. */
{% endif %}
