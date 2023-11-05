# Automated Water Level Control System (AWLC)

A system for monitoring water levels in a tank and automatically controlling a water pump based on the readings.

## Project Structure

The project is organized as follows:

```
AWTC/
├── main.py                           # Main script to run both simulator and controller
├── src/
│   ├── water_level_server/           # Water level simulator module
│   │   └── water_level_simulator.py  # Simulates water level readings
│   └── middleware/                   # Middleware module
│       └── pump_controller.py        # Controls the pump based on water level
└── flows/
    ├── simplified_water_level_dashboard.json  # Main Node-RED flow
    └── archive/                      # Archive of older flows
        ├── water_level_dashboard.json
        ├── improved_dashboard_flow.json
        ├── simple_flow.json
        └── minimal_flow.json
```

## Overview

This project implements an automated water level monitoring and control system using:

- Python for water level simulation and pump control
- MQTT for communication between components
- Node-RED for dashboard visualization and control

## Requirements

- Python 3.6+
- MQTT Broker (e.g., Mosquitto)
- Node-RED
- Paho MQTT Python client (`pip install paho-mqtt`)

## Installation

1. Install the required Python packages:
   ```
   pip install paho-mqtt
   ```

2. Install MQTT broker (Mosquitto):
   - Mac: `brew install mosquitto`
   - Linux: `sudo apt-get install mosquitto`
   - Windows: Download from https://mosquitto.org/download/

3. Install Node-RED:
   - Follow instructions at https://nodered.org/docs/getting-started/

## Usage

### 1. Start the MQTT Broker

```
mosquitto
```

### 2. Start the Water Level Control System

You can run the entire system using the main script:

```
python main.py
```

Alternatively, you can run the components separately:

```
# Run the water level simulator
python src/water_level_server/water_level_simulator.py

# Run the pump controller
python src/middleware/pump_controller.py
```

Options:
- `--broker`: MQTT broker address (default: localhost)
- `--port`: MQTT broker port (default: 1883)
- `--tank-height`: Tank height in cm (default: 100)
- `--interval`: Update interval in seconds (default: 2)
- `--high-threshold`: High water level threshold percentage (default: 80)
- `--low-threshold`: Low water level threshold percentage (default: 20)

### 3. Import the Node-RED Flow

1. Start Node-RED:
   ```
   node-red
   ```

2. Open Node-RED in your browser (typically http://localhost:1880)

3. Import the flow from `flows/simplified_water_level_dashboard.json`

4. Deploy the flow

5. Access the dashboard at http://localhost:1880/ui

## Features

- **Water Level Simulation**: Simulates changing water levels with natural fluctuations
- **Automatic Pump Control**: Turns the pump on/off based on water level thresholds
- **Real-time Dashboard**: Visualizes water levels and pump status
- **Manual Override**: Allows manual control of the pump from the dashboard
- **Configurable Thresholds**: Adjustable high and low water level thresholds
- **Flow Rate Display**: Shows water flow rate in liters per minute

## System Architecture

```
┌─────────────────┐     MQTT      ┌─────────────────┐     MQTT      ┌─────────────────┐
│  Water Level    │  water/level  │  Pump           │  water/pump   │  Node-RED       │
│  Simulator      │───────────────▶  Controller     │───────────────▶  Dashboard      │
└─────────────────┘               └─────────────────┘               └─────────────────┘
```

## Troubleshooting

- If you have issues with MQTT connection, ensure the broker is running and accessible
- If the dashboard doesn't update, check the MQTT topics in Node-RED match those used by the Python script
- For manual mode issues, ensure the correct topics are being used for communication
