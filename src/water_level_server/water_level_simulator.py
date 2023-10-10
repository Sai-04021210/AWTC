#!/usr/bin/env python3
"""
Water Level Simulator
This script simulates an ultrasonic sensor reading water levels in a tank
and publishes the data to an MQTT broker.

Created: October 10, 2023
"""

import paho.mqtt.client as mqtt
import time
import random
import json
import logging
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WaterLevelSimulator")

# Default configuration
DEFAULT_BROKER = "localhost"
DEFAULT_PORT = 1883
DEFAULT_TOPIC = "water/level"
DEFAULT_TANK_HEIGHT = 100  # cm
DEFAULT_INTERVAL = 2  # seconds

class WaterLevelSimulator:
    def __init__(self, broker=DEFAULT_BROKER, port=DEFAULT_PORT,
                 topic=DEFAULT_TOPIC, tank_height=DEFAULT_TANK_HEIGHT,
                 interval=DEFAULT_INTERVAL):
        """Initialize the water level simulator."""
        self.broker = broker
        self.port = port
        self.topic = topic
        self.tank_height = tank_height
        self.interval = interval
        self.client = None
        self.current_level = random.uniform(20, 80)  # Start with random level
        self.is_filling = True
        self.connected = False

    def connect_mqtt(self):
        """Connect to the MQTT broker."""
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        try:
            logger.info(f"Connecting to MQTT broker at {self.broker}:{self.port}")
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False

    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker."""
        if rc == 0:
            self.connected = True
            logger.info("Connected to MQTT broker")
        else:
            logger.error(f"Failed to connect to MQTT broker with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the broker."""
        self.connected = False
        logger.warning(f"Disconnected from MQTT broker with code {rc}")

    def simulate_water_level(self):
        """Simulate changing water level in the tank."""
        # Simulate natural fluctuation with some randomness
        change_rate = random.uniform(0.5, 2.0)

        if self.is_filling:
            self.current_level += change_rate
            if self.current_level >= 95:
                self.is_filling = False
        else:
            self.current_level -= change_rate
            if self.current_level <= 10:
                self.is_filling = True

        # Ensure level stays within bounds
        self.current_level = max(0, min(self.current_level, self.tank_height))

        # Calculate percentage
        percentage = (self.current_level / self.tank_height) * 100

        return {
            "level_cm": round(self.current_level, 2),
            "level_percentage": round(percentage, 2),
            "timestamp": datetime.now().isoformat(),
            "tank_status": "filling" if self.is_filling else "draining"
        }

    def publish_reading(self, reading):
        """Publish water level reading to MQTT topic."""
        if not self.connected:
            logger.warning("Not connected to MQTT broker, attempting to reconnect...")
            self.connect_mqtt()
            return

        try:
            payload = json.dumps(reading)
            result = self.client.publish(self.topic, payload)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published: {payload}")
            else:
                logger.error(f"Failed to publish message: {result}")
        except Exception as e:
            logger.error(f"Error publishing message: {e}")

    def run(self):
        """Run the simulator continuously."""
        if not self.connect_mqtt():
            logger.error("Failed to start simulator due to MQTT connection issues")
            return

        logger.info(f"Starting water level simulator. Publishing to {self.topic}")
        logger.info(f"Tank height: {self.tank_height}cm, Update interval: {self.interval}s")

        try:
            while True:
                reading = self.simulate_water_level()
                self.publish_reading(reading)
                time.sleep(self.interval)
        except KeyboardInterrupt:
            logger.info("Simulator stopped by user")
        finally:
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()
            logger.info("Simulator shutdown complete")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Water Level Simulator')
    parser.add_argument('--broker', default=DEFAULT_BROKER, help='MQTT broker address')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='MQTT broker port')
    parser.add_argument('--topic', default=DEFAULT_TOPIC, help='MQTT topic to publish to')
    parser.add_argument('--tank-height', type=float, default=DEFAULT_TANK_HEIGHT,
                        help='Tank height in cm')
    parser.add_argument('--interval', type=float, default=DEFAULT_INTERVAL,
                        help='Update interval in seconds')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    simulator = WaterLevelSimulator(
        broker=args.broker,
        port=args.port,
        topic=args.topic,
        tank_height=args.tank_height,
        interval=args.interval
    )
    simulator.run()
