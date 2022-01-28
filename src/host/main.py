"""Main module"""

import json
from typing import List, Optional, Tuple

from serial import Serial, SerialException


class Node:
    def __init__(self, id: int, serial_connection: Optional[Serial] = None):
        self.id = id
        self.serial_connection = serial_connection

    def set_distance(self, distance: float):
        self.distance = distance

    def get_distance(self) -> float:
        return self.distance

    def get_serial_connection(self) -> Optional[Serial]:
        return self.serial_connection

    def get_id(self) -> int:
        return self.id


def main():
    """Main function. Loops forever and performs ranging."""

    connections: List[Node] = connect()
    known_peers: List[Node] = []

    while True:
        for node in connections:
            connection = node.get_serial_connection()
            if connection:
                line = connection.readline()
                try:
                    json_string = str(line)
                    json_string = json_string[2 : len(json_string) - 3]  # TODO
                    decoded_json = json.JSONDecoder().decode(json_string)
                    if decoded_json:
                        try:
                            sender_id = decoded_json["range"]["sender_id"]
                            print("Received message from " + str(sender_id))
                        except KeyError:
                            pass
                except json.JSONDecodeError:
                    pass  # Apparently we did not get a valid json


def range_next() -> Optional[Tuple[Node, Node]]:
    return (Node(1), Node(2))


def connect() -> List[Node]:
    """Generates a list of connections."""
    connections = []
    connections.append(Node(1, Serial("/dev/tty.usbmodem0007601185891", 115200, timeout=1)))
    connections.append(Node(2, Serial("/dev/tty.usbmodem0007601197931", 115200, timeout=1)))
    connections.append(Node(3, Serial("/dev/tty.usbmodem0007601194831", 115200, timeout=1)))

    return connections


if __name__ == "__main__":
    main()
