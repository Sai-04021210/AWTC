#!/usr/bin/env python3
"""
Water Level Simulator
This script simulates an ultrasonic sensor reading water levels in a tank
and publishes the data to an MQTT broker. The water level is influenced by
motor status and simulated household water usage.

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
DEFAULT_LEVEL_TOPIC = "water/level"
DEFAULT_PUMP_TOPIC = "water/pump"
DEFAULT_MANUAL_TOPIC = "water/manual"
DEFAULT_TANK_HEIGHT = 100  # cm
DEFAULT_INTERVAL = 2  # seconds
DEFAULT_USAGE_RATE = 0.8  # cm per interval when water is being used
DEFAULT_TANK_DIAMETER = 50  # cm - for calculating volume
DEFAULT_FILL_RATE = 2.0  # cm per interval when pump is on

class WaterLevelSimulator:
    def __init__(self, broker=DEFAULT_BROKER, port=DEFAULT_PORT,
                 level_topic=DEFAULT_LEVEL_TOPIC, pump_topic=DEFAULT_PUMP_TOPIC,
                 manual_topic=DEFAULT_MANUAL_TOPIC, tank_height=DEFAULT_TANK_HEIGHT,
                 interval=DEFAULT_INTERVAL, usage_rate=DEFAULT_USAGE_RATE,
                 tank_diameter=DEFAULT_TANK_DIAMETER, fill_rate=DEFAULT_FILL_RATE):
        """Initialize the water level simulator."""
        self.broker = broker
        self.port = port
        self.level_topic = level_topic
        self.pump_topic = pump_topic
        self.manual_topic = manual_topic
        self.tank_height = tank_height
        self.interval = interval
        self.usage_rate = usage_rate
        self.tank_diameter = tank_diameter
        self.fill_rate = fill_rate
        self.client = None
        self.current_level = random.uniform(40, 60)  # Start with random level
        self.pump_status = False  # Pump is initially OFF
        self.manual_mode = False  # Auto mode by default
        self.water_usage = True   # Simulate water being used
        self.connected = False
        self.current_flow_rate = 0.0  # Current flow rate in L/min

        # Calculate tank area for volume calculations
        self.tank_area = 3.14159 * (self.tank_diameter/2)**2  # cm²

        # Randomize water usage patterns
        self.usage_timer = 0
        self.usage_duration = random.randint(5, 15)  # Duration of water usage in intervals
        self.no_usage_duration = random.randint(10, 30)  # Duration of no water usage in intervals

    def connect_mqtt(self):
        """Connect to the MQTT broker."""
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

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

            # Subscribe to pump status and manual mode topics
            self.client.subscribe(self.pump_topic)
            logger.info(f"Subscribed to {self.pump_topic}")

            self.client.subscribe(self.manual_topic)
            logger.info(f"Subscribed to {self.manual_topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the broker."""
        self.connected = False
        logger.warning(f"Disconnected from MQTT broker with code {rc}")

    def _on_message(self, client, userdata, msg):
        """Callback for when a message is received from the broker."""
        try:
            payload = json.loads(msg.payload.decode())
            logger.debug(f"Received message on topic {msg.topic}: {payload}")

            if msg.topic == self.pump_topic:
                if "status" in payload:
                    self.pump_status = payload["status"] == "ON"
                    logger.info(f"Pump status updated: {'ON' if self.pump_status else 'OFF'}")
                elif "value" in payload:
                    self.pump_status = bool(payload["value"])
                    logger.info(f"Pump status updated: {'ON' if self.pump_status else 'OFF'}")

            elif msg.topic == self.manual_topic:
                if "manual" in payload:
                    self.manual_mode = bool(payload["manual"])
                    logger.info(f"Manual mode updated: {'ON' if self.manual_mode else 'OFF'}")

        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON message: {msg.payload}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def simulate_water_level(self):
        """Simulate changing water level in the tank."""
        # Update water usage pattern
        self.usage_timer += 1
        if self.water_usage and self.usage_timer >= self.usage_duration:
            self.water_usage = False
            self.usage_timer = 0
            self.no_usage_duration = random.randint(10, 30)
            logger.info("Water usage stopped")
        elif not self.water_usage and self.usage_timer >= self.no_usage_duration:
            self.water_usage = True
            self.usage_timer = 0
            self.usage_duration = random.randint(5, 15)
            logger.info("Water usage started")

        # Calculate level change based on pump status and water usage
        level_change = 0
        inflow_rate = 0.0  # L/min
        outflow_rate = 0.0  # L/min

        # If pump is ON, water level increases
        if self.pump_status:
            # Filling rate when pump is on (with some randomness)
            fill_rate = self.fill_rate * random.uniform(0.9, 1.1)
            level_change += fill_rate

            # Calculate inflow in liters per minute
            # Volume change = area * height change
            # Convert to liters (1000 cm³ = 1 L) and adjust for interval to get L/min
            volume_change_cm3 = self.tank_area * fill_rate
            inflow_rate = (volume_change_cm3 / 1000) * (60 / self.interval)

        # If water is being used, water level decreases
        if self.water_usage:
            # Usage rate (with some randomness)
            usage = self.usage_rate * random.uniform(0.8, 1.2)
            level_change -= usage

            # Calculate outflow in liters per minute
            volume_change_cm3 = self.tank_area * usage
            outflow_rate = (volume_change_cm3 / 1000) * (60 / self.interval)

        # In manual mode, behavior depends on pump status and water usage
        if self.manual_mode:
            # Log the manual mode status for debugging
            logger.debug(f"Manual mode active: Pump is {'ON' if self.pump_status else 'OFF'}, " +
                        f"Water usage is {'active' if self.water_usage else 'inactive'}")

            # If no water usage and pump is off, keep level constant
            if not self.water_usage and not self.pump_status:
                level_change = 0
                inflow_rate = 0.0
                outflow_rate = 0.0

        # Calculate net flow rate
        self.current_flow_rate = inflow_rate - outflow_rate

        # Apply the level change
        self.current_level += level_change

        # Ensure level stays within bounds
        self.current_level = max(0, min(self.current_level, self.tank_height))

        # Calculate percentage
        percentage = (self.current_level / self.tank_height) * 100

        # Determine tank status
        if level_change > 0:
            tank_status = "filling"
        elif level_change < 0:
            tank_status = "draining"
        else:
            tank_status = "stable"

        return {
            "level_cm": round(self.current_level, 2),
            "level_percentage": round(percentage, 2),
            "timestamp": datetime.now().isoformat(),
            "tank_status": tank_status,
            "pump_status": "ON" if self.pump_status else "OFF",
            "water_usage": self.water_usage,
            "manual_mode": self.manual_mode,
            "inflow_rate": round(inflow_rate, 2),  # L/min
            "outflow_rate": round(outflow_rate, 2),  # L/min
            "net_flow_rate": round(self.current_flow_rate, 2)  # L/min
        }

    def publish_reading(self, reading):
        """Publish water level reading to MQTT topic."""
        if not self.connected:
            logger.warning("Not connected to MQTT broker, attempting to reconnect...")
            self.connect_mqtt()
            return

        try:
            payload = json.dumps(reading)
            result = self.client.publish(self.level_topic, payload)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published water level: {reading['level_percentage']}%, Pump: {reading['pump_status']}")
            else:
                logger.error(f"Failed to publish message: {result}")
        except Exception as e:
            logger.error(f"Error publishing message: {e}")

    def run(self):
        """Run the simulator continuously."""
        if not self.connect_mqtt():
            logger.error("Failed to start simulator due to MQTT connection issues")
            return

        logger.info(f"Starting water level simulator. Publishing to {self.level_topic}")
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
    parser.add_argument('--level-topic', default=DEFAULT_LEVEL_TOPIC, help='MQTT topic to publish water level')
    parser.add_argument('--pump-topic', default=DEFAULT_PUMP_TOPIC, help='MQTT topic for pump status')
    parser.add_argument('--manual-topic', default=DEFAULT_MANUAL_TOPIC, help='MQTT topic for manual mode')
    parser.add_argument('--tank-height', type=float, default=DEFAULT_TANK_HEIGHT,
                        help='Tank height in cm')
    parser.add_argument('--tank-diameter', type=float, default=DEFAULT_TANK_DIAMETER,
                        help='Tank diameter in cm')
    parser.add_argument('--interval', type=float, default=DEFAULT_INTERVAL,
                        help='Update interval in seconds')
    parser.add_argument('--usage-rate', type=float, default=DEFAULT_USAGE_RATE,
                        help='Water usage rate in cm per interval')
    parser.add_argument('--fill-rate', type=float, default=DEFAULT_FILL_RATE,
                        help='Fill rate in cm per interval when pump is on')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    simulator = WaterLevelSimulator(
        broker=args.broker,
        port=args.port,
        level_topic=args.level_topic,
        pump_topic=args.pump_topic,
        manual_topic=args.manual_topic,
        tank_height=args.tank_height,
        tank_diameter=args.tank_diameter,
        interval=args.interval,
        usage_rate=args.usage_rate,
        fill_rate=args.fill_rate
    )
    simulator.run()
