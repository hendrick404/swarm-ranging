from math import cos, pi, sin
import os
from random import uniform

from node import Node
from config import second
from simulate import simulate
from evaluate import evaluate_static

def experiment(interval: int, num_messages: int, transmission_success_rate: float, circle_size: int, max_clock_drift: float) -> None:
    name: str = f"{int(interval/second*1000):04d}_{int(transmission_success_rate*100):03d}"
    nodes = []
    for i in range(1,circle_size+1):
        nodes.append(Node(i,(sin(i * (2 * pi / circle_size)),cos(i * (2 * pi / circle_size))), clock_offset=int(uniform(0,second)), clock_err=uniform(1-max_clock_drift, 1+max_clock_drift)))
    simulate(nodes, interval, num_messages, transmission_success_rate, f"evaluation_{name}.txt")
    evaluate_static(nodes, f"evaluation_{name}.txt" , name)
    os.remove(os.path.join("evaluation", f"evaluation_{name}.txt" ))

def main():
    experiment(10 * second, 10000, 1, 12, 20 / 1_000_000)
    experiment(1 * second, 10000, 1, 12, 20 / 1_000_000)
    experiment(int(0.1 * second), 10000, 1, 12, 20 / 1_000_000)
    experiment(int(0.01 * second), 10000, 1, 12, 20 / 1_000_000)



if __name__ == "__main__":
    main()