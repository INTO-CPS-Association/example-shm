import json
import sys
import threading
from typing import Any, List, Dict, Tuple
import numpy as np
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
from methods.constants import PARAMS
from methods.mode_clustering_functions.clustering import cluster_func
from functions.plot_sysid import plot_stabilization_diagram
from functions.plot_clusters import plot_clusters
from data.comm.mqtt import load_config, setup_mqtt_client
# pylint: disable=C0103, W0603

# Global threading event to wait for sysid data
result_ready = threading.Event()
sysid_output_global = None  # will store received sysid data inside callback

def _convert_sysid_output(obj: Any) -> Any:
    """Recursively convert JSON structure into complex numbers and numpy arrays."""
    if isinstance(obj, dict):
        if "real" in obj and "imag" in obj:
            return complex(obj["real"], obj["imag"])
        return {k: _convert_sysid_output(v) for k, v in obj.items()}

    if isinstance(obj, list):
        try:
            return np.array([_convert_sysid_output(item) for item in obj])
        except Exception:
            return [_convert_sysid_output(item) for item in obj]

    return obj


def _on_connect(client: mqtt.Client, userdata: dict, flags: dict, reason_code: int, properties: mqtt.Properties) -> None:
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
    print(f"Message received on topic: {msg.topic}")
    try:
        raw = json.loads(msg.payload.decode("utf-8"))
        sysid_output = _convert_sysid_output(raw["sysid_output"])
        timestamp = raw["timestamp"]
        print(f"Received sysid data at timestamp: {timestamp}")
        sysid_output_global = sysid_output
        result_ready.set()
    except Exception as e:
        print(f"Error processing sysid message: {e}")


def cluster_sysid(sysid_output: Any, params: Dict[str, Any]) -> Tuple[Dict[str, Any], np.ndarray]:
    """
    Runs the mode clustering algorithm.

    Args:
        sysid_output (Any): sysid output from subscription or elsewhere.
    Returns:
        cluster_dict (dict[str,Any]), 
        median_frequencies (np.ndarray), 
    """
    dictionary_clusters = cluster_func(sysid_output, params)

    median_frequencies = np.array([dictionary_clusters[key]["median_f"]
                                   for key in dictionary_clusters.keys()])
    return dictionary_clusters, median_frequencies

def subscribe_and_cluster(config_path: str, params: Dict[str,Any]
                          ) -> Tuple[Dict[str,Any], Dict[str,Any]]:
    """
    Subscribes to MQTT broker, receives one sysid message, runs mode clustering, and returns results.

    Args:
        config_path (str): Path to config JSON.
        params (Dict[str,Any]): clustering parameters

    Returns:
        sysid_output_global (Dict[str,Any]): sysid output
        clusters (Dict[str,Any]]): Clusters
    """
    global sysid_output_global
    sysid_output_global = None  # Reset in case old data is present
    result_ready.clear()

    config = load_config(config_path)
    mqtt_client, selected_topic = setup_mqtt_client(config["sysID"], topic_index=0)

    mqtt_client.user_data_set({"topic": selected_topic, "qos": 0})
    mqtt_client.on_connect = _on_connect
    mqtt_client.on_message = _on_message
    mqtt_client.connect(config["sysID"]["host"], config["sysID"]["port"], keepalive=60)
    mqtt_client.loop_start()
    print("Waiting for sysid data...")
    try:
        result_ready.wait()  # Wait until message arrives
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

        if sysid_output_global is None:
            raise RuntimeError("Failed to receive sysid data.")

        print("sysid data received. Running mode clustering and tracking...")
        clusters, median_frequencies = cluster_sysid(sysid_output_global,params)
        print("Clustered frequencies", median_frequencies)

    except KeyboardInterrupt:
        print("Shutting down gracefully")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
    except Exception as e:
        print(f"Unexpected error: {e}")

    return sysid_output_global, clusters, median_frequencies


def live_mode_clustering(config_path: str, topic_index: int = 0,
                        plot: np.ndarray = np.array([1,1])
                        ) -> Tuple[List[Dict], np.ndarray, np.ndarray]:
    """
    Subscribes to MQTT broker, receives one sysid message, runs mode clustering, plots results. Continue until stopped.

    Args:
        config_path (str): Path to config JSON.
        topic_index (int): Topic to subscribe
        plot (np.ndarray): Array describing what plots to show

    Returns:
        sysid_output_global (Dict[str,Any]): sysid output
        clusters (Dict[str,Any]]): Clusters
        tracked_clusters (Dict[str,Any]]): Tracked clusters
    """
    global sysid_output_global
    sysid_output_global = None  # Reset in case old data is present
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
        try:
            print("Waiting for sysid data...")
            result_ready.wait()  # Wait until message arrives

            if sysid_output_global is None:
                raise RuntimeError("Failed to receive sysid data.")

            print("sysid data received. Running mode clustering and tracking...")
            result_ready.clear()

            if plot[0] == 1:
                fig_ax1 = plot_stabilization_diagram(sysid_output_global,PARAMS,fig_ax=fig_ax1)
                plt.show(block=False)

            clusters, median_frequencies = cluster_sysid(sysid_output_global,PARAMS)
            print("Clustered frequencies", median_frequencies)

            if plot[1] == 1:
                fig_ax2 = plot_clusters(clusters,sysid_output_global,PARAMS,fig_ax=fig_ax2)
                plt.show(block=False)

            sys.stdout.flush()
        except KeyboardInterrupt:
            print("Shutting down gracefully")
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
            break
        except Exception as e:
            print(f"Unexpected error: {e}")