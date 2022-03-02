#include "unity.h"
#include "unity_fixture.h"

#include "util.h"

TEST_GROUP(Util);

TEST_SETUP(Util) {}

TEST_TEAR_DOWN(Util) {}

TEST(Util, message_read_timestamp_should_the_same_number_that_message_write_timestamp_previously_wrote) {
    uint8_t buffer[5] = {0,0,0,0,0};
    message_write_timestamp(buffer, 1337);
    TEST_ASSERT_EQUAL_INT64(1337, message_read_timestamp(buffer));
}