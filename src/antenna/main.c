#include <data/json.h>
#include <drivers/uart.h>
#include <logging/log.h>
#include <zephyr.h>

#include "deca_device_api.h"
#include "deca_regs.h"
#include "deca_spi.h"
#include "port.h"

#include "configuration.h"
#include "json_configuration.h"
#include "message_definition.h"
#include "misc.h"
#include "typedefs.h"

#define LOG_LEVEL 4
LOG_MODULE_REGISTER(main);

#define PAN_ID 0xDECA

#define UART_BUFFER_SIZE 1024

static const struct device* uart_device = DEVICE_DT_GET(DT_CHOSEN(zephyr_console));

static dwt_config_t config = {5, DWT_PRF_64M, DWT_PLEN_128, DWT_PAC8, 9, 9, 1, DWT_BR_6M8, DWT_PHRMODE_STD, (129)};

static sequence_number_t sequence_number = 1;

static uint16_t counter = 0;

static received_message_list_t* received_messages = NULL;

static ranging_id_t id;

static tx_timestamp_list_t* tx_timestamps = NULL;

void print_received_message_list() {
    received_message_list_t* iterator = received_messages;
    int i = 0;
    while (iterator != NULL) {
        LOG_DBG("%d. element: id: %d, seq num: %d, ts %lld", i, iterator->data.sender_id,
                iterator->data.sequence_number, iterator->data.rx_timestamp);
        i++;
        iterator = iterator->next;
    }
}

timestamp_t get_tx_timestamp(sequence_number_t sequence_number) {
    tx_timestamp_list_t* iterator = tx_timestamps;
    for (int i = 0; i < sequence_number / TX_TIMESTAMP_BLOCKSIZE; i++) {
        if (iterator == NULL || iterator->next == NULL) {
            return 0;
        }
        iterator = iterator->next;
    }
    return iterator->timestamps[sequence_number % TX_TIMESTAMP_BLOCKSIZE];
}

void set_tx_timestamp(sequence_number_t sequence_number, timestamp_t timestamp) {
    tx_timestamp_list_t* iterator = tx_timestamps;
    for (int i = 0; i < sequence_number / TX_TIMESTAMP_BLOCKSIZE; i++) {
        if (iterator->next == NULL) {
            iterator->next = k_malloc(sizeof(tx_timestamp_list_t));
            iterator->next->next = NULL;
        }
        iterator = iterator->next;
    }
    iterator->timestamps[sequence_number % TX_TIMESTAMP_BLOCKSIZE] = timestamp;
}

timestamp_t read_systemtime() {
    uint8_t timestamp_buffer[5];
    dwt_readsystime(timestamp_buffer);
    timestamp_t timestamp = 0;
    for (int i = 4; i >= 0; i--) {
        timestamp <<= 8;
        timestamp |= timestamp_buffer[i];
    }
    return timestamp;
}

timestamp_t read_rx_timestamp() {
    uint32_t nrf_time = (uint32_t) ((double) k_uptime_get() / 1000 / DWT_TIME_UNITS);
    uint8_t timestamp_buffer[5];
    dwt_readrxtimestamp(timestamp_buffer);
    timestamp_t timestamp = 0;
    for (int i = 4; i >= 0; i--) {
        timestamp <<= 8;
        timestamp |= timestamp_buffer[i];
    }
    return timestamp;  // | nrf_time << (5 * 8);
}

timestamp_t read_tx_timestamp() {
    uint32_t nrf_time = (uint32_t) ((double) k_uptime_get() / 1000 / DWT_TIME_UNITS);
    uint8_t timestamp_buffer[5];
    dwt_readtxtimestamp(timestamp_buffer);
    timestamp_t timestamp = 0;
    for (int i = 4; i >= 0; i--) {
        timestamp <<= 8;
        timestamp |= timestamp_buffer[i];
    }
    return timestamp;  // | nrf_time << (5 * 8);
}

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

/**
 * @brief Get the id object
 *
 * This is a static part id to ranging id mapping.
 *
 * @return uint16_t the id. If no mapping exists, 0 is returned as default.
 */
uint16_t get_id() {
    uint32_t part_id = dwt_getpartid();
    LOG_DBG("Part id %d", part_id);
    switch (part_id) {
        case 268447190:
            return 1;
        case 268446691:
            return 2;
        case 268447501:
            return 3;
        default:
            return 0;
    }
}

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
    // sprintf(uart_buffer, "{\"rx range\":%s}", json_buffer);
    // uart_out(uart_buffer);
}

void process_message(range_info_t* info) {
    char uart_buffer[UART_BUFFER_SIZE];
    int ret = json_obj_encode(json_range_descr, 2, (void*) info, json_send_bytes_uart, NULL);
    if (ret) {
        LOG_ERR("Failed to encode json errno: %d", ret);
        return;
    }
    // uart_out(uart_buffer);
    // snprintf(uart_buffer, UART_BUFFER_SIZE, "{");
    // char temp[256];
    // if (info->rx_info != NULL) {
    //     snprintf(temp, 256, "\"rx range\": {\"sender id\": %u, \"tx time\": %llu, \"rx time\": %llu, \"timestamps\":
    //     [",
    //              info->rx_info->sender_id, info->rx_info->tx_time, info->rx_info->rx_time);
    //     strncat(uart_buffer, temp, UART_BUFFER_SIZE);
    //     for (int i = 0; i < info->rx_info->timestamps_len; i++) {
    //         rx_range_timestamp_t* ts = info->rx_info->timestamps + i;
    //         snprintf(temp, 256, "{\"node id\": %u, \"sequence number\": %u, \"rx time\": %llu}", ts->node_id,
    //                  ts->sequence_number, ts->rx_time);
    //         strncat(uart_buffer, temp, UART_BUFFER_SIZE);
    //         if (i < info->rx_info->timestamps_len - 1) {
    //             strncat(uart_buffer, ",", UART_BUFFER_SIZE);
    //         }
    //     }
    //     strncat(uart_buffer, "]}", UART_BUFFER_SIZE);
    //     if (info->tx_info != NULL) {
    //         strncat(uart_buffer, ",", UART_BUFFER_SIZE);
    //     }
    // }

    // if (info->tx_info != NULL) {
    //     snprintf(temp, 256, "\"tx range\": {\"id\": %u, \"sequence number\": %u, \"tx time\": %llu}",
    //     info->tx_info->id,
    //              info->tx_info->sequence_number, info->tx_info->tx_time);
    //     strncat(uart_buffer, temp, UART_BUFFER_SIZE);
    // }

    // strncat(uart_buffer, "}", UART_BUFFER_SIZE);

    // for (int i = 0; i < UART_BUFFER_SIZE && uart_buffer[i] != '\0'; i++) {
    //     uart_poll_out(uart_device, uart_buffer[i]);
    // }
    // uart_poll_out(uart_device, '\n');
}

/**
 * @brief Transmits a message.
 *
 * @param data the data that should be trasmitted.
 * @return int 0 on successful transmission.
 */
int send_message(/*message_data_t data*/) {
    LOG_DBG("Sending message %d", sequence_number);
    int num_timestamp = 0;
    received_message_list_t* iterator = received_messages;
    while (iterator != NULL) {
        num_timestamp++;
        iterator = iterator->next;
    }

    size_t message_size = 9 + sizeof(timestamp_t) +
                          num_timestamp * (sizeof(timestamp_t) + sizeof(ranging_id_t) + sizeof(sequence_number_t));
    uint8_t* message_buffer = (uint8_t*) k_malloc(message_size);
    message_buffer[FRAME_CONTROL_IDX_1] = 0x88;
    message_buffer[FRAME_CONTROL_IDX_2] = 0x41;
    message_buffer[SEQUENCE_NUMBER_IDX_1] = sequence_number & 0xFF;
    message_buffer[SEQUENCE_NUMBER_IDX_2] = (sequence_number >> 8) & 0xFF;
    message_buffer[PAN_ID_IDX_1] = PAN_ID & 0xFF;
    message_buffer[PAN_ID_IDX_2] = (PAN_ID >> 8) & 0xFF;
    message_buffer[SENDER_ID_IDX_1] = id & 0xFF;
    message_buffer[SENDER_ID_IDX_2] = (id >> 8) & 0xFF;

    iterator = received_messages;
    for (int i = 0; i < num_timestamp && iterator != NULL; i++) {
        int index = RX_TIMESTAMP_OFFSET + (RX_TIMESTAMP_SIZE * i);
        message_buffer[index] = iterator->data.sender_id & 0xFF;
        message_buffer[index + 1] = (iterator->data.sender_id >> 8) & 0xFF;
        message_buffer[index + 2] = iterator->data.sequence_number & 0xFF;
        message_buffer[index + 3] = (iterator->data.sequence_number >> 8) & 0xFF;
        message_write_timestamp(message_buffer + index + RX_TIMESTAMP_TIMESTAMP_OFFSET, iterator->data.rx_timestamp);
        iterator = iterator->next;
    }

    uint32_t tx_time = (read_systemtime() + (TX_PROCESSING_DELAY * UUS_TO_DWT_TIME)) >> 8;
    timestamp_t tx_timestamp = (((uint64) (tx_time & 0xFFFFFFFEUL)) << 8) + TX_ANTENNA_DELAY;
    dwt_setdelayedtrxtime(tx_time);

    message_write_timestamp(message_buffer + TX_TIMESTAMP_IDX, tx_timestamp);

    dwt_writetxdata(message_size, message_buffer, 0);
    dwt_writetxfctrl(message_size, 0, 1);
    dwt_starttx(DWT_START_TX_DELAYED);

    while (!(dwt_read32bitreg(SYS_STATUS_ID) & SYS_STATUS_TXFRS)) {
    };
    set_tx_timestamp(sequence_number, tx_timestamp);
    k_free(message_buffer);

    tx_range_info_t tx_info;
    tx_info.id = id;
    tx_info.sequence_number = sequence_number;
    tx_info.tx_time = tx_timestamp;
    range_info_t info = {.rx_info = NULL, .tx_info = &tx_info};
    process_out_message(&tx_info);

    dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_TXFRS);
    dwt_rxenable(DWT_START_RX_IMMEDIATE);
    return 0;
}

/**
 * @brief Checks if there are incoming messages and processes them
 *
 */
void check_received_messages() {
    uint32_t status = dwt_read32bitreg(SYS_STATUS_ID);
    if (status & SYS_STATUS_RXFCG) {
        LOG_DBG("Received frame");
        uint32_t frame_length = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;
        LOG_DBG("Frame length: %d", frame_length);
        uint8_t* rx_buffer = (uint8_t*) k_malloc(frame_length);
        dwt_readrxdata(rx_buffer, frame_length, 0);

        rx_range_info_t rx_info;
        rx_info.sender_id = rx_buffer[SENDER_ID_IDX_1] | (rx_buffer[SENDER_ID_IDX_2] << 8);
        rx_info.rx_time = read_rx_timestamp();
        rx_info.tx_time = message_read_timestamp(rx_buffer + TX_TIMESTAMP_IDX);

        rx_info.timestamps_len = (frame_length - RX_TIMESTAMP_OFFSET) / RX_TIMESTAMP_SIZE;
        LOG_DBG("Timestamp num: %d", rx_info.timestamps_len);
        rx_info.timestamps = k_malloc(sizeof(rx_range_timestamp_t) * rx_info.timestamps_len);

        for (int i = 0; i < rx_info.timestamps_len; i++) {
            LOG_DBG("Reading timestamp %d", i);
            int timestamp_index = RX_TIMESTAMP_OFFSET + i * RX_TIMESTAMP_SIZE;
            rx_info.timestamps[i].node_id = rx_buffer[timestamp_index + RX_TIMESTAMP_RANGING_ID_OFFSET] |
                                            rx_buffer[timestamp_index + RX_TIMESTAMP_RANGING_ID_OFFSET + 1] << 8;
            rx_info.timestamps[i].sequence_number = rx_buffer[timestamp_index + RX_TIMESTAMP_SEQUENCE_NUMBER_OFFSET] |
                                                    rx_buffer[timestamp_index + RX_TIMESTAMP_SEQUENCE_NUMBER_OFFSET + 1]
                                                        << 8;
            rx_info.timestamps[i].rx_time =
                message_read_timestamp(rx_buffer + timestamp_index + RX_TIMESTAMP_TIMESTAMP_OFFSET);
        }

        range_info_t info = {.rx_info = &rx_info, .tx_info = NULL};
        process_in_message(&rx_info);

        if (received_messages == NULL) {
            received_messages = k_malloc(sizeof(received_message_list_t));
            received_messages->data.sender_id = rx_info.sender_id;
            received_messages->data.sequence_number = rx_info.sequence_number;
            received_messages->data.rx_timestamp = rx_info.rx_time;
            received_messages->next = NULL;
        } else {
            received_message_list_t* iterator = received_messages;
            while (1) {
                if (iterator->data.sender_id == rx_info.sender_id) {
                    iterator->data.sequence_number = rx_info.sequence_number;
                    iterator->data.rx_timestamp = rx_info.rx_time;
                    break;
                } else if (iterator->next == NULL) {
                    iterator->next = k_malloc(sizeof(received_message_list_t));
                    iterator->next->data.sender_id = rx_info.sender_id;
                    iterator->next->data.sequence_number = rx_info.sequence_number;
                    iterator->next->data.rx_timestamp = rx_info.rx_time;
                    iterator->next->next = NULL;
                    break;
                }
                iterator = iterator->next;
            }
        }

        LOG_HEXDUMP_DBG(rx_buffer, frame_length - 2, "Received data");

        k_free(rx_info.timestamps);
        k_free(rx_buffer);
        dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);
    } else if (status & SYS_STATUS_ALL_RX_ERR) {
        LOG_WRN("Reception error");
        dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_ERR);
    }
}

/**
 * @brief Checks if there are messages pending to be send and send them if so.
 *
 */
void check_message_to_send() {
    counter++;
    if (counter >= 5000) {
        send_message();
        print_received_message_list();
        sequence_number++;
        counter = 0;
    }
}

int main(void) {
    // Initialise dwm1001
    reset_DW1000();
    port_set_dw1000_slowrate();
    openspi();
    if (dwt_initialise(DWT_LOADUCODE | DWT_READ_OTP_PID) == DWT_ERROR) {
        LOG_ERR("Failed to initialize dwm");
        return -1;
    }
    port_set_dw1000_fastrate();
    dwt_configure(&config);
    dwt_setrxantennadelay(RX_ANTENNA_DELAY);
    dwt_settxantennadelay(TX_ANTENNA_DELAY);
    dwt_setleds(1);

    id = get_id();
    LOG_DBG("Ranging id %d", id);

    tx_timestamps = k_malloc(sizeof(tx_timestamp_list_t));
    tx_timestamps->next = NULL;

    while (1) {
        check_received_messages();
        check_message_to_send();
        k_msleep(1);
    }
    return 0;
}