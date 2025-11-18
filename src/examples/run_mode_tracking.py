import sys
from methods import mode_clustering as MC
from methods import mode_tracking as MT
from methods.constants import PARAMS
from data.comm.mqtt import load_config

# pylint: disable=R0914
def run_mode_tracking_with_local_sysid(config_path):
    number_of_minutes = 1
    data_topic_indexes = [0, 2, 3, 4]

    sysid_ouput, clusters, median_frequencies = MC.cluster_of_local_sysid(config_path,
                                                                          number_of_minutes,
                                                                          data_topic_indexes)

    # Print frequencies
    print("\nMedian frequencies:", median_frequencies)

    tracked_clusters = {}
    tracked_clusters = MT.track_clusters(clusters,tracked_clusters,PARAMS)

    _ = MT.tracked_cluster_plots([0,1], tracked_clusters, clusters, sysid_ouput,
                              PARAMS, fig_axes = [None,None], hold = True, x_length = None)
    sys.stdout.flush()

def run_mode_tracking_with_remote_sysid(config_path):
    config = load_config(config_path)
    mqtt_client, _, __ = MC.setup_client(config["mode_cluster"])
    sysid_ouput, clusters, tracked_clusters = MT.subscribe_and_track_clusters(mqtt_client,
                                                                              config,{},PARAMS)
    _ = MT.tracked_cluster_plots([0,1], tracked_clusters, clusters, sysid_ouput,
                              PARAMS, fig_axes = [None,None], hold = True, x_length = None)
    sys.stdout.flush()

def run_live_mode_tracking_with_remote_sysid(config_path):
    config = load_config(config_path)
    mqtt_client, _, __ = MC.setup_client(config["mode_cluster"])
    MT.live_mode_tracking(mqtt_client,config,plot=[1,1])
