from math import sqrt
from typing import Dict, Tuple, List, Callable
from scipy.constants import speed_of_light

second = 1_000_000_000_000


class Node:
    def __init__(self, node_id: int, pos, clock_err: float = 1, clock_offset: int = 0):
        self.node_id = node_id
        self.pos = pos
        self.clock_err = clock_err
        self.clock_offset = clock_offset
        self.sequence_number = 1
        self.receive_timestamps: Dict[int, Tuple[int, int]] = {}

        # Evaluation
        self.tx_timestamps: Dict[int, int] = {}
        self.rx_timestamps: Dict[Tuple[int, int], int] = {}
        self.other_tx_timestamps: Dict[Tuple[int, int], int] = {}
        self.active_ranging_distances: Dict[int, List[float]] = {}

    def get_pos(self, global_time: int) -> Tuple[float, float]:
        return self.pos(global_time) if type(self.pos) == Callable else self.pos

    def get_distance(self, global_time: int, other_node):
        (own_pos_x, own_pos_y) = self.get_pos(global_time)
        (other_pos_x, other_pos_y) = other_node.get_pos(global_time)
        return sqrt((own_pos_x - other_pos_x) ** 2 + (own_pos_y - other_pos_y) ** 2)

    def tx(self, global_time: int) -> Tuple[Dict, Dict, Tuple[int, int]]:
        json_obj = {
            "id": self.node_id,
            "tx range": {
                "seq num": self.sequence_number,
                "tx time": int(global_time * self.clock_err + self.clock_offset),
            },
        }
        self.sequence_number += 1
        if type(self.pos) == Callable:
            pos = self.pos(global_time)
        else:
            pos = self.pos
        return (json_obj, self.receive_timestamps, pos)

    def rx(
        self,
        global_time: int,
        message: Dict,
        pos: Tuple[int, int],
        message_receive_timestamps: Dict[int, Tuple[int, int]],
    ) -> Dict:
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

    def evaluate_tx(self, message: Dict):
        assert (
            message["id"] == self.node_id
        ), "We only want to process information created at our own end"

        self.tx_timestamps[message["tx range"]["seq num"]] = message["tx range"][
            "tx time"
        ]

    def evaluate_rx(self, message: Dict):
        assert (
            message["id"] == self.node_id
        ), "We only want to process information created at our own end"

        for rx_timestamp in message["rx range"]["timestamps"]:
            if rx_timestamp["id"] == self.node_id:
                self.other_tx_timestamps[
                    (message["rx range"]["sender id"], message["rx range"]["seq num"])
                ] = message["rx range"]["tx time"]
                self.rx_timestamps[
                    (message["rx range"]["sender id"], message["rx range"]["seq num"])
                ] = message["rx range"]["rx time"]

                i =  message["rx range"]["seq num"] - 1
                while (message["rx range"]["sender id"], i) not in self.rx_timestamps.keys():
                    if i <= 0:
                        return
                    i -= 1
                
                try:
                    tx_b1 = self.other_tx_timestamps[(message["rx range"]["sender id"], i)]
                    rx_a1 =  self.rx_timestamps[(message["rx range"]["sender id"], i)]
                    tx_a = self.tx_timestamps[rx_timestamp["seq num"]]
                    rx_b = rx_timestamp["rx time"]
                    tx_b2 = message["rx range"]["tx time"]
                    rx_a2 = message["rx range"]["rx time"]
                except KeyError:
                    return
                    
                r_a = rx_a2 - tx_a
                r_b = rx_b - tx_b1
                d_a = tx_a - rx_a1
                d_b = tx_b2 - rx_b
                if (
                    message["rx range"]["sender id"]
                    not in self.active_ranging_distances
                ):
                    self.active_ranging_distances[message["rx range"]["sender id"]] = []
                tof = (r_a * r_b - d_a * d_b) / (r_a + r_b + d_a + d_b)
                self.active_ranging_distances[message["rx range"]["sender id"]].append(
                    (tof / second) * speed_of_light
                )

    def __eq__(self, other):
        return self.node_id == other.node_id