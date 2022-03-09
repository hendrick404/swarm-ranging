import json
from typing import List

from node import Node

def evaluate_static(nodes: List[Node], input_file: str):
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
                    real_distance = node.get_distance(0, peer)
                    errors: List[float] = list(map(lambda x: x - real_distance, measurements))
                    print(f"Error of node {node.node_id} measuring distance to {peer.node_id}: {errors}")

def main():
    nodes = [Node(1,(0,0)), Node(2,(0,15)), Node(3,(15,15))]
    evaluate_static(nodes, "evaluation.txt")

if __name__ == "__main__":
    main()