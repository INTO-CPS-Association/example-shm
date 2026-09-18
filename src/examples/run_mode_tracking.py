from data.comm.mqtt import load_config
from methods import mode_clustering as MC
from methods import mode_tracking as MT
from settings import PARAMS

# pylint: disable=R0914
def run_mode_tracking_with_local_sysid(config_path):

    sysid_ouput, clusters, median_frequencies = MC.cluster_from_local_sysid(config_path,
                                                                          PARAMS)

    # Print frequencies
    print("\nMedian frequencies:", median_frequencies)

    tracked_clusters = {}
    tracked_clusters = MT.track_clusters(clusters,tracked_clusters,PARAMS)

    _ = MT.tracked_cluster_plots((0,1), tracked_clusters, clusters, sysid_ouput,
                              PARAMS, fig_axes = [None,None], hold = True, x_length = None)

def run_mode_tracking_with_remote_sysid(config_path):
    print("Beware mode-tracking-with-remote-sysid requires live-sysid-publish to run in parallel")
    config = load_config(config_path)
    sysid_ouput, clusters, tracked_clusters = MT.subscribe_and_track_clusters(config,{},PARAMS)
    _ = MT.tracked_cluster_plots((0,1), tracked_clusters, clusters, sysid_ouput,
                              PARAMS, fig_axes = [None,None], hold = True, x_length = None)

def run_live_mode_tracking_with_remote_sysid(config_path):
    print("Beware live-mode-tracking-with-remote-sysid requires live-sysid-publish to run in parallel")
    config = load_config(config_path)
    MT.live_mode_tracking(config,PARAMS,plot=(1,1))
