/* Thin C API over libsimavr for the AVR simulator tests.
 *
 * Build with `make sim`: the Makefile compiles this file against PlatformIO's tool-simavr.
 * The API is intentionally small: one powered AVR, run for microseconds, read the UART text.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <avr_uart.h>
#include <sim_avr.h>
#include <sim_elf.h>
#include <sim_io.h>
#include <sim_time.h>

#define UART_OUTPUT_SIZE 8192

typedef struct {
    avr_t *avr;
    char output[UART_OUTPUT_SIZE];
    size_t output_length;
} sim_t;

static void on_uart_output(struct avr_irq_t *irq, uint32_t value, void *param)
{
    sim_t *sim = (sim_t *)param;
    (void)irq;
    if (sim->output_length < UART_OUTPUT_SIZE - 1) {
        sim->output[sim->output_length++] = (char)value;
        sim->output[sim->output_length] = '\0';
    }
}

sim_t *sim_new(const char *elf_path, uint32_t frequency)
{
    elf_firmware_t firmware;
    memset(&firmware, 0, sizeof(firmware));
    if (elf_read_firmware(elf_path, &firmware)) {
        return NULL;
    }
    const char *mcu = firmware.mmcu[0] ? firmware.mmcu : "atmega328p";
    avr_t *avr = avr_make_mcu_by_name(mcu);
    if (avr == NULL) {
        return NULL;
    }
    sim_t *sim = calloc(1, sizeof(sim_t));
    if (sim == NULL) {
        return NULL;
    }
    sim->avr = avr;
    avr_init(avr);
    avr->frequency = frequency ? frequency : (firmware.frequency ? firmware.frequency : 16000000);
    avr->vcc = avr->avcc = avr->aref = 5000;
    avr_load_firmware(avr, &firmware);
    avr_irq_register_notify(
        avr_io_getirq(avr, AVR_IOCTL_UART_GETIRQ('0'), UART_IRQ_OUTPUT),
        on_uart_output, sim);
    return sim;
}

int sim_run_us(sim_t *sim, uint64_t usec)
{
    avr_cycle_count_t target = sim->avr->cycle + avr_usec_to_cycles(sim->avr, usec);
    int state = cpu_Running;
    while (sim->avr->cycle < target) {
        state = avr_run(sim->avr);
        if (state == cpu_Done || state == cpu_Crashed) {
            break;
        }
    }
    return state;
}

const char *sim_uart_text(sim_t *sim)
{
    return sim->output;
}

void sim_free(sim_t *sim)
{
    if (sim != NULL) {
        avr_terminate(sim->avr);
        free(sim->avr);
        free(sim);
    }
}
