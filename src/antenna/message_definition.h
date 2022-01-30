#ifndef MESSAGE_DEFINITION_H
#define MESSAGE_DEFINITION_H

#include "typedefs.h"

#define FRAME_CONTROL_1 0x88
#define FRAME_CONTROL_2 0x41

#define TIMESTAMP_SIZE 8

#define FRAME_CONTROL_IDX_1 0
#define FRAME_CONTROL_IDX_2 1

#define PAN_ID_IDX_1 3
#define PAN_ID_IDX_2 4

#define SEQUENCE_NUMBER_IDX_1 5
#define SEQUENCE_NUMBER_IDX_2 6

#define SENDER_ID_IDX_1 7
#define SENDER_ID_IDX_2 8

#define TX_TIMESTAMP_IDX 9

#define RX_TIMESTAMP_OFFSET TX_TIMESTAMP_IDX + sizeof(timestamp_t)

#endif
