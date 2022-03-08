"""
Simulates a scenario with a number of static nodes and some dynamic nodes. Configure
`ranging_interval`, `nodes` and `transmission_succes_rate` in the main function.
"""

import json
from random import random
from math import sqrt
from typing import Dict, Tuple, List
from scipy.constants import speed_of_light

from node import Node


second = 1_000_000_000_000


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
