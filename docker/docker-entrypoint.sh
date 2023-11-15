#!/bin/bash
set -e

# Start Mosquitto MQTT broker in the background
mosquitto -d

# Wait a moment for Mosquitto to start
sleep 2

# Start Node-RED in the background with the simplified flow
mkdir -p /root/.node-red
cp /app/node-red/flows/simplified_water_level_dashboard.json /root/.node-red/flows.json

# Ensure dashboard nodes are installed
cd /root/.node-red
npm install --no-fund --no-audit node-red-dashboard

# Start Node-RED with settings
node-red --settings /app/config/settings.js &

# Wait a moment for Node-RED to start
sleep 5

# Run the Python application with localhost as the broker
# since we're inside the container
cd /app
python main.py --broker localhost

# Keep the container running
exec "$@"
