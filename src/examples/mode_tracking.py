import numpy as np
from data.comm.mqtt import load_config
from data.accel.hbk.aligner import Aligner
from methods import sys_id as sysID
from methods import model_update_module as MT

# pylint: disable=R0914
def run_mode_tracking_with_local_sysid(config_path):
    number_of_minutes = 0.5
    config = load_config(config_path)
    mqtt_config = config["MQTT"]

    # Setting up the client and extracting Fs
    data_client, fs = sysID.setup_client(mqtt_config)

    # Setting up the aligner
    data_topic_indexes = [0, 2]
    selected_topics = [mqtt_config["TopicsToSubscribe"][i] for i in data_topic_indexes]
    aligner = Aligner(data_client, topics=selected_topics)

    aligner_time = None
    while aligner_time is None:
        oma_output, aligner_time = sysID.get_oma_results(number_of_minutes, aligner, fs)
    data_client.disconnect()

    # Mode Track
    cleaned_values, median_frequencies, confidence_intervals = MT.run_mode_track(
        oma_output)

    median_frequencies = []
    mode_shapes_list = []

    for cluster in cleaned_values:
        mode_shapes = cluster["mode_shapes"]   # shape: (n_modes_in_cluster, n_channels)
        median_shape = np.median(mode_shapes, axis=0)  # median across modes
        median_frequencies.append(cluster["median"])
        mode_shapes_list.append(median_shape)

    # Convert to numpy arrays
    median_frequencies = np.array(median_frequencies)
    mode_shapes_array = np.array(mode_shapes_list)  # shape: (n_clusters, n_channels)
    print("Mode shapes:", mode_shapes_array)
    print("\nMedian frequencies:", median_frequencies)
    print("\nConfidence intervals:", confidence_intervals)


def run_mode_tracking_with_remote_sysid(config_path):
    config = load_config(config_path)
    cleaned_values, median_frequencies, confidence_intervals = (
        MT.subscribe_and_get_cleaned_values(config_path)
    )
    print("Cleaned values:", cleaned_values)
    print("Tracked frequencies:", median_frequencies)
    print("\nConfidence intervals:", confidence_intervals)
