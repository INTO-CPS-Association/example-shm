from typing import Any, Dict, Optional, Tuple, List
import time
from paho.mqtt.client import Client as MQTTClient
from data.comm.mqtt import setup_mqtt_client, load_config  # type: ignore
from data.accel.metadata import extract_metadata
from data.accel.hbk.aligner import Aligner
from methods.constants import DEFAULT_FS
# pylint: disable=C0103

def setup_client(mqtt_config: Dict[str, Any]) -> Tuple[MQTTClient, float]:
    """
    Sets up and starts the MQTT client for subscribing to sensor data.
    Also extracts sampling frequency from metadata if available.

    Args:
        mqtt_config: Configuration dictionary for the MQTT client.

    Returns:
        (Tuple[MQTTClient, float]): A tuple of the connected MQTTClient instance and the extracted sampling frequency.
    """
    try:
        metadata = extract_metadata(mqtt_config)
        fs = metadata["Analysis chain"][0]["Sampling"]
    except Exception:
        print("Failed to extract FS from metadata. Using DEFAULT_FS = ",DEFAULT_FS)
        fs = DEFAULT_FS

    data_client = setup_mqtt_client(mqtt_config, mqtt_config["TopicsToSubscribe"][0])
    data_client.connect(mqtt_config["host"], mqtt_config["port"], 60)
    data_client.loop_start()
    return data_client, fs, metadata


def setup_aligner(config_path, config_name: str = "sysid",
                  data_topic_indexes: List[int] = None) -> Tuple[Aligner, MQTTClient,
                                                          Dict[str,Any], float]:
    """
    Helper function to set up aligner.

    Parameters:
        config_path (str): Path to the configuration file.
        config_name (str): Name of configuration
        data_topic_indexes (list): Indexes of topics to subscribe to.

    Returns:
        Aligner (Aligner): The aligner object for data alignment.
        data_client (MQTTClient): The MQTT client used for data subscription.
        mqtt_config (Dict[str,Any]): Configuration dictionary for the MQTT client.
        fs (float): Sampling frequency.
    """
    config = load_config(config_path)
    mqtt_config = config[config_name]

    # Setting up the client and extracting Fs
    data_client, fs, metadata = setup_client(mqtt_config)

    # Setting up the aligner
    if data_topic_indexes is None:
        data_topic_indexes = list(range(len(mqtt_config["TopicsToSubscribe"])))
    selected_topics = [mqtt_config["TopicsToSubscribe"][i] for i in data_topic_indexes]
    aligner = Aligner(data_client, topics=selected_topics, metadata=metadata)
    return aligner, data_client, mqtt_config, fs

def get_data(
        samples: int, aligner: Aligner
        ) -> Optional[Tuple[Dict[str, Any], str]]:
    """
    Extracts aligned sensor data and runs system identification (sysID).

    Args:
        samples (int): How many minutes of data to pass to sysid.
        aligner: An initialized Aligner object.

    Returns:
        A tuple (sysid_output, timestamp) if successful, or None if data is not ready.
    """

    data, timestamp = aligner.extract(int(samples))

    if data.size < samples:
        return None, None

    return data, timestamp.isoformat()

def wait_for_data(samples: int, aligner: Aligner,
                          fs: float) -> Optional[Tuple[Dict[str, Any],str]]:
    aligner_time = None
    t1 = time.time()
    try:
        while aligner_time is None:
            time.sleep(0.05)
            t2 = time.time()
            t_text = f"Waiting for data for {round(t2-t1,1)} seconds"
            print(t_text,end="\r")
            data, aligner_time = get_data(samples, aligner)

            if (t2-t1) > 100*samples/fs:
                raise RuntimeError("Aligned data not received in time")

        return data, aligner_time
    except KeyboardInterrupt as exc:
        raise RuntimeError("Keyboard interrupt") from exc