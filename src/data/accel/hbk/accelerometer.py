import threading
import struct
from collections import deque
from typing import Tuple, Any, Optional, List
import numpy as np
import paho.mqtt.client as mqtt
# Project Imports
from data.accel.accelerometer import IAccelerometer
from data.accel.constants import MAX_MAP_SIZE
from data.accel.metadata_constants import DESCRIPTOR_LENGTH_BYTES

class Accelerometer(IAccelerometer):
    def __init__(
        self,
        mqtt_client: mqtt.Client,
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
        self.mqtt_client.subscribe(self.topic, qos=1)

        self.mqtt_client.on_message = self._on_message

    # pylint: disable=unused-argument
    def _on_message(self, client: Any, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        """Handles incoming MQTT messages."""
        #print(f"Received message on topic {msg.topic}")

        def safe_process():  # This ensures that an exception does not crash the entire thread
            try:
                self.process_message(msg)
            except Exception as e:
                print(f"Error processing message: {e}")

        threading.Thread(target=safe_process, daemon=True).start()


    def process_message(self, msg: mqtt.MQTTMessage) -> None:
        """
            Processes incoming MQTT messages, extracts accelerometer data,
            and stores it in a dictionary of FIFO queues.

            - Each unique `samples_from_daq_start` gets its own `deque`.
            - If the number of keys in `self.data_map` exceeds `_map_size`, 
            the oldest key is removed (oldest data batch is discarded).
            """
        try:
            raw_payload = msg.payload

            descriptor_length = struct.unpack("<H", raw_payload[:DESCRIPTOR_LENGTH_BYTES])[0]
            (descriptor_length, _, __, ___,
             samples_from_daq_start,) = struct.unpack("<HHQQQ", raw_payload[:descriptor_length])

            # Extract sensor data
            data_payload = raw_payload[descriptor_length:]
            num_samples = len(data_payload) // 4
            accel_values = struct.unpack(f"<{num_samples}f", data_payload)

            # Store each data batch (e.g 32 samples in one message)
            # in the map samples_from_daq_start is used as the key for each batch
            with self._lock:
                if samples_from_daq_start not in self.data_map:
                    self.data_map[samples_from_daq_start] = deque(accel_values)

                total_samples = sum(len(dq) for dq in self.data_map.values())
                # Check if the total samples in the map exceeds the max,
                # then remove the oldest data batch
                while total_samples > self._map_size:
                    oldest_key = min(self.data_map.keys())  # Find the oldest batch
                    oldest_deque = self.data_map[oldest_key]
                    oldest_deque.popleft() # Delete samples from the oldest deque
                    if not oldest_deque:  # Remove the key/deque from the map if it's empty
                        del self.data_map[oldest_key]
                    total_samples = sum(len(dq) for dq in self.data_map.values())
            #print(f" Channel: {self.topic}  Key: {samples_from_daq_start}, Samples: {num_samples}")

        except Exception as e:
            print(f"Error processing message: {e}")


    def get_batch_size(self) -> Optional[int]:
        """
        Returns the number of samples in the first available data batch.
        Useful for determining alignment batch size.
        """
        with self._lock:
            if not self.data_map:
                return None
            first_key = next(iter(self.data_map))
            return len(self.data_map[first_key])


    def get_sorted_keys(self) -> List[int]:
        """
        Returns the sorted list of sample keys currently available.
        """
        with self._lock:
            return sorted(self.data_map.keys())


    def get_samples_for_key(self, key: int) -> Optional[List[float]]:
        """
        Returns a copy of the sample list for a given key,
        or None if the key is not present.
        """
        with self._lock:
            if key in self.data_map:
                return list(self.data_map[key])
            return None


    def clear_used_data(self, start_key: int, samples_to_remove: int) -> None:
        """
        Deletes all keys older than `start_key` and consumes `samples_to_remove`
        samples starting from `start_key`, across subsequent keys in order.
        """
        with self._lock:
            # Delete older keys
            keys_to_delete = [k for k in self.data_map if k < start_key]
            for k in keys_to_delete:
                del self.data_map[k]

            # Remove samples from start_key and onwards until all samples used are removed
            keys = sorted(k for k in self.data_map if k >= start_key)
            remaining_to_remove = samples_to_remove

            for key in keys:
                if remaining_to_remove <= 0:
                    break
                dq = self.data_map[key]
                num_available = len(dq)
                num_to_remove = min(remaining_to_remove, num_available)

                for _ in range(num_to_remove):
                    dq.popleft()

                if not dq:
                    del self.data_map[key]

                remaining_to_remove -= num_to_remove


    def read(self, requested_samples: int) -> Tuple[(int, np.ndarray)]:
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


    def acquire_lock(self)-> threading.Lock:
        return self._lock
