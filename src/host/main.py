"""Main module"""

import json
from typing import Callable, Dict, List, Optional, Tuple

from scipy.constants import speed_of_light
from serial import Serial

from node import RealNode

evaluate: bool = True
EVALUATE_NUMBER_OF_MESSAGES = 100


# class Node:
#     def __init__(
#         self,
#         ranging_id: int,
#         serial_connection: Optional[Serial] = None,
#         distance_callback: Optional[Callable[[int, float], None]] = None,
#         distance_difference_callback: Optional[
#             Callable[[int, int, float], None]
#         ] = None,
#         distance_foreign_callback: Optional[Callable[[int, int, float], None]] = None,
#     ):
#         self.ranging_id: int = ranging_id
#         self.serial_connection: Optional[Serial] = serial_connection
#         self.distance_callback = distance_callback
#         self.distance_difference_callback = distance_difference_callback
#         self.distance_foreign_callback = distance_foreign_callback
#         self.tx_timestamps: Dict[int, int] = {}
#         self.rx_timestamps: Dict[Tuple[int, int], int] = {}
#         self.other_tx_timestamps: Dict[Tuple[int, int], int] = {}

#     def get_ranging_id(self) -> int:
#         return self.ranging_id

#     def get_serial_connection(self) -> Optional[Serial]:
#         return self.serial_connection

#     def range(self, message):
#         self.rx_timestamps[(message["sender id"], message["seq num"])] = message[
#             "rx time"
#         ]
#         self.other_tx_timestamps[(message["sender id"], message["seq num"])] = message[
#             "tx time"
#         ]
#         for timestamp in message["timestamps"]:
#             print("timestamp from " + str(timestamp["id"]))
#             if timestamp["id"] == self.ranging_id:
#                 i = message["seq num"] - 1
#                 while (message["sender id"], i) not in self.rx_timestamps.keys():
#                     i -= 1
#                     if i <= 0:
#                         print("Missing timestamp")
#                         return

#                 try:
#                     r_a = message["rx time"] - self.tx_timestamps[timestamp["seq num"]]
#                     r_b = (
#                         timestamp["rx time"]
#                         - self.other_tx_timestamps[(message["sender id"], i)]
#                     )
#                     d_a = (
#                         self.tx_timestamps[timestamp["seq num"]]
#                         - self.rx_timestamps[(message["sender id"], i)]
#                     )
#                     d_b = message["tx time"] - timestamp["rx time"]

#                     tof_dtu = (r_a * r_b - d_a * d_b) / (d_a + d_b + r_a + r_b)
#                     tof = tof_dtu * (1.0 / 499.2e6 / 128.0)
#                     distance = tof * speed_of_light
#                     sender_id = message["sender id"]
#                     if self.distance_callback:
#                         self.distance_callback(sender_id, distance)
#                     print(
#                         f"Distance from {self.ranging_id} to {sender_id} is {distance} m"
#                     )
#                 except KeyError:
#                     print("Missing timestamp")
#             else:
#                 pass  # Passive ranging

#     def tx_event(self, message):
#         self.tx_timestamps[message["seq num"]] = message["tx time"]


def main():
    """Main function. Loops forever and performs ranging."""

    connections = connect()

    eval_file = open("evaluation.txt", "a") if evaluate else None

    while True:
        for node in connections:
            connection = node.get_serial_connection()
            if connection:
                line = connection.readline()
                try:
                    json_string = str(line)
                    json_string = json_string[
                        2 : len(json_string) - 3
                    ]  # TODO: Trim dynamically
                    decoded_json = json.JSONDecoder().decode(json_string)
                    if decoded_json:
                        if evaluate:
                            eval_file.write(json_string + "\n")
                        if "rx range" in decoded_json:
                            node.evaluate_rx(decoded_json["rx range"])
                        elif "tx range" in decoded_json:
                            node.evaluate_tx(decoded_json["tx range"])
                except json.JSONDecodeError:
                    # Apparently we did not get a valid json, maybe a debug log
                    pass
                except KeyError:
                    pass


def connect() -> List[RealNode]:
    """Generates a list of connections."""
    # Home
    connections = [
        RealNode(1, Serial("/dev/tty.usbmodem0007601185891", 115200, timeout=1)),
        RealNode(2, Serial("/dev/tty.usbmodem0007601197931", 115200, timeout=1)),
        RealNode(3, Serial("/dev/tty.usbmodem0007601194831", 115200, timeout=1)),
    ]

    # # Lab
    # connections = [
    #     Node(4, Serial("/dev/tty.usbmodem0007601194661", 115200, timeout=1)),
    #     Node(5, Serial("/dev/tty.usbmodem0007601202211", 115200, timeout=1)),
    #     Node(6, Serial("/dev/tty.usbmodem0007601195171", 115200, timeout=1)),
    # ]

    return connections


if __name__ == "__main__":
    main()
