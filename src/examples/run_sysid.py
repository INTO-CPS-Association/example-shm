import sys
import time
import matplotlib.pyplot as plt
from data.comm.mqtt import load_config
from data.accel.hbk.aligner import Aligner
from functions.plot_sysid import (plot_stabilization_diagram, plot_pre_stabilization_diagram)
from methods import sysid as sysID
from methods.constants import PARAMS


def setup_sysid(config_path, data_topic_indexes):
    """
    Helper function to set up sysid (Operational Modal Analysis).

    Parameters:
        config_path (str): Path to the configuration file.
        data_topic_indexes (list): Indexes of topics to subscribe to.

    Returns:
        tuple: (aligner, data_client, fs)
    """
    config = load_config(config_path)
    mqtt_config = config["MQTT"]

    # Setting up the client and extracting Fs
    data_client, fs = sysID.setup_client(mqtt_config)

    # Setting up the aligner
    selected_topics = [mqtt_config["TopicsToSubscribe"][i] for i in data_topic_indexes]
    aligner = Aligner(data_client, topics=selected_topics)

    return aligner, data_client, fs


def run_sysid_and_plot(config_path):
    number_of_minutes = 1
    data_topic_indexes = [0, 2, 3, 4]
    aligner, data_client, fs = setup_sysid(config_path, data_topic_indexes)

    fig_ax1 = None
    fig_ax = None
    aligner_time = None
    t1 = time.time()
    while aligner_time is None:
        time.sleep(0.1)
        t2 = time.time()
        t_text = f"Waiting for data for {round(t2-t1,1)} seconds"
        print(t_text,end="\r")
        results, aligner_time = sysID.get_sysid_results(number_of_minutes, aligner, fs)
    data_client.disconnect()
    print(aligner_time)
    fig_ax1 = plot_pre_stabilization_diagram(results, PARAMS, fig_ax=fig_ax1)
    fig_ax = plot_stabilization_diagram(results, PARAMS, fig_ax=fig_ax)
    plt.show(block=True)
    sys.stdout.flush()


def run_sysid_and_print(config_path):
    number_of_minutes = 0.2
    data_topic_indexes = [0, 2, 3, 4]
    aligner, data_client, fs = setup_sysid(config_path, data_topic_indexes)

    aligner_time = None
    t1 = time.time()
    while aligner_time is None:
        time.sleep(0.1)
        t2 = time.time()
        t_text = f"Waiting for data for {round(t2-t1,1)} seconds"
        print(t_text,end="\r")
        results, aligner_time = sysID.get_sysid_results(number_of_minutes, aligner, fs)
    data_client.disconnect()
    sys.stdout.flush()

    print(f"\n System Frequencies \n {results['Fn_poles']}")
    print(f"\n Cov \n{results['Fn_poles_cov']}")
    print(f"\n damping_ratios  \n{results['Xi_poles']}")
    print(f"\n cov_damping \n{results['Xi_poles_cov']}")


def run_sysid_and_publish(config_path):
    number_of_minutes = 0.2
    data_topic_indexes = [0, 2, 3, 4]
    aligner, data_client, fs = setup_sysid(config_path, data_topic_indexes)
    publish_config = load_config(config_path)["sysID"]

    # Setting up the client for publishing sysid results
    publish_client, _ = sysID.setup_client(publish_config)  # fs not needed here

    publish_result = sysID.publish_sysid_results(
        number_of_minutes,
        aligner,
        publish_client,
        publish_config["TopicsToSubscribe"][0],
        fs
    )

    if publish_result is True:
        print(f"Publishing to topic: {publish_config['TopicsToSubscribe'][0]}")
    data_client.disconnect()
    sys.stdout.flush()


def live_sysid_and_publish(config_path):
    number_of_minutes = 1
    data_topic_indexes = [0, 2, 3, 4]
    aligner, data_client, fs = setup_sysid(config_path, data_topic_indexes)
    publish_config = load_config(config_path)["sysID"]

    # Setting up the client for publishing sysid results
    publish_client, _ = sysID.setup_client(publish_config)  # fs not needed here

    publish_result = True
    while publish_result:
        publish_result = sysID.publish_sysid_results(
            number_of_minutes,
            aligner,
            publish_client,
            publish_config["TopicsToSubscribe"][0],
            fs
        )
        if publish_result is True:
            print(f"Publishing to topic: {publish_config['TopicsToSubscribe'][0]}")
