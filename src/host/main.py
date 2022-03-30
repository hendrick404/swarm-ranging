"""Main module"""

import json
from typing import List

from serial import Serial

from node import RealNode

evaluate: bool = True
EVALUATE_NUMBER_OF_MESSAGES = 100


def main():
    """Main function. Loops forever and performs ranging."""

    connections = connect()

    eval_file = open("evaluation.txt", "a", encoding="UTF-8") if evaluate else None

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
