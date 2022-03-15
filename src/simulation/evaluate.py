import json
from statistics import stdev
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple

from node import Node

def evaluate_static(nodes: List[Node], input_file: str):
    error_dict: Dict[int, List[float]] = {}
    passive_error_dict: Dict[Tuple[int, int], List[float]] = {}
    with open(input_file, "r") as eval_file:
        for line in eval_file.readlines():
            message = json.JSONDecoder().decode(line)
            for node in nodes:
                if node.node_id == message["id"]:
                    if "tx range" in message.keys():
                        node.evaluate_tx(message)
                    elif "rx range" in message.keys():
                        node.evaluate_rx(message)

    for node in nodes:
        print(str(node.passive_ranging_distances))
        for (peer_id, measurements) in node.active_ranging_distances.items():
            for peer in nodes:
                if peer.node_id == peer_id:
                    real_distance = int(node.get_distance(0, peer) * 1000)
                    if real_distance not in error_dict.keys():
                        error_dict[real_distance] = []
                    error_dict[real_distance] += list(map(lambda x: int(x * 1000) - real_distance, measurements))
        for B in nodes:
            for C in nodes:
                if B != C and B != node and C != node:
                    try:
                        passive_measurements = node.passive_ranging_distances[B.node_id, C.node_id]
                        real_distance_difference = (node.get_distance(0, C) - node.get_distance(0,B))* 1000
                        passive_error_dict[(B.node_id, C.node_id)] = list(map(lambda x: int(x * 1000) - real_distance_difference, passive_measurements))
                    except KeyError:
                        pass


    with open("err_file.txt","a") as out_file:
        out_file.write(str(error_dict))
    with open("err_diff_file.txt","a") as out_file:
        out_file.write(str(passive_error_dict))

    fig, ax = plt.subplots()
    max_deviation = 0.0
    for err_list in error_dict.values():
        for err in err_list:
            if abs(err) > max_deviation:
                max_deviation = abs(err)
    max_distance = max(error_dict.keys())

    x = []
    y = []
    yerr = []
    for (distance, err_list) in error_dict.items():
        x.append(distance)
        err = np.mean(err_list)
        y.append(err)
        yerr.append(stdev(err_list,err))

    ax.errorbar(x,y, yerr, fmt="o", linewidth=2, capsize=6)
    ax.set(xlim=(0,int(max_distance*1.1)), ylim=(-max_deviation, max_deviation))

    plt.style.use('_mpl-gallery')
    plt.show()
    
def main():
    nodes = [Node(1,(0,0)), Node(2,(0,15)), Node(3,(15,15))]
    evaluate_static(nodes, "evaluation.txt")

if __name__ == "__main__":
    main()