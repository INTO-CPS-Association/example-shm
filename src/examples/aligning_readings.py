import time

from data.comm.mqtt import setup_mqtt_client, load_config, shutdown  # type: ignore
from data.accel.hbk.aligner import Aligner


def align_acceleration_readings(config_path):
    config = load_config(config_path)
    sysid_config = config["sysid"]

    all_topics = sysid_config["TopicsToSubscribe"]

    mqtt_client = setup_mqtt_client(sysid_config, sysid_config["TopicsToSubscribe"][0])
    mqtt_client.connect(sysid_config["host"], sysid_config["port"], 60)
    mqtt_client.loop_start()

    aligner = Aligner(mqtt_client, topics=all_topics, map_size=2560)

    while True:
        time.sleep(1)
        data, utime = aligner.extract(16)
        if data.shape[0] == 0:
            print("Not enough aligned data yet.")
        else:
            print(f"Collected this batch at: {utime}")
            print(f"Extracted aligned data shape: {data.shape}\n{data}")
            break
        time.sleep(1)
    shutdown(mqtt_client, "aligner example")
