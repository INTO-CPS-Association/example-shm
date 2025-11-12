import sys
from typing import Any, List, Dict, Tuple
import numpy as np
import matplotlib.pyplot as plt
from methods.constants import PARAMS
from methods.mode_clustering import (subscribe_and_cluster)
from methods.mode_tracking_functions.mode_tracking import cluster_tracking
from functions.plot_mode_tracking import plot_tracked_modes
from functions.plot_clusters import plot_clusters
# pylint: disable=C0103, W0603

def track_clusters(cluster_dict: Dict[str, Any], tracked_clusters: Dict[str, Any],
                      params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs the mode tracking algorithm.

    Args:
        cluster_dict (dict[str,Any]): Clusters from OMA
    Returns:
        tracked_clusters (dict[str,Any]): Tracked clusters
    """
    tracked_clusters = cluster_tracking(cluster_dict, tracked_clusters, params)
    return tracked_clusters

def subscribe_and_track_clusters(config_path: str) -> Tuple[List[Dict], np.ndarray, np.ndarray]:
    """
    Subscribes to MQTT broker, receives one OMA message, runs mode tracking, and returns results.

    Args:
        config_path (str): Path to config JSON.

    Returns:
        oma_output_global (Dict[str,Any]): OMA output
        clusters (Dict[str,Any]]): Clusters
        tracked_clusters (Dict[str,Any]]): Tracked clusters
    """
    tracked_clusters = {}
    sysid_output, clusters, median_frequencies = subscribe_and_cluster(config_path,PARAMS)

    print("Clustered frequencies", median_frequencies)
    tracked_clusters = track_clusters(clusters, tracked_clusters,PARAMS)

    return sysid_output, clusters, tracked_clusters

def live_mode_tracking(config_path: str,
                        plot: np.ndarray[bool] = np.array([1,1])
                        ) -> Tuple[List[Dict], np.ndarray, np.ndarray]:
    """
    Subscribes to MQTT broker, receives one OMA message, runs mode tracking, plot results. Continue until stopped.

    Args:
        config_path (str): Path to config JSON.
        plot (np.ndarray[bool]): Array describing what plots to show

    Returns:

    Plots:
        Stabilization diagram
        Cluster plot
        Tracked clusters plot
    """
    tracked_clusters = {}
    fig_ax1 = None
    fig_ax2 = None
    
    while True:
        try:
            sysid_output, clusters, median_frequencies = subscribe_and_cluster(config_path,PARAMS)

            print("Clustered frequencies", median_frequencies)
            tracked_clusters = track_clusters(clusters, tracked_clusters,PARAMS)

            if plot[0] == 1:
                fig_ax1 = plot_clusters(clusters,sysid_output,PARAMS,fig_ax=fig_ax1)
                plt.show(block=False)
            if plot[1] == 1:
                fig_ax2 = plot_tracked_modes(tracked_clusters,PARAMS,fig_ax=fig_ax2,x_length=None)
                plt.show(block=False)
            sys.stdout.flush()

        except KeyboardInterrupt:
            print("Shutting down gracefully")
            plt.close()
        except Exception as e:
            print(f"Unexpected error: {e}")