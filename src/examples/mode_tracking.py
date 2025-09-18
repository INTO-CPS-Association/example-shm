import sys
import time as timing
import matplotlib.pyplot as plt
from data.comm.mqtt import load_config
from data.accel.hbk.aligner import Aligner
from methods.packages import sys_id as sysID
from methods import model_update_module as MT
from functions.sysid_plot import plot_clusters, plot_stabilization_diagram

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

    # Setting up the client and extracting Fs
    data_client, fs = sysID.setup_client(mqtt_config)

    # Setting up the aligner
    selected_topics = [mqtt_config["TopicsToSubscribe"][i] for i in data_topic_indexes]
    print(selected_topics)
    aligner = Aligner(data_client, topics=selected_topics)

    return aligner, data_client, fs

# pylint: disable=R0914
def run_mode_clustering_with_local_sysid(config_path):
    number_of_minutes = 2
    data_topic_indexes = [0, 1]#[0, 2, 3, 4]

    aligner, data_client, fs = setup_oma(config_path, data_topic_indexes)

    t1 = timing.time()
    aligner_time = None
    while aligner_time is None:
        oma_output, aligner_time, oma_params = sysID.get_oma_results(number_of_minutes, aligner, fs)
        t2 = timing.time()
        t_text = f"Waiting for data for {round(t2-t1,1)} seconds"
        print (t_text, end="\r")
    print(t_text)
    data_client.disconnect()

    fig_ax = None
    fig_ax = plot_stabilization_diagram(oma_output,oma_params,fig_ax=fig_ax)

    plt.show(block=True)
    sys.stdout.flush()

    # Mode Track
    cluster_dict_before, cluster_dict = MT.run_mode_clustering(oma_output)

    median_frequencies = []
    for key in cluster_dict.keys():
        median_frequencies.append(cluster_dict[key]['median_f'])
    print("\nMedian frequencies:", median_frequencies)

    fig_ax = None
    fig_ax = plot_clusters(cluster_dict,oma_output,oma_params,fig_ax=fig_ax)

    plt.show(block=True)
    sys.stdout.flush()



def run_mode_tracking_with_remote_sysid(config_path):
    # config = load_config(config_path)
    cluster_dict_initial, cluster_dict = (
        MT.subscribe_and_get_cleaned_values(config_path)
    )
    print("Cleaned values:", cluster_dict['f'])
    print("Tracked frequencies:", cluster_dict['median_f'])
