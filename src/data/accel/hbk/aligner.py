import threading
from typing import List, Tuple, Optional
from datetime import datetime
import numpy as np

#project imports
from data.accel.hbk.accelerometer import Accelerometer


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
        seen = set()
        # Create one Accelerometer per uniqe topic
        unique_topics = [topic for topic in topics if not (topic in seen or seen.add(topic))]
        for topic in unique_topics:
            seen.add(topic)
            acc = Accelerometer(mqtt_client, topic=topic, map_size=map_size)
            self.channels.append(acc)
            mqtt_client.subscribe(topic, qos=1)
            mqtt_client.message_callback_add(topic, lambda _, __,
                                            msg, acc=acc: acc.process_message(msg))


    def find_continuous_key_groups(self) -> Tuple[Optional[int], Optional[List[List[int]]]]:
        """
        Determines the batch size, finds common keys, and groups them into continuous sequences.
        Returns:
            tuple: (batch_size, grouped_keys) or (None, None) if data is insufficient.
        """
        if not self.channels:
            return None, None

        # Get the batch size from any channel
        batch_size = None
        for ch in self.channels:
            batch_size = ch.get_batch_size()
            if batch_size is not None:
                break

        # Get common keys across all channels
        key_sets = [set(ch.get_sorted_keys()) for ch in self.channels]
        if not key_sets or batch_size is None:
            return None, None
        common_keys = sorted(set.intersection(*key_sets))

        # Group keys into continuous sequences
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
            2. Selects the first group that has enough samples.
            3. Collects aligned samples across all channels using their accessors.
            4. Cleans up used and older data via `clear_used_data()` on each Accelerometer.

        Parameters:
            requested_samples (int): The total number of samples to extract across all channels.

        Returns:
           tuple: (aligned_data, utc_timestamp)
                   aligned_data is a NumPy array of shape (channels, requested_samples)
                   utc_timestamp is the UTC time of the first aligned sample.
            Returns an empty array if alignment is not possible.
        """
        with self._lock:
            batch_size, key_groups = self.find_continuous_key_groups()
            print("Keys", key_groups)

            if batch_size is None or key_groups is None:
                return np.empty((0, len(self.channels)), dtype=np.float32)

            for group in key_groups:
                total_samples = len(group) * batch_size
                if total_samples < requested_samples:
                    continue  # Skip groups that don't have enough samples
                # Proceed with aligned extraction
                aligned_data = [[] for _ in self.channels]
                samples_collected = 0
                utc_time = datetime.utcnow()


                for key in group:
                    entries = [ch.get_samples_for_key(key) for ch in self.channels]
                    for i in range(batch_size):
                        if samples_collected >= requested_samples:
                            break
                        for ch_idx, channel_data in enumerate(entries):
                            aligned_data[ch_idx].append(channel_data[i])
                        samples_collected += 1

                    if samples_collected >= requested_samples:
                        break

                # Clean up used and older data
                for ch in self.channels:
                    ch.clear_used_data(group[0], requested_samples)

                aligned_array = np.array(aligned_data, dtype=np.float32)
                print(f"Aligned shape: {aligned_array.shape}")
                return aligned_array, utc_time

            return np.empty((0, len(self.channels)), dtype=np.float32)
