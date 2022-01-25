"""Main module"""

import json
from typing import List

from serial import Serial


def main():
    """Main function. Loops forever and performs ranging."""
    connections = connect()
    while True:
        for connection in connections:
            line = connection.readline()
            try:
                json_string = str(line)
                json_string = json_string[2 : len(json_string) - 3]  # TODO
                decoded_json = json.JSONDecoder().decode(json_string)
                if decoded_json:
                    try:
                        sender_id = decoded_json["sender id"]
                        print("Received message from " + str(sender_id))
                    except KeyError:
                        pass
            except json.JSONDecodeError:
                pass  # Apparently we did not get a valid json


def connect() -> List[Serial]:
    """Generates a list of connections."""
    connections = []
    connections.append(Serial("/dev/tty.usbmodem0007601185891", 115200, timeout=1))
    return connections


if __name__ == "__main__":
    main()
