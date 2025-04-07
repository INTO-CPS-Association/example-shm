import threading
import struct
from collections import deque
import numpy as np

# Project Imports
from data.accel.accelerometer import IAccelerometer
from data.accel.constants import MAX_MAP_SIZE

class Accelerometer(IAccelerometer):
    def __init__(
        self,
        mqtt_client,
        topic: str = "cpsens/d8-3a-dd-f5-92-48/cpsns_Simulator/1/acc/raw/data",
        map_size: int = MAX_MAP_SIZE ):


        """
        Initializes the Accelerometer instance with a pre-configured MQTT client.

        Parameters:
            mqtt_client: A pre-configured and connected MQTT client.
            topic (str): The MQTT topic to subscribe to. Defaults to "channel 0 topic".
            map_size (int): The maximum number of samples to store in the Map.
        """
        self.mqtt_client = mqtt_client

        self.topic = topic
        self._map_size = map_size
        self.data_map = {}
        self._lock = threading.Lock()

        # Setting up MQTT callback
        self.mqtt_client.on_message = self._on_message

    def _on_message(self, _, __, msg):
        """Handles incoming MQTT messages."""
        print(f"Received message on topic {msg.topic}")

        def safe_process():  # This ensures that an exception does not crash the entire thread
            try:
                self._process_message(msg)
            except Exception as e:
                print(f"Error processing message: {e}")

        threading.Thread(target=safe_process, daemon=True).start()


    def _process_message(self, msg):
        """
            Processes incoming MQTT messages, extracts accelerometer data,
            and stores it in a dictionary of FIFO queues.

            - Each unique `samples_from_daq_start` gets its own `deque`.
            - If the number of keys in `self.data_map` exceeds `_map_size`, 
            the oldest key is removed (oldest data batch is discarded).
            """
        try:
            raw_payload = msg.payload

            # The first 2 bytes tells the length of the descriptor
            descriptor_length = struct.unpack("<H", raw_payload[:2])[0]
            (descriptor_length, _, __, ___,
             samples_from_daq_start,) = struct.unpack("<HHQQQ", raw_payload[:descriptor_length])

            # Extract sensor data
            data_payload = raw_payload[descriptor_length:]
            num_samples = len(data_payload) // 4
            accel_values = struct.unpack(f"<{num_samples}f", data_payload)

            # Store each data batch (e.g 32 samples in one message)
            # in the map samples_from_daq_start is used as the key for each batch
            with self._lock:
                self.data_map[samples_from_daq_start] = deque(accel_values)
                # Check if the total samples in the map exceeds the max,
                # then remove the oldest data batch
                while sum(len(deque) for deque in self.data_map.values()) > self._map_size:
                    oldest_key = min(self.data_map.keys())  # Find the oldest batch
                    del self.data_map[oldest_key]  # Remove oldest batch
            print(f" Channel: {self.topic}  Key: {samples_from_daq_start}, Samples: {num_samples}")

        except Exception as e:
            print(f"Error processing message: {e}")


    def read(self, requested_samples: int) -> (int, np.ndarray):
        """
        Reads the oldest accelerometer data from the FIFO buffer and removes only the read samples.

        Parameters:
            requested_samples (int): The number of samples desired.

        Returns:
            Tuple[int, np.ndarray]:
                - status: 1 if the number of samples returned equals the requested number,
                        0 if fewer samples were available.
                - data: A NumPy array of shape (n_samples,).
        """
        with self._lock:
            sorted_keys = sorted(self.data_map.keys())

            samples = []
            samples_collected = 0

            for key in sorted_keys:
                entry = self.data_map[key]  # Access the deque directly

                if samples_collected + len(entry) <= requested_samples:
                    # Take the whole entry and remove it
                    samples.extend(entry)
                    samples_collected += len(entry)
                    del self.data_map[key]
                else:
                    # Take only the required number of samples
                    remaining_samples = requested_samples - samples_collected
                    # Using list here because we need to slice it in order to only take what we need
                    samples.extend(list(entry)[:remaining_samples])
                    for _ in range(remaining_samples):
                        entry.popleft()  # Remove samples from deque
                    samples_collected += remaining_samples
                    break  # Stop once we have enough samples

            samples = np.array(samples, dtype=np.float64)
            status = 1 if samples_collected == requested_samples else 0

        return status, samples


    def acquire_lock(self)->(threading.Lock):
        return self._lock
