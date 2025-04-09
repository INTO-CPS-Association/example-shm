import threading
import numpy as np #type: ignore

#project imports
from data.accel.hbk.accelerometer import Accelerometer  # type: ignore



class Aligner:
    def __init__(self, mqtt_client, topics: list, map_size=44840, missing_value=np.nan):
        """
        Initializes the Aligner to receive and align data from multiple MQTT topics.

        Parameters:
            mqtt_client: MQTT client instance.
            topics (list): List of MQTT topics (one per channel).
            map_size (int): Maximum number of stored keys for each channel.
            missing_value (float): Value to use when a sample is missing (default: NaN).
        """
        self.mqtt_client = mqtt_client
        self.topics = topics
        self.map_size = map_size
        self.missing_value = missing_value

        self.channels = []
        self._lock = threading.Lock()

        # Create one Accelerometer per topic
        for topic in topics:
            acc = Accelerometer(mqtt_client, topic=topic, map_size=map_size)
            self.channels.append(acc)
            mqtt_client.subscribe(topic, qos=1)
            mqtt_client.message_callback_add(topic, lambda _, __,
                                              msg, acc=acc: acc.process_message(msg))




    def find_continuous_key_groups(self):
        """
        Determines the batch size, finds common keys, and groups them into continuous sequences.
        Returns:
            tuple: (batch_size, grouped_keys) or (None, None) if data is insufficient.
            example of grouped keys: [[96, 128, 160, 192, 224, 256, 288, 320, 352, 384]]
        """
        if not self.channels:
            return None, None

        # Step 1: Determine batch size (By using the length of data samples in first messages,
                                # so all messages should contain the same number of data samples)
        batch_size = None
        for ch in self.channels:
            if ch.data_map:
                first_key = next(iter(ch.data_map))
                batch_size = len(ch.data_map[first_key])
                break
        if batch_size is None:
            return None, None

        # Step 2: Find common keys across channels
        key_sets = [set(ch.data_map.keys()) for ch in self.channels]
        common_keys = sorted(set.intersection(*key_sets))

        # Step 3: Group keys into continuous sequences
        key_groups = []
        current_group = []

        for key in common_keys:
            if not current_group:
                current_group.append(key)
            elif key == current_group[-1] + batch_size:
                current_group.append(key)
            else:
                key_groups.append(current_group)
                current_group = [key]
        if current_group:
            key_groups.append(current_group)

        return batch_size, key_groups


    def extract(self, requested_samples: int) -> np.ndarray:
        """
        Extracts a specified number of aligned samples from all channels.

        This method:
            1. Uses `find_continuous_key_groups()` to determine batch size 
                                    and group keys into continuous aligned blocks.
            2. Searches for the first key group that contains enough samples.
            3. Collects aligned samples across all channels.
            4. Cleans up old and used data from each channel's buffer.

        Parameters:
            requested_samples (int): The total number of samples to extract across all channels.

        Returns:
            np.ndarray: A 2D NumPy array of shape 
                    (channels, requested_samples) containing aligned data.
                        Returns an empty array if alignment is not possible.
        """
        with self._lock:
            batch_size, key_groups = self.find_continuous_key_groups()
            print("Keys",key_groups)
            if batch_size is None or not key_groups:
                return np.empty((0, len(self.channels)), dtype=np.float32)

            # Pick the first group that gives us enough samples
            for group in key_groups:
                total_samples = len(group) * batch_size
                if total_samples >= requested_samples:
                    aligned_data = [[] for _ in self.channels]
                    samples_collected = 0

                    for key in group:
                        entries = [list(ch.data_map[key]) for ch in self.channels]
                        for i in range(batch_size):
                            if samples_collected >= requested_samples:
                                break
                            for ch_idx, channel_data in enumerate(entries):
                                aligned_data[ch_idx].append(channel_data[i])
                            samples_collected += 1

                    # Delete used and older data
                    for ch in self.channels:
                        for k in list(ch.data_map.keys()):
                            if k < group[0]:
                                del ch.data_map[k]
                            elif k in group:
                                for _ in range(min(requested_samples, len(ch.data_map[k]))):
                                    ch.data_map[k].popleft()
                                if not ch.data_map[k]:
                                    del ch.data_map[k]

                    aligned_array = np.array(aligned_data, dtype=np.float32)
                    print(f"Aligned shape: {aligned_array.shape}")
                    return aligned_array

            # No group had enough samples
            return np.empty((0, len(self.channels)), dtype=np.float32)
