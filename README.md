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

## Run Tests

The project contains unit test for the Python and C source code.
