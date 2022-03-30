from math import sqrt
from typing import Dict, Optional, Tuple, List, Callable
from scipy.constants import speed_of_light

from src.simulation.config import SECOND


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
        self.other_rx_timestamps: Dict[Tuple[int, int, int], int] = {}
        self.active_ranging_distances: Dict[int, List[float]] = {}
        self.passive_ranging_distances: Dict[Tuple[int, int], List[float]] = {}
        self.passive_ranging_distances_adjusted: Dict[Tuple[int, int], List[float]] = {}

    def get_pos(self, global_time: int) -> Tuple[float, float]:
        return self.pos(global_time) if type(self.pos) == Callable else self.pos

    def get_distance(self, global_time: int, other_node):
        (own_pos_x, own_pos_y) = self.get_pos(global_time)
        (other_pos_x, other_pos_y) = other_node.get_pos(global_time)
        return sqrt((own_pos_x - other_pos_x) ** 2 + (own_pos_y - other_pos_y) ** 2)

    def tx(self, global_time: int) -> Tuple[Dict, Dict, Tuple[float, float]]:
        json_obj = {
            "id": self.node_id,
            "tx range": {
                "seq num": self.sequence_number,
                "tx time": int(global_time * self.clock_err + self.clock_offset),
            },
        }
        self.sequence_number += 1

        return (json_obj, self.receive_timestamps, self.get_pos(global_time))

    def rx(
        self,
        global_time: int,
        message: Dict,
        pos: Tuple[float, float],
        message_receive_timestamps: Dict[int, Tuple[int, int]],
    ) -> Dict:
        own_pos = self.get_pos(global_time)
        rx_time = (
            global_time
            + (
                sqrt((own_pos[0] - pos[0]) ** 2 + (own_pos[1] - pos[1]) ** 2)
                / (speed_of_light / SECOND)
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

    def get_stored_rx_timestamp(
        self, sender_id: int, receiver_id: int, seq_num: int
    ) -> Optional[Tuple[int, int]]:
        i = seq_num - 1
        if receiver_id == self.node_id:
            while (sender_id, i) not in self.rx_timestamps.keys():
                i -= 1
                if i < 0:
                    return None

            return (i, self.rx_timestamps[sender_id, i])
        else:
            while (sender_id, receiver_id, i) not in self.other_rx_timestamps.keys():
                i -= 1
                if i < 0:
                    return None
            return (i, self.other_rx_timestamps[(sender_id, receiver_id, i)])

    def get_stored_tx_timestamp(
        self, sender_id: int, seq_num: int
    ) -> Optional[Tuple[int, int]]:
        i = seq_num - 1
        if sender_id == self.node_id:
            while i not in self.tx_timestamps.keys():
                i -= 1
                if i < 0:
                    return None

            return (i, self.rx_timestamps[(i, sender_id)])
        else:
            while (sender_id, i) not in self.other_tx_timestamps.keys():
                i -= 1
                if i < 0:
                    return None
            return (i, self.other_tx_timestamps[(sender_id, i)])

    def evaluate_rx(self, message: Dict):
        assert (
            message["id"] == self.node_id
        ), "We only want to process information created at our own end"

        # Node ids
        # A: (This node)
        a_id = self.node_id
        # B:
        b_id = message["rx range"]["sender id"]

        # M_{B,2}: B -> A
        m_3_s = message["rx range"]["seq num"]

        self.other_tx_timestamps[b_id, message["rx range"]["seq num"]] = message[
            "rx range"
        ]["tx time"]
        self.rx_timestamps[
            (message["rx range"]["sender id"], message["rx range"]["seq num"])
        ] = message["rx range"]["rx time"]
        for rx_timestamp in message["rx range"]["timestamps"]:
            self.other_rx_timestamps[
                (
                    message["rx range"]["sender id"],
                    rx_timestamp["id"],
                    rx_timestamp["seq num"],
                )
            ] = rx_timestamp["rx time"]
            if rx_timestamp["id"] == self.node_id:
                # Active Ranging

                # Sequence numbers
                # M_{A,1}: A -> B
                m_2_s = rx_timestamp["seq num"]
                # M_{B,2}: B -> A
                m_3_s = message["rx range"]["seq num"]
                # M_{B,1}: B -> A
                m_1 = self.get_stored_rx_timestamp(b_id, a_id, m_3_s)
                if m_1:
                    (m_1_s, _) = m_1
                else:
                    print("Missing timestamp")
                    break  # We don't have the right timestamp yet

                r_a = self.rx_timestamps[b_id, m_3_s] - self.tx_timestamps[m_2_s]
                r_b = (
                    self.other_rx_timestamps[b_id, a_id, m_2_s]
                    - self.other_tx_timestamps[b_id, m_1_s]
                )
                d_a = self.tx_timestamps[m_2_s] - self.rx_timestamps[b_id, m_1_s]
                d_b = (
                    self.other_tx_timestamps[b_id, m_3_s]
                    - self.other_rx_timestamps[b_id, a_id, m_2_s]
                )

                # i = message["rx range"]["seq num"] - 1
                # while (
                #     message["rx range"]["sender id"],
                #     i,
                # ) not in self.rx_timestamps.keys():
                #     if i <= 0:
                #         break
                #     i -= 1

                # try:
                #     tx_b1 = self.other_tx_timestamps[
                #         (message["rx range"]["sender id"], i)
                #     ]
                #     rx_a1 = self.rx_timestamps[(message["rx range"]["sender id"], i)]
                #     tx_a = self.tx_timestamps[rx_timestamp["seq num"]]
                #     rx_b = rx_timestamp["rx time"]
                #     tx_b2 = message["rx range"]["tx time"]
                #     rx_a2 = message["rx range"]["rx time"]
                # except KeyError:
                #     break

                # r_a = rx_a2 - tx_a
                # r_b = rx_b - tx_b1
                # d_a = tx_a - rx_a1
                # d_b = tx_b2 - rx_b
                if b_id not in self.active_ranging_distances:
                    self.active_ranging_distances[b_id] = []
                # Alternative DS-TWR (Neirynck et al. 2016)
                tof = (r_a * r_b - d_a * d_b) / (r_a + r_b + d_a + d_b)
                self.active_ranging_distances[message["rx range"]["sender id"]].append(
                    (tof / SECOND) * speed_of_light
                )
            else:
                # Passive Ranging
                # Passively ranging nodes: B: message["rx range"]["sender id"]
                #                     and: C: rx_timestamp["id"]
                # Message sequence numbers: M_B1: i
                #                           M_C1: timestamp["seq num"]
                #                           M_B2: message["rx range"]["seq num"]
                i = message["rx range"]["seq num"] - 1
                while (
                    message["rx range"]["sender id"],
                    i,
                ) not in self.rx_timestamps.keys():
                    if i <= 0:
                        break
                    i -= 1
                try:
                    a_rx_b1 = self.rx_timestamps[(message["rx range"]["sender id"], i)]

                    a_rx_c1 = self.rx_timestamps[
                        (rx_timestamp["id"], rx_timestamp["seq num"])
                    ]

                    a_rx_b2 = message["rx range"]["rx time"]

                    c_rx_b1 = self.other_rx_timestamps[
                        (rx_timestamp["id"], message["rx range"]["sender id"], i)
                    ]

                    c_tx_1 = self.other_tx_timestamps[
                        (rx_timestamp["id"], rx_timestamp["seq num"])
                    ]

                    b_rx_c1 = rx_timestamp["rx time"]
                    b_tx_2 = message["rx range"]["tx time"]

                    b_tx_1 = self.other_tx_timestamps[
                        (message["rx range"]["sender id"], i)
                    ]
                except KeyError:
                    break

                r_a1 = a_rx_c1 - a_rx_b1
                r_a2 = a_rx_b2 - a_rx_c1
                t_rB = b_rx_c1 - b_tx_1
                t_dB = b_tx_2 - b_rx_c1
                t_dC = c_tx_1 - c_rx_b1

                estimated_clock_drift_ab = (a_rx_b2 - a_rx_b1) / (b_tx_2 - b_tx_1)

                if (
                    message["rx range"]["sender id"],
                    rx_timestamp["id"],
                ) not in self.passive_ranging_distances.keys():
                    self.passive_ranging_distances[
                        message["rx range"]["sender id"], rx_timestamp["id"]
                    ] = []
                self.passive_ranging_distances[
                    message["rx range"]["sender id"], rx_timestamp["id"]
                ].append((r_a1 - t_dC - r_a2 + t_dB) / 2 / SECOND * speed_of_light)

                if (
                    message["rx range"]["sender id"],
                    rx_timestamp["id"],
                ) not in self.passive_ranging_distances_adjusted.keys():
                    self.passive_ranging_distances_adjusted[
                        message["rx range"]["sender id"], rx_timestamp["id"]
                    ] = []
                self.passive_ranging_distances_adjusted[
                    message["rx range"]["sender id"], rx_timestamp["id"]
                ].append(
                    (r_a2 - t_dB * estimated_clock_drift_ab) / SECOND * speed_of_light
                )

    def __eq__(self, other):
        return self.node_id == other.node_id
