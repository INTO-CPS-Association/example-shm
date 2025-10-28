import sys
import time
import matplotlib.pyplot as plt
from data.comm.mqtt import load_config
from data.accel.hbk.aligner import Aligner
from methods import sysid as sysID
from methods import mode_clustering as MC
from methods.constants import PARAMS
from functions.plot_clusters import plot_clusters

# pylint: disable=R0914
def run_mode_clustering_with_local_sysid(config_path):
    number_of_minutes = 1
    config = load_config(config_path)
    mqtt_config = config["MQTT"]

    # Setting up the client and extracting Fs
    data_client, fs = sysID.setup_client(mqtt_config)

    # Setting up the aligner
    data_topic_indexes = [0, 2, 3, 4]
    selected_topics = [mqtt_config["TopicsToSubscribe"][i] for i in data_topic_indexes]
    aligner = Aligner(data_client, topics=selected_topics)

    aligner_time = None
    t1 = time.time()
    while aligner_time is None:
        time.sleep(0.1)
        t2 = time.time()
        t_text = f"Waiting for data for {round(t2-t1,1)} seconds"
        print(t_text,end="\r")
        sysid_output, aligner_time = sysID.get_sysid_results(number_of_minutes, aligner, fs)
    data_client.disconnect()

    # Mode Tracks
    dictionary_of_clusters, median_frequencies = MC.cluster_sysid(
        sysid_output,PARAMS)

    # Print frequencies
    print("\nMedian frequencies:", median_frequencies)

    fig_ax = plot_clusters(dictionary_of_clusters, sysid_output, PARAMS, fig_ax = None)
    plt.show(block=True)
    sys.stdout.flush()

def run_mode_clustering_with_remote_sysid(config_path):
    sysid_output, dictionary_of_clusters, meadian_frequencies = MC.subscribe_and_cluster(config_path,PARAMS)
    fig_ax = plot_clusters(dictionary_of_clusters, sysid_output, PARAMS, fig_ax = None)
    plt.show(block=True)
    sys.stdout.flush()

def run_live_mode_clustering_with_remote_sysid(config_path):
    MC.live_mode_clustering(config_path,topic_index=0,plot=[1,1])
