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
    size_t buffer_len = construct_message(buffer, NULL, 0, self, tx_timestamp);
    uint8_t test_buffer[] = {0x88, 0x41, 0, 0xca, 0xde, 1, 0, 1, 0, 0xAB, 0xCD, 0xEF, 0xAB, 0xCD};
    
    buffer[2] = 0;
    TEST_ASSERT_EQUAL_MESSAGE(buffer_len, 14, "The encoded message seems to not have the correct size");
    TEST_ASSERT_TRUE_MESSAGE(memcmp(buffer, test_buffer, buffer_len), "The encoded message seems to not have a wrong byte");
}