"""
Simulates a scenario with a number of static nodes. Configure `ranging_interval`,
`nodes` and `transmission_succes_rate` in the main function.
"""

import json
import os
from random import random, uniform
from math import sin, cos, pi
from typing import List

from config import SECOND
from node import Node
from evaluate import evaluate_static


def simulate(
    nodes: List[Node],
    ranging_interval: int,
    exchanges: int,
    transmission_success_rate: float,
    output_file: str = "evaluation.txt",
):
    if not os.path.exists("evaluation"):
        os.mkdir("evaluation")
    with open(os.path.join("evaluation", output_file), "a", encoding="UTF-8") as eval_file:
        exchange_counter = 1
        global_clock: int = 0
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
    simulate(
        [Node(1, (0, 0)), Node(2, (60, 0))],
        1 * SECOND,
        100,
        0.95,
        "evaluation_small.txt",
    )
    circle_size = 12
    max_clock_error = 20 / 1_000_000
    nodes = []
    for i in range(1, circle_size + 1):
        nodes.append(
            Node(
                i,
                (sin(i * (2 * pi / circle_size)), cos(i * (2 * pi / circle_size))),
                clock_offset=int(uniform(0, SECOND)),
                clock_err=uniform(1 - max_clock_error, 1 + max_clock_error),
            )
        )
    simulate(nodes, 1 * SECOND, 100, 1, "evaluation_circle.txt")
    evaluate_static(nodes, "evaluation_circle.txt")


if __name__ == "__main__":
    main()
