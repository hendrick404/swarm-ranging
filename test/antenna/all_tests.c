#include "unity.h"
#include "unity_fixture.h"

TEST_GROUP_RUNNER(Messages) {
    RUN_TEST_CASE(Messages, message_read_timestamp_should_the_same_number_that_message_write_timestamp_previously_wrote);
    RUN_TEST_CASE(Messages, message_write_timestamp);
    RUN_TEST_CASE(Messages, construct_message_without_reception_timestamps_correct);

}

static void run_all_tests(void) {
    RUN_TEST_GROUP(Messages)
}

int main(int argc, const char* argv[]) {
    return UnityMain(argc, argv, run_all_tests);
}