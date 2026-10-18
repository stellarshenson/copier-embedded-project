#include "core.h"

uint8_t core_crc8(const uint8_t *data, size_t length)
{
    uint8_t crc = 0x00;
    for (size_t i = 0; i < length; i++) {
        crc ^= data[i];
        for (uint8_t bit = 0; bit < 8; bit++) {
            crc = (crc & 0x80u) ? (uint8_t)((crc << 1) ^ 0x07u) : (uint8_t)(crc << 1);
        }
    }
    return crc;
}

void core_ring_init(core_ring *ring, uint8_t *storage, size_t capacity)
{
    ring->data = storage;
    ring->capacity = capacity;
    ring->head = 0;
    ring->count = 0;
}

int core_ring_push(core_ring *ring, uint8_t value)
{
    if (ring->count == ring->capacity) {
        return 0;
    }
    ring->data[(ring->head + ring->count) % ring->capacity] = value;
    ring->count++;
    return 1;
}

int core_ring_pop(core_ring *ring, uint8_t *value)
{
    if (ring->count == 0) {
        return 0;
    }
    *value = ring->data[ring->head];
    ring->head = (ring->head + 1) % ring->capacity;
    ring->count--;
    return 1;
}

size_t core_ring_count(const core_ring *ring)
{
    return ring->count;
}
