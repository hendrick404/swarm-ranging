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
    size_t timestamps_len;
    rx_range_timestamp_t* timestamps;
} rx_range_info_t;

typedef struct tx_range {
    ranging_id_t id;
    sequence_number_t sequence_number;
    timestamp_t tx_time;
} tx_range_info_t;

typedef struct range_info {
    tx_range_info_t* tx_info;
    rx_range_info_t* rx_info;
} range_info_t;

struct json_obj_descr json_rx_range_timestamps_descr[] = {
    JSON_OBJ_DESCR_PRIM_NAMED(struct rx_range_timestamp, "id", node_id, JSON_TOK_NUMBER),
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

struct json_obj_descr json_range_descr[] = {
    JSON_OBJ_DESCR_OBJECT_NAMED(struct range_info, "tx range", tx_info, json_tx_range_descr),
    JSON_OBJ_DESCR_OBJECT_NAMED(struct range_info, "rx range", rx_info, json_rx_range_descr),
};

#endif