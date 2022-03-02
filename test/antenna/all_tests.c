#include "unity.h"
#include "unity_fixture.h"

TEST_GROUP_RUNNER(Util) {
    RUN_TEST_CASE(Util, message_read_timestamp_should_the_same_number_that_message_write_timestamp_previously_wrote);
}

static void run_all_tests(void) {
    RUN_TEST_GROUP(Util)
}

int main(int argc, const char* argv[]) {
    return UnityMain(argc, argv, run_all_tests);
}