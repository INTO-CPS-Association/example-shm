import sys
import matplotlib.pyplot as plt
from methods import sys_id as sysID
from data.comm.mqtt import load_config
from data.accel.hbk.aligner import Aligner
from functions.natural_freq import plot_natural_frequencies


def run_experiment_3_plot(config_path):
    number_of_minutes = 0.2
    config = load_config(config_path)
    mqtt_config = config["MQTT"]

    # Setting up the client and extracting Fs
    data_client, fs = sysID.setup_client(mqtt_config)

    # Setting up the aligner
    data_topic_indexes = [0, 2]
    selected_topics = [mqtt_config["TopicsToSubscribe"][i] for i in data_topic_indexes]
    aligner = Aligner(data_client, topics=selected_topics)

    fig_ax = None
    aligner_time = None
    while aligner_time is None:
        results, aligner_time = sysID.get_oma_results(number_of_minutes, aligner, fs)
    data_client.disconnect()
    fig_ax = plot_natural_frequencies(results['Fn_poles'], freqlim=(0, 75), fig_ax=fig_ax)
    plt.show(block=True)
    sys.stdout.flush()


def run_experiment_3_print(config_path):
    number_of_minutes = 0.2
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
        results, aligner_time = sysID.get_oma_results(number_of_minutes, aligner, fs)
    data_client.disconnect()
    sys.stdout.flush()

    print(f"\n System Frequencies \n {results['Fn_poles']}")
    print(f"\n Cov \n{results['Fn_poles_cov']}")
    print(f"\n damping_ratios  \n{results['Xi_poles']}")
    print(f"\n cov_damping \n{results['Xi_poles_cov']}")


def run_experiment_3_publish(config_path):
    number_of_minutes = 0.02
    config = load_config(config_path)
    mqtt_config = config["MQTT"]
    publish_config = config["sysID"]

    # Setting up the client for getting accelerometer data
    data_client, fs = sysID.setup_client(mqtt_config)

    # Setting up the aligner
    data_topic_indexes = [0, 2]
    selected_topics = [mqtt_config["TopicsToSubscribe"][i] for i in data_topic_indexes]
    aligner = Aligner(data_client, topics=selected_topics)

    # Setting up the client for publishing OMA results
    publish_client, _ = sysID.setup_client(publish_config)  # fs not needed here

    sysID.publish_oma_results(
        number_of_minutes,
        aligner,
        publish_client,
        publish_config["TopicsToSubscribe"][0],
        fs
    )

    print(f"Publishing to topic: {publish_config['TopicsToSubscribe'][0]}")
    sys.stdout.flush()
