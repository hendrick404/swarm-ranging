#include <data/json.h>
#include <drivers/uart.h>
#include <logging/log.h>
#include <zephyr.h>

#include "deca_device_api.h"
#include "deca_regs.h"
#include "deca_spi.h"
#include "port.h"

#include "json_configuration.h"
#include "message_definition.h"
#include "typedefs.h"

#define LOG_LEVEL 4
LOG_MODULE_REGISTER(main);

#define PAN_ID 0xDECA

#define UART_BUFFER_SIZE 512

static const struct device* uart_device = DEVICE_DT_GET(DT_CHOSEN(zephyr_console));

static dwt_config_t config = {5, DWT_PRF_64M, DWT_PLEN_128, DWT_PAC8, 9, 9, 1, DWT_BR_6M8, DWT_PHRMODE_STD, (129)};

static timestamp_t last_tx_timestamp = 0;

static sequence_number_t sequence_number = 1;

static uint16_t counter = 0;

static received_message_list_t* received_messages = NULL;

static ranging_id_t id;

timestamp_t read_rx_timestamp() {
    uint8_t timestamp_buffer[5];
    dwt_readrxtimestamp(timestamp_buffer);
    timestamp_t timestamp = 0;
    for (int i = 4; i >= 0; i--) {
        timestamp <<= 8;
        timestamp |= timestamp_buffer[i];
    }
    return timestamp;
}

timestamp_t read_tx_timestamp() {
    uint8_t timestamp_buffer[5];
    dwt_readtxtimestamp(timestamp_buffer);
    timestamp_t timestamp = 0;
    for (int i = 4; i >= 0; i--) {
        timestamp <<= 8;
        timestamp |= timestamp_buffer[i];
    }
    return timestamp;
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

void process_message(message_info_t info) {
    struct json_uart_message msg;
    struct json_range msg_range;
    struct json_range_timestamps msg_range_timestamps;

    msg.range = &msg_range;
    msg.range->timestamps = &msg_range_timestamps;
    msg.get = NULL;
    msg.set = NULL;
    msg.report = NULL;

    msg.range->sender_id = info.sender_id;
    msg.range->receiver_id = id;
    // msg.range->type = "poll";
    msg.range->sequence_number = info.sequence_number;
    msg.range->timestamps->rx_response_ts = info.timestamp;

    char message[UART_BUFFER_SIZE];
    int ret = json_obj_encode_buf(uart_message_descr, 4, &msg, message, UART_BUFFER_SIZE);
    if (ret) {
        LOG_ERR("Failed to encode json");
        return;
    }

    for (int i = 0; i < UART_BUFFER_SIZE && message[i] != '\0'; i++) {
        uart_poll_out(uart_device, message[i]);
    }
    uart_poll_out(uart_device, '\n');
}

/**
 * @brief Transmits a message.
 *
 * @param data the data that should be trasmitted.
 * @return int 0 on successful transmission.
 */
int send_message(/*message_data_t data*/) {
    LOG_INF("Sending message");
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
    for (int i = 0; i < num_timestamp; i++) {
        int index = RX_TIMESTAMP_OFFSET + (sizeof(timestamp_t) + sizeof(ranging_id_t) + sizeof(sequence_number_t)) * i;
        message_buffer[index] = iterator->data.sender_id & 0xFF;
        message_buffer[index + 1] = (iterator->data.sender_id >> 8) & 0xFF;
        message_buffer[index + 2] = iterator->data.sequence_number & 0xFF;
        message_buffer[index + 3] = (iterator->data.sequence_number >> 8) & 0xFF;
        for (int j = 0; j < sizeof(timestamp_t); j++) {
            message_buffer[index + 4 + j] = (iterator->data.rx_timestamp >> j) & 0xFF;
        }
    }

    dwt_writetxdata(message_size, message_buffer, 0);
    dwt_writetxfctrl(message_size, 0, 1);
    dwt_starttx(DWT_START_TX_IMMEDIATE);

    while (!(dwt_read32bitreg(SYS_STATUS_ID) & SYS_STATUS_TXFRS)) {
    };
    last_tx_timestamp = read_tx_timestamp();
    k_free(message_buffer);
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
        LOG_INF("Received frame");
        uint32_t frame_length = dwt_read32bitreg(RX_FINFO_ID) & RX_FINFO_RXFL_MASK_1023;
        LOG_INF("Frame length: %d", frame_length);
        uint8_t* rx_buffer = (uint8_t*) k_malloc(frame_length);
        dwt_readrxdata(rx_buffer, frame_length, 0);

        ranging_id_t sender_id = rx_buffer[SENDER_ID_IDX_1] | (rx_buffer[SENDER_ID_IDX_2] << 8);
        sequence_number_t sequence_number = rx_buffer[SEQUENCE_NUMBER_IDX_1] | (rx_buffer[SEQUENCE_NUMBER_IDX_2] << 8);

        if (received_messages == NULL) {
            received_messages = k_malloc(sizeof(received_message_list_t));
            received_messages->data.sender_id = sender_id;
            received_messages->data.sequence_number = sequence_number;
            received_messages->data.rx_timestamp = read_rx_timestamp();
            received_messages->next = NULL;
        } else {
            received_message_list_t* iterator = received_messages;
            while (1) {
                if (iterator->data.sender_id == sender_id) {
                    iterator->data.sequence_number = sequence_number;
                    iterator->data.rx_timestamp = read_rx_timestamp();
                    break;
                } else if (iterator->next == NULL) {
                    iterator->next = k_malloc(sizeof(received_message_list_t));
                    iterator->next->data.sender_id = sender_id;
                    iterator->next->data.sequence_number = sequence_number;
                    iterator->next->data.rx_timestamp = read_rx_timestamp();
                    iterator->next->next = NULL;
                    break;
                }
                iterator = iterator->next;
            }
        }

        LOG_HEXDUMP_DBG(rx_buffer, frame_length - 2, "Received data");

        k_free(rx_buffer);
        dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_RXFCG);
    } else if (status & SYS_STATUS_ALL_RX_ERR) {
        LOG_WRN("Reception error");
        dwt_write32bitreg(SYS_STATUS_ID, SYS_STATUS_ALL_RX_ERR);
    }
}

void process_incoming_uart(char* message_buffer, int size) {
    LOG_INF("Received uart");
    struct json_uart_message message;
    int ret = json_obj_parse(message_buffer, size, uart_message_descr, 4, &message);
    if (ret) {
        LOG_ERR("Could not decode json");
        return;
    }

    if (message.range != NULL) {
        message_data_t info;
        info.sender_id = id;
        info.receiver_id = message.range->receiver_id;
        info.sequence_number = message.range->sequence_number;
        send_message(info);
    }
}

/**
 * @brief Checks if there are messages pending to be send and send them if so.
 *
 */
void check_message_to_send() {
    counter++;
    if (counter == 500) {
        send_message();
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
    dwt_setleds(1);

    id = get_id();
    LOG_DBG("Ranging id %d", id);

    while (1) {
        check_received_messages();
        check_message_to_send();
        k_msleep(10);
    }
    return 0;
}