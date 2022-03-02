#include <stdint.h>

#include "typedefs.h"

timestamp_t message_read_timestamp(uint8_t* buffer) {
    timestamp_t result = 0;
    for (int i = 0; i < 8; i++) {
        result <<= 8;
        result |= buffer[i];
    }
    return result;
}

void message_write_timestamp(uint8_t* buffer, timestamp_t ts) {
    for (int i = 0; i < 8; i++) {
        buffer[i] = (ts >> (8 * (7 - i))) & 0xFF;
    }
}