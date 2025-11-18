import json
import sys
import threading
from typing import Any, List, Dict, Tuple
import numpy as np
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
from methods.constants import PARAMS
from methods import sysid as sysID
from methods.mode_clustering_functions.clustering import cluster_func
from functions.util import (convert_numpy_to_list, _convert_list_to_dict_or_array)
from functions.plot_sysid import plot_stabilization_diagram
from functions.plot_clusters import plot_clusters
from data.comm.mqtt import (setup_mqtt_client, reconnect_client, shutdown)
# pylint: disable=C0103, W0603

# Global threading event to wait for sysid data
result_ready = threading.Event()
sysid_output_global = None  # will store received sysid data inside callback
timestamp_global = None

def _on_connect(client: mqtt.Client, userdata: dict, flags: dict,
                reason_code: int, properties: mqtt.Properties) -> None:
    """Callback when MQTT client connects."""
    if reason_code == 0:
        print("Connected to MQTT broker.")
        client.subscribe(userdata["topic"], qos=userdata["qos"])
        print(f"Subscribed to topic: {userdata['topic']}")
    else:
        print(f"Failed to connect to MQTT broker. Code: {reason_code}")


def _on_message(_client: mqtt.Client, _userdata: dict, msg: mqtt.MQTTMessage) -> None:
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

def setup_client(mqtt_config: Dict[str, Any]) -> Tuple[mqtt.Client, float]:
    """
    Sets up and starts the MQTT client for subscribing to sensor data.

    Args:
        mqtt_config: Configuration dictionary for the MQTT client.

    Returns:
        A tuple of the connected MQTTClient instance and the extracted sampling frequency.
    """

    (data_client, subcribe_topic,
     publish_topic) = setup_mqtt_client(mqtt_config)
    data_client.connect(mqtt_config["host"], mqtt_config["port"], 60)
    data_client.loop_start()

    return data_client, subcribe_topic, publish_topic

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
        fig_ax1 = plot_stabilization_diagram(sysid_output,params,fig_ax=fig_axes[0])
    else:
        fig_ax1 = None
    if plot[1] == 1:
        fig_ax2 = plot_clusters(clusters,sysid_output,params,fig_ax=fig_axes[1])
    else:
        fig_ax2 = None
    plt.show(block=hold)
    return [fig_ax1, fig_ax2]

def cluster_of_local_sysid(config_path: str, number_of_minutes: float,
                           data_topic_indexes: List[int]) -> Tuple[Dict[str,Any],Dict[str,Any],
                                                                   List[float]]:
    """
    Run local sysid and mode clustering

    Args:
        config_path (str): Path to config JSON.
        number_of_minutes (float): Number of mintues of data to align
        data_topic_indexes (List[int])

    Returns:
        sysid_output (Dict[str,Any]): sysid output
        dictionary_of_clusters (Dict[str,Any]]): Clusters from clustering of sysid output
        median_frequencies (List[float]): Median frequencies of clusters
    """

    aligner, data_client, _, fs = sysID.setup_sysid(config_path, data_topic_indexes)

    sysid_output, _ = sysID.wait_for_sysid_output(number_of_minutes, aligner, fs)
    data_client.disconnect()

    # Mode clustering
    dictionary_of_clusters, median_frequencies = cluster_sysid_output(sysid_output,PARAMS)

    return sysid_output, dictionary_of_clusters, median_frequencies

def subscribe_and_cluster(mqtt_client: mqtt.Client, config: Dict[str,Any], params: Dict[str,Any]
                          ) -> Tuple[Dict[str,Any], Dict[str,Any]]:
    """
    Subscribes to MQTT broker, receives one sysid message,
    runs mode clustering, and returns results.

    Args:
        mqtt_config (mqtt.Client): Configuration dictionary for the MQTT client.
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

    mqtt_client.user_data_set({"topic": config["mode_cluster"]["TopicsToSubscribe"][0], "qos": 1})
    mqtt_client.on_connect = _on_connect
    mqtt_client.on_message = _on_message
    mqtt_client.connect(config["mode_cluster"]["host"],
                        config["mode_cluster"]["port"], keepalive=60)
    mqtt_client.loop_start()
    print("Waiting for sysid data...")
    try:
        result_ready.wait()  # Wait until message arrives
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

        if sysid_output_global is None:
            raise RuntimeError("Failed to receive sysid data.")

        print("Sysid data received. Running mode clustering...")
        clusters, median_frequencies = cluster_sysid_output(sysid_output_global,params)
        print("Clustered frequencies", median_frequencies)

        return sysid_output_global, clusters, median_frequencies, timestamp_global

    except KeyboardInterrupt as exc:
        raise RuntimeError("Keyboard interrupt") from exc


def publish_clusters(publish_client: mqtt.Client, publish_topic: str, timestamp: str,
                     clusters: Dict[str,Any]) -> None:
    """
    Publish clusters to publish topic

    Args:
        publish_client (mqtt.Client): MQTT client
        publish_topic (str): Topic to publish
        timestamp (str): Timestamp of data
        clusters (Dict[str,Any]): Dictionary of clusters

    Returns:
    """
    payload = {
                "timestamp": timestamp,
                "cluster_dictionary": convert_numpy_to_list(clusters)
            }
    try:
        message = json.dumps(payload)

        _ = reconnect_client(publish_client)

        publish_client.publish(publish_topic, message, qos=1)
        print(f"[{timestamp}] Published mode clusters to {publish_topic}")

    except Exception as e:
        print(f"\nFailed to publish mode clusters: {e}")

def live_mode_clustering(mqtt_client: mqtt.Client, config: Dict[str,Any],
                        publish_topic: str, plot: List[bool] = [1,1]
                        ) -> None:
    """
    Subscribes to MQTT broker, receives one sysid message, runs mode clustering, plots results.
                                                                        Continue until stopped.

    Args:
        config (Dict): Config JSON.
        mqtt_client (mqtt.Client): MQTT client
        publish_topic (str): Topic to publish
        plot (list[bool]): Array describing what plots to show

    Returns:
        sysid_output_global (Dict[str,Any]): sysid output
        clusters (Dict[str,Any]]): Clusters
        tracked_clusters (Dict[str,Any]]): Tracked clusters
    """
    fig_axes = [None, None]
    try:
        while True:
            (sysid_output, clusters,
             _, timestamp) = subscribe_and_cluster(mqtt_client,config,PARAMS)

            fig_axes = cluster_plots(plot, clusters, sysid_output, PARAMS, fig_axes)
            if publish_topic is not None:
                publish_clusters(mqtt_client, publish_topic, timestamp, clusters)
    except KeyboardInterrupt:
        shutdown(mqtt_client,"clustering")
    except Exception as e:
        print(f"Unexpected error: {e}")
        shutdown(mqtt_client,"clustering")
