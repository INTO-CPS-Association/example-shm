import time

from data.sources.mqtt import setup_mqtt_client, load_config  # type: ignore
from data.accel.hbk.aligner import Aligner


def run_experiment_2(config_path):
    config = load_config(config_path)
    mqtt_config = config["MQTT"]
    topic_indexes = [0,1]

    all_topics = mqtt_config["TopicsToSubscribe"]
    selected_topics = [all_topics[i] for i in topic_indexes]

    mqtt_client, _ = setup_mqtt_client(mqtt_config, topic_index=topic_indexes[0])
    mqtt_client.connect(mqtt_config["host"], mqtt_config["port"], 60)
    mqtt_client.loop_start()

    aligner = Aligner(mqtt_client, topics=selected_topics, map_size=2560)

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


def main(config):
    run_experiment_2(config)

if __name__ == "__main__":
    main()
