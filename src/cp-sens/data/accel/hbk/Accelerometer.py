
import json
import time
import threading
import  numpy as np
from accel.accelerometer import IAccelerometer, us_multiplier
from sources import mqtt


class Accelerometer(IAccelerometer):
    def __init__(self, mqtt_client, topic: str = "accelerometer/data"):
        """
        Initializes the Accelerometer instance with a pre-configured MQTT client.
        
        Parameters:
            mqtt_client: A pre-configured and connected MQTT client.
            topic (str): The MQTT topic to subscribe to. Defaults to "accelerometer/data"
        """
        self.mqtt_client = mqtt_client
        self.topic = topic
        self._message_event = threading.Event()
        self._message_payload = None

        # Assign the internal on_message handler.
        self.mqtt_client.on_message = self._on_message
        self.mqtt_client.subscribe(self.topic)
        self.mqtt_client.loop_start()
        time.sleep(1)

    def _on_message(self, client, userdata, msg):
        """
        Internal handler for MQTT messages.
        Decodes the message payload and signals data availability.
        """
        try:
            payload_str = msg.payload.decode("utf-8")
            data = json.loads(payload_str)
        except Exception:
            data = {}
        self._message_payload = data
        self._message_event.set()

def read(self, axis: list = ['x', 'y', 'z'], samples: int = 1) -> dict:
    """
    Reads accelerometer data from MQTT messages.
    
    Parameters:
        axis (list): List of axes to include in the result. Defaults to ['x', 'y', 'z'].
        samples (int): Maximum number of samples to collect (capped at 500). The function returns as soon as data is available.
    
    Returns:
        dict: A dictionary containing a timestamp and an 'accel' dictionary with sensor data.
              If more than one sample is collected, the values are averaged.
    
    Raises:
        TimeoutError: If no data is received within the overall timeout period.
    """
    max_samples = min(samples, 500)
    collected_samples = []
    overall_timeout = 5.0  # total seconds to try collecting samples
    poll_interval = 0.1    # seconds between polling _message_event
    start_time = time.time()

    # Attempt to collect up to max_samples within the overall timeout.
    while (time.time() - start_time) < overall_timeout and len(collected_samples) < max_samples:
        if self._message_event.wait(timeout=poll_interval):
            # A sample is available; add it and clear the event for the next sample.
            collected_samples.append(self._message_payload)
            self._message_event.clear()

    if not collected_samples:
        raise TimeoutError("Timed out waiting for accelerometer data")


    #Average the readings. If only one sample is requested, return it directly.
    if len(collected_samples) == 1:
        result = collected_samples[0]
    else:
        avg = {}
        for ax in axis:
            total = sum(sample.get("accel", {}).get(ax, 0) for sample in collected_samples)
            avg[ax] = total / len(collected_samples)
        result = {
            "timestamp": collected_samples[-1].get("timestamp", int(time.time() * us_multiplier)),
            "accel": avg
        }
    
    # Filter the returned axes to only those requested.
    if axis != ['x', 'y', 'z']:
        result["accel"] = {ax: result["accel"].get(ax, None) for ax in axis}

    return result

def read_numpy(self, axis: list = ['x', 'y', 'z'], samples: int = 1) -> np.ndarray:
    """
    Reads accelerometer data and returns it as a NumPy array.
    Each row corresponds to one sample, and each column corresponds to one of the specified axes.
    
    The `samples` parameter is treated as the maximum number of samples to collect (capped at 500).
    The method polls for incoming samples and returns whichever samples are collected within
    the overall timeout period.
    """
    max_samples = min(samples, 500)
    collected_samples = []
    overall_timeout = 5.0  # seconds to try collecting samples
    poll_interval = 0.1    # seconds between polls
    start_time = time.time()

    while (time.time() - start_time) < overall_timeout and len(collected_samples) < max_samples:
        if self._message_event.wait(timeout=poll_interval):
            # Extract the accelerometer data for the requested axes.
            sample = self._message_payload.get("accel", {})
            collected_samples.append([sample.get(ax, 0) for ax in axis])
            self._message_event.clear()

    if not collected_samples:
        raise TimeoutError("Timed out waiting for accelerometer data")

    # Convert the list of samples into a NumPy array.
    return np.array(collected_samples)
