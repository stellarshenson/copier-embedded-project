/* Host tests of lib/core/core.c: no board, no toolchain beyond the host C compiler. */
#include <stdio.h>

#include "core.h"

static int failures = 0;

static void check(int condition, const char *name)
{
    if (!condition) {
        failures++;
        printf("FAIL %s\n", name);
    }
}

int main(void)
{
    const uint8_t text[] = "123456789";

    check(core_crc8(text, 9) == 0xF4, "crc8 of 123456789 is 0xF4");
    check(core_crc8(text, 0) == 0x00, "crc8 of an empty buffer is 0x00");

    uint8_t storage[4];
    core_ring ring;
    core_ring_init(&ring, storage, sizeof(storage));
    check(core_ring_count(&ring) == 0, "a new ring is empty");
    check(core_ring_push(&ring, 0x11) == 1, "push into an empty ring");
    check(core_ring_push(&ring, 0x22) == 1, "push a second byte");
    uint8_t value = 0;
    check(core_ring_pop(&ring, &value) == 1 && value == 0x11, "pop the oldest byte");
    check(core_ring_push(&ring, 0x33) == 1, "push after pop");
    check(core_ring_push(&ring, 0x44) == 1, "push to three bytes");
    check(core_ring_push(&ring, 0x55) == 1, "push to four bytes");
    check(core_ring_push(&ring, 0x66) == 0, "a full ring refuses a byte");
    check(core_ring_count(&ring) == 4, "four bytes remain");
    check(core_ring_pop(&ring, &value) == 1 && value == 0x22,
          "the ring keeps its order after a wrap");

    if (failures == 0) {
        printf("host tests passed\n");
        return 0;
    }
    printf("%d host test(s) failed\n", failures);
    return 1;
}
