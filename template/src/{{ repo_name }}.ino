/* Starter sketch of {{ repo_name }}.
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
