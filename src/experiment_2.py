import time
import numpy as np # pylint: disable=unused-import
import uuid

# Project imports
from data.sources.mqtt import setup_mqtt_client, load_config  # type: ignore
from data.accel.hbk.alligner import Alligner  # type: ignore


def main():
    config = load_config("config/r-pi.json")
    mqtt_config = config["MQTT"]


    topic_indexes = [0,1] # Indexes of the topics/channels to allign

    # Resolve topic names from config
    all_topics = config["MQTT"]["TopicsToSubscribe"]
    selected_topics = [all_topics[i] for i in topic_indexes]

    mqtt_client, _ = setup_mqtt_client(mqtt_config, topic_index=topic_indexes[0])
    mqtt_client.connect(mqtt_config["host"], mqtt_config["port"], 60)
    mqtt_client.loop_start()

    # We might need to give it some time before strating allignment,
                # so we make sure that there is enough data to allign.

    # pass actual topic as string
    alligner = Alligner(mqtt_client, topics=selected_topics, map_size=2560)

    while True:
        time.sleep(5)
        data = alligner.extract(100)
        if data.shape[0] == 0:
            print("Not enough aligned data yet.")
        else:
            print(f"Extracted aligned data shape: {data.shape}\n{data}")
            break
        time.sleep(1)


if __name__ == "__main__":
    main()




