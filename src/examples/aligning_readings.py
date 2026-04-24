import time
from typing import Any, Dict, Optional, Tuple
from data.comm.mqtt import setup_mqtt_client, load_config, shutdown  # type: ignore
from data.accel.hbk.aligner import Aligner


def align_acceleration_readings(config_path):
    config = load_config(config_path)
    sysid_config = config["sysid"]

    all_topics = sysid_config["TopicsToSubscribe"]

    mqtt_client = setup_mqtt_client(sysid_config, sysid_config["TopicsToSubscribe"][0])
    mqtt_client.connect(sysid_config["host"], sysid_config["port"], 60)
    mqtt_client.loop_start()

    aligner = Aligner(mqtt_client, topics=all_topics)

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

def get_data(
        sampling_period: int, aligner: Aligner, fs: float
        ) -> Optional[Tuple[Dict[str, Any], str]]:
    """
    Extracts aligned sensor data and runs system identification (sysID).

    Args:
        sampling_period: How many minutes of data to pass to sysid.
        aligner: An initialized Aligner object.
        fs: Sampling frequency to use in the sysid algorithm.

    Returns:
        A tuple (sysid_output, timestamp) if successful, or None if data is not ready.
    """

    number_of_samples = int(sampling_period * 60 * fs)
    data, timestamp = aligner.extract(number_of_samples)

    if data.size < number_of_samples:
        return None, None

    return data, timestamp.isoformat()

def wait_for_data(number_of_minutes: float, aligner: Aligner,
                          fs: float) -> Optional[Tuple[Dict[str, Any],str]]:
    aligner_time = None
    t1 = time.time()
    try:
        while aligner_time is None:
            time.sleep(0.1)
            t2 = time.time()
            t_text = f"Waiting for data for {round(t2-t1,1)} seconds"
            print(t_text,end="\r")
            data, aligner_time = get_data(number_of_minutes, aligner, fs)

            if (t2-t1) > 100*number_of_minutes*60:
                raise RuntimeError("Aligned data not received in time")

        return data, aligner_time
    except KeyboardInterrupt as exc:
        raise RuntimeError("Keyboard interrupt") from exc

from methods import sysid as sysID

