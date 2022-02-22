#ifndef HOST_INTERFACE_H
#define HOST_INTERFACE_H

#include "typedefs.h"

void process_out_message(tx_range_info_t* info, ranging_id_t id);

void process_in_message(rx_range_info_t* info, ranging_id_t id);

#endif