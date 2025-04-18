import time
import sys
import numpy as np

from data.accel.hbk.accelerometer import Accelerometer
from data.sources.mqtt import setup_mqtt_client, load_config  # type: ignore

def run_experiment_1(config_path):
    config = load_config(config_path)
    mqtt_config = config["MQTT"]
    topic_index = 0
    mqtt_client, selected_topic = setup_mqtt_client(mqtt_config, topic_index)
    mqtt_client.connect(mqtt_config["host"], mqtt_config["port"], 60)
    mqtt_client.loop_start()

    accelerometer = Accelerometer(
        mqtt_client,
        topic=selected_topic,
        map_size=1920
    )

    with accelerometer.acquire_lock():
        accelerometer.data_map.clear()

    time.sleep(1)
    with accelerometer.acquire_lock():
        for key, fifo in sorted(accelerometer.data_map.items()):
            print(f"Key: {key} -> Data: {list(fifo)}\n")
    _, data = accelerometer.read(requested_samples=256)

    mqtt_client.loop_stop()
    mqtt_client.disconnect()

    print("Data requested", data)
    sys.stdout.flush()


def main(config):
    run_experiment_1(config)

if __name__ == "__main__":
    main()
