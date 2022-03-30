import json
import os
from statistics import stdev
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple

from node import SimulationNode


def evaluate_static(nodes: List[SimulationNode], input_file: str, graph_name: str = "graphs"):
    error_dict: Dict[int, Dict[int, List[float]]] = {}
    passive_error_dict: Dict[Tuple[int, int, int], List[float]] = {}
    passive_error_dict_adjusted = {}
    with open(os.path.join("evaluation", input_file), "r") as eval_file:
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
        for B in nodes:
            for C in nodes:
                if B != C and B != node and C != node:
                    try:        
                        real_distance_difference = node.get_distance(
                            0, C
                        ) - node.get_distance(0, B)


                        passive_error_dict_adjusted[
                            (node.node_id, B.node_id, C.node_id)
                        ] = list(
                            map(
                                lambda x: x
                                - B.get_distance(0, C)
                                + real_distance_difference,
                                node.passive_ranging_distances_adjusted[
                                    B.node_id, C.node_id
                                ],
                            )
                        )
                    except KeyError:
                        pass

    # with open("err_file.txt","a") as out_file:
    #     out_file.write(str(error_dict))
    # with open("err_diff_file.txt","a") as out_file:
    #     out_file.write(str(passive_error_dict))
    # with open("err_diff_alt_file.txt","a") as out_file:
    #     out_file.write(str(passive_alternative_error_dict))
    # with open("err_diff_adj_file.txt","a") as out_file:
    #     out_file.write(str(passive_error_dict_adjusted))

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

    _, ax_passive = plt.subplots()
    ax_passive.set_xlabel("node id")
    ax_passive.set_ylabel("deviation from real distance in km")
    x_passive = []
    y_passive = []
    yerr_passive = []
    for ((a, b, c), err_list) in passive_error_dict.items():
        if a == 1 and b == 4:
            x_passive.append(c)
            err = np.mean(err_list)
            y_passive.append(err / 1000)
            yerr_passive.append(stdev(err_list, err) / 1000)

    ax_passive.errorbar(
        x_passive, y_passive, yerr_passive, fmt="o", linewidth=2, capsize=6
    )
    ax_passive.set(xlim=(0, 13))

    plt.savefig(
        os.path.join("evaluation", f"graph_{graph_name}_passive_not_adjusted.pdf"),
        format="pdf",
        transparent=True,
    )

    ax_passive_adj = {}
    x_passive_adj = {}
    y_passive_adj = {}
    yerr_passive_adj = {}
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
    nodes = [Node(1, (0, 0)), Node(2, (0, 15)), Node(3, (15, 15))]
    evaluate_static(nodes, "evaluation.txt")


if __name__ == "__main__":
    main()
