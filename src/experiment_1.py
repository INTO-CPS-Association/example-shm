import time
import numpy as np
import logging

# Project imports
from data.accel.hbk.Accelerometer import Accelerometer  # type: ignore
from data.accel.constants import MIN_SAMPLES_NEEDED  # type: ignore
from data.sources.mqtt import setup_mqtt_client, load_config  # type: ignore



def main():
    config = load_config("src/config/mqtt.json")
    mqtt_config = config["MQTT"]["real_server"]

    topic_index = 2
    mqtt_client, selected_topic = setup_mqtt_client(mqtt_config, topic_index)
    mqtt_client.connect(mqtt_config["host"], mqtt_config["port"], 60)
    mqtt_client.loop_start()

    # Initialize Accelerometer
    accelerometer = Accelerometer(mqtt_client, topic=selected_topic, map_size=192)

    # Clear stored data
    with accelerometer._lock:
        accelerometer.data_map.clear()

    while True:
        time.sleep(2.1)

        with accelerometer._lock:  
            for key, fifo in sorted(accelerometer.data_map.items()):
                print(f"Key: {key} -> Data: {list(fifo)}\n")
        status, data = accelerometer.read(requested_samples=128)
        break  

    mqtt_client.loop_stop()
    print("Data",data)

if __name__ == '__main__':
    main()
