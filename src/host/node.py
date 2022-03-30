from math import sqrt
from typing import Dict, Optional, Tuple, List, Callable
from scipy.constants import speed_of_light
from serial import Serial

# from config import self.second


class Node:
    def __init__(self, node_id: int):
        self.node_id = node_id
        # self.sequence_number = 1
        self.second = 1_000_000_000_000

        self.tx_ts: Dict[int, int] = {}
        self.rx_ts: Dict[Tuple[int, int], int] = {}
        self.other_tx_ts: Dict[Tuple[int, int], int] = {}
        self.other_rx_ts: Dict[Tuple[int, int, int], int] = {}

        self.active_ranging_distances: Dict[int, List[float]] = {}
        self.passive_ranging_distances_adjusted: Dict[Tuple[int, int], List[float]] = {}

    def set_timeunit(self, second: int):
        self.second = second

    def get_timeunit(self) -> int:
        return self.second

    def get_stored_rx_timestamp(
        self, sender_id: int, receiver_id: int, seq_num: int
    ) -> Optional[Tuple[int, int]]:
        i = seq_num - 1
        if receiver_id == self.node_id:
            while (sender_id, i) not in self.rx_ts.keys():
                i -= 1
                if i < 0:
                    return None

            return (i, self.rx_ts[sender_id, i])
        else:
            while (sender_id, receiver_id, i) not in self.other_rx_ts.keys():
                i -= 1
                if i < 0:
                    return None
            return (i, self.other_rx_ts[(sender_id, receiver_id, i)])

    def get_stored_tx_timestamp(
        self, sender_id: int, seq_num: int
    ) -> Optional[Tuple[int, int]]:
        i = seq_num - 1
        if sender_id == self.node_id:
            while i not in self.tx_ts.keys():
                i -= 1
                if i < 0:
                    return None

            return (i, self.rx_ts[(i, sender_id)])
        else:
            while (sender_id, i) not in self.other_tx_ts.keys():
                i -= 1
                if i < 0:
                    return None
            return (i, self.other_tx_ts[(sender_id, i)])

    def evaluate_tx(self, message: Dict):
        assert (
            message["id"] == self.node_id
        ), "We only want to process information created at our own end"

        self.tx_ts[message["tx range"]["seq num"]] = message["tx range"]["tx time"]

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

        self.other_tx_ts[b_id, m_3_s] = message["rx range"]["tx time"]
        self.rx_ts[b_id, m_3_s] = message["rx range"]["rx time"]

        for rx_timestamp in message["rx range"]["timestamps"]:
            self.other_rx_ts[b_id, rx_timestamp["id"], rx_timestamp["seq num"]] = rx_timestamp["rx time"]
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

                r_a = self.rx_ts[b_id, m_3_s] - self.tx_ts[m_2_s]
                r_b = self.other_rx_ts[b_id, a_id, m_2_s] - self.other_tx_ts[b_id, m_1_s]

                d_a = self.tx_ts[m_2_s] - self.rx_ts[b_id, m_1_s]
                d_b = self.other_tx_ts[b_id, m_3_s] - self.other_rx_ts[b_id, a_id, m_2_s]
                

                if b_id not in self.active_ranging_distances:
                    self.active_ranging_distances[b_id] = []
                # Alternative DS-TWR (Neirynck et al. 2016)
                tof = (r_a * r_b - d_a * d_b) / (r_a + r_b + d_a + d_b)
                self.active_ranging_distances[message["rx range"]["sender id"]].append(
                    (tof / self.second) * speed_of_light
                )
            else:
                # Passive Ranging
                c_id = rx_timestamp["id"]

                # Sequence numbers
                # M_{C,1}: C -> A,B
                m_2_s = rx_timestamp["seq num"]
                # M_{B,2}: B -> A,C
                m_3_s = message["rx range"]["seq num"]
                # M_{B,1}: B -> A,C
                m_1 = self.get_stored_rx_timestamp(b_id, a_id, m_3_s)
                if m_1:
                    (m_1_s, _) = m_1
                else:
                    print("Missing timestamp")
                    break  # We don't have the right timestamp yet

                try:
                    a_rx_b1 = self.rx_ts[b_id, m_1_s]

                    a_rx_c1 = self.rx_ts[c_id, m_2_s]

                    a_rx_b2 = message["rx range"]["rx time"]

                    b_rx_c1 = rx_timestamp["rx time"]
                    b_tx_2 = message["rx range"]["tx time"]

                    b_tx_1 = self.other_tx_ts[b_id, m_1_s]
                except KeyError:
                    print("Missing timestamp")
                    break

                r_a2 = a_rx_b2 - a_rx_c1
                t_dB = b_tx_2 - b_rx_c1

                estimated_clock_drift_ab = (a_rx_b2 - a_rx_b1) / (b_tx_2 - b_tx_1)

                if (b_id, c_id) not in self.passive_ranging_distances_adjusted.keys():
                    self.passive_ranging_distances_adjusted[b_id, c_id ] = []
                self.passive_ranging_distances_adjusted[b_id, c_id].append(
                    (r_a2 - t_dB * estimated_clock_drift_ab) / self.second * speed_of_light
                )

    def __eq__(self, other):
        return self.node_id == other.node_id


class SimulationNode(Node):
    def __init__(self, node_id: int, pos, clock_err: float = 1, clock_offset: int = 0):
        self.node_id = node_id
        self.pos = pos
        self.clock_err = clock_err
        self.clock_offset = clock_offset
        self.sequence_number = 1
        self.receive_timestamps: Dict[int, Tuple[int, int]] = {}

        self.tx_ts: Dict[int, int] = {}
        self.rx_ts: Dict[Tuple[int, int], int] = {}
        self.other_tx_ts: Dict[Tuple[int, int], int] = {}
        self.other_rx_ts: Dict[Tuple[int, int, int], int] = {}

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
                / (speed_of_light / self.second)
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


class RealNode(Node):
    def __init__(self, node_id: int, serial_connection: Serial):
        self.node_id = node_id

        self.serial_connection = serial_connection

        self.tx_ts: Dict[int, int] = {}
        self.rx_ts: Dict[Tuple[int, int], int] = {}
        self.other_tx_ts: Dict[Tuple[int, int], int] = {}
        self.other_rx_ts: Dict[Tuple[int, int, int], int] = {}

        self.active_ranging_distances: Dict[int, List[float]] = {}
        self.passive_ranging_distances: Dict[Tuple[int, int], List[float]] = {}
        self.passive_ranging_distances_adjusted: Dict[Tuple[int, int], List[float]] = {}

    def get_serial_connection(self) -> Serial:
        return self.serial_connection
