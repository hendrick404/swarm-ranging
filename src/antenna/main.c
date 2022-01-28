#include <data/json.h>
#include <drivers/uart.h>
#include <logging/log.h>
#include <zephyr.h>

#include "deca_device_api.h"
#include "deca_regs.h"
#include "deca_spi.h"
#include "port.h"

#include "json_configuration.h"

#define LOG_LEVEL 4
LOG_MODULE_REGISTER(main);

#define PAN_ID 0xDECA

#define UART_BUFFER_SIZE 512


static const struct device* uart_device = DEVICE_DT_GET(DT_CHOSEN(zephyr_console));

typedef enum { rx, tx } message_direction_t;

typedef struct {
    uint16_t sender_id;
    uint16_t receiver_id;
    uint8_t sequence_number;
} message_data_t;

typedef struct {
    uint16_t sender_id;
    uint16_t receiver_id;
    uint8_t sequence_number;
    uint64_t timestamp;
    message_direction_t mode;
} message_info_t;

static dwt_config_t config = {5, DWT_PRF_64M, DWT_PLEN_128, DWT_PAC8, 9, 9, 1, DWT_BR_6M8, DWT_PHRMODE_STD, (129)};

static uint16_t counter = 0;

static uint8_t sequence_number = 0;

static uint16_t id;

uint64_t read_rx_timestamp() {
    uint8_t timestamp_buffer[5];
    dwt_readrxtimestamp(timestamp_buffer);
    uint64_t timestamp = 0;
    for (int i = 4; i >= 0; i--) {
        timestamp <<= 8;
        timestamp |= timestamp_buffer[i];
    }
    return timestamp;
}

uint64_t read_tx_timestamp() {
    uint8_t timestamp_buffer[5];
    dwt_readtxtimestamp(timestamp_buffer);
    uint64_t timestamp = 0;
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
int send_message(message_data_t data) {
    LOG_INF("Sending message");
    uint8_t* message_buffer = (uint8_t*) k_malloc(12);
    message_buffer[0] = 0x88;
    message_buffer[1] = 0x41;
    message_buffer[2] = data.sequence_number;
    message_buffer[3] = PAN_ID & 0xFF;
    message_buffer[4] = (PAN_ID >> 8) & 0xFF;
    message_buffer[5] = data.receiver_id & 0xFF;
    message_buffer[6] = (data.receiver_id >> 8) & 0xFF;
    message_buffer[7] = data.sender_id & 0xFF;
    message_buffer[8] = (data.sender_id >> 8) & 0xFF;
    message_buffer[9] = 0x21;

    dwt_writetxdata(12, message_buffer, 0);
    dwt_writetxfctrl(12, 0, 1);
    dwt_starttx(DWT_START_TX_IMMEDIATE);

    while (!(dwt_read32bitreg(SYS_STATUS_ID) & SYS_STATUS_TXFRS)) {
    };
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

        message_info_t info;
        info.mode = rx;
        info.receiver_id = rx_buffer[6] << 8 | rx_buffer[5];
        info.sender_id = rx_buffer[8] << 8 | rx_buffer[7];
        info.sequence_number = rx_buffer[2];
        info.timestamp = read_rx_timestamp();
        process_message(info);

        LOG_HEXDUMP_DBG(rx_buffer, frame_length - 2, "Received data");

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
    if (counter == 500) {
        message_data_t data;
        data.receiver_id = 0;
        data.sender_id = id;
        data.sequence_number = sequence_number;
        send_message(data);
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