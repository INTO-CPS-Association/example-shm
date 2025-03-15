from datetime import datetime
import random
from .accelerometer import IAccelerometer, us_multiplier

"""
A dummy accelerometer that generates
random (x,y,z) values in the [-1,1] range
"""
class RandomSource(IAccelerometer):

    def read(self) -> dict:
        accel = {
           'x': random.uniform(-1, 1),
           'y': random.uniform(-1, 1),
           'z': random.uniform(-1, 1)
        }
        # represents time at resolution of a microsecond
        # but depends on the underlying clock
        timestamp = datetime.timestamp(datetime.now())
        key = round(timestamp*us_multiplier)
        sample = {
            'timestamp': timestamp,
            'acceleration': accel
            }
        return sample
