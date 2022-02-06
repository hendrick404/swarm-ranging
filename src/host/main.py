"""Main module"""

import json
from typing import Dict, List, Optional, Tuple

from serial import Serial
import scipy as sc


class Node:
    def __init__(self, ranging_id: int, serial_connection: Optional[Serial] = None):
        self.ranging_id: int = ranging_id
        self.serial_connection: Optional[Serial] = serial_connection
        self.distance: Optional[float] = None
        self.tx_timestamps: Dict[int, int] = {}

    def get_ranging_id(self) -> int:
        return self.ranging_id

    def get_serial_connection(self) -> Optional[Serial]:
        return self.serial_connection

    def set_distance(self, distance: float):
        self.distance = distance

    def get_distance(self) -> Optional[float]:
        return self.distance

    def range(self, message):
        for timestamp in message["timestamps"]:
            if timestamp["node id"] == self.ranging_id:
                try:
                    distance = (
                        message["rx time"]
                        - self.tx_timestamps[timestamp["sequence number"]]
                    ) - (
                        message["tx time"] - timestamp["rx time"]
                    ) / 2 * sc.speed_of_light
                    sender_id = message["sender id"]
                    print(f"Distance to {sender_id} is {distance}")
                except KeyError:
                    print("Missing tx timestamp")
            else:
                pass  # Passive ranging

    def tx_event(self, message):
        assert message["node id"] == self.ranging_id
        self.tx_timestamps[message["sequence number"]] = message["tx time"]


connections: List[Node] = []
known_peers: List[Node] = []


def main():
    """Main function. Loops forever and performs ranging."""
    global connections, known_peers

    connections = connect()
    known_peers = connect()

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
                        # print(decoded_json)
                        if "rx range" in decoded_json:
                            print("RX Event")
                            node.range(decoded_json["rx range"])
                        if "tx range" in decoded_json:
                            node.tx_event(decoded_json["tx range"])
                            print("TX Event")
                except json.JSONDecodeError:
                    # Apparently we did not get a valid json, maybe a debug log
                    pass
                except KeyError:
                    pass


def connect() -> List[Node]:
    """Generates a list of connections."""
    connections = [
        Node(1, Serial("/dev/tty.usbmodem0007601185891", 115200, timeout=1)),
        Node(2, Serial("/dev/tty.usbmodem0007601197931", 115200, timeout=1)),
        Node(3, Serial("/dev/tty.usbmodem0007601194831", 115200, timeout=1)),
    ]

    return connections


if __name__ == "__main__":
    main()
