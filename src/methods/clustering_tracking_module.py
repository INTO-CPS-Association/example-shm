import json
import sys
import threading
from typing import Any, List, Dict, Tuple
import numpy as np
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
from methods.constants import PARAMS
from methods.packages.clustering import cluster_func
from methods.packages.mode_tracking import cluster_tracking
from functions.sysid_plot import (plot_clusters,plot_stabilization_diagram)
from functions.plot_mode_tracking import plot_tracked_modes
from data.comm.mqtt import load_config, setup_mqtt_client
# pylint: disable=C0103, W0603

# Global threading event to wait for OMA data
result_ready = threading.Event()
oma_output_global = None  # will store received OMA data inside callback

def _convert_oma_output(obj: Any) -> Any:
    """Recursively convert JSON structure into complex numbers and numpy arrays."""
    if isinstance(obj, dict):
        if "real" in obj and "imag" in obj:
            return complex(obj["real"], obj["imag"])
        return {k: _convert_oma_output(v) for k, v in obj.items()}

    if isinstance(obj, list):
        try:
            return np.array([_convert_oma_output(item) for item in obj])
        except Exception:
            return [_convert_oma_output(item) for item in obj]

    return obj


def _on_connect(client: mqtt.Client, userdata: dict, flags: dict, reason_code: int, properties: mqtt.Properties) -> None:
    """Callback when MQTT client connects."""
    if reason_code  == 0:
        print("Connected to MQTT broker.")
        client.subscribe(userdata["topic"], qos=userdata["qos"])
        print(f"Subscribed to topic: {userdata['topic']}")
    else:
        print(f"Failed to connect to MQTT broker. Code: {reason_code}")


def _on_message(_client: mqtt.Client, _userdata: dict, msg: mqtt.MQTTMessage) -> None:
    """Callback when a message is received."""
    global oma_output_global
    print(f"Message received on topic: {msg.topic}")
    try:
        raw = json.loads(msg.payload.decode("utf-8"))
        oma_output = _convert_oma_output(raw["OMA_output"])
        timestamp = raw["timestamp"]
        print(f"Received OMA data at timestamp: {timestamp}")
        oma_output_global = oma_output
        result_ready.set()
    except Exception as e:
        print(f"Error processing OMA message: {e}")


def run_mode_clustering(oma_output: Any, params: dict[str,Any]) -> Tuple[dict[str,Any], np.ndarray]:
    """
    Runs the mode clustering algorithm.

    Args:
        oma_output (Any): OMA output from subscription or elsewhere.
    Returns:
        cluster_dict (dict[str,Any]), 
        median_frequencies (np.ndarray), 
    """
    dictionary_clusters = cluster_func(oma_output, params)

    median_frequencies = np.array([dictionary_clusters[key]["median_f"]
                                   for key in dictionary_clusters.keys()])
    return dictionary_clusters, median_frequencies


def run_mode_tracking(cluster_dict: dict[str,Any], tracked_clusters: dict[str,Any],
                      params: dict[str,Any]) -> dict[str,Any]:
    """
    Runs the mode tracking algorithm.

    Args:
        cluster_dict (dict[str,Any]): Clusters from OMA
    Returns:
        tracked_clusters (dict[str,Any]): Tracked clusters
    """
    tracked_clusters = cluster_tracking(cluster_dict, tracked_clusters, params)
    return tracked_clusters


def subscribe_and_cluster(config_path: str, params: Dict[str,Any]
                          ) -> Tuple[Dict[str,Any], Dict[str,Any]]:
    """
    Subscribes to MQTT broker, receives one OMA message, runs mode tracking, and returns results.

    Args:
        config_path (str): Path to config JSON.

    Returns:
        oma_output_global (Dict[str,Any]): OMA output
        clusters (Dict[str,Any]]): Clusters
    """
    global oma_output_global
    oma_output_global = None  # Reset in case old data is present
    result_ready.clear()

    config = load_config(config_path)
    mqtt_client, selected_topic = setup_mqtt_client(config["sysID"], topic_index=0)

    mqtt_client.user_data_set({"topic": selected_topic, "qos": 0})
    mqtt_client.on_connect = _on_connect
    mqtt_client.on_message = _on_message
    mqtt_client.connect(config["sysID"]["host"], config["sysID"]["port"], keepalive=60)
    mqtt_client.loop_start()
    print("Waiting for OMA data...")
    try:
        result_ready.wait()  # Wait until message arrives
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

        if oma_output_global is None:
            raise RuntimeError("Failed to receive OMA data.")

        print("OMA data received. Running mode clustering and tracking...")
        clusters, median_frequencies = run_mode_clustering(oma_output_global,params)
        print("Clustered frequencies", median_frequencies)

    except KeyboardInterrupt:
        print("Shutting down gracefully")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
    except Exception as e:
        print(f"Unexpected error: {e}")

    return oma_output_global, clusters


def subscribe_and_get_clusters(config_path: str) -> Tuple[List[Dict], np.ndarray, np.ndarray]:
    """
    Subscribes to MQTT broker, receives one OMA message, runs mode tracking, and returns results.

    Args:
        config_path (str): Path to config JSON.

    Returns:
        oma_output_global (Dict[str,Any]): OMA output
        clusters (Dict[str,Any]]): Clusters
        tracked_clusters (Dict[str,Any]]): Tracked clusters
    """
    global oma_output_global
    oma_output_global = None  # Reset in case old data is present
    result_ready.clear()
    tracked_clusters = {}

    config = load_config(config_path)
    mqtt_client, selected_topic = setup_mqtt_client(config["sysID"], topic_index=0)

    mqtt_client.user_data_set({"topic": selected_topic, "qos": 0})
    mqtt_client.on_connect = _on_connect
    mqtt_client.on_message = _on_message
    mqtt_client.connect(config["sysID"]["host"], config["sysID"]["port"], keepalive=60)
    mqtt_client.loop_start()
    print("Waiting for OMA data...")
    try:
        result_ready.wait()  # Wait until message arrives
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

        if oma_output_global is None:
            raise RuntimeError("Failed to receive OMA data.")

        print("OMA data received. Running mode clustering and tracking...")
        clusters, median_frequencies = run_mode_clustering(oma_output_global,PARAMS)
        print("Clustered frequencies", median_frequencies)
        tracked_clusters = run_mode_tracking(clusters, tracked_clusters,PARAMS)

    except KeyboardInterrupt:
        print("Shutting down gracefully")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
    except Exception as e:
        print(f"Unexpected error: {e}")

    return oma_output_global, clusters, tracked_clusters


def subscribe_cluster_looping(config_path: str, topic_index: int = 0,
                              plot: np.ndarray[bool] = np.array([1,1])
                              ) -> Tuple[List[Dict], np.ndarray, np.ndarray]:
    """
    Subscribes to MQTT broker, receives one OMA message, runs mode tracking, and returns results.

    Args:
        config_path (str): Path to config JSON.
        topic_index (int): Topic to subscribe
        plot (np.ndarray[bool]): Array describing what plots to show

    Returns:
        oma_output_global (Dict[str,Any]): OMA output
        clusters (Dict[str,Any]]): Clusters
        tracked_clusters (Dict[str,Any]]): Tracked clusters
    """
    global oma_output_global
    oma_output_global = None  # Reset in case old data is present
    result_ready.clear()

    config = load_config(config_path)
    mqtt_client, selected_topic = setup_mqtt_client(config["sysID"], topic_index)

    mqtt_client.user_data_set({"topic": selected_topic, "qos": 0})
    mqtt_client.on_connect = _on_connect
    mqtt_client.on_message = _on_message
    mqtt_client.connect(config["sysID"]["host"], config["sysID"]["port"], keepalive=60)
    mqtt_client.loop_start()

    fig_ax1 = None
    fig_ax2 = None
    while True:
        # try:
        print("Waiting for OMA data...")
        result_ready.wait()  # Wait until message arrives

        if oma_output_global is None:
            raise RuntimeError("Failed to receive OMA data.")

        print("OMA data received. Running mode clustering and tracking...")
        result_ready.clear()

        if plot[0] == 1:
            fig_ax1 = plot_stabilization_diagram(oma_output_global,PARAMS,fig_ax=fig_ax1)
            plt.show(block=False)

        clusters, median_frequencies = run_mode_clustering(oma_output_global,PARAMS)
        print("Clustered frequencies", median_frequencies)

        if plot[1] == 1:
            fig_ax2 = plot_clusters(clusters,oma_output_global,PARAMS,fig_ax=fig_ax2)
            plt.show(block=False)

        sys.stdout.flush()
        # except KeyboardInterrupt:
        #     print("Shutting down gracefully")
        #     mqtt_client.loop_stop()
        #     mqtt_client.disconnect()
        #     break
        # except Exception as e:
        #     print(f"Unexpected error: {e}")

def subscribe_cluster_and_tracking_looping(config_path: str, topic_index: int = 0,
                                           plot: np.ndarray[bool] = np.array([1,1,1])
                                           ) -> Tuple[List[Dict], np.ndarray, np.ndarray]:
    """
    Subscribes to MQTT broker, receives one OMA message, runs mode tracking, and returns results.

    Args:
        config_path (str): Path to config JSON.
        topic_index (int): Topic to subscribe
        plot (np.ndarray[bool]): Array describing what plots to show

    Returns:

    Plots:
        Stabilization diagram
        Cluster plot
        Tracked clusters plot
    """
    global oma_output_global
    oma_output_global = None  # Reset in case old data is present
    result_ready.clear()
    tracked_clusters = {}

    config = load_config(config_path)
    mqtt_client, selected_topic = setup_mqtt_client(config["sysID"], topic_index)

    mqtt_client.user_data_set({"topic": selected_topic, "qos": 0})
    mqtt_client.on_connect = _on_connect
    mqtt_client.on_message = _on_message
    mqtt_client.connect(config["sysID"]["host"], config["sysID"]["port"], keepalive=60)
    mqtt_client.loop_start()

    fig_ax1 = None
    fig_ax2 = None
    fig_ax3 = None
    while True:
        try:
            print("Waiting for OMA data...")
            result_ready.wait()  # Wait until message arrives

            if oma_output_global is None:
                raise RuntimeError("Failed to receive OMA data.")

            print("OMA data received. Running mode clustering and tracking...")
            result_ready.clear()

            if plot[0] == 1:
                fig_ax1 = plot_stabilization_diagram(oma_output_global,PARAMS,fig_ax=fig_ax1)
                plt.show(block=False)

            clusters, median_frequencies = run_mode_clustering(oma_output_global,PARAMS)
            print("Clustered frequencies", median_frequencies)
            tracked_clusters = run_mode_tracking(clusters, tracked_clusters,PARAMS)

            if plot[1] == 1:
                fig_ax2 = plot_clusters(clusters,oma_output_global,PARAMS,fig_ax=fig_ax2)
                plt.show(block=False)
            if plot[2] == 1:
                fig_ax3 = plot_tracked_modes(tracked_clusters,PARAMS,fig_ax=fig_ax3,x_length=None)
                plt.show(block=False)
            sys.stdout.flush()
        except KeyboardInterrupt:
            print("Shutting down gracefully")
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
