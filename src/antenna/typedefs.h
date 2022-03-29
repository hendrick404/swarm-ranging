#ifndef TYPEDEFS_H
#define TYPEDEFS_H

#include <stddef.h>
#include <stdint.h>

#define TX_TIMESTAMP_BLOCKSIZE 32

typedef int16_t ranging_id_t;

typedef int16_t sequence_number_t;

typedef uint64_t timestamp_t;

typedef struct received_message {
    ranging_id_t sender_id;
    sequence_number_t sequence_number;
    timestamp_t rx_timestamp;
} received_message_t;

typedef struct {
    ranging_id_t id;
    sequence_number_t sequence_number;
} self_t;

typedef struct rx_range_timestamp {
    ranging_id_t node_id;
    sequence_number_t sequence_number;
    timestamp_t rx_time;
} rx_range_timestamp_t;

typedef struct rx_range {
    ranging_id_t sender_id;
    sequence_number_t sequence_number;
    timestamp_t tx_time;
    timestamp_t rx_time;
    size_t timestamps_len;
    rx_range_timestamp_t* timestamps;
} rx_range_info_t;

typedef struct tx_range {
    ranging_id_t id;
    sequence_number_t sequence_number;
    timestamp_t tx_time;
} tx_range_info_t;

#endif