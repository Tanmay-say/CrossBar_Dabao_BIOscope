#include <stdint.h>
#include "bio.h" // BIO-sim ABI header must be first

// Xous v0.10.1-43-g8964027ff configures this program with `bio clk 7000`.
// BIO quantum frequency is therefore 7 kHz (350 MHz / integer divider 50000).
// 3500 quantum waits produce a 0.5 s half-period, approximately 1 Hz total.
#define BIO_PIN 1
#define HALF_PERIOD_QUANTA 3500u
#define RISING_EDGES 10u

static void wait_quanta(uint32_t count) {
    while (count != 0u) {
        wait_quantum();
        --count;
    }
}

void main(void) {
    const uint32_t pin_mask = 1u << BIO_PIN;
    set_gpio_mask(pin_mask);
    set_output_pins(pin_mask);
    clear_gpio_pins_n(~pin_mask); // establish safe LOW before starting

    for (uint32_t edge = 0; edge < RISING_EDGES; ++edge) {
        set_gpio_pins(pin_mask);
        wait_quanta(HALF_PERIOD_QUANTA);
        clear_gpio_pins_n(~pin_mask);
        wait_quanta(HALF_PERIOD_QUANTA);
    }

    // The 10th pulse has returned LOW; remain there indefinitely.
    for (;;) wait_quantum();
}
