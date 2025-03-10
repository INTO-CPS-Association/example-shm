import abc
import numpy as np
# multiplier to convert time from
us_multiplier = 1000000 # factor to convert time to microseconds

class IAccelerometer(abc.ABC):
    @abc.abstractmethod
    def read(self, requested_samples: int) -> (int, np.ndarray): # type: ignore
        """
        This method provides a single accelerometer reading.
        A sample reading is:
        sample = {
        'timestamp': 0,
        'accel_readings':  {
            'x': 0,
            'y': 0,
            'z': 0
            }
        }
        """
        pass

