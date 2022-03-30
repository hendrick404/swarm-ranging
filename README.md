# Swarm Ranging

Implementation of my bachelor thesis "Ultra Wideband Swarm Ranging Using Passive Ranging Techniques".

## Project Overview

The implementation of the swarm ranging is split into two parts. One part runs on the DWM1001 UWB transceiver by Decawave in the directory `src/antenna`.  The other part is a python implementation that can run on any device that is connected to the board via USB. It is found in the directory `src/host`. In addition, there is a simulation to that generates messages for any configuration of nodes. The simulation is located in `src/simulation`.

## Getting Started

The antenna module is built with Zephyr. Install the [Zephyr Toolchain](https://docs.zephyrproject.org/latest/getting_started/index.html) and build the project with:
```
west build -b nrf52_dwm1001 .
```

The host module is written in Python. Install the dependencies from `requirements.txt` and execute the module with:
```
python3 src/host/main.py
```
Make sure to adjust the paths of the devices in the `connect` function in `main.py`.

To execute the simulation, run:
```
python3 src/host/run_experiments.py
```
The results will be stored in `evaluation`.

## Run Tests

The project contains unit test for the Python and C source code. To run the python tests make sure the dependencies from `requirements.txt` are installed and run:
```
pytest test/host
```
To run the C tests change the directory to `test/antenna` and run:
```
make
```

## About the implementation

The heart of the implementation is the `Node` class in `src/host/node.py`. The methods `evaluate_tx` and `evaluate_rx` take the information from the board or previously recorded file and process them. The method `evaluate_rx` iterates over the timestamps of a received message and performs the ranging.

The `Node` class has two extensions. `SimulationNode` is used in the simulation to generate an evaluation file. The `RealNode` uses a serial connection to receive data from the DWM1001 boards.

## Miscellaneous

Check out the branch `platformio` to see how this project can be build with PlatformIO.