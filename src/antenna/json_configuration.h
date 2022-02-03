#ifndef JSON_CONFIGURATION_H
#define JSON_CONFIGURATION_H

#include "typedefs.h"

#define NUM_MAX_TIMESTAMPS 128

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
    int timestamps_len;
    rx_range_timestamp_t* timestamps;
} rx_range_t;

typedef struct tx_range {
    ranging_id_t id;
    sequence_number_t sequence_number;
    timestamp_t tx_time;
} tx_range_t;

struct json_obj_descr json_rx_range_timestamps_descr[] = {
    JSON_OBJ_DESCR_PRIM_NAMED(struct rx_range_timestamp, "node id", node_id, JSON_TOK_NUMBER),
    JSON_OBJ_DESCR_PRIM_NAMED(struct rx_range_timestamp, "sequence number", sequence_number, JSON_TOK_NUMBER),
    JSON_OBJ_DESCR_PRIM_NAMED(struct rx_range_timestamp, "rx time", rx_time, JSON_TOK_NUMBER),
};

struct json_obj_descr json_rx_range_descr[] = {
    JSON_OBJ_DESCR_PRIM_NAMED(struct rx_range, "sender id", sender_id, JSON_TOK_NUMBER),
    JSON_OBJ_DESCR_PRIM_NAMED(struct rx_range, "sequence number", sequence_number, JSON_TOK_NUMBER),
    JSON_OBJ_DESCR_PRIM_NAMED(struct rx_range, "tx time", tx_time, JSON_TOK_NUMBER),
    JSON_OBJ_DESCR_PRIM_NAMED(struct rx_range, "rx time", rx_time, JSON_TOK_NUMBER),
    JSON_OBJ_DESCR_OBJ_ARRAY(struct rx_range,
                             timestamps,
                             NUM_MAX_TIMESTAMPS,
                             timestamps_len,
                             json_rx_range_timestamps_descr,
                             3),
};

struct json_obj_descr json_tx_range_descr[] = {
    JSON_OBJ_DESCR_PRIM_NAMED(struct tx_range, "id", id, JSON_TOK_NUMBER),
    JSON_OBJ_DESCR_PRIM_NAMED(struct tx_range, "sequence number", sequence_number, JSON_TOK_NUMBER),
    JSON_OBJ_DESCR_PRIM_NAMED(struct tx_range, "time", tx_time, JSON_TOK_NUMBER),
};

#endif