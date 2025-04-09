import time
import numpy as np # pylint: disable=unused-import

# Project imports
from data.accel.hbk.accelerometer import Accelerometer  # type: ignore
from data.sources.mqtt import setup_mqtt_client, load_config  # type: ignore


def main():
    config = load_config("config/production.json")
    mqtt_config = config["MQTT"]

    topic_index = 0
    mqtt_client, selected_topic = setup_mqtt_client(mqtt_config, topic_index)
    mqtt_client.connect(mqtt_config["host"], mqtt_config["port"], 60)
    mqtt_client.loop_start()

    # Initialize Accelerometer
    accelerometer = Accelerometer(
        mqtt_client,
        topic=selected_topic,
        map_size=192)

    # Clear stored data
    with accelerometer.acquire_lock():
        accelerometer.data_map.clear()

    while True:
        time.sleep(1)

        with accelerometer.acquire_lock():
            # This print to see the dictionary
            for key, fifo in sorted(accelerometer.data_map.items()):
                print(f"Key: {key} -> Data: {list(fifo)}\n")
        _, data = accelerometer.read(requested_samples=128)
        print("Data requsted", data)
        break

    mqtt_client.loop_stop()
    print("Data requsted", data)


if __name__ == '__main__':
    main()
