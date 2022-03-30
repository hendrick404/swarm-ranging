import json
import os
from statistics import stdev
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple

from node import SimulationNode


def evaluate_static(
    nodes: List[SimulationNode], input_file: str, graph_name: str = "graphs"
):
    error_dict: Dict[int, Dict[int, List[float]]] = {}
    passive_error_dict: Dict[Tuple[int, int, int], List[float]] = {}
    passive_error_dict_adjusted = {}
    with open(os.path.join("evaluation", input_file), "r", encoding="UTF-8") as eval_file:
        for line in eval_file.readlines():
            message = json.JSONDecoder().decode(line)
            for node in nodes:
                if node.node_id == message["id"]:
                    if "tx range" in message.keys():
                        node.evaluate_tx(message)
                    elif "rx range" in message.keys():
                        node.evaluate_rx(message)

    for node in nodes:
        for (peer_id, measurements) in node.active_ranging_distances.items():
            for peer in nodes:
                if peer.node_id == peer_id:
                    real_distance = node.get_distance(0, peer)
                    if node.node_id not in error_dict.keys():
                        error_dict[node.node_id] = {}
                    error_dict[node.node_id][peer_id] = list(
                        map(lambda x: x - real_distance, measurements)
                    )
        for node_b in nodes:
            for node_c in nodes:
                if node_b != node_c and node_b != node and node_c != node:
                    try:
                        real_distance_difference = node.get_distance(
                            0, node_c
                        ) - node.get_distance(0, node_b)

                        passive_error_dict_adjusted[
                            (node.node_id, node_b.node_id, node_c.node_id)
                        ] = list(
                            map(
                                lambda x: x
                                - node_b.get_distance(0, node_c)
                                + real_distance_difference,
                                node.passive_ranging_distances_adjusted[
                                    node_b.node_id, node_c.node_id
                                ],
                            )
                        )
                    except KeyError:
                        pass

    with open(os.path.join("evalutation", "err_file.txt"), "a", encoding="UTF-8") as out_file:
        out_file.write(str(error_dict))
    with open(os.path.join("evalutation", "err_diff_file.txt"), "a", encoding="UTF-8") as out_file:
        out_file.write(str(passive_error_dict))
    with open(os.path.join("evalutation", "err_diff_adj_file.txt"), "a", encoding="UTF-8") as out_file:
        out_file.write(str(passive_error_dict_adjusted))

    _, ax_active = plt.subplots()
    ax_active.set_xlabel("node id")
    ax_active.set_ylabel("deviation from real distance in mm")

    x = []
    y = []
    yerr = []
    for (distance, err_list) in error_dict[1].items():
        x.append(distance)
        err = np.mean(err_list)
        y.append(err * 1000)
        yerr.append(stdev(err_list, err) * 1000)

    ax_active.errorbar(x, y, yerr, fmt="o", linewidth=2, capsize=6)
    ax_active.set(xlim=(0, 13))
    plt.savefig(
        os.path.join("evaluation", f"graph_{graph_name}_active.pdf"),
        format="pdf",
        transparent=True,
    )

    ax_passive_adj = {}
    x_passive_adj: Dict[int, List[float]] = {}
    y_passive_adj: Dict[int, List[float]] = {}
    yerr_passive_adj: Dict[int, List[float]] = {}
    for i in range(2, 13):
        if i == 4:
            _, ax_passive_adj[i] = plt.subplots()
            ax_passive_adj[i].set_xlabel("node id")
            ax_passive_adj[i].set_ylabel("deviation from real distance in mm")
            x_passive_adj[i] = []
            y_passive_adj[i] = []
            yerr_passive_adj[i] = []

    for ((a, b, c), err_list) in passive_error_dict_adjusted.items():
        if a == 1 and b == 4:
            if len(err_list) < 10:
                print("Small error list for nodes {a} and {b}: {err_list}")
            x_passive_adj[b].append(c)
            err = np.mean(err_list)
            y_passive_adj[b].append(err * 1000)
            yerr_passive_adj[b].append(stdev(err_list, err) * 1000)

    for i in range(2, 13):
        if i == 4:
            ax_passive_adj[i].errorbar(
                x_passive_adj[i],
                y_passive_adj[i],
                yerr_passive_adj[i],
                fmt="o",
                linewidth=2,
                capsize=6,
            )
            ax_passive_adj[i].set(xlim=(0, 13))

            plt.savefig(
                os.path.join("evaluation", f"graph_{graph_name}_passive.pdf"),
                format="pdf",
                transparent=True,
            )


def main():
    nodes = [
        SimulationNode(1, (0, 0)),
        SimulationNode(2, (0, 15)),
        SimulationNode(3, (15, 15)),
    ]
    evaluate_static(nodes, "evaluation.txt")


if __name__ == "__main__":
    main()
