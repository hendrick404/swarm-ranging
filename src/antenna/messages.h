#ifndef MESSAGES_H
#define MESSAGES_H

#include <stdint.h>

#include "typedefs.h"

// If we are not using the Zephyr build system (e.g. for unit tests)
#ifndef CONFIG_PAN_ID
#define CONFIG_PAN_ID 0xDECA
#endif

timestamp_t message_read_timestamp(uint8_t* buffer);

void message_write_timestamp(uint8_t* buffer, timestamp_t ts);

rx_range_info_t analyse_message(uint8_t* message_buffer, size_t message_buffer_len, timestamp_t rx_time);

size_t construct_message(uint8_t* message_buffer, size_t message_buffer_size, received_message_t* received_messages, size_t received_messages_len, self_t self, timestamp_t tx_timestamp);

#endif
