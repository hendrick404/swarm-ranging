#ifndef UTIL_H
#define UTIL_H

#include <stdint.h>

#include "typedefs.h"

timestamp_t message_read_timestamp(uint8_t* buffer);

void message_write_timestamp(uint8_t* buffer, timestamp_t ts);

#endif
