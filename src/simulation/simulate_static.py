"""
Simulates a scenario with a number of static nodes. Configure `ranging_interval`,
`nodes` and `transmission_succes_rate` in the main function.
"""

import json
from random import random
from math import sqrt
from typing import Dict, Tuple, List
from scipy.constants import speed_of_light

from node import Node


second = 1_000_000_000_000

def simulate(nodes: List[Node], ranging_interval: int, exchanges: int, transmission_success_rate: float, output_file: str = "evaluation.txt"):
    with open(output_file, "a") as eval_file:
        exchange_counter = 1
        global_clock: int = 0
        transmission_success_rate = 0.95
        while exchange_counter <= exchanges * len(nodes):
            for tx_node in nodes:
                global_clock += int(ranging_interval / len(nodes))
                (tx_message, receive_timestamps, pos) = tx_node.tx(global_clock)
                eval_file.write(json.JSONEncoder().encode(tx_message) + "\n")
                for rx_node in nodes:
                    if rx_node != tx_node and random() <= transmission_success_rate:
                        rx_message = rx_node.rx(
                            global_clock,
                            tx_message,
                            pos,
                            receive_timestamps,
                        )
                        eval_file.write(json.JSONEncoder().encode(rx_message) + "\n")
            exchange_counter += 1


def main():
    simulate([Node(1, (0, 0)), Node(2, (60, 0))], 1 * second, 4, 0.95, "evaluation_simulated.txt")


if __name__ == "__main__":
    main()
