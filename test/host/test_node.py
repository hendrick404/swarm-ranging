from src.host.node import Node


def test_active_ranging_no_clock_drift():
    node_a: Node = Node(1)

    message_1 = {
        "id": 1,
        "rx range": {
            "sender id": 2,
            "seq num": 1,
            "tx time": 0,
            "rx time": 1_000,
            "timestamps": [],
        },
    }
    message_2 = {"id": 1, "tx range": {"tx time": 1_000_000, "seq num": 1}}
    message_3 = {
        "id": 1,
        "rx range": {
            "sender id": 2,
            "seq num": 2,
            "tx time": 2_500_000,
            "rx time": 2_501_000,
            "timestamps": [{"id": 1, "seq num": 1, "rx time": 1_001_000}],
        },
    }

    node_a.evaluate_rx(message_1)
    node_a.evaluate_tx(message_2)
    node_a.evaluate_rx(message_3)

    assert node_a.active_ranging_distances[2]
    assert abs(node_a.active_ranging_distances[2][0] - 0.2998) < 0.01

def test_passive_ranging_no_clock_drift():
    node_a: Node = Node(1)

    message_1 = {
        "id": 1,
        "rx range": {
            "sender id": 2,
            "seq num": 1,
            "tx time": 0,
            "rx time": 1_000,
            "timestamps": [],
        },
    }
    message_2 = {
        "id": 1,
        "rx range": {
            "sender id": 3,
            "seq num": 1,
            "tx time": 0,
            "rx time": 1_000,
            "timestamps": [],
        },
    }
    message_3 = {
        "id": 1,
        "rx range": {
            "sender id": 2,
            "seq num": 2,
            "tx time": 2_500_000,
            "rx time": 2_501_000,
            "timestamps": [{"id": 3, "seq num": 1, "rx time": 1_001_000}],
        },
    }

    node_a.evaluate_rx(message_1)
    node_a.evaluate_rx(message_2)
    node_a.evaluate_rx(message_3)

    print(node_a.passive_ranging_distances_adjusted)

    assert abs(node_a.passive_ranging_distances_adjusted[2,3][0] - 300.0923) < 0.01