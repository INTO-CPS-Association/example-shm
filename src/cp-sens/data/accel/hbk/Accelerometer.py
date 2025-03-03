import json
import time
import numpy as np
import concurrent.futures
import threading  
from collections import deque
from accel.accelerometer import IAccelerometer, us_multiplier
from sources import mqtt


class Accelerometer(IAccelerometer):
    def __init__(self, mqtt_client, topic: str = "accelerometer/data", fifo_size: int = 10000, axis: list = ['x', 'y', 'z']):
        """
        Initializes the Accelerometer instance with a pre-configured MQTT client.
        
        Parameters:
            mqtt_client: A pre-configured and connected MQTT client.
            topic (str): The MQTT topic to subscribe to. Defaults to "accelerometer/data".
            fifo_size (int): The maximum number of samples to store in the FIFO buffer.
            axis (list): List of axes to extract from incoming data. Defaults to ['x', 'y', 'z'].
        """
        self.mqtt_client = mqtt_client
        self.topic = topic
        self._axis = axis
        self._fifo = deque(maxlen=fifo_size)
        self._lock = threading.Lock()  

        # Setting the thread pool executor
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

        self.mqtt_client.on_message = self._on_message
        self.mqtt_client.subscribe(self.topic)

        # First thread
        self.executor.submit(self.mqtt_client.loop_forever)
        time.sleep(1)  # Allow time for the connection

            
    def _on_message(self, client, userdata, msg):
        """Handles incoming MQTT messages asynchronously."""
        #Second thread
        self.executor.submit(self._process_message, msg)  

    def _process_message(self, msg):
        """Extracts accelerometer data and appends it to the FIFO buffer while ensuring correct timestamp order."""
        try:
            payload_str = msg.payload.decode("utf-8")
            data = json.loads(payload_str)
        except Exception as e:
            raise ValueError(f"Invalid JSON format received: {e}")

        if "accel_readings" not in data or "timestamp" not in data:
            raise KeyError("Missing 'accel_readings' or 'timestamp' key in MQTT message payload.")

        # Extract accelerometer data and timestamp
        accel_data = data["accel_readings"]
        timestamp = data["timestamp"]
        sample = [accel_data.get(ax, 0) for ax in self._axis] + [timestamp]  # Append timestamp to sample

        with self._lock:
            # If FIFO is empty OR new timestamp is the latest, append normally.
            if len(self._fifo) == 0 or timestamp >= self._fifo[-1][-1]:
                self._fifo.append(sample)
            else:
                # Insert at correct position (manually maintaining order)
                for i in range(len(self._fifo)):
                    if timestamp < self._fifo[i][-1]:  # Compare timestamps
                        self._fifo.insert(i, sample)
                        break  # Stop after inserting at correct position


    def read(self, requested_samples: int) -> (int, np.ndarray):
        """
        Reads the latest accelerometer data from the FIFO buffer.

        Parameters:
            requested_samples (int): The number of most recent samples desired.

        Returns:
            Tuple[int, np.ndarray]:
                - status: 1 if the number of samples returned equals the requested number,
                        0 if fewer samples were available.
                - data: A NumPy array of shape (n_samples, len(axis)), where n_samples is the number of
                        samples returned.

        Note:
            The FIFO buffer is **not emptied**—only the requested latest samples are retrieved.
        """
        with self._lock:  # <-- Lock before reading
            available = len(self._fifo)
        
            # If requested samples are more than available, return as many as possible
            if available >= requested_samples:
                status = 1
                # Get the latest `requested_samples` elements (from the right)
                ret_samples = [sample[:3] for sample in list(self._fifo)[-requested_samples:]]
            else:
                status = 0
                ret_samples = [sample[:3] for sample in list(self._fifo)]  # Get all available samples

        return status, np.array(ret_samples)
