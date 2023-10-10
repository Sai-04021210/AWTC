#!/usr/bin/env python3
"""
Pump Controller Middleware
This script subscribes to water level readings from an MQTT broker
and controls a water pump based on the water level.

Created: October 10, 2023
"""

import paho.mqtt.client as mqtt
import time
import json
import logging
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PumpController")

# Default configuration
DEFAULT_BROKER = "localhost"
DEFAULT_PORT = 1883
DEFAULT_LEVEL_TOPIC = "water/level"
DEFAULT_PUMP_TOPIC = "water/pump"
DEFAULT_HIGH_THRESHOLD = 80  # Turn off pump when water level is above 80%
DEFAULT_LOW_THRESHOLD = 20   # Turn on pump when water level is below 20%

class PumpController:
    def __init__(self, broker=DEFAULT_BROKER, port=DEFAULT_PORT,
                 level_topic=DEFAULT_LEVEL_TOPIC, pump_topic=DEFAULT_PUMP_TOPIC,
                 high_threshold=DEFAULT_HIGH_THRESHOLD, low_threshold=DEFAULT_LOW_THRESHOLD):
        """Initialize the pump controller."""
        self.broker = broker
        self.port = port
        self.level_topic = level_topic
        self.pump_topic = pump_topic
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold
        self.client = None
        self.pump_status = False  # False = OFF, True = ON
        self.connected = False

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
            # Subscribe to water level topic
            self.client.subscribe(self.level_topic)
            logger.info(f"Subscribed to {self.level_topic}")
            # Publish initial pump status
            self._publish_pump_status()
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
            logger.debug(f"Received message: {payload}")

            if 'level_percentage' in payload:
                self._process_water_level(payload['level_percentage'])
            else:
                logger.warning(f"Received message without level_percentage: {payload}")
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON message: {msg.payload}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def _process_water_level(self, level_percentage):
        """Process water level reading and control pump accordingly."""
        logger.info(f"Current water level: {level_percentage}%")

        # Implement hysteresis control to prevent rapid switching
        if level_percentage >= self.high_threshold and self.pump_status:
            logger.info(f"Water level ({level_percentage}%) above high threshold ({self.high_threshold}%). Turning pump OFF.")
            self.pump_status = False
            self._publish_pump_status()
        elif level_percentage <= self.low_threshold and not self.pump_status:
            logger.info(f"Water level ({level_percentage}%) below low threshold ({self.low_threshold}%). Turning pump ON.")
            self.pump_status = True
            self._publish_pump_status()

    def _publish_pump_status(self):
        """Publish pump status to MQTT topic."""
        if not self.connected:
            logger.warning("Not connected to MQTT broker, cannot publish pump status")
            return

        try:
            status_str = "ON" if self.pump_status else "OFF"
            payload = json.dumps({
                "status": status_str,
                "value": 1 if self.pump_status else 0,
                "timestamp": datetime.now().isoformat()
            })

            result = self.client.publish(self.pump_topic, payload)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published pump status: {status_str}")
            else:
                logger.error(f"Failed to publish pump status: {result}")
        except Exception as e:
            logger.error(f"Error publishing pump status: {e}")

    def run(self):
        """Run the pump controller."""
        if not self.connect_mqtt():
            logger.error("Failed to start pump controller due to MQTT connection issues")
            return

        logger.info(f"Starting pump controller. Listening on {self.level_topic}")
        logger.info(f"High threshold: {self.high_threshold}%, Low threshold: {self.low_threshold}%")

        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Pump controller stopped by user")
        finally:
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()
            logger.info("Pump controller shutdown complete")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Water Pump Controller')
    parser.add_argument('--broker', default=DEFAULT_BROKER, help='MQTT broker address')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='MQTT broker port')
    parser.add_argument('--level-topic', default=DEFAULT_LEVEL_TOPIC,
                        help='MQTT topic to subscribe for water level')
    parser.add_argument('--pump-topic', default=DEFAULT_PUMP_TOPIC,
                        help='MQTT topic to publish pump status')
    parser.add_argument('--high-threshold', type=float, default=DEFAULT_HIGH_THRESHOLD,
                        help='High water level threshold percentage to turn pump OFF')
    parser.add_argument('--low-threshold', type=float, default=DEFAULT_LOW_THRESHOLD,
                        help='Low water level threshold percentage to turn pump ON')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    controller = PumpController(
        broker=args.broker,
        port=args.port,
        level_topic=args.level_topic,
        pump_topic=args.pump_topic,
        high_threshold=args.high_threshold,
        low_threshold=args.low_threshold
    )
    controller.run()
