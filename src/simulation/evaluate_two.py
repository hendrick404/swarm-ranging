import json
from typing import List, Tuple

from scipy.constants import speed_of_light

# time_units = (1.0 / 499.2e6 / 128.0)
time_units = 1 / 1_000_000_000_000


def main():
    # The ids of the peers
    peer1 = 1
    peer2 = 2
    # The distance in meters
    distance = 0.6

    peer1_transmissions: List[Tuple[int, int]] = []
    peer2_transmissions: List[Tuple[int, int]] = []

    peer1_distance_measurements: List[float] = []
    peer2_distance_measurements: List[float] = []

    eval_file = open("evaluation_simulated.txt", "r")
    lines = eval_file.readlines()
    for line in lines:
        operation = json.JSONDecoder().decode(line)
        if operation["id"] == peer1:
            if "tx range" in operation.keys():
                peer1_transmissions.append(
                    (operation["tx range"]["seq num"], operation["tx range"]["tx time"])
                )
            elif "rx range" in operation.keys():
                for rx_timestamp in operation["rx range"]["timestamps"]:
                    if rx_timestamp["id"] == peer1:
                        for (seq_num, tx_a) in peer1_transmissions:
                            if seq_num == rx_timestamp["seq num"]:
                                rx_a = operation["rx range"]["rx time"]
                                tx_b = operation["rx range"]["tx time"]
                                rx_b = rx_timestamp["rx time"]
                                (newest_seq_num, _) = peer1_transmissions[-1]
                                if (
                                    rx_a > tx_a
                                    and tx_b > rx_b
                                    and newest_seq_num - seq_num < 3
                                ):
                                    peer1_distance_measurements.append(
                                        measure_distance(tx_a, rx_a, tx_b, rx_b)
                                    )
        elif operation["id"] == peer2:
            if "tx range" in operation.keys():
                peer2_transmissions.append(
                    (operation["tx range"]["seq num"], operation["tx range"]["tx time"])
                )
            elif "rx range" in operation.keys():
                for rx_timestamp in operation["rx range"]["timestamps"]:
                    if rx_timestamp["id"] == peer2:
                        for (seq_num, tx_a) in peer2_transmissions:
                            if seq_num == rx_timestamp["seq num"]:
                                rx_a = operation["rx range"]["rx time"]
                                tx_b = operation["rx range"]["tx time"]
                                rx_b = rx_timestamp["rx time"]
                                (newest_seq_num, _) = peer1_transmissions[-1]
                                if (
                                    rx_a > tx_a
                                    and tx_b > rx_b
                                    and newest_seq_num - seq_num < 3
                                ):
                                    peer2_distance_measurements.append(
                                        measure_distance(tx_a, rx_a, tx_b, rx_b)
                                    )
    print(peer1_distance_measurements)
    print(peer2_distance_measurements)


def measure_distance(tx_a, rx_a, tx_b, rx_b):
    return ((rx_a - tx_a) - (tx_b - rx_b)) / 2 * time_units * speed_of_light


if __name__ == "__main__":
    main()
