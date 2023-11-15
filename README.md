# Automated Water Level Control System (AWLC)

A system for monitoring water levels in a tank and automatically controlling a water pump based on the readings. The system uses MQTT for communication between components and provides a real-time dashboard for monitoring and control.

## Project Structure

The project is organized as follows:

```
AWTC/
├── config/                           # Configuration files
│   ├── mosquitto.conf                # MQTT broker configuration
│   └── settings.js                   # Node-RED settings
├── docker/                           # Docker-related files
│   ├── Dockerfile                    # Docker configuration for the application
│   ├── docker-compose.yml            # Docker Compose configuration for easy deployment
│   ├── docker-entrypoint.sh          # Startup script for the Docker container
│   └── .dockerignore                 # Files to exclude from Docker build
├── node-red/                         # Node-RED related files
│   ├── package.json                  # Node.js dependencies
│   ├── package-lock.json             # Dependency lock file
│   └── flows/                        # Node-RED flows
│       └── simplified_water_level_dashboard.json  # Main Node-RED flow
├── src/                              # Python source code
│   ├── water_level_server/           # Water level simulator module
│   │   └── water_level_simulator.py  # Simulates water level readings
│   └── middleware/                   # Middleware module
│       └── pump_controller.py        # Controls the pump based on water level
├── main.py                           # Main script to run both simulator and controller
└── requirements.txt                  # Python dependencies
```

## Overview

This project implements an automated water level monitoring and control system using:

- Python for water level simulation and pump control
- MQTT for communication between components
- Node-RED for dashboard visualization and control
- Docker for easy deployment and containerization

## System Requirements

### For Docker Deployment
- Docker Engine 19.03.0+
- Docker Compose 1.27.0+
- 1GB RAM minimum
- 2GB free disk space

### For Manual Installation
- Python 3.6+
- Node.js 14.0+ (for Node-RED)
- MQTT Broker (e.g., Mosquitto)
- npm (Node Package Manager)

## Command Line Options

When running the Python scripts manually, the following options are available:

- `--broker`: MQTT broker address (default: localhost)
- `--port`: MQTT broker port (default: 1883)
- `--tank-height`: Tank height in cm (default: 100)
- `--interval`: Update interval in seconds (default: 2)
- `--high-threshold`: High water level threshold percentage (default: 80)
- `--low-threshold`: Low water level threshold percentage (default: 20)

Example:
```
python main.py --broker localhost --port 1883 --tank-height 150 --interval 1
```

## Dashboard Features

The Node-RED dashboard provides the following features:

1. **Water Level Display**:
   - Real-time gauge showing current water level percentage
   - Historical chart of water level changes

2. **Pump Control**:
   - Current pump status indicator
   - Manual pump control switch
   - Auto/Manual mode selection buttons

3. **System Settings**:
   - Adjustable high and low water thresholds
   - Flow rate indicators (inflow and outflow)
   - Control mode status indicator

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

## Running the Application

There are two ways to run this application: using Docker (recommended) or manually.

### Option 1: Docker Deployment (Recommended)

The easiest way to run this project is using Docker, which packages all components together and handles their configuration automatically.

#### Prerequisites

- Docker and Docker Compose installed on your system

#### Running with Docker Compose

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/AWTC.git
   cd AWTC
   ```

2. Start the application with a single command:
   ```
   cd docker
   docker-compose up -d
   ```

3. Access the Node-RED dashboard:
   - Open your browser and navigate to http://localhost:1880/ui
   - The Node-RED editor is available at http://localhost:1880

4. To stop the application:
   ```
   docker-compose down
   ```

5. If you make changes to the code, rebuild and restart:
   ```
   docker-compose up --build -d
   ```

6. To view logs:
   ```
   docker logs awlc
   ```

#### Port Configuration

The Docker setup uses the following ports:
- 1880: Node-RED web interface
- 1884: MQTT broker (mapped to 1883 inside the container)
- 9001: MQTT websockets (if needed)

If you have conflicts with these ports, you can modify them in the `docker/docker-compose.yml` file:

```yaml
ports:
  - "1880:1880"  # Format: "HOST_PORT:CONTAINER_PORT"
  - "1884:1883"  # Change 1884 to another available port
  - "9001:9001"  # Change if needed
```

### Option 2: Manual Setup

If you prefer to run components separately or can't use Docker, follow these steps:

#### Prerequisites

- Python 3.6+
- MQTT Broker (e.g., Mosquitto)
- Node-RED with dashboard nodes installed
- Paho MQTT Python client

#### Installation

1. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

2. Install MQTT broker (Mosquitto):
   - Mac: `brew install mosquitto`
   - Linux: `sudo apt-get install mosquitto`
   - Windows: Download from https://mosquitto.org/download/

3. Install Node-RED:
   - Follow instructions at https://nodered.org/docs/getting-started/

4. Install Node-RED dashboard nodes:
   ```
   cd ~/.node-red
   npm install node-red-dashboard
   ```

#### Running Components Manually

1. Start the MQTT Broker:
   ```
   mosquitto -c config/mosquitto.conf
   ```

2. Start Node-RED:
   ```
   node-red --settings config/settings.js
   ```

3. Import the flow in Node-RED:
   - Open http://localhost:1880
   - Import the flow from `node-red/flows/simplified_water_level_dashboard.json`
   - Deploy the flow

4. Start the Water Level Control System:
   ```
   python main.py --broker localhost
   ```

## Configuration Files

Key configuration files and what to modify if needed:

### 1. docker/docker-compose.yml
- Port mappings for Node-RED and MQTT
- Volume mounts for persistent data

### 2. config/settings.js
- Node-RED settings
- Dashboard UI path (currently set to `/ui`)
- HTTP and WebSocket configurations

### 3. config/mosquitto.conf
- MQTT broker settings
- Listener ports and protocols

### 4. docker/docker-entrypoint.sh
- Startup sequence for the Docker container
- Component initialization

## Troubleshooting

- **Missing UI Components**: If dashboard elements show as "unknown", ensure node-red-dashboard is installed
- **MQTT Connection Issues**:
  - Check if the broker is running (`docker logs awlc | grep mosquitto`)
  - Verify the broker address and port are correct
- **Dashboard Not Updating**:
  - Check MQTT topics in Node-RED match those used by the Python script
  - Verify the UI path is correctly set in settings.js (`ui: { path: "ui" }`)
- **Port Conflicts**:
  - If ports are already in use, modify the port mappings in docker-compose.yml
  - Common conflicts: 1880 (Node-RED), 1883/1884 (MQTT)
- **Docker Issues**:
  - Check logs with `docker logs awlc`
  - Rebuild with `docker-compose up --build -d` after code changes

## Updates (November 15, 2023)

The following improvements were made to the project:
- Fixed Node-RED dashboard installation in Docker
- Added proper MQTT broker configuration
- Corrected Python script execution path in docker-entrypoint.sh
- Updated settings.js to enable dashboard UI
- Improved volume mounting for persistent data
- Added detailed documentation for both Docker and manual setup
