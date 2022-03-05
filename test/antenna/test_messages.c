#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "unity.h"
#include "unity_fixture.h"

#include "messages.h"
#include "typedefs.h"


TEST_GROUP(Messages);

TEST_SETUP(Messages) {}

TEST_TEAR_DOWN(Messages) {}

TEST(Messages, message_read_timestamp_should_the_same_number_that_message_write_timestamp_previously_wrote) {
    uint8_t buffer[5] = {0,0,0,0,0};
    message_write_timestamp(buffer, 1337);
    TEST_ASSERT_EQUAL_UINT64(1337, message_read_timestamp(buffer));
    message_write_timestamp(buffer, 0xABABABABAB);
    TEST_ASSERT_EQUAL_UINT64(0xABABABABAB, message_read_timestamp(buffer));
    message_write_timestamp(buffer, 0xFBABABABAB);
    TEST_ASSERT_EQUAL_UINT64(0xFBABABABAB, message_read_timestamp(buffer));
}

TEST(Messages, message_write_timestamp) {
    uint8_t buffer[5] = {0,0,0,0,0};
    uint8_t expected_1[5] = {0,0,0,5,57};
    uint8_t expected_2[5] = {0xAB,0xAB,0xAB,0xAB,0xAB};
    uint8_t expected_3[5] = {0xFB,0xAB,0xAB,0xAB,0xAB};

    message_write_timestamp(buffer, 1337);
    TEST_ASSERT_EQUAL_UINT8_ARRAY(expected_1, buffer, 5);
    message_write_timestamp(buffer, 0xABABABABAB);
    TEST_ASSERT_EQUAL_UINT8_ARRAY(expected_2, buffer, 5);
    message_write_timestamp(buffer, 0xFBABABABAB);
    TEST_ASSERT_EQUAL_UINT8_ARRAY(expected_3, buffer, 5);

}

TEST(Messages, construct_message_without_reception_timestamps_correct) {
    self_t self = {.id = 1, .sequence_number = 1};
    timestamp_t tx_timestamp = 0xABCDEFABCD;
    uint8_t buffer[32];
    size_t buffer_len = construct_message(buffer, 32, NULL, 0, self, tx_timestamp);
    uint8_t test_buffer[] = {0x88, 0x41, 0, 0xca, 0xde, 1, 0, 1, 0, 0xAB, 0xCD, 0xEF, 0xAB, 0xCD};
    
    buffer[2] = 0;

    TEST_ASSERT_EQUAL_MESSAGE(14, buffer_len, "The encoded message seems to not have the correct size");
    TEST_ASSERT_FALSE_MESSAGE(memcmp(buffer, test_buffer, buffer_len), "The encoded message seems to have a wrong byte");
}

TEST(Messages, analyse_message_without_reception_timestamps_correct) {
    timestamp_t rx_timestamp = 0xABCDEFABCD;
    uint8_t test_buffer[] = {0x88, 0x41, 0, 0xca, 0xde, 1, 0, 1, 0, 0xAB, 0xCD, 0xEF, 0xAB, 0xCD};
    rx_range_info_t rx_info = analyse_message(test_buffer, 14, rx_timestamp);

    TEST_ASSERT_EQUAL_INT16(1, rx_info.sender_id);
    TEST_ASSERT_EQUAL_INT16(1, rx_info.sequence_number);
    TEST_ASSERT_EQUAL_UINT64(0xABCDEFABCD, rx_info.tx_time);
    TEST_ASSERT_EQUAL_INT(0, rx_info.timestamps_len);
    TEST_ASSERT_EQUAL(NULL, rx_info.timestamps);
}

TEST(Messages, encode_decode_message) {
    self_t self = {.id = 1, .sequence_number = 1};
    received_message_t rx_timestamps[3] = {
        {.sender_id = 1, .sequence_number = 11, .rx_timestamp = 0xAAAAAAAAAA},
        {.sender_id = 2, .sequence_number = 12, .rx_timestamp = 0xBBBBBBBBBB},
        {.sender_id = 3, .sequence_number = 13, .rx_timestamp = 0xCCCCCCCCCC}
    };
    timestamp_t tx_time = 0xDDDDDDDDDD;
    timestamp_t rx_time = 0xEEEEEEEEEE;
    uint8_t message_buffer[64];
    size_t message_size = construct_message(message_buffer, 64, rx_timestamps, 3, self, tx_time);
    rx_range_info_t rx_info = analyse_message(message_buffer, message_size, rx_time);

    TEST_ASSERT_EQUAL_INT16(1, rx_info.sender_id);
    TEST_ASSERT_EQUAL_INT16(1, rx_info.sequence_number);
    TEST_ASSERT_EQUAL_UINT64(0xDDDDDDDDDD, rx_info.tx_time);
    TEST_ASSERT_EQUAL_INT(3, rx_info.timestamps_len);

    for (int i = 0; i < 3; i++) {
        if (rx_info.timestamps[i].node_id == 1) {
            TEST_ASSERT_EQUAL_UINT64(0xAAAAAAAAAA, rx_info.timestamps[i].rx_time);
            TEST_ASSERT_EQUAL(11, rx_info.timestamps[i].sequence_number);
        } else if (rx_info.timestamps[i].node_id == 2) {
            TEST_ASSERT_EQUAL_UINT64(0xBBBBBBBBBB, rx_info.timestamps[i].rx_time);
            TEST_ASSERT_EQUAL(12, rx_info.timestamps[i].sequence_number);
        } else if (rx_info.timestamps[i].node_id == 3) {
            TEST_ASSERT_EQUAL_UINT64(0xCCCCCCCCCC, rx_info.timestamps[i].rx_time);
            TEST_ASSERT_EQUAL(13, rx_info.timestamps[i].sequence_number);
        } else {
            TEST_FAIL_MESSAGE("Unknown id");
        }
    }
}