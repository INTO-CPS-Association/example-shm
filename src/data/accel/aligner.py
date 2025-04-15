# pylint: disable=W0107
import abc
from datetime import datetime
from typing import List, Optional, Tuple
import numpy as np

class IAligner(abc.ABC):
    @abc.abstractmethod
    def find_continuous_key_groups(self) -> Tuple[Optional[int], Optional[List[List[int]]]]:
        """
        Finds common continuous key groups across all channels.

        Returns:
            Tuple:
                - batch_size (Optional[int]): Size of each data batch if found, else None.
                - key_groups (Optional[List[List[int]]]): 
                            Groups of continuous sample keys common to all channels.
        """
        pass


    @abc.abstractmethod
    def extract(self, requested_samples: int) -> Tuple[np.ndarray, Optional[datetime]]:
        """
        Extracts aligned accelerometer samples from all channels.

        Parameters:
            requested_samples (int): The number of aligned samples to extract.

        Returns:
            Tuple:
                - np.ndarray: A 2D NumPy array of shape (num_channels, num_samples).
                - Optional[datetime]: UTC timestamp 
                            when the aligned samples were extracted, or None on failure.
        """
        pass
