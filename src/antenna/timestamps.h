#ifndef TIMESTAMPS_H
#define TIMESTAMPS_H

#include "typedefs.h"

timestamp_t read_systemtime();

timestamp_t read_rx_timestamp();

timestamp_t read_tx_timestamp();

#endif