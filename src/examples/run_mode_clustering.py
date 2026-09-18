from data.comm.mqtt import load_config
from methods import mode_clustering as MC
from settings import PARAMS

# pylint: disable=R0914
def run_mode_clustering_with_local_sysid(config_path):
    sysid_output, clusters, median_frequencies = MC.cluster_from_local_sysid(config_path,
                                                                           PARAMS)
    # Print frequencies
    print("\nMedian frequencies:", median_frequencies)

    _ = MC.cluster_plots((1,1,1), clusters, sysid_output, PARAMS,
                         fig_axes = [None,None,None], hold = True)

def run_mode_clustering_with_remote_sysid(config_path):
    print("Beware clustering-with-remote-sysid requires live-sysid-publish to run in parallel")
    config = load_config(config_path)
    sysid_output, clusters, _, _ = MC.subscribe_and_cluster(config,PARAMS)
    if sysid_output is not None:
        _ = MC.cluster_plots((0,0,1), clusters, sysid_output, PARAMS,
                             fig_axes = [None,None,None], hold = True)

def run_live_mode_clustering_with_remote_sysid(config_path):
    print("Beware live-clustering-with-remote-sysid requires live-sysid-publish to run in parallel")
    config = load_config(config_path)
    MC.live_mode_clustering(config, PARAMS, publish=False, plot=(0,0,1))

def run_live_mode_clustering_with_remote_sysid_and_publish(config_path):
    print("Beware live-clustering-with-remote-sysid-and-publish requires live-sysid-publish to run in parallel")
    config = load_config(config_path)
    MC.live_mode_clustering(config,PARAMS, publish=True, plot=(0,0,0))
