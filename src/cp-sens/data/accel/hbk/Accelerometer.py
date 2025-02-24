
import os
import json
import time
import threading

import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.abspath(os.path.join(current_dir, "../../"))

if data_dir not in sys.path:
    sys.path.insert(0, data_dir)
from accel.accelerometer import IAccelerometer, us_multiplier
from sources import mqtt

class Accelerometer(IAccelerometer):
    def __init__(self):
        """
        Initializes the Accelerometer instance by setting up the MQTT client.
        Loads MQTT configuration from a JSON file, subscribes to the accelerometer topic,
        and starts the MQTT client loop.
        """
        config_path = os.path.join(current_dir, "../../../config/mqtt.json")
        self.config = mqtt.load_config(config_path)
        
        # Set MQTT client up
        self.mqtt_client = mqtt.setup_mqtt_client(self.config)
        
        # Get the topic to subscribe to
        self.topic = self.config["MQTT"].get("accelerometer_topic", "accelerometer/data") 
        
        # Create a threading event and a variable to store the latest message payload.
        self._message_event = threading.Event()
        self._message_payload = None
        
        # This function captures MQTT messages. And decodes the byte payload. 
        def on_message(client, userdata, msg):
            try:
                payload_str = msg.payload.decode("utf-8")
                data = json.loads(payload_str)
            except Exception:
                data = {}
            self._message_payload = data
            self._message_event.set()
        
        self.mqtt_client.on_message = on_message
        
        # Connect to the MQTT broker and subscribe to the accelerometer topic.
        self.mqtt_client.connect(self.config["MQTT"]["host"],
                                 self.config["MQTT"]["port"],
                                 60)
        self.mqtt_client.subscribe(self.topic)
        self.mqtt_client.loop_start()
        
        time.sleep(1)

    def read(self, axis: list = ['x', 'y', 'z'], samples: int = 1) -> dict:
        """
        Reads accelerometer data from MQTT messages.
        
        Parameters:
            axis (list): List of axes to include in the result. Defaults to ['x', 'y', 'z'].
            samples (int): Number of samples to collect and average. Defaults to 1.
        
        Returns:
            dict: A dictionary containing a timestamp and an 'accel' dictionary with sensor data.
                  Example:
                  {
                      "timestamp": 1620345678901234,
                      "accel": {
                          "x": 0.12,
                          "y": -0.03,
                          "z": 0.98
                      }
                  }
                  
        Raises:
            TimeoutError: If no MQTT message is received within the timeout period.
        """
        collected_samples = []
        for _ in range(samples):
            self._message_event.clear()
            # Wait up to 5 seconds for a new MQTT message.
            if not self._message_event.wait(timeout=5):
                raise TimeoutError("Timed out waiting for accelerometer data")
            sample = self._message_payload
            collected_samples.append(sample)
        
        #  Average the readings. If only one sample is requested, return it directly.
        if samples == 1:
            result = collected_samples[0]
        else:            
            avg = {}
            for ax in axis:
                total = sum(sample.get("accel", {}).get(ax, 0) for sample in collected_samples)
                avg[ax] = total / samples
            # Use the timestamp from the latest sample (or generate one if missing).
            result = {
                "timestamp": collected_samples[-1].get("timestamp", int(time.time() * us_multiplier)),
                "accel": avg
            }
        
        # If in some case we only need only one ax.
        if axis != ['x', 'y', 'z']:
            result["accel"] = {ax: result["accel"].get(ax, None) for ax in axis}
        
        return result

if __name__ == "__main__":
    print(us_multiplier)
