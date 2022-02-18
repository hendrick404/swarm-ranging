#include <data/json.h>
#include <drivers/uart.h>
#include <zephyr.h>

#include "host_interface.h"
#include "typedefs.h"

#define LOG_LEVEL 4
LOG_MODULE_REGISTER(host_interface);

const struct json_obj_descr json_rx_range_timestamps_descr[] = {
    JSON_OBJ_DESCR_PRIM_NAMED(struct rx_range_timestamp, "id", node_id, JSON_TOK_NUMBER),
    JSON_OBJ_DESCR_PRIM_NAMED(struct rx_range_timestamp, "sequence number", sequence_number, JSON_TOK_NUMBER),
    JSON_OBJ_DESCR_PRIM_NAMED(struct rx_range_timestamp, "rx time", rx_time, JSON_TOK_NUMBER),
};

const struct json_obj_descr json_rx_range_descr[] = {
    JSON_OBJ_DESCR_PRIM_NAMED(struct rx_range, "sender id", sender_id, JSON_TOK_NUMBER),
    JSON_OBJ_DESCR_PRIM_NAMED(struct rx_range, "sequence number", sequence_number, JSON_TOK_NUMBER),
    JSON_OBJ_DESCR_PRIM_NAMED(struct rx_range, "tx time", tx_time, JSON_TOK_NUMBER),
    JSON_OBJ_DESCR_PRIM_NAMED(struct rx_range, "rx time", rx_time, JSON_TOK_NUMBER),
    JSON_OBJ_DESCR_OBJ_ARRAY(struct rx_range,
                             timestamps,
                             CONFIG_NUM_MAX_TIMESTAMPS,
                             timestamps_len,
                             json_rx_range_timestamps_descr,
                             3),
};

const struct json_obj_descr json_tx_range_descr[] = {
    JSON_OBJ_DESCR_PRIM_NAMED(struct tx_range, "id", id, JSON_TOK_NUMBER),
    JSON_OBJ_DESCR_PRIM_NAMED(struct tx_range, "sequence number", sequence_number, JSON_TOK_NUMBER),
    JSON_OBJ_DESCR_PRIM_NAMED(struct tx_range, "time", tx_time, JSON_TOK_NUMBER),
};

const struct json_obj_descr json_range_descr[] = {
    JSON_OBJ_DESCR_OBJECT_NAMED(struct range_info, "tx range", tx_info, json_tx_range_descr),
    JSON_OBJ_DESCR_OBJECT_NAMED(struct range_info, "rx range", rx_info, json_rx_range_descr),
};

static const struct device* uart_device = DEVICE_DT_GET(DT_CHOSEN(zephyr_console));

void uart_out(char* msg) {
    while (*msg != '\0') {
        uart_poll_out(uart_device, *msg);
        msg++;
    }
}

int json_send_bytes_uart(const char* bytes, size_t len, void* data) {
    for (int i = 0; i < len; i++) {
        uart_poll_out(uart_device, bytes[i]);
    }
    return 0;
}

void process_out_message(tx_range_info_t* info) {
    uart_out("{\"tx range\": ");
    int ret = json_obj_encode(json_tx_range_descr, 3, (void*) info, json_send_bytes_uart, NULL);
    if (ret) {
        LOG_ERR("Failed to encode json errno: %d", ret);
        return;
    }
    uart_out("}\n");
}

void process_in_message(rx_range_info_t* info) {
    uart_out("{\"rx range\": ");
    int ret = json_obj_encode(json_rx_range_descr, 5, (void*) info, json_send_bytes_uart, NULL);
    if (ret) {
        LOG_ERR("Failed to encode json errno: %d", ret);
        return;
    }
    uart_out("}\n");
}

void process_message(range_info_t* info) {
    int ret = json_obj_encode(json_range_descr, 2, (void*) info, json_send_bytes_uart, NULL);
    if (ret) {
        LOG_ERR("Failed to encode json errno: %d", ret);
        return;
    }
}