import json
import threading
from typing import Any, List, Dict, Tuple
import numpy as np
import matplotlib.pyplot as plt
from paho.mqtt.client import Client as MQTTClient, MQTTMessage, Properties
from data.comm.mqtt import (start_mqtt, publish_to_mqtt, shutdown)
from methods import sysid as sysID
from methods.mode_clustering_functions.clustering import cluster_func
from functions.util import (convert_numpy_to_list, _convert_list_to_dict_or_array)
from functions.plot_sysid import plot_stabilization_diagram, plot_pre_stabilization_diagram
from functions.plot_clusters import plot_clusters

# pylint: disable=C0103, W0603

# Global threading event to wait for sysid data
result_ready = threading.Event()
sysid_output_global = None  # will store received sysid data inside callback
timestamp_global = None

def _on_connect(client: MQTTClient, userdata: Dict, flags: Dict,
                reason_code: int, properties: Properties) -> None:
    """Callback when MQTT client connects."""
    if reason_code == 0:
        print("Connected to MQTT broker.")
        client.subscribe(userdata["topic"], qos=userdata["qos"])
        print(f"Subscribed to topic: {userdata['topic']}")
    else:
        print(f"Failed to connect to MQTT broker. Code: {reason_code}")

def _on_message(_client: MQTTClient, _userdata: Dict, msg: MQTTMessage) -> None:
    """Callback when a message is received."""
    global sysid_output_global
    global timestamp_global
    print(f"Message received on topic: {msg.topic}")
    try:
        raw = json.loads(msg.payload.decode("utf-8"))
        sysid_output = _convert_list_to_dict_or_array(raw["sysid_output"])
        timestamp = raw["timestamp"]
        print(f"Received sysid data at timestamp: {timestamp}")
        sysid_output_global = sysid_output
        timestamp_global = timestamp
        result_ready.set()
    except Exception as e:
        print(f"Error processing sysid message: {e}")

def cluster_sysid_output(sysid_output: Any, params: Dict[str,Any]) -> Tuple[Dict[str,Any],
                                                                            np.ndarray[float]]:
    """
    Runs the mode clustering algorithm.

    Args:
        sysid_output (Any): sysid output from subscription or elsewhere.
    Returns:
        cluster_dict (Dict[str,Any]), 
        median_frequencies (np.ndarray[float]), 
    """
    dictionary_clusters = cluster_func(sysid_output, params)

    median_frequencies = np.array([dictionary_clusters[key]["median_f"]
                                   for key in dictionary_clusters.keys()])
    return dictionary_clusters, median_frequencies

def publish_clusters(config: Dict[str,Any], timestamp: str,
                     clusters: Dict[str,Any]) -> None:
    """
    Publish clusters to publish topic

    Args:
        config (Dict[str,Any]): Configuration dictionary
        timestamp (str): Timestamp of data
        clusters (Dict[str,Any]): Dictionary of clusters

    Returns:
    """
   
    publish_client, _, publish_topics = start_mqtt(config["mode_cluster"], _on_connect)

    payload = {
                    "timestamp": timestamp,
                    "cluster_dictionary": convert_numpy_to_list(clusters)
                }
    
    publish_to_mqtt(publish_client,publish_topics, payload, "clusters")
    shutdown(publish_client)

def cluster_plots(plot: List[bool], clusters: Dict[str,Any], sysid_output: Dict[str, Any],
                  params: Dict[str, Any], fig_axes: List[Tuple[plt.Figure,plt.Axes]],
                  hold: bool = False) -> List[Tuple[plt.Figure,plt.Axes]]:
    """
    Plot clusters and stabilization diagram

    Args:
        plot (List[bool]): List of bools to state what plots should be made/updated
        clusters (Dict[str,Any]): Dictionary of new clusters
        sysid_output (Any): sysid output from SSI.
        params (Dict[str,Any]): Parameters ("Fs", "freq_variance_treshold"
                                            and "damp_variance_treshold")
        fig_axes (List[plt.Fig,plt.Axes]): List of figure and axes of plots
        hold (bool): To show graph until it is closed, plt.show(block=False)

    Returns:
        fig_axes (List[plt.Fig,plt.Axes]): List of figure and axes of plots
    """
    if plot[0] == 1:
        fig_ax1 = plot_pre_stabilization_diagram(sysid_output,params,fig_ax=fig_axes[0])
    else:
        fig_ax1 = None
    if plot[1] == 1:
        fig_ax2 = plot_stabilization_diagram(sysid_output,params,fig_ax=fig_axes[1])
    else:
        fig_ax2 = None
    if plot[2] == 1:
        fig_ax3 = plot_clusters(clusters,sysid_output,params,fig_ax=fig_axes[2])
    else:
        fig_ax3 = None
    plt.show(block=hold)
    return [fig_ax1, fig_ax2, fig_ax3]

def cluster_from_local_sysid(config_path: str,
                           params: Dict[str,Any],
                           data_topic_indexes: List[int] = None) -> Tuple[Dict[str,Any],
                                                                        Dict[str,Any],
                                                                        List[float]]:
    """
    Run local sysid and mode clustering

    Args:
        config_path (str): Path to config JSON.
        data_topic_indexes (List[int]): Indexes of topics to subscribe to
        params (Dict[str,Any]): clustering parameters

    Returns:
        sysid_output (Dict[str,Any]): sysid output
        dictionary_of_clusters (Dict[str,Any]]): Clusters from clustering of sysid output
        median_frequencies (List[float]): Median frequencies of clusters
    """

    mqtt_client, sysid_output, _ = sysID.local_sysid(config_path,
                                                              data_topic_indexes)
    shutdown(mqtt_client)

    # Mode clustering
    dictionary_of_clusters, median_frequencies = cluster_sysid_output(sysid_output,params)

    return sysid_output, dictionary_of_clusters, median_frequencies

def subscribe_and_cluster(config: Dict[str,Any], params: Dict[str,Any]
                          ) -> Tuple[Dict[str,Any], Dict[str,Any], List[float], str]:
    """
    Subscribes to MQTT broker, receives one sysid message,
    runs mode clustering, and returns results.

    Args:
        config (Dict[str,Any]): Configuration dictionary
        params (Dict[str,Any]): clustering parameters

    Returns:
        sysid_output_global (Dict[str,Any]): sysid output
        clusters (Dict[str,Any]]): Clusters
        median_frequencies (List[float]): Median eigenfrequencies of clusters
        timestamp_global (str): Timestamp of aligned data
    """
    global sysid_output_global
    global timestamp_global

    sysid_output_global = None  # Reset in case old data is present
    timestamp_global = None
    result_ready.clear()

    mqtt_client, _, __ = start_mqtt(config["mode_cluster"], _on_connect, _on_message=_on_message)
    print("Waiting for sysid data...")
    try:
        result_ready.wait()  # Wait until message arrives
        if sysid_output_global is None:
            raise RuntimeError("Failed to receive sysid data.")

        print("Sysid data received. Running mode clustering...")
        clusters, median_frequencies = cluster_sysid_output(sysid_output_global,params)
        print("Clustered frequencies", median_frequencies)

        shutdown(mqtt_client)
        return sysid_output_global, clusters, median_frequencies, timestamp_global

    except KeyboardInterrupt as exc:
        shutdown(mqtt_client,"clustering")
        raise RuntimeError("Keyboard interrupt") from exc

def live_mode_clustering(config: Dict[str,Any], params: Dict[str,Any],
                        publish: bool = False, plot: List[bool] = [1,1,1]
                        ) -> None:
    """
    Subscribes to MQTT broker, receives one sysid message, runs mode clustering, plots results.
                                                                        Continue until stopped.

    Args:
        config (Dict[str,Any]): Configuration dictionary
        params (Dict[str,Any]): clustering parameters
        publish (bool): Whether to publish clustering results
        plot (list[bool]): Array describing what plots to show

    Returns:
    """
    fig_axes = [None, None, None]
    try:
        while True:
            (sysid_output, clusters,
             _, timestamp) = subscribe_and_cluster(config,params)

            fig_axes = cluster_plots(plot, clusters, sysid_output, params, fig_axes)
            if publish:
                publish_clusters(config, timestamp, clusters)
    except KeyboardInterrupt:
        print("Keyboard interrupt of live clustering\n")
    except Exception as e:
        print(f"Unexpected error: {e}")
