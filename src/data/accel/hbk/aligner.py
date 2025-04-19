import threading
from typing import List, Tuple, Optional
from datetime import datetime
import numpy as np

# project imports
from data.accel.aligner import IAligner
from data.accel.hbk.accelerometer import Accelerometer
from data.accel.constants import MAX_MAP_SIZE



class Aligner(IAligner):
    def __init__(self, mqtt_client, topics: list, map_size=MAX_MAP_SIZE, missing_value=np.nan):
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
            mqtt_client.message_callback_add(topic, lambda _,
                                             __, msg, acc=acc: acc.process_message(msg))


    def _get_common_keys(self, batch_size: Optional[int]) -> Optional[List[int]]:
        """
        Gets the sorted list of keys that are common across all channels.

        Returns:
            A sorted list of common keys or None if batch_size is invalid.
        """
        # Get common keys across all channels
        key_sets = [set(ch.get_sorted_keys()) for ch in self.channels]
        if not key_sets or batch_size is None:
            return None
        return sorted(set.intersection(*key_sets))


    def _group_continuous_keys(self, keys: List[int], batch_size: int) -> List[List[int]]:
        """
        Groups sorted keys into continuous sequences based on batch_size.

        Returns:
            A list of key groups (each group is a list of consecutive keys).
        """
        key_groups = []
        current_group = []
        for key in keys:
            if not current_group:
                current_group.append(key)
            elif key == current_group[-1] + batch_size:
                current_group.append(key)
            else:
                key_groups.append(current_group)
                current_group = [key]
        if current_group:
            key_groups.append(current_group)
        return key_groups


    def find_continuous_key_groups(self) -> Tuple[Optional[int], Optional[List[List[int]]]]:
        if not self.channels:
            return None, None

        batch_size = None
        for ch in self.channels:
            batch_size = ch.get_batch_size()
            if batch_size is not None:
                break
        common_keys = self._get_common_keys(batch_size)
        if common_keys is None:
            return None, None
        return batch_size, self._group_continuous_keys(common_keys, batch_size)


    def _extract_aligned_block(self, group: List[int], batch_size: int,
                               requested_samples: int) -> Tuple[np.ndarray, datetime]:
        """
        Extracts samples from the given aligned key group.

        Collects aligned samples across all channels and returns them
        along with the UTC timestamp of the first aligned sample.

        Returns:
            A tuple (aligned_data, utc_time)
        """
        aligned_data = [[] for _ in self.channels]
        samples_collected = 0
        utc_time = datetime.now()

        for key in group:
            entries = [ch.get_samples_for_key(key) for ch in self.channels]
            for i in range(batch_size):
                if samples_collected >= requested_samples:
                    break
                for ch_idx, channel_data in enumerate(entries):
                    if channel_data is not None:
                        aligned_data[ch_idx].append(channel_data[i])
                    else:
                        print(f"Missing data for channel index {ch_idx} skipping")
                samples_collected += 1
            if samples_collected >= requested_samples:
                break

        for ch in self.channels:
            ch.clear_used_data(group[0], requested_samples)

        aligned_array = np.array(aligned_data, dtype=np.float32)
        print(f"Aligned shape: {aligned_array.shape}")
        return aligned_array, utc_time


    def extract(self, requested_samples: int) -> Tuple[np.ndarray, Optional[datetime]]:
        with self._lock:
            batch_size, key_groups = self.find_continuous_key_groups()
            print("Keys", key_groups)

            if batch_size is None or key_groups is None:
                # No data or groups to align, returun empty
                return np.empty((0, len(self.channels)), dtype=np.float32), None

            for group in key_groups:
                total_samples = len(group) * batch_size
                if total_samples >= requested_samples:
                    return self._extract_aligned_block(group, batch_size, requested_samples)
            # No data or groups to align, returun empty
            return np.empty((0, len(self.channels)), dtype=np.float32), None
