from math import sqrt
from typing import Dict, Tuple, List
from scipy.constants import speed_of_light

second = 1_000_000_000_000

class Node:
    def __init__(self, node_id: int, pos: Tuple[int, int], clock_err: float = 1, clock_offset: int = 0):
        self.node_id = node_id
        self.pos = pos
        self.clock_err = clock_err
        self.clock_offset = clock_offset
        self.sequence_number = 1
        self.receive_timestamps: Dict[int, Tuple[int, int]] = {}

    def get_pos(self):
        return self.pos

    def tx(self, global_time: int):
        json_obj = {
            "id": self.node_id,
            "tx range": {
                "seq num": self.sequence_number,
                "tx time": int(global_time * self.clock_err + self.clock_offset),
            },
        }
        self.sequence_number += 1
        return (json_obj, self.receive_timestamps)

    def rx(self, global_time: int, message, pos: Tuple[int, int], message_receive_timestamps: Dict[int, Tuple[int, int]]):
        rx_time = (
            global_time
            + (
                sqrt((self.pos[0] - pos[0]) ** 2 + (self.pos[1] - pos[1]) ** 2)
                / (speed_of_light / second)
            )
        ) * self.clock_err + self.clock_offset
        self.receive_timestamps[message["id"]] = (
            message["tx range"]["seq num"],
            int(rx_time),
        )
        rx_timestamps = []
        for (node_id, (seq_num, rx_timestamp)) in message_receive_timestamps.items():
            rx_timestamps.append(
                {"id": node_id, "seq num": seq_num, "rx time": rx_timestamp}
            )
        json_obj = {
            "id": self.node_id,
            "rx range": {
                "sender id": message["id"],
                "seq num": message["tx range"]["seq num"],
                "tx time": message["tx range"]["tx time"],
                "rx time": int(rx_time),
                "timestamps": rx_timestamps,
            },
        }
        return json_obj

    def __eq__(self, other):
        return self.node_id == other.node_id
