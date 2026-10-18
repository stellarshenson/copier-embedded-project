/* Pure logic of the firmware: no hardware register, no Arduino, no HAL.
 * It compiles for every target and for the host, so the host tests exercise the same source. */
#ifndef CORE_H
#define CORE_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/** CRC-8 of a byte buffer, polynomial 0x07, initial value 0x00. */
uint8_t core_crc8(const uint8_t *data, size_t length);

/** A fixed-capacity byte ring; the caller owns the storage. */
typedef struct {
    uint8_t *data;
    size_t capacity;
    size_t head;
    size_t count;
} core_ring;

void core_ring_init(core_ring *ring, uint8_t *storage, size_t capacity);

/** Append one byte; returns 0 when the ring is full and the byte is dropped. */
int core_ring_push(core_ring *ring, uint8_t value);

/** Remove the oldest byte; returns 0 when the ring is empty. */
int core_ring_pop(core_ring *ring, uint8_t *value);

size_t core_ring_count(const core_ring *ring);

#ifdef __cplusplus
}
#endif

#endif /* CORE_H */
