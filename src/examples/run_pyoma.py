import sys
import time as timing
import matplotlib.pyplot as plt
from methods.packages import sys_id as sysID
from data.comm.mqtt import load_config
from data.accel.hbk.aligner import Aligner
from functions.sysid_plot import plot_stabilization_diagram
from functions.plot_data import plot_data


def setup_oma(config_path, data_topic_indexes):
    """
    Helper function to set up OMA (Operational Modal Analysis).

    Parameters:
        config_path (str): Path to the configuration file.
        data_topic_indexes (list): Indexes of topics to subscribe to.

    Returns:
        tuple: (aligner, data_client, fs)
    """
    config = load_config(config_path)
    mqtt_config = config["MQTT"]
    print(mqtt_config)

    # Setting up the client and extracting Fs
    data_client, fs = sysID.setup_client(mqtt_config)

    # Setting up the aligner
    selected_topics = [mqtt_config["TopicsToSubscribe"][i] for i in data_topic_indexes]
    print(selected_topics)
    aligner = Aligner(data_client, topics=selected_topics)

    return aligner, data_client, fs

def read_accelerometers_and_plot(config_path):
    number_of_minutes = 0.5
    data_topic_indexes = [0,2]
    aligner, data_client, fs = setup_oma(config_path, data_topic_indexes)

    t1 = timing.time()
    fig_ax = None
    aligner_time = None
    while aligner_time is None:
        data, aligner_time = sysID.get_oma_data(number_of_minutes, aligner, fs)
        t2 = timing.time()
        t_text = f"Waiting for data for {round(t2-t1,1)} seconds"
        print (t_text, end="\r")
    data_client.disconnect()
    print(t_text)

    fig_ax = plot_data(data, fig_ax)

    plt.show(block=True)
    sys.stdout.flush()

def read_accelerometers_and_plot_continuously(config_path):
    number_of_runs = 5
    number_of_minutes = 0.1
    data_topic_indexes = [0,2]
    fig_ax = None

    counter = 0
    while counter < number_of_runs:
        aligner, data_client, fs = setup_oma(config_path, data_topic_indexes)

        t1 = timing.time()
        aligner_time = None
        while aligner_time is None:
            data, aligner_time = sysID.get_oma_data(number_of_minutes, aligner, fs)
            t2 = timing.time()
            t_text = f"Waiting for data for {round(t2-t1,1)} seconds"
            print (t_text, end="\r")
        data_client.disconnect()
        print(t_text)

        fig_ax = plot_data(data, fig_ax)
        plt.show(block=False)
        sys.stdout.flush()

        counter += 1

def run_oma_and_plot(config_path):
    number_of_minutes = 1
    data_topic_indexes = [0,2]
    aligner, data_client, fs = setup_oma(config_path, data_topic_indexes)

    t1 = timing.time()
    fig_ax = None
    aligner_time = None
    while aligner_time is None:
        oma_results, aligner_time, oma_params = sysID.get_oma_results(number_of_minutes,
                                                                      aligner, fs)
        t2 = timing.time()
        t_text = f"Waiting for data for {round(t2-t1,1)} seconds"
        print (t_text, end="\r")
    data_client.disconnect()
    print(t_text)

    fig_ax = plot_stabilization_diagram(oma_results, oma_params, fig_ax)
    plt.show(block=True)
    sys.stdout.flush()

def run_oma_and_plot_continuously(config_path):
    number_of_runs = 5
    number_of_minutes = 1
    data_topic_indexes = [0,2]

    fig_ax = None
    counter = 0
    while counter < number_of_runs:
        aligner, data_client, fs = setup_oma(config_path, data_topic_indexes)

        t1 = timing.time()
        aligner_time = None
        while aligner_time is None:
            oma_results, aligner_time, oma_params = sysID.get_oma_results(number_of_minutes,
                                                                          aligner, fs)
            t2 = timing.time()
            t_text = f"Waiting for data for {round(t2-t1,1)} seconds"
            print (t_text, end="\r")
        data_client.disconnect()
        print(t_text)

        fig_ax = plot_stabilization_diagram(oma_results, oma_params, fig_ax)
        plt.show(block=False)
        sys.stdout.flush()

        counter += 1

def run_oma_and_print(config_path):
    number_of_minutes = 2
    data_topic_indexes = [0, 2]
    aligner, data_client, fs = setup_oma(config_path, data_topic_indexes)

    aligner_time = None
    while aligner_time is None:
        results, aligner_time, _ = sysID.get_oma_results(number_of_minutes, aligner, fs)
    data_client.disconnect()
    sys.stdout.flush()

    print(f"\n System Frequencies \n {results['Fn_poles']}")
    print(f"\n Cov \n{results['Fn_poles_cov']}")
    print(f"\n damping_ratios  \n{results['Xi_poles']}")
    print(f"\n cov_damping \n{results['Xi_poles_cov']}")


def run_oma_and_publish(config_path):
    number_of_minutes = 0.02
    data_topic_indexes = [0, 2]
    aligner, data_client, fs = setup_oma(config_path, data_topic_indexes)
    publish_config = load_config(config_path)["sysID"]

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
    data_client.disconnect()
    sys.stdout.flush()
