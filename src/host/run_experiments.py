from math import cos, pi, sin
import os
from random import uniform

from node import SimulationNode
from config import SECOND
from simulate import simulate
from evaluate import evaluate_static


def experiment(
    interval: int,
    num_messages: int,
    success_rate: float,
    circle_size: int,
    max_clock_drift: float,
) -> None:
    name: str = f"{int(interval / SECOND * 1000):04d}_{int(success_rate * 100):03d}"
    nodes = []
    for i in range(1, circle_size + 1):
        nodes.append(
            SimulationNode(
                i,
                (sin(i * (2 * pi / circle_size)), cos(i * (2 * pi / circle_size))),
                clock_offset=int(uniform(0, SECOND)),
                clock_err=uniform(1 - max_clock_drift, 1 + max_clock_drift),
            )
        )
    simulate(
        nodes,
        interval,
        num_messages,
        success_rate,
        f"evaluation_{name}.txt",
    )
    evaluate_static(nodes, f"evaluation_{name}.txt", name)
    os.remove(os.path.join("evaluation", f"evaluation_{name}.txt"))


def main():
    experiment(10 * SECOND, 100, 1, 12, 20 / 1_000_000)
    experiment(1 * SECOND, 100, 1, 12, 20 / 1_000_000)
    experiment(int(0.1 * SECOND), 100, 1, 12, 20 / 1_000_000)
    experiment(int(0.01 * SECOND), 100, 1, 12, 20 / 1_000_000)


if __name__ == "__main__":
    main()
