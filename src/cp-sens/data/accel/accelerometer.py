import abc

# multiplier to convert time from
us_multiplier = 1000000 # factor to convert time to microseconds

class IAccelerometer(abc.ABC):
    @abc.abstractmethod
    def read() -> dict:
        """
        This method provides a single accelerometer reading.
        A sample reading is:
        sample = {
        'timestamp': 0,
        'accel':  {
            'x': 0,
            'y': 0,
            'z': 0
            }
        }
        """
        pass

