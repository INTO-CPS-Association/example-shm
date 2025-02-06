from datetime import datetime
from sense_hat import SenseHat
from .accelerometer import IAccelerometer, us_multiplier

"""
Collects one reading from STM LSM9DS1 IMU
available on the senseHAT

TODO: This class works correctly only if it is
1) Raspberry Pi with senseHAT installed on it
2) used in non virtual environments (no venv)
"""
class senseHAT(IAccelerometer):
    sense = SenseHat()

    def read(self) -> dict:
        accel = self.sense.get_accelerometer_raw()
        # represents time at resolution of a microsecond
        # but depends on the underlying clock
        timestamp = datetime.timestamp(datetime.now())
        key = round(timestamp*us_multiplier)
        sample = {
            'timestamp': timestamp,
            'acceleration': accel
            }
        return sample
