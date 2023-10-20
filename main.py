#!/usr/bin/env python3
"""
Water Level Control System - Main Script
This script runs both the water level simulator and pump controller
in separate threads.

Created: May 1, 2023
"""

import threading
import logging
import time
import argparse
from src.water_level_server.water_level_simulator import WaterLevelSimulator, DEFAULT_BROKER, DEFAULT_PORT, \
    DEFAULT_LEVEL_TOPIC, DEFAULT_PUMP_TOPIC, DEFAULT_MANUAL_TOPIC, DEFAULT_TANK_HEIGHT, \
    DEFAULT_INTERVAL, DEFAULT_USAGE_RATE, DEFAULT_TANK_DIAMETER, DEFAULT_FILL_RATE
from src.middleware.pump_controller import PumpController, DEFAULT_HIGH_THRESHOLD, DEFAULT_LOW_THRESHOLD, \
    DEFAULT_MANUAL_CONTROL_TOPIC, DEFAULT_HIGH_THRESHOLD_TOPIC, DEFAULT_LOW_THRESHOLD_TOPIC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WaterControlSystem")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Water Level Control System')
    parser.add_argument('--broker', default=DEFAULT_BROKER, help='MQTT broker address')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='MQTT broker port')
    parser.add_argument('--level-topic', default=DEFAULT_LEVEL_TOPIC, help='MQTT topic for water level')
    parser.add_argument('--pump-topic', default=DEFAULT_PUMP_TOPIC, help='MQTT topic for pump status')
    parser.add_argument('--manual-topic', default=DEFAULT_MANUAL_TOPIC, help='MQTT topic for manual mode')
    parser.add_argument('--manual-control-topic', default=DEFAULT_MANUAL_CONTROL_TOPIC, help='MQTT topic for manual control')
    parser.add_argument('--high-threshold-topic', default=DEFAULT_HIGH_THRESHOLD_TOPIC, help='MQTT topic for high threshold')
    parser.add_argument('--low-threshold-topic', default=DEFAULT_LOW_THRESHOLD_TOPIC, help='MQTT topic for low threshold')
    parser.add_argument('--tank-height', type=float, default=DEFAULT_TANK_HEIGHT, help='Tank height in cm')
    parser.add_argument('--tank-diameter', type=float, default=DEFAULT_TANK_DIAMETER, help='Tank diameter in cm')
    parser.add_argument('--interval', type=float, default=DEFAULT_INTERVAL, help='Update interval in seconds')
    parser.add_argument('--usage-rate', type=float, default=DEFAULT_USAGE_RATE, help='Water usage rate in cm per interval')
    parser.add_argument('--fill-rate', type=float, default=DEFAULT_FILL_RATE, help='Fill rate in cm per interval when pump is on')
    parser.add_argument('--high-threshold', type=float, default=DEFAULT_HIGH_THRESHOLD, help='High water level threshold percentage')
    parser.add_argument('--low-threshold', type=float, default=DEFAULT_LOW_THRESHOLD, help='Low water level threshold percentage')
    return parser.parse_args()

def main():
    """Main function to run both simulator and controller."""
    args = parse_arguments()
    
    # Create simulator and controller instances
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
    
    # Start simulator and controller in separate threads
    simulator_thread = threading.Thread(target=simulator.run)
    controller_thread = threading.Thread(target=controller.run)
    
    simulator_thread.daemon = True
    controller_thread.daemon = True
    
    simulator_thread.start()
    controller_thread.start()
    
    logger.info("Water Level Control System started")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("System stopped by user")
        
if __name__ == "__main__":
    main()
