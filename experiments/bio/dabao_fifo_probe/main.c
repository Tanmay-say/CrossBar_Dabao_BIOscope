#include <stdint.h>
#include "bio.h"

/*
 * Physical-target probe: emit a single documented FIFO0 word, then wait.
 * This does not touch BIO GPIO or external pins. The value is captured through
 * dabao-console's documented `bio rx` command after the BIO loader is approved.
 */
void main(void) {
    push_fifo0(0xB105C0DEu);
    for (;;) {
        wait_quantum();
    }
}
