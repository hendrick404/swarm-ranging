#ifndef STORAGE_H
#define STORAGE_H

#include "typedefs.h"

timestamp_t get_tx_timestamp(sequence_number_t sequence_number);

void set_tx_timestamp(sequence_number_t sequence_number, timestamp_t timestamp);

#endif