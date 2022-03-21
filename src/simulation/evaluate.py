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
                    real_distance = int(node.get_distance(0, peer) )
                    # if real_distance not in error_dict.keys():
                    #     error_dict[real_distance] = []
                    # error_dict[real_distance] += list(map(lambda x: int(x * 1000) - real_distance, measurements))
                    if node.node_id not in error_dict.keys():
                        error_dict[node.node_id] = {}
                    error_dict[node.node_id][peer_id] = list(map(lambda x: int(x ) - real_distance, measurements))
        for B in nodes:
            for C in nodes:
                if B != C and B != node and C != node:
                    try:
                        passive_measurements = node.passive_ranging_distances[B.node_id, C.node_id]
                        real_distance_difference = (node.get_distance(0,C) - node.get_distance(0,B))
                        
                        distance_BC = B.get_distance(0, C)
                        distance_BA = B.get_distance(0, node)
                        distance_CA = C.get_distance(0, node)
                        
                        passive_error_dict[(node.node_id, B.node_id, C.node_id)] = list(map(lambda x: int(x ) - real_distance_difference, passive_measurements))
                        
                        passive_error_dict_adjusted[(node.node_id, B.node_id, C.node_id)] = list(map(lambda x: int(x(distance_BC / speed_of_light * second)) - real_distance_difference, node.passive_ranging_distances_adjusted[B.node_id, C.node_id]))

                        passive_alternative_error_dict[(node.node_id, B.node_id, C.node_id)] = list(map(lambda x: int(x(distance_BA / speed_of_light * second)) - (distance_BC - distance_CA ), node.passive_ranging_distances_alternative[B.node_id, C.node_id]))

                        with open("debug_file.txt","a") as out_file:
                            out_file.write(f"({node.node_id},{B.node_id},{C.node_id}): " + str(list(map(lambda x: x(distance_BA / speed_of_light * second), node.passive_ranging_distances_alternative[B.node_id, C.node_id]))) + "\n")
                                # out_file.write("(1,3,2): " + str(passive_alternative_error_dict[(1,3,2)]) + "\n\n")
                                # out_file.write("(2,1,3): " + str(passive_alternative_error_dict[(2,1,3)]) + "\n")
                                # out_file.write("(2,3,1): " + str(passive_alternative_error_dict[(2,3,1)]) + "\n\n")
                                # out_file.write("(3,1,2): " + str(passive_alternative_error_dict[(3,1,2)]) + "\n")
                                # out_file.write("(3,2,1): " + str(passive_alternative_error_dict[(3,2,1)]) + "\n\n")
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

    

    fig_active, ax_active = plt.subplots()
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

    ax_active.errorbar(x,y, yerr, fmt="o", linewidth=2, capsize=6)
    ax_active.set(xlim=(0,len(x) + 2), ylim=(-2, 2))

    fig_passive, ax_passive = plt.subplots()
    x_passive = []
    y_passive = []
    yerr_passive = []
    for ((a,b,c), err_list) in passive_error_dict.items():
        if a == 1 and b == 4:
            x_passive.append(c)
            err = np.mean(err_list)
            y_passive.append(err / 1000)
            yerr_passive.append(stdev(err_list,err) / 1000)
            if abs(err) + abs(stdev(err_list,err)) > max_deviation:
                max_deviation = abs(err) + abs(stdev(err_list,err))

    ax_passive.errorbar(x_passive, y_passive, yerr_passive, fmt="o", linewidth=2, capsize=6)
    ax_passive.set(xlim=(0,len(x_passive) + 2), ylim=(-2, 2))

    ax_passive_adj = {}
    x_passive_adj = {}
    y_passive_adj = {}
    yerr_passive_adj = {}
    for i in range(2,13):
            _, ax_passive_adj[i] =  plt.subplots()
            x_passive_adj[i] = []
            y_passive_adj[i] = []
            yerr_passive_adj[i] = []

    
    for ((a,b,c), err_list) in passive_error_dict_adjusted.items():
        if a == 1:
            x_passive_adj[b].append(c)
            err = np.mean(err_list)
            y_passive_adj[b].append(err)
            yerr_passive_adj[b].append(stdev(err_list,err))
            if abs(err) + abs(stdev(err_list,err)) > max_deviation:
                max_deviation = abs(err) + abs(stdev(err_list,err))
    for i in range(2,13):
            ax_passive_adj[i].errorbar(x_passive_adj[i], y_passive_adj[i], yerr_passive_adj[i], fmt="o", linewidth=2, capsize=6)
            ax_passive_adj[i].set(xlim=(0,len(x_passive_adj) + 2), ylim=(-2, 2))

    plt.style.use('_mpl-gallery')
    plt.show()
    
def main():
    nodes = [Node(1,(0,0)), Node(2,(0,15)), Node(3,(15,15))]
    evaluate_static(nodes, "evaluation.txt")

if __name__ == "__main__":
    main()