import time

# Project imports
from data.sources.mqtt import setup_mqtt_client, load_config  # type: ignore
from data.accel.hbk.aligner import Aligner  # type: ignore


def main():
    config = load_config("config/production.json")
    mqtt_config = config["MQTT"]


    topic_indexes = [1,1,0,1,0] # Indexes of the topics/channels to align

    # Resolve topic names from config
    all_topics = config["MQTT"]["TopicsToSubscribe"]
    selected_topics = [all_topics[i] for i in topic_indexes]

    mqtt_client, _ = setup_mqtt_client(mqtt_config, topic_index=topic_indexes[0])
    mqtt_client.connect(mqtt_config["host"], mqtt_config["port"], 60)
    mqtt_client.loop_start()


    # pass actual topic as string
    aligner = Aligner(mqtt_client, topics=selected_topics, map_size=2560)

    while True:
        time.sleep(1)
        data, utime = aligner.extract(16)
        if data.shape[0] == 0:
            print("Not enough aligned data yet.")
        else:
            print(f"Colllected this batch at:{utime}")
            print(f"Extracted aligned data shape: {data.shape}\n{data}")
            break
        time.sleep(1)


if __name__ == "__main__":
    main()
