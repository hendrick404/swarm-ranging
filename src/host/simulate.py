import json
from math import sqrt
from scipy.constants import speed_of_light

class Node:
    def __init__(self, id, pos, clock_err = 1, clock_offset = 0):
        self.id = id
        self.pos = pos
        self.clock_err = clock_err
        self.clock_offset = clock_offset
        self.sequence_number = 1
        self.receive_timestamps: Dict[Int, Tuple[Int, Int]] = {}

    def get_pos(self):
        return self.pos

    def tx(self, global_time):
        json_obj = {"id": self.id, "tx range": {"seq num": self.sequence_number, "tx time": int(global_time * self.clock_err + self.clock_offset)}}
        self.sequence_number += 1
        return (json_obj, self.receive_timestamps)

    def rx(self, global_time, message, pos, receive_timestamps):
        rx_time = (global_time + (sqrt((self.pos[0] - pos[0]) ** 2 + (self.pos[1] + pos[1]) ** 2) / (speed_of_light / 1_000_000_000_000))) * self.clock_err + self.clock_offset
        self.receive_timestamps[message["id"]] = (message["tx range"]["seq num"], int(rx_time))
        rx_timestamps = []
        for (id, (seq_num, rx_time)) in receive_timestamps.items():
            rx_timestamps.append({"id": id, "seq num": seq_num, "rx time": rx_time})
        json_obj = {"id": self.id, "rx range": {"sender id": message["id"], "seq num": message["tx range"]["seq num"], "tx time": message["tx range"]["tx time"], "rx time": int(rx_time), "timestamps": rx_timestamps}}
        return json_obj

    def __eq__(self, other):
        return self.id == other.id

def main():
    eval_file = open("evaluation_simulated.txt", "a")
    exchange_counter = 1
    ranging_interval = 1_000_000_000_000
    global_clock = 0
    nodes: List[Node] = [Node(1,(0,0)), Node(2,(60,0))]
    while exchange_counter <= 100 * len(nodes):
        for tx_node in nodes:
            global_clock += ranging_interval / len(nodes)
            (tx_message, receive_timestamps) = tx_node.tx(global_clock)
            eval_file.write(json.JSONEncoder().encode(tx_message) + "\n")
            for rx_node in nodes:
                if rx_node != tx_node:
                    rx_message = rx_node.rx(global_clock, tx_message, tx_node.get_pos(), receive_timestamps)
                    eval_file.write(json.JSONEncoder().encode(rx_message) + "\n")
        exchange_counter += 1


    




if __name__ == "__main__":
    main()