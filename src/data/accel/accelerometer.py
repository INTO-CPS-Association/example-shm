# pylint: disable=W0107
import abc
from typing import Tuple, Optional, List
import numpy as np

class IAccelerometer(abc.ABC):
    @abc.abstractmethod
    def read(self, requested_samples: int) -> Tuple[int, np.ndarray]:
        """
        Read and return the requested number of accelerometer samples from the buffer.

        Parameters:
            requested_samples (int): The number of samples to retrieve.

        Returns:
            Tuple[int, np.ndarray]:
                - status: 1 if the requested number of samples was returned,
                          0 if fewer samples were available.
                - data: A NumPy array containing the retrieved samples.
        """
        pass


    @abc.abstractmethod
    def get_batch_size(self) -> Optional[int]:
        """
        Get the number of samples in the first data batch.

        Returns:
            int or None: The size of the first batch, or None if no data is available.
        """
        pass


    @abc.abstractmethod
    def get_sorted_keys(self) -> List[int]:
        """
        Get the sorted list of keys (samples since data first acquisition) available in the buffer.

        Returns:
            List[int]: Sorted keys representing batches of data.
        """
        pass


    @abc.abstractmethod
    def get_samples_for_key(self, key: int) -> Optional[List[float]]:
        """
        Get the list of samples for a given key.

        Parameters:
            key (int): The identifier for the desired data batch.

        Returns:
            List[float] or None: A copy of the sample list if the key exists, otherwise None.
        """
        pass


    @abc.abstractmethod
    def clear_used_data(self, start_key: int, samples_to_remove: int) -> None:
        """
        Remove old and used data from the buffer.

        Parameters:
            start_key (int): The first key from which data will be retained.
            samples_to_remove (int): The number of samples to remove starting from `start_key`.
        """
        pass
