//! Host tests of `src/lib.rs`: the shared core, compiled for the machine that runs the tests.

use {{ repo_name | replace('-', '_') }}::{crc8, Ring};

#[test]
fn crc8_of_the_check_string_is_f4() {
    assert_eq!(crc8(b"123456789"), 0xF4);
}

#[test]
fn crc8_of_an_empty_buffer_is_zero() {
    assert_eq!(crc8(b""), 0x00);
}

#[test]
fn a_new_ring_is_empty() {
    let mut storage = [0u8; 4];
    let ring = Ring::new(&mut storage);

    assert_eq!(ring.len(), 0);
}

#[test]
fn a_ring_keeps_its_order_after_a_wrap() {
    let mut storage = [0u8; 4];
    let mut ring = Ring::new(&mut storage);
    assert!(ring.push(0x11));
    assert!(ring.push(0x22));
    assert_eq!(ring.pop(), Some(0x11));
    assert!(ring.push(0x33));
    assert!(ring.push(0x44));
    assert!(ring.push(0x55));
    assert!(!ring.push(0x66), "a full ring refuses a byte");
    assert_eq!(ring.len(), 4);
    assert_eq!(ring.pop(), Some(0x22));
}
