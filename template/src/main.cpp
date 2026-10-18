{% if platform == 'avr' and avr_language == 'cpp' %}
/* Starter firmware of {{ repo_name }} on bare AVR in C++.
 *
 * The starter proves the toolchain, the upload and the serial console: it prints one boot line and
 * keeps the board alive. Replace the loop with the firmware this project is for.
 */
#include <avr/io.h>
#include <util/delay.h>

#include "core.h"

{% if avr_mcu == 'attiny85' %}
/* The ATtiny85 has no UART, so this starter only blinks and exercises the core module. */
int main()
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

static void uart_init()
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

int main()
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
{% elif platform == 'esp' or (platform == 'stm32' and stm32_toolchain == 'platformio' and stm32_framework == 'arduino') %}
/* Starter firmware of {{ repo_name }} on the Arduino framework.
 *
 * setup() prints one boot line; loop() exercises the core module and the onboard LED. Replace both
 * with the firmware this project is for.
 */
#include <Arduino.h>

#include "core.h"

void setup()
{
    Serial.begin({{ serial_baud }});
    Serial.println("[BOOT] {{ repo_name }}");
#ifdef LED_BUILTIN
    pinMode(LED_BUILTIN, OUTPUT);
#endif
}

void loop()
{
    static uint8_t crc = core_crc8((const uint8_t *)"{{ repo_name }}", sizeof("{{ repo_name }}") - 1);
    Serial.print("[CRC] ");
    Serial.println(crc, HEX);
    crc = core_crc8(&crc, 1);
#ifdef LED_BUILTIN
    digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
#endif
    delay(1000);
}
{% else %}
/* This adapter belongs to another scaffold; post_gen removes the file. */
{% endif %}
