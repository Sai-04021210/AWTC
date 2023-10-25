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
DEFAULT_MANUAL_TOPIC = "water/manual"
DEFAULT_MANUAL_CONTROL_TOPIC = "water/pump/manual"
DEFAULT_HIGH_THRESHOLD_TOPIC = "water/threshold/high"
DEFAULT_LOW_THRESHOLD_TOPIC = "water/threshold/low"
DEFAULT_HIGH_THRESHOLD = 80  # Turn off pump when water level is above 80%
DEFAULT_LOW_THRESHOLD = 20   # Turn on pump when water level is below 20%

class PumpController:
    def __init__(self, broker=DEFAULT_BROKER, port=DEFAULT_PORT,
                 level_topic=DEFAULT_LEVEL_TOPIC, pump_topic=DEFAULT_PUMP_TOPIC,
                 manual_topic=DEFAULT_MANUAL_TOPIC, manual_control_topic=DEFAULT_MANUAL_CONTROL_TOPIC,
                 high_threshold_topic=DEFAULT_HIGH_THRESHOLD_TOPIC, low_threshold_topic=DEFAULT_LOW_THRESHOLD_TOPIC,
                 high_threshold=DEFAULT_HIGH_THRESHOLD, low_threshold=DEFAULT_LOW_THRESHOLD):
        """Initialize the pump controller."""
        self.broker = broker
        self.port = port
        self.level_topic = level_topic
        self.pump_topic = pump_topic
        self.manual_topic = manual_topic
        self.manual_control_topic = manual_control_topic
        self.high_threshold_topic = high_threshold_topic
        self.low_threshold_topic = low_threshold_topic
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold
        self.client = None
        self.pump_status = False  # False = OFF, True = ON
        self.manual_mode = False  # Auto mode by default
        self.connected = False
        self.current_level = 50.0  # Default level

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

            # Subscribe to manual control topic
            self.client.subscribe(self.manual_control_topic)
            logger.info(f"Subscribed to {self.manual_control_topic}")

            # Subscribe to threshold topics
            self.client.subscribe(self.high_threshold_topic)
            logger.info(f"Subscribed to {self.high_threshold_topic}")

            self.client.subscribe(self.low_threshold_topic)
            logger.info(f"Subscribed to {self.low_threshold_topic}")

            # Publish initial pump status and manual mode
            self._publish_pump_status()
            self._publish_manual_mode()
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

            if msg.topic == self.level_topic:
                if 'level_percentage' in payload:
                    self.current_level = payload['level_percentage']
                    if not self.manual_mode:
                        self._process_water_level(self.current_level)
                else:
                    logger.warning(f"Received level message without level_percentage: {payload}")

            elif msg.topic == self.manual_control_topic:
                # Handle manual pump control
                if 'manual' in payload:
                    self.manual_mode = bool(payload['manual'])
                    logger.info(f"Manual mode set to: {'ON' if self.manual_mode else 'OFF'}")
                    self._publish_manual_mode()

                    # If switching to auto mode, process current level
                    if not self.manual_mode:
                        logger.info("Switching to automatic mode")
                        self._process_water_level(self.current_level)
                        return

                # Handle pump status changes in manual mode
                if 'status' in payload:
                    new_status = payload['status'] == 'ON'
                    if new_status != self.pump_status:
                        logger.info(f"Manual control: Setting pump to {'ON' if new_status else 'OFF'}")
                        self.pump_status = new_status
                        self._publish_pump_status()
                elif 'value' in payload:
                    new_status = bool(payload['value'])
                    if new_status != self.pump_status:
                        logger.info(f"Manual control: Setting pump to {'ON' if new_status else 'OFF'}")
                        self.pump_status = new_status
                        self._publish_pump_status()

            elif msg.topic == self.high_threshold_topic:
                # Handle high threshold updates
                if 'high_threshold' in payload:
                    new_threshold = float(payload['high_threshold'])
                    if new_threshold > self.low_threshold:
                        self.high_threshold = new_threshold
                        logger.info(f"Updated high threshold to {self.high_threshold}%")
                        # Re-evaluate water level with new threshold if in auto mode
                        if not self.manual_mode:
                            self._process_water_level(self.current_level)
                    else:
                        logger.warning(f"Rejected high threshold {new_threshold}% as it's not greater than low threshold {self.low_threshold}%")

            elif msg.topic == self.low_threshold_topic:
                # Handle low threshold updates
                if 'low_threshold' in payload:
                    new_threshold = float(payload['low_threshold'])
                    if new_threshold < self.high_threshold:
                        self.low_threshold = new_threshold
                        logger.info(f"Updated low threshold to {self.low_threshold}%")
                        # Re-evaluate water level with new threshold if in auto mode
                        if not self.manual_mode:
                            self._process_water_level(self.current_level)
                    else:
                        logger.warning(f"Rejected low threshold {new_threshold}% as it's not less than high threshold {self.high_threshold}%")

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
        else:
            # Log current status for debugging
            status_str = "ON" if self.pump_status else "OFF"
            logger.info(f"Auto mode active: Water level at {level_percentage}%. Pump remains {status_str}.")

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
                "timestamp": datetime.now().isoformat(),
                "manual": self.manual_mode
            })

            result = self.client.publish(self.pump_topic, payload)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published pump status: {status_str} (Manual mode: {self.manual_mode})")
            else:
                logger.error(f"Failed to publish pump status: {result}")
        except Exception as e:
            logger.error(f"Error publishing pump status: {e}")

    def _publish_manual_mode(self):
        """Publish manual mode status to MQTT topic."""
        if not self.connected:
            logger.warning("Not connected to MQTT broker, cannot publish manual mode status")
            return

        try:
            payload = json.dumps({
                "manual": self.manual_mode,
                "timestamp": datetime.now().isoformat()
            })

            result = self.client.publish(self.manual_topic, payload)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published manual mode status: {'ON' if self.manual_mode else 'OFF'}")
            else:
                logger.error(f"Failed to publish manual mode status: {result}")
        except Exception as e:
            logger.error(f"Error publishing manual mode status: {e}")

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
    parser.add_argument('--manual-topic', default=DEFAULT_MANUAL_TOPIC,
                        help='MQTT topic to publish manual mode status')
    parser.add_argument('--manual-control-topic', default=DEFAULT_MANUAL_CONTROL_TOPIC,
                        help='MQTT topic to receive manual control commands')
    parser.add_argument('--high-threshold-topic', default=DEFAULT_HIGH_THRESHOLD_TOPIC,
                        help='MQTT topic to receive high threshold updates')
    parser.add_argument('--low-threshold-topic', default=DEFAULT_LOW_THRESHOLD_TOPIC,
                        help='MQTT topic to receive low threshold updates')
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
        manual_topic=args.manual_topic,
        manual_control_topic=args.manual_control_topic,
        high_threshold_topic=args.high_threshold_topic,
        low_threshold_topic=args.low_threshold_topic,
        high_threshold=args.high_threshold,
        low_threshold=args.low_threshold
    )
    controller.run()
