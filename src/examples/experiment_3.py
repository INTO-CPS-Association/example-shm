from methods import sys_id as sysID
from data.comm.mqtt import load_config
from data.accel.hbk.aligner import Aligner
from data.functions.natural_freq import plot_natural_frquencies


def run_experiment_3_plot(config_path):
    number_of_minutes = 2
    config = load_config(config_path)
    mqtt_config = config["MQTT"]

    # Extracting the Sampling frequency from metadata (topix_index 1 is assumed to be metadata)
    fs = sysID.extract_fs_from_metadata(mqtt_config)

    # Setting up the client
    data_client = sysID.setup_client(mqtt_config)

    # Setting up the aligner
    data_topic_indexes = [0, 2]
    selected_topics = [mqtt_config["TopicsToSubscribe"][i] for i in data_topic_indexes]
    aligner = Aligner(data_client, topics=selected_topics)

    fig_ax = None
    while True:
        aligner_time = None
        while aligner_time is None:
            results, aligner_time = sysID.get_oma_results(number_of_minutes, aligner)
        fig_ax = plot_natural_frquencies(results['Fn_poles'],  fig_ax)



def run_experiment_3_print(config_path):
    number_of_minutes = 2
    config = load_config(config_path)
    mqtt_config = config["MQTT"]

    # Extracting the Sampling frequency from metadata (topix_index 1 is assumed to be metadata)
    fs = sysID.extract_fs_from_metadata(mqtt_config)

    # Setting up the client
    data_client = sysID.setup_client(mqtt_config)

    # Setting up the aligner
    data_topic_indexes = [0, 2]
    selected_topics = [mqtt_config["TopicsToSubscribe"][i] for i in data_topic_indexes]
    aligner = Aligner(data_client, topics=selected_topics)

    aligner_time = None
    while aligner_time is None:
        results, aligner_time = sysID.get_oma_results(number_of_minutes, aligner)
    print(f"\n System Frequencies \n {results['Fn_poles']}")
    print(f"\n Cov \n{results['Fn_poles_cov']}")
    print(f"\n damping_ratios  \n{results['Xi_poles']}")
    print(f"\n cov_damping \n{results['Xi_poles_cov']}")


def run_experiment_3_publish(config_path):
    number_of_minutes = 2
    config = load_config(config_path)
    mqtt_config = config["MQTT"]
    publish_config = config["sysID"]

    # Extracting the Sampling frequency from metadata (topix_index 1 is assumed to be metadata)
    fs = sysID.extract_fs_from_metadata(mqtt_config)

    # Setting up the client for getting accelerometer data
    data_client = sysID.setup_client(mqtt_config)

    # Setting up the aligner
    data_topic_indexes = [0, 2]
    selected_topics = [mqtt_config["TopicsToSubscribe"][i] for i in data_topic_indexes]
    aligner = Aligner(data_client, topics=selected_topics)

    # Setting up the client for publishing OMA results
    publish_client = sysID.setup_client(publish_config)

    sysID.publish_oma_results(number_of_minutes, aligner, publish_client
                            , publish_config["TopicsToSubscribe"][0])
    print(f"Publishing to topic: {publish_config["TopicsToSubscribe"][0]}")
