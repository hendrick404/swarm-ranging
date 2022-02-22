"""Main module"""

import json
from typing import Callable, Dict, List, Optional

from scipy.constants import speed_of_light
from serial import Serial

evaluate: bool = True
evaluate_number_of_messages = 100


class Node:
    def __init__(
        self,
        ranging_id: int,
        serial_connection: Optional[Serial] = None,
        distance_callback: Callable[[int, float], None] = None,
        distance_difference_callback: Callable[[int, int, float], None] = None,
        distance_foreign_callback: Callable[[int, int, float], None] = None,
    ):
        self.ranging_id: int = ranging_id
        self.serial_connection: Optional[Serial] = serial_connection
        self.distance_callback = distance_callback
        self.distance_difference_callback = distance_difference_callback
        self.distance_foreign_callback = distance_foreign_callback
        self.tx_timestamps: Dict[int, int] = {}

    def get_ranging_id(self) -> int:
        return self.ranging_id

    def get_serial_connection(self) -> Optional[Serial]:
        return self.serial_connection

    def range(self, message):
        for timestamp in message["timestamps"]:
            print("timestamp from " + str(timestamp["id"]))
            if timestamp["id"] == self.ranging_id:
                try:
                    tof_dtu = ((message["rx time"] - self.tx_timestamps[timestamp["seq num"]]) - (message["tx time"] - timestamp["rx time"])) / 2
                    tof = tof_dtu * (1.0 / 499.2e6 / 128.0)
                    distance = tof * speed_of_light
                    sender_id = message["sender id"]
                    if self.distance_callback:
                        self.distance_callback(sender_id, distance)
                    print(
                        f"Distance from {self.ranging_id} to {sender_id} is {distance} m"
                    )
                except KeyError:
                    print("Missing tx timestamp")
            else:
                pass  # Passive ranging

    def tx_event(self, message):
        self.tx_timestamps[message["seq num"]] = message["tx time"]


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
                    # TODO: Trim dynamically
                    json_string = json_string[2 : len(json_string) - 3]
                    decoded_json = json.JSONDecoder().decode(json_string)
                    if decoded_json:
                        if evaluate:
                            eval_file.write(json_string + "\n")
                        if "rx range" in decoded_json:
                            node.range(decoded_json["rx range"])
                        elif "tx range" in decoded_json:
                            node.tx_event(decoded_json["tx range"])
                except json.JSONDecodeError:
                    # Apparently we did not get a valid json, maybe a debug log
                    pass
                except KeyError:
                    pass


def connect() -> List[Node]:
    """Generates a list of connections."""
    # # Home
    # connections = [
    #     Node(1, Serial("/dev/tty.usbmodem0007601185891", 115200, timeout=1)),
    #     Node(2, Serial("/dev/tty.usbmodem0007601197931", 115200, timeout=1)),
    #     Node(3, Serial("/dev/tty.usbmodem0007601194831", 115200, timeout=1)),
    # ]

    # Lab
    connections = [
        Node(4, Serial("/dev/tty.usbmodem0007601194661", 115200, timeout=1)),
        Node(5, Serial("/dev/tty.usbmodem0007601202211", 115200, timeout=1)),
        Node(6, Serial("/dev/tty.usbmodem0007601195171", 115200, timeout=1)),
    ]

    return connections


if __name__ == "__main__":
    main()
