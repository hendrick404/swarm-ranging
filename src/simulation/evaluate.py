import json
from statistics import stdev
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple
from scipy.constants import speed_of_light

from config import second
from node import Node

def evaluate_static(nodes: List[Node], input_file: str):
    error_dict: Dict[int, Dict[int, List[float]]] = {}
    passive_error_dict: Dict[Tuple[int, int, int], List[float]] = {}
    passive_error_dict_adjusted = {}
    passive_alternative_error_dict: Dict[Tuple[int, int, int], List[float]] = {}
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
        for (peer_id, measurements) in node.active_ranging_distances.items():
            for peer in nodes:
                if peer.node_id == peer_id:
                    real_distance = int(node.get_distance(0, peer) * 1000)
                    # if real_distance not in error_dict.keys():
                    #     error_dict[real_distance] = []
                    # error_dict[real_distance] += list(map(lambda x: int(x * 1000) - real_distance, measurements))
                    if node.node_id not in error_dict.keys():
                        error_dict[node.node_id] = {}
                    error_dict[node.node_id][peer_id] = list(map(lambda x: int(x * 1000) - real_distance, measurements))
        for B in nodes:
            for C in nodes:
                if B != C and B != node and C != node:
                    try:
                        passive_measurements = node.passive_ranging_distances[B.node_id, C.node_id]
                        real_distance_difference = (node.get_distance(0,C) - node.get_distance(0,B)) * 1000
                        
                        distance_BC = B.get_distance(0, C)
                        distance_BA = B.get_distance(0, node)
                        distance_CA = C.get_distance(0, node)
                        
                        passive_error_dict[(node.node_id, B.node_id, C.node_id)] = list(map(lambda x: int(x * 1000) - real_distance_difference, passive_measurements))
                        
                        passive_error_dict_adjusted[(node.node_id, B.node_id, C.node_id)] = list(map(lambda x: int(x(distance_BA / speed_of_light * second) * 1000) - real_distance_difference, node.passive_ranging_distances_adjusted[B.node_id, C.node_id]))

                        passive_alternative_error_dict[(node.node_id, B.node_id, C.node_id)] = list(map(lambda x: int(x(distance_BA / speed_of_light * second) * 1000) - (distance_BC - distance_CA ) * 1000, node.passive_ranging_distances_alternative[B.node_id, C.node_id]))

                        with open("debug_file.txt","a") as out_file:
                            out_file.write(f"({node.node_id},{B.node_id},{C.node_id}): " + str(list(map(lambda x: x(distance_BA / speed_of_light * second), node.passive_ranging_distances_alternative[B.node_id, C.node_id]))) + "\n")
                                # out_file.write("(1,3,2): " + str(passive_alternative_error_dict[(1,3,2)]) + "\n\n")
                                # out_file.write("(2,1,3): " + str(passive_alternative_error_dict[(2,1,3)]) + "\n")
                                # out_file.write("(2,3,1): " + str(passive_alternative_error_dict[(2,3,1)]) + "\n\n")
                                # out_file.write("(3,1,2): " + str(passive_alternative_error_dict[(3,1,2)]) + "\n")
                                # out_file.write("(3,2,1): " + str(passive_alternative_error_dict[(3,2,1)]) + "\n\n")
                    except KeyError:
                        pass


    with open("err_file.txt","a") as out_file:
        out_file.write(str(error_dict))
    with open("err_diff_file.txt","a") as out_file:
        out_file.write(str(passive_error_dict))
    with open("err_diff_alt_file.txt","a") as out_file:
        out_file.write(str(passive_alternative_error_dict))
    with open("err_diff_adj_file.txt","a") as out_file:
        out_file.write(str(passive_error_dict_adjusted))

    

    fig, ax = plt.subplots()
    max_deviation = 0.0
    # for err_list in error_dict.values():
    #     for err in err_list:
    #         if abs(err) > max_deviation:
    #             max_deviation = abs(err)
    # max_distance = max(error_dict.keys())

    x = []
    y = []
    yerr = []
    for (distance, err_list) in error_dict[1].items():
        x.append(distance)
        err = np.mean(err_list)
        y.append(err)
        yerr.append(stdev(err_list,err))
        if abs(err) + abs(stdev(err_list,err)) > max_deviation:
            max_deviation = abs(err) + abs(stdev(err_list,err))

    ax.errorbar(x,y, yerr, fmt="o", linewidth=2, capsize=6)
    ax.set(xlim=(0,len(x) + 2), ylim=(-2, 2))

    plt.style.use('_mpl-gallery')
    # plt.show()
    
def main():
    nodes = [Node(1,(0,0)), Node(2,(0,15)), Node(3,(15,15))]
    evaluate_static(nodes, "evaluation.txt")

if __name__ == "__main__":
    main()