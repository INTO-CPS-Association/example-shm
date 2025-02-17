import json
from datetime import datetime
import queue
import random
from threading import Thread
from time import sleep
from sense_hat import SenseHat

from mqtt_client import MQTT

samples = 5000
time_step=1 #seconds
measurements = {}
accel_queue = queue.Queue()
mqttc = MQTT('config.json')


def accelerometer() -> None:
    us_multiplier = 1000000 # factor to convert time to microseconds
    sense = SenseHat()
    #sense.set_imu_config(compass_disabled, gyro_disabled, acc_enabled)
    sense.set_imu_config(False, False, True)

    for sample in range(0,samples):
        #print('accelerometer collecting sample')
        accel = sense.get_accelerometer_raw()
        #accel = {
        #    'x': random.uniform(-1, 1),
        #    'y': random.uniform(-1, 1),
        #    'z': random.uniform(-1, 1)
        #}
        # represents time at resolution of a microsecond
        # but depends on the underlying clock
        timestamp = datetime.timestamp(datetime.now())
        key = round(timestamp*us_multiplier)
        measurements[key] = {
            'timestamp': timestamp,
            'acceleration': accel
            }
        print(f'accelerometer sample: {measurements[key]}')
        accel_queue.put(accel)
        sleep(time_step)

def publish_acceleration() -> None:
  while True:
    #print('publishing accelerometer sample')
    if not accel_queue.empty():
      accel = accel_queue.get()
      msg = json.dumps(accel)
      mqttc.publish(msg)
    sleep(time_step)


def stop_publishing() -> None:
  mqttc.stop()

def main():
  accel_thread = Thread(target=accelerometer,name='accelerometer')
  accel_thread.start()

  pub = Thread(target=publish_acceleration,name='publish', daemon=True)
  pub.start()

  accel_thread.join()
  stop_publishing()


if __name__ == "__main__":
    main()
