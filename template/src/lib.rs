//! Pure logic of the firmware: no peripheral, no HAL, so the host tests exercise the same source.
//!
//! The adapter in `src/bin/` calls this crate; `test/host/core.rs` covers it on the host.

#![cfg_attr(not(test), no_std)]

/// CRC-8 of a byte buffer, polynomial 0x07, initial value 0x00.
pub fn crc8(data: &[u8]) -> u8 {
    let mut crc = 0x00u8;
    for byte in data {
        crc ^= *byte;
        for _ in 0..8 {
            crc = if crc & 0x80 != 0 { (crc << 1) ^ 0x07 } else { crc << 1 };
        }
    }
    crc
}

/// A fixed-capacity byte ring over caller-owned storage.
pub struct Ring<'a> {
    data: &'a mut [u8],
    head: usize,
    count: usize,
}

impl<'a> Ring<'a> {
    pub fn new(data: &'a mut [u8]) -> Self {
        Ring { data, head: 0, count: 0 }
    }

    /// Append one byte; returns false when the ring is full and the byte is dropped.
    pub fn push(&mut self, value: u8) -> bool {
        if self.count == self.data.len() {
            return false;
        }
        let index = (self.head + self.count) % self.data.len();
        self.data[index] = value;
        self.count += 1;
        true
    }

    /// Remove the oldest byte; returns None when the ring is empty.
    pub fn pop(&mut self) -> Option<u8> {
        if self.count == 0 {
            return None;
        }
        let value = self.data[self.head];
        self.head = (self.head + 1) % self.data.len();
        self.count -= 1;
        Some(value)
    }

    pub fn len(&self) -> usize {
        self.count
    }

    pub fn is_empty(&self) -> bool {
        self.count == 0
    }
}

#[cfg(test)]
mod tests {
    use super::{crc8, Ring};

    #[test]
    fn crc8_of_the_check_string_is_f4() {
        assert_eq!(crc8(b"123456789"), 0xF4);
    }

    #[test]
    fn crc8_of_an_empty_buffer_is_zero() {
        assert_eq!(crc8(b""), 0x00);
    }

    #[test]
    fn ring_keeps_order_and_drops_when_full() {
        let mut storage = [0u8; 3];
        let mut ring = Ring::new(&mut storage);
        assert!(ring.push(1) && ring.push(2) && ring.push(3));
        assert!(!ring.push(4));
        assert_eq!(ring.len(), 3);
        assert_eq!(ring.pop(), Some(1));
        assert_eq!(ring.pop(), Some(2));
        assert_eq!(ring.pop(), Some(3));
        assert_eq!(ring.pop(), None);
        assert!(ring.is_empty());
    }
}
