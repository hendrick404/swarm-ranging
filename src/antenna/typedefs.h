#ifndef TYPEDEFS_H
#define TYPEDEFS_H

#define TX_TIMESTAMP_BLOCKSIZE 32

typedef enum { rx, tx } message_direction_t;

typedef uint16_t ranging_id_t;

typedef uint16_t sequence_number_t;

typedef uint64_t timestamp_t;

typedef struct {
    ranging_id_t sender_id;
    ranging_id_t receiver_id;
    sequence_number_t sequence_number;
} message_data_t;

typedef struct {
    ranging_id_t sender_id;
    ranging_id_t receiver_id;
    sequence_number_t sequence_number;
    timestamp_t timestamp;
    message_direction_t mode;
} message_info_t;

typedef struct received_message {
    ranging_id_t sender_id;
    sequence_number_t sequence_number;
    timestamp_t rx_timestamp;
} received_message_t;

typedef struct received_message_list {
    struct received_message_list* next;
    received_message_t data;
} received_message_list_t;

typedef struct tx_timestamp_list {
    struct tx_timestamp_list* next;
    timestamp_t timestamps[TX_TIMESTAMP_BLOCKSIZE];
} tx_timestamp_list_t;

#endif