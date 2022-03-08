"""
Simulates a scenario with a number of static nodes. Configure `ranging_interval`,
`nodes` and `transmission_succes_rate` in the main function.
"""

import json
from random import random
from math import sqrt
from typing import Dict, Tuple, List
from scipy.constants import speed_of_light


second = 1_000_000_000_000


class Node:
    def __init__(self, node_id, pos, clock_err=1, clock_offset=0):
        self.node_id = node_id
        self.pos = pos
        self.clock_err = clock_err
        self.clock_offset = clock_offset
        self.sequence_number = 1
        self.receive_timestamps: Dict[int, Tuple[int, int]] = {}

    def get_pos(self):
        return self.pos

    def tx(self, global_time):
        json_obj = {
            "id": self.id,
            "tx range": {
                "seq num": self.sequence_number,
                "tx time": int(global_time * self.clock_err + self.clock_offset),
            },
        }
        self.sequence_number += 1
        return (json_obj, self.receive_timestamps)

    def rx(self, global_time, message, pos, message_receive_timestamps):
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
            "id": self.id,
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
        return self.id == other.id


def main():
    with open("evaluation_simulated.txt", "a") as eval_file:
        exchange_counter = 1
        ranging_interval = 1 * second
        global_clock = 0
        nodes: List[Node] = [Node(1, (0, 0)), Node(2, (60, 0))]
        transmission_success_rate = 0.95
        while exchange_counter <= 2 * len(nodes):
            for tx_node in nodes:
                global_clock += ranging_interval / len(nodes)
                (tx_message, receive_timestamps) = tx_node.tx(global_clock)
                eval_file.write(json.JSONEncoder().encode(tx_message) + "\n")
                for rx_node in nodes:
                    if rx_node != tx_node and random() <= transmission_success_rate:
                        rx_message = rx_node.rx(
                            global_clock,
                            tx_message,
                            tx_node.get_pos(),
                            receive_timestamps,
                        )
                        eval_file.write(json.JSONEncoder().encode(rx_message) + "\n")
            exchange_counter += 1


if __name__ == "__main__":
    main()
