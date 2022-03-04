#include <stdint.h>

#include "message_definition.h"
#include "messages.h"
#include "typedefs.h"

timestamp_t message_read_timestamp(uint8_t* buffer) {
    timestamp_t result = 0;
    for (int i = 0; i < TIMESTAMP_SIZE; i++) {
        result <<= 8;
        result |= buffer[i];
    }
    return result;
}

void message_write_timestamp(uint8_t* buffer, timestamp_t ts) {
    for (int i = 0; i < TIMESTAMP_SIZE; i++) {
        buffer[i] = (ts >> (8 * (TIMESTAMP_SIZE - 1 - i))) & 0xFF;
    }
}

size_t construct_message(uint8_t* message_buffer, received_message_t* received_messages, size_t received_messages_len, self_t self, timestamp_t tx_timestamp) {
    int num_timestamp = 0;
    for (int i = 0; i < received_messages_len; i++) {
        if (received_messages[i].sequence_number != 0) {
            num_timestamp++;
        }
    }

    size_t message_size = 9 + sizeof(timestamp_t) +
                          num_timestamp * (sizeof(timestamp_t) + sizeof(ranging_id_t) + sizeof(sequence_number_t));
    // uint8_t* message_buffer = (uint8_t*) k_malloc(message_size);
    message_buffer[FRAME_CONTROL_IDX_1] = 0x88;
    message_buffer[FRAME_CONTROL_IDX_2] = 0x41;
    message_buffer[SEQUENCE_NUMBER_IDX_1] = self.sequence_number & 0xFF;
    message_buffer[SEQUENCE_NUMBER_IDX_2] = (self.sequence_number >> 8) & 0xFF;
    message_buffer[PAN_ID_IDX_1] = CONFIG_PAN_ID & 0xFF;
    message_buffer[PAN_ID_IDX_2] = (CONFIG_PAN_ID >> 8) & 0xFF;
    message_buffer[SENDER_ID_IDX_1] = self.id & 0xFF;
    message_buffer[SENDER_ID_IDX_2] = (self.id >> 8) & 0xFF;

    message_write_timestamp(message_buffer + TX_TIMESTAMP_IDX, tx_timestamp);

    // We use j as an index for the message buffer and i as an index for the `received_messages` list.
    int j = 0;
    for (int i = 0; i < received_messages_len; i++) {
        if (received_messages[i].sequence_number != 0) {
            int index = RX_TIMESTAMP_OFFSET + (RX_TIMESTAMP_SIZE * j);
            message_buffer[index + RX_TIMESTAMP_RANGING_ID_OFFSET] = received_messages[i].sender_id & 0xFF;
            message_buffer[index + RX_TIMESTAMP_RANGING_ID_OFFSET + 1] = (received_messages[i].sender_id >> 8) & 0xFF;
            message_buffer[index + RX_TIMESTAMP_SEQUENCE_NUMBER_OFFSET] = received_messages[i].sequence_number & 0xFF;
            message_buffer[index + RX_TIMESTAMP_SEQUENCE_NUMBER_OFFSET + 1] =
                (received_messages[i].sequence_number >> 8) & 0xFF;
            message_write_timestamp(message_buffer + index + RX_TIMESTAMP_TIMESTAMP_OFFSET,
                                    received_messages[i].rx_timestamp);
            j++;
        }
    }
    return message_size;
}
