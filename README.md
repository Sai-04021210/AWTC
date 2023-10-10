# Automated Water Level Control System (AWLC)

A system for monitoring water levels in a tank and automatically controlling a water pump based on the readings.

**Created:** October 10, 2023

## Overview

This project implements an automated water level monitoring and control system using:

- Python for water level simulation and pump control
- MQTT for communication between components
- Node-RED for dashboard visualization and control

The system consists of the following components:

1. **Water Level Simulator**: Simulates an ultrasonic sensor reading water levels in a tank
2. **Pump Controller**: Controls a water pump based on water level readings
3. **Node-RED Dashboard**: Visualizes water levels and pump status

## System Architecture

```
┌─────────────────┐     MQTT      ┌─────────────────┐     MQTT      ┌─────────────────┐
│  Water Level    │  water/level  │  Pump           │  water/pump   │  Node-RED       │
│  Simulator      │───────────────▶  Controller     │───────────────▶  Dashboard      │
└─────────────────┘               └─────────────────┘               └─────────────────┘
```

## Requirements

- Python 3.6+
- MQTT Broker (e.g., Mosquitto)
- Node-RED
- Paho MQTT Python client

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/AWLC.git
   cd AWLC
   ```

2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

3. Install and start an MQTT broker (if not already running):
   ```
   # For Ubuntu/Debian
   sudo apt-get install mosquitto mosquitto-clients
   sudo systemctl start mosquitto

   # For macOS
   brew install mosquitto
   brew services start mosquitto
   ```

4. Install Node-RED (if not already installed):
   ```
   npm install -g --unsafe-perm node-red
   ```

## Usage

### 1. Start the Water Level Simulator

```
python src/water_level_server/water_level_simulator.py
```

Options:
- `--broker`: MQTT broker address (default: localhost)
- `--port`: MQTT broker port (default: 1883)
- `--topic`: MQTT topic to publish to (default: water/level)
- `--tank-height`: Tank height in cm (default: 100)
- `--interval`: Update interval in seconds (default: 2)

### 2. Start the Pump Controller

```
python src/middleware/pump_controller.py
```

Options:
- `--broker`: MQTT broker address (default: localhost)
- `--port`: MQTT broker port (default: 1883)
- `--level-topic`: MQTT topic to subscribe for water level (default: water/level)
- `--pump-topic`: MQTT topic to publish pump status (default: water/pump)
- `--high-threshold`: High water level threshold percentage to turn pump OFF (default: 80)
- `--low-threshold`: Low water level threshold percentage to turn pump ON (default: 20)

### 3. Import the Node-RED Flow

1. Start Node-RED:
   ```
   node-red
   ```

2. Open Node-RED in your browser (typically http://localhost:1880)

3. Import the flow from `flows/water_level_dashboard.json`

4. Deploy the flow

5. Access the dashboard at http://localhost:1880/ui

## Features

- **Water Level Simulation**: Simulates changing water levels with natural fluctuations
- **Automatic Pump Control**: Turns the pump on/off based on water level thresholds
- **Real-time Dashboard**: Visualizes water levels and pump status
- **Manual Override**: Allows manual control of the pump from the dashboard
- **Configurable Thresholds**: Adjustable high and low water level thresholds

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
