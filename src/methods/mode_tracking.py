from typing import Any, List, Dict, Tuple, Optional
import matplotlib.pyplot as plt
import methods.mode_clustering as MC
from methods.mode_tracking_functions.mode_tracking_func import cluster_tracking
from methods.mode_tracking_functions.plot_mode_tracking import plot_tracked_modes
from functions.plot_clusters import plot_clusters
# pylint: disable=C0103, W0603

def track_clusters(cluster_dict: Dict[str,Any], tracked_clusters: Dict[str,Any],
                      params: Dict[str,Any]) -> Dict[str,Any]:
    """
    Runs the mode tracking algorithm.

    Args:
        cluster_dict (Dict[str,Any]): Clusters from OMA
    Returns:
        tracked_clusters (Dict[str,Any]): Tracked clusters
    """
    tracked_clusters = cluster_tracking(cluster_dict, tracked_clusters, params)
    return tracked_clusters

def tracked_cluster_plots(plot: List[bool],tracked_clusters: Dict[str,Any],
                          clusters: Dict[str,Any], sysid_output: Dict[str, Any],
                          params: Dict[str, Any], fig_axes: List[Tuple[plt.Figure,plt.Axes]],
                          hold: bool = False,
                          x_length: int = None) -> List[Tuple[plt.Figure,plt.Axes]]:
    """
    Plot tracked modes and clustered modes.

    Args:
        plot (List[bool]): List of bools to state what plots should be made/updated
        tracked_clusters (Dict[str,Any]): Dictionary of tracked clusters
        clusters (Dict[str,Any]): Dictionary of new clusters
        sysid_output (Any): sysid output from SSI.
        params (Dict[str,Any]): Parameters ("Fs", "freq_variance_treshold"
                                            and "damp_variance_treshold")
        fig_axes (List[plt.Fig,plt.Axes]): List of figure and axes of plots
        hold (bool): To show graph until it is closed, plt.show(block=False)
        x_length (int): Limit on x axis for tracked modes, default=None.

    Returns:
        fig_axes (List[plt.Fig,plt.Axes]): List of figure and axes of plots
    """
    if plot[0] == 1:
        fig_ax1 = plot_clusters(clusters,sysid_output,params,fig_ax=fig_axes[0])
    else:
        fig_ax1 = None
    if plot[1] == 1:
        fig_ax2 = plot_tracked_modes(tracked_clusters,params,fig_ax=fig_axes[1],x_length=x_length)
    else:
        fig_ax2 = None
    plt.show(block=hold)
    return [fig_ax1, fig_ax2]

def subscribe_and_track_clusters(config: Dict[str,Any],
                                 tracked_clusters: Dict[str,Any],
                                 params: Dict[str,Any]) -> Optional[Tuple[List[Dict],
                                                                          Dict[str,Any],
                                                                          Dict[str,Any]]]:
    """
    Subscribes to MQTT broker, receives one OMA message, runs mode tracking, and returns results.

    Args:
        config (Dict[str,Any]): Configuration dictionary
        tracked_clusters (Dict[str,Any]): Previously tracked clusters
        params (Dict[str,Any]): clustering parameters

    Returns:
        sysid_output (Dict[str,Any]): sysid output from clustering
        clusters (Dict[str,Any]): Clusters
        tracked_clusters (Dict[str,Any]): Tracked clusters
    """
    sysid_output, clusters, _, __ = MC.subscribe_and_cluster(config,params)
    tracked_clusters = track_clusters(clusters, tracked_clusters,params)
    return sysid_output, clusters, tracked_clusters

def live_mode_tracking(config: Dict[str,Any],
                        params: Dict[str,Any], plot: List[bool] = [1,1]
                        ) -> None:
    """
    Subscribes to MQTT broker, receives one OMA message, runs mode tracking, plot results.
    Continue until stopped.

    Args:
        mqtt_config (mqtt.Client): Configuration dictionary for the MQTT client.
        config (Dict[str,Any]): Configuration dictionary
        plot (List[bool]): Array describing what plots to show

    Returns:

    Plots:
        Stabilization diagram
        Cluster plot
        Tracked clusters plot
    """
    tracked_clusters = {}
    fig_axes = [None,None]
    try:
        while True:
            sysid_output, clusters, tracked_clusters = subscribe_and_track_clusters(config,
                                                                tracked_clusters, params)
            if clusters is not None:
                fig_axes = tracked_cluster_plots(plot,tracked_clusters,
                                                 clusters,sysid_output,params,fig_axes)

    except KeyboardInterrupt:
        print("Keyboard interrupt of live mode tracking\n")
    except Exception as e:
        print(f"Unexpected error at: {e}")
