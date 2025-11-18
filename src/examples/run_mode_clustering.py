import sys
import matplotlib.pyplot as plt
from data.comm.mqtt import load_config
from methods import mode_clustering as MC
from methods.constants import PARAMS

# pylint: disable=R0914
def run_mode_clustering_with_local_sysid(config_path):
    number_of_minutes = 0.5
    data_topic_indexes = [0, 2, 3, 4]

    sysid_output, clusters, median_frequencies = MC.cluster_of_local_sysid(config_path,
                                                                           number_of_minutes,
                                                                           data_topic_indexes)
    # Print frequencies
    print("\nMedian frequencies:", median_frequencies)

    _ = MC.cluster_plots([0,1], clusters, sysid_output, PARAMS, fig_axes = [None,None], hold = True)
    sys.stdout.flush()

def run_mode_clustering_with_remote_sysid(config_path):
    config = load_config(config_path)
    mqtt_client, _, __ = MC.setup_client(config["mode_cluster"])
    sysid_output, clusters, _, _ = MC.subscribe_and_cluster(mqtt_client,config,PARAMS)
    if sysid_output is not None:
        _ = MC.cluster_plots([0,1], clusters, sysid_output, PARAMS,
                             fig_axes = [None,None], hold = True)
        plt.show(block=True)
    sys.stdout.flush()

def run_live_mode_clustering_with_remote_sysid(config_path):
    config = load_config(config_path)
    mqtt_client, _, __ = MC.setup_client(config["mode_cluster"])
    MC.live_mode_clustering(mqtt_client, config, None, plot=[1,1])

def run_live_mode_clustering_with_remote_sysid_and_publish(config_path):
    config = load_config(config_path)
    mqtt_client, _, publish_topic = MC.setup_client(config["mode_cluster"])
    MC.live_mode_clustering(mqtt_client, config, publish_topic, plot=[0,0])
