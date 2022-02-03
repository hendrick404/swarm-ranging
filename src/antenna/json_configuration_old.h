#ifndef JSON_CONFIGURATION_H
#define JSON_CONFIGURATION_H

struct json_uart_message {
    struct json_range {
        int sender_id;
        int receiver_id;
        int sequence_number;
        // char* type;
        struct json_range_timestamps {
            int tx_poll_ts;
            int rx_response_ts;
            int tx_final_ts;
        } * timestamps;
    } * range;
    struct json_set {
    } * get;
    struct json_get {
    } * set;
    struct json_report {
    } * report;
};

static struct json_obj_descr timestamp_descriptor[] = {
    JSON_OBJ_DESCR_PRIM(struct json_range_timestamps, tx_poll_ts, JSON_TOK_NUMBER),
    JSON_OBJ_DESCR_PRIM(struct json_range_timestamps, rx_response_ts, JSON_TOK_NUMBER),
    JSON_OBJ_DESCR_PRIM(struct json_range_timestamps, tx_final_ts, JSON_TOK_NUMBER),
};

static struct json_obj_descr range_descriptor[] = {
    JSON_OBJ_DESCR_PRIM(struct json_range, sender_id, JSON_TOK_NUMBER),
    JSON_OBJ_DESCR_PRIM(struct json_range, receiver_id, JSON_TOK_NUMBER),

    JSON_OBJ_DESCR_PRIM(struct json_range, sequence_number, JSON_TOK_NUMBER),
    // JSON_OBJ_DESCR_PRIM(struct json_range, type, JSON_TOK_STRING),
    JSON_OBJ_DESCR_OBJECT(struct json_range, timestamps, timestamp_descriptor),
};

static struct json_obj_descr get_descr[] = {};
static struct json_obj_descr set_descr[] = {};
static struct json_obj_descr report_descr[] = {};

struct json_obj_descr uart_message_descr[] = {
    JSON_OBJ_DESCR_OBJECT(struct json_uart_message, range, range_descriptor),
    JSON_OBJ_DESCR_OBJECT(struct json_uart_message, set, get_descr),
    JSON_OBJ_DESCR_OBJECT(struct json_uart_message, get, set_descr),
    JSON_OBJ_DESCR_OBJECT(struct json_uart_message, report, report_descr),
};

#endif