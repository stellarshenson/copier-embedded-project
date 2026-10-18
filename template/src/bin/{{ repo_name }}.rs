{% if platform == 'avr' and avr_language == 'rust' %}
//! Starter firmware of {{ repo_name }} on bare AVR in Rust.
//!
//! The starter prints one boot line on the UART and keeps the board alive. Replace the loop with
//! the firmware this project is for.

#![no_std]
#![no_main]

use panic_halt as _;

use {{ crate_name }}::crc8;

{% if avr_mcu == 'attiny85' %}
#[no_mangle]
pub extern "C" fn main() -> ! {
    let mut crc = crc8(b"{{ repo_name }}");
    loop {
        crc = crc8(&[crc]);
        core::hint::spin_loop();
    }
}
{% else %}
const BAUD: u32 = {{ serial_baud }};

{% if avr_mcu == 'atmega32u4' %}
// USART1 of the ATmega32U4.
const UBRR_H: *mut u8 = 0xCD as *mut u8;
const UBRR_L: *mut u8 = 0xCC as *mut u8;
const UCSR_A: *const u8 = 0xC8 as *const u8;
const UCSR_B: *mut u8 = 0xC9 as *mut u8;
const UCSR_C: *mut u8 = 0xCA as *mut u8;
const UDR: *mut u8 = 0xCE as *mut u8;
{% else %}
// USART0 of the ATmega328P and of the other AVR boards.
const UBRR_H: *mut u8 = 0xC5 as *mut u8;
const UBRR_L: *mut u8 = 0xC4 as *mut u8;
const UCSR_A: *const u8 = 0xC0 as *const u8;
const UCSR_B: *mut u8 = 0xC1 as *mut u8;
const UCSR_C: *mut u8 = 0xC2 as *mut u8;
const UDR: *mut u8 = 0xC6 as *mut u8;
{% endif %}

const UBRR: u16 = (({{ avr_clock }}u32 / (16 * BAUD)) - 1) as u16;

unsafe fn uart_init() {
    core::ptr::write_volatile(UBRR_H, (UBRR >> 8) as u8);
    core::ptr::write_volatile(UBRR_L, UBRR as u8);
    core::ptr::write_volatile(UCSR_B, 1 << 3);
    core::ptr::write_volatile(UCSR_C, (1 << 2) | (1 << 1));
}

unsafe fn uart_putc(byte: u8) {
    while core::ptr::read_volatile(UCSR_A) & (1 << 5) == 0 {}
    core::ptr::write_volatile(UDR, byte);
}

unsafe fn uart_puts(text: &[u8]) {
    for &byte in text {
        uart_putc(byte);
    }
}

#[no_mangle]
pub extern "C" fn main() -> ! {
    unsafe {
        uart_init();
        uart_puts(b"[BOOT] {{ repo_name }}\r\n");
    }

    let mut crc = crc8(b"{{ repo_name }}");
    loop {
        crc = crc8(&[crc]);
        core::hint::spin_loop();
    }
}
{% endif %}
{% elif platform == 'stm32' and stm32_toolchain == 'rust' %}
//! Starter firmware of {{ repo_name }} on STM32 in Rust.
//!
//! The starter prints one boot line on the console UART and keeps the board alive. Replace the
//! loop with the firmware this project is for.

#![no_std]
#![no_main]

use panic_halt as _;

use {{ crate_name }}::crc8;

const BAUD: u32 = {{ serial_baud }};

{% if stm32_board == 'f103c8' %}
// USART1 on PA9, clocked from APB2. The F103 has HSI at 8 MHz after reset.
const RCC_APB2ENR: *mut u32 = 0x4002_1018 as *mut u32;
const GPIOA_CRH: *mut u32 = 0x4001_0804 as *mut u32;
const USART_SR: *const u32 = 0x4001_3800 as *const u32;
const USART_DR: *mut u32 = 0x4001_3804 as *mut u32;
const USART_BRR: *mut u32 = 0x4001_3808 as *mut u32;
const USART_CR1: *mut u32 = 0x4001_380C as *mut u32;
const PCLK: u32 = 8_000_000;
{% elif stm32_board == 'l476rg' %}
// USART2 on PA2 and PA3, clocked from APB1. The L4 has HSI at 16 MHz after reset.
const RCC_AHB2ENR: *mut u32 = 0x4002_104C as *mut u32;
const RCC_APB1ENR1: *mut u32 = 0x4002_1058 as *mut u32;
const GPIOA_MODER: *mut u32 = 0x4800_0000 as *mut u32;
const GPIOA_AFRL: *mut u32 = 0x4800_0020 as *mut u32;
const USART_ISR: *const u32 = 0x4000_441C as *const u32;
const USART_TDR: *mut u32 = 0x4000_4428 as *mut u32;
const USART_BRR: *mut u32 = 0x4000_4408 as *mut u32;
const USART_CR1: *mut u32 = 0x4000_440C as *mut u32;
const PCLK: u32 = 16_000_000;
{% else %}
// USART2 on PA2 and PA3, clocked from APB1. The F4 has HSI at 16 MHz after reset.
const RCC_AHB1ENR: *mut u32 = 0x4002_3830 as *mut u32;
const RCC_APB1ENR: *mut u32 = 0x4002_3840 as *mut u32;
const GPIOA_MODER: *mut u32 = 0x4002_0000 as *mut u32;
const GPIOA_AFRL: *mut u32 = 0x4002_0020 as *mut u32;
const USART_SR: *const u32 = 0x4000_4400 as *const u32;
const USART_DR: *mut u32 = 0x4000_4404 as *mut u32;
const USART_BRR: *mut u32 = 0x4000_4408 as *mut u32;
const USART_CR1: *mut u32 = 0x4000_440C as *mut u32;
const PCLK: u32 = 16_000_000;
{% endif %}

unsafe fn console_init() {
{% if stm32_board == 'f103c8' %}
    let apb2 = core::ptr::read_volatile(RCC_APB2ENR);
    core::ptr::write_volatile(RCC_APB2ENR, apb2 | (1 << 2) | (1 << 14));
    let crh = core::ptr::read_volatile(GPIOA_CRH);
    core::ptr::write_volatile(GPIOA_CRH, (crh & !(0xF << 4) & !(0xF << 8)) | (0xB << 4) | (0x4 << 8));
{% elif stm32_board == 'l476rg' %}
    let ahb2 = core::ptr::read_volatile(RCC_AHB2ENR);
    core::ptr::write_volatile(RCC_AHB2ENR, ahb2 | (1 << 0));
    let apb1 = core::ptr::read_volatile(RCC_APB1ENR1);
    core::ptr::write_volatile(RCC_APB1ENR1, apb1 | (1 << 17));
    let moder = core::ptr::read_volatile(GPIOA_MODER);
    core::ptr::write_volatile(GPIOA_MODER, (moder & !(0x3 << 4) & !(0x3 << 6)) | (0x2 << 4) | (0x2 << 6));
    let afrl = core::ptr::read_volatile(GPIOA_AFRL);
    core::ptr::write_volatile(GPIOA_AFRL, (afrl & !(0xF << 8) & !(0xF << 12)) | (0x7 << 8) | (0x7 << 12));
{% else %}
    let ahb1 = core::ptr::read_volatile(RCC_AHB1ENR);
    core::ptr::write_volatile(RCC_AHB1ENR, ahb1 | (1 << 0));
    let apb1 = core::ptr::read_volatile(RCC_APB1ENR);
    core::ptr::write_volatile(RCC_APB1ENR, apb1 | (1 << 17));
    let moder = core::ptr::read_volatile(GPIOA_MODER);
    core::ptr::write_volatile(GPIOA_MODER, (moder & !(0x3 << 4) & !(0x3 << 6)) | (0x2 << 4) | (0x2 << 6));
    let afrl = core::ptr::read_volatile(GPIOA_AFRL);
    core::ptr::write_volatile(GPIOA_AFRL, (afrl & !(0xF << 8) & !(0xF << 12)) | (0x7 << 8) | (0x7 << 12));
{% endif %}
    core::ptr::write_volatile(USART_BRR, (PCLK + BAUD / 2) / BAUD);
{% if stm32_board == 'l476rg' %}
    core::ptr::write_volatile(USART_CR1, (1 << 0) | (1 << 3));
{% else %}
    core::ptr::write_volatile(USART_CR1, (1 << 13) | (1 << 3));
{% endif %}
}

unsafe fn console_putc(byte: u8) {
{% if stm32_board == 'l476rg' %}
    while core::ptr::read_volatile(USART_ISR) & (1 << 7) == 0 {}
    core::ptr::write_volatile(USART_TDR, byte as u32);
{% else %}
    while core::ptr::read_volatile(USART_SR) & (1 << 7) == 0 {}
    core::ptr::write_volatile(USART_DR, byte as u32);
{% endif %}
}

unsafe fn console_puts(text: &[u8]) {
    for &byte in text {
        console_putc(byte);
    }
}

#[cortex_m_rt::entry]
fn main() -> ! {
    unsafe {
        console_init();
        console_puts(b"[BOOT] {{ repo_name }}\r\n");
    }

    let mut crc = crc8(b"{{ repo_name }}");
    loop {
        crc = crc8(&[crc]);
        cortex_m::asm::wfi();
    }
}
{% else %}
// This adapter belongs to another scaffold; post_gen removes the file.
{% endif %}
