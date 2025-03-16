import json
import threading
import struct
import bisect
from collections import deque
import numpy as np

# Project Imports
from data.accel.accelerometer import IAccelerometer
from data.accel.constants import MAX_FIFO_SIZE


class Accelerometer(IAccelerometer):
    def __init__(
        self,
        mqtt_client,
        topic: str = "accelerometer/data",
        fifo_size: int = MAX_FIFO_SIZE,
        axis: tuple = [
            "x",
            "y",
            "z"]):
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
        self._fifo_size = fifo_size
        self._fifo = deque(maxlen=self._fifo_size)
        self._timestamps = deque(maxlen=fifo_size)
        self._lock = threading.Lock()

        # Setting up MQTT callback
        self.mqtt_client.on_message = self._on_message
        self.mqtt_client.subscribe(self.topic, qos=1)

        self.mqtt_client.loop_start()

    def _on_message(self, client, userdata, msg):
        """Handles incoming MQTT messages."""
        print(f"Received message on topic {msg.topic}: {msg.payload}")

        def safe_process():  # This ensures that an exception does not crash the entire thread
            try:
                self._process_message(msg)
            except Exception as e:
                print(f"Error processing message: {e}")

        threading.Thread(target=safe_process, daemon=True).start()

    def _process_message(self, msg):
        """
        Processes incoming MQTT messages and extracts accelerometer data.

        JSON-based messages containing acceleration values.

        Workflow:
        - If the message is empty, it is ignored.
        - If the message is JSON:
            - Extracts acceleration values from the "data" or "accel_readings" field.
            - Extracts the timestamp from the "descriptor" field.
            - Ensures FIFO buffer size constraints before inserting.
            - Uses `bisect_left` to maintain sorted timestamp order.

        Parameters:
            msg (paho.mqtt.client.MQTTMessage): The incoming MQTT message.

        Raises:
            json.JSONDecodeError: If JSON parsing fails.
        """
        if not msg.payload or msg.payload == b'':
            print(f" Received an empty : {msg.payload!r}, ignoring it.")
            return
        # Check if the payload is JSON
        if msg.payload.startswith(b"{"):
            print(" Processing JSON message")
            try:
                payload_str = msg.payload.decode("utf-8").strip()
                data = json.loads(payload_str)

                # Extract values (two different format examples)
                if "data" in data and "values" in data["data"]:
                    values = data["data"]["values"]
                elif "accel_readings" in data:
                    accel = data["accel_readings"]
                    values = [accel["x"], accel["y"], accel["z"]]
                else:
                    print("Invalid JSON format")
                    return

                # Validate values
                if len(values) < 3:  # In case we do not have all x y z
                    print(f"Insufficient values: {values}")
                    return

                # Create standardized array
                data_array = np.array(values[:3], dtype=np.float64)

                # Extract timestamp
                timestamp = data["descriptor"]["timestamp"]

                with self._lock:
                    # Ensure we don't exceed FIFO size before inserting
                    while len(self._fifo) >= self._fifo_size:
                        # If FIFO is full then remove the oldest sample
                        removed_timestamp = self._timestamps.popleft()
                        removed_sample = self._fifo.popleft()
                        print(
                            f"Trimming FIFO: Removedd sample {
                                removed_sample[0]} with timestamp {removed_timestamp}")

                # Convert timestamps to a sorted list for indexing
                ts_list = list(self._timestamps)
                # Find correct position using bisect
                idx = bisect.bisect_left(ts_list, timestamp)
                # Insert in correct order
                self._timestamps.insert(idx, timestamp)
                self._fifo.insert(idx, data_array)

            except json.JSONDecodeError:
                print("JSON decoding failed")

        elif isinstance(msg.payload, bytes) and not msg.payload.startswith(b"{"):
            print(" Processing binary message")
        try:
            raw_payload = msg.payload

            # Validate payload size
            if len(raw_payload) != 156:
                print(
                    f" Invalid binary payload size: {
                        len(raw_payload)} (expected 156 bytes)")
                return
            else:
                print(" Payload size is valid (156 bytes)")

            # Extract descriptor header
            descriptor = struct.unpack("<HHQQQ", raw_payload[:28])
            descriptor_length, metadata_version, seconds_since_epoch, nanoseconds, samples_from_daq_start = descriptor
            # Extract data payload (32 floats)
            accel_values = struct.unpack("<32f", raw_payload[28:156])
            print(f" Extracted binary values: {accel_values}")
            # Validate values
            if len(accel_values) < 3:
                print("Insufficient binary values")
                return
            else:
                print("Extracted 32 binary values")

            # Ensure each array has exactly 3 elements
            num_samples = len(accel_values) // 3
            # Create standardized arrays for all 32 samples
            data_arrays = [np.array(
                accel_values[i * 3:(i + 1) * 3], dtype=np.float64) for i in range(num_samples)]
            print(f" Data arrays: {data_arrays}")

            # Calculate timestamps for each sample
            sampling_rate = 512.0  # Based on metadata
            time_increment = 1.0 / sampling_rate  # Time between samples in seconds

            with self._lock:
                for i, data_array in enumerate(data_arrays):
                    # Calculate timestamp for this sample
                    sample_timestamp = seconds_since_epoch + \
                        (nanoseconds / 1e9) + (i * time_increment)

                    # Ensure we don't exceed FIFO size before inserting
                    while len(self._fifo) >= self._fifo_size:
                        # If FIFO is full then remove the oldest sample
                        removed_timestamp = self._timestamps.popleft()
                        removed_sample = self._fifo.popleft()
                        print(
                            f" Trimming FIFO: Removed sample {
                                removed_sample[0]} with timestamp {removed_timestamp}")

                    # Convert timestamps to a sorted list for indexing
                    ts_list = list(self._timestamps)

                    # Find correct position using bisect
                    idx = bisect.bisect_left(ts_list, sample_timestamp)

                    # Insert in correct order
                    self._timestamps.insert(idx, sample_timestamp)
                    self._fifo.insert(idx, data_array)

        except struct.error as e:
            print(f"Binary decoding failed: {e}")

    def read(self, requested_samples: int) -> (int, np.ndarray):  # type: ignore
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
        with self._lock:
            available = len(self._fifo)
            # If requested samples are more than available, return as many as
            # possible
            if available >= requested_samples:
                status = 1
                # Get the latest `requested_samples` elements (from the right)
                ret_samples = [sample[:3]
                               for sample in list(self._fifo)[-requested_samples:]]
            else:
                status = 0
                ret_samples = [sample[:3] for sample in list(
                    self._fifo)]  # Get all available samples
        return status, np.array(ret_samples)
