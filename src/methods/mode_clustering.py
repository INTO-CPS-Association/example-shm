import json
import sys
import threading
from typing import Any, List, Dict, Tuple
import numpy as np
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
from methods.constants import PARAMS
from functions.util import (convert_numpy_to_list, _convert_list_to_dict_or_array)
from methods.mode_clustering_functions.clustering import cluster_func
from functions.plot_sysid import plot_stabilization_diagram
from functions.plot_clusters import plot_clusters
from data.comm.mqtt import (load_config, setup_mqtt_client, reconnect_client)
# pylint: disable=C0103, W0603

# Global threading event to wait for sysid data
result_ready = threading.Event()
sysid_output_global = None  # will store received sysid data inside callback

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

def setup_publish_client(mqtt_config: Dict[str, Any]) -> Tuple[mqtt.Client, float]:
    """
    Sets up and starts the MQTT client for subscribing to sensor data.

    Args:
        mqtt_config: Configuration dictionary for the MQTT client.

    Returns:
        A tuple of the connected MQTTClient instance and the extracted sampling frequency.
    """

    data_client, topic = setup_mqtt_client(mqtt_config, topic_index=0)
    data_client.connect(mqtt_config["host"], mqtt_config["port"], 60)
    data_client.loop_start()
    return data_client, topic

def cluster_sysid(sysid_output: Any, params: Dict[str,Any]) -> Tuple[Dict[str,Any], np.ndarray]:
    """
    Runs the mode clustering algorithm.

    Args:
        sysid_output (Any): sysid output from subscription or elsewhere.
    Returns:
        cluster_dict (Dict[str,Any]), 
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
    global timestamp_global

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

        else:
            print("Sysid data received. Running mode clustering...")
            clusters, median_frequencies = cluster_sysid(sysid_output_global,params)
            print("Clustered frequencies", median_frequencies)

            cluster_results = True
            return cluster_results, sysid_output_global, clusters, median_frequencies, timestamp_global

    except KeyboardInterrupt:
        print("Shutting down gracefully")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        cluster_results = False
        return cluster_results, None, None, None, None
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    return None, None, None, None, None


def live_mode_clustering(config_path: str, topic_index: int = 0,
                        plot: np.ndarray = np.array([1,1])
                        ) -> Tuple[List[Dict], np.ndarray, np.ndarray]:
    """
    Subscribes to MQTT broker, receives one sysid message, runs mode clustering, plots results. Continue until stopped.

    Args:
        config_path (str): Path to config JSON.
        topic_index (int): Topic to subscribe
        plot (np.ndarray[bool]): Array describing what plots to show

    Returns:
        sysid_output_global (Dict[str,Any]): sysid output
        clusters (Dict[str,Any]]): Clusters
        tracked_clusters (Dict[str,Any]]): Tracked clusters
    """
    global sysid_output_global
    global timestamp_global
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

def live_mode_clustering_publish(config_path: str, topic_index: int = 0
                        ) -> Tuple[List[Dict], np.ndarray, np.ndarray]:
    """
    Subscribes to MQTT broker, receives one sysid message, runs mode clustering, plots results. Continue until stopped.

    Args:
        config_path (str): Path to config JSON.
        topic_index (int): Topic to subscribe

    Returns:
        sysid_output_global (Dict[str,Any]): sysid output
        clusters (Dict[str,Any]]): Clusters
        tracked_clusters (Dict[str,Any]]): Tracked clusters
    """
    global sysid_output_global
    global timestamp_global
    sysid_output_global = None  # Reset in case old data is present
    timestamp_global = None # Reset in case old data is present
    result_ready.clear()

    config = load_config(config_path)
    mqtt_client, selected_topic = setup_mqtt_client(config["sysID"], topic_index)

    mqtt_client.user_data_set({"topic": selected_topic, "qos": 0})
    mqtt_client.on_connect = _on_connect
    mqtt_client.on_message = _on_message
    mqtt_client.connect(config["sysID"]["host"], config["sysID"]["port"], keepalive=60)
    mqtt_client.loop_start()

    publish_config = config["mode_cluster"]
    publish_client, publish_topic = setup_publish_client(publish_config)

    
    while True:
        try:
            print("Waiting for sysid data...")
            result_ready.wait()  # Wait until message arrives

            if sysid_output_global is None:
                raise RuntimeError("Failed to receive sysid data.")

            timestamp = timestamp_global
            print(f"sysid data received at {timestamp}. Running mode clustering and tracking...")
            result_ready.clear()

            clusters, median_frequencies = cluster_sysid(sysid_output_global,PARAMS)
            print("Clustered frequencies", median_frequencies)
            
            payload = {
                "timestamp": timestamp,
                "cluster_dictionary": convert_numpy_to_list(clusters)
            }
            try:
                message = json.dumps(payload)

                reconnect_succes = reconnect_client(publish_client)

                publish_client.publish(publish_topic, message, qos=1)
                print(f"[{timestamp}] Published mode clusters to {publish_topic}")
                    
            except Exception as e:
                print(f"\nFailed to publish mode clusters: {e}")

            sys.stdout.flush()
        except KeyboardInterrupt:
            print("Shutting down gracefully")
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
            publish_client.disconnect()
            break
        except Exception as e:
            print(f"Unexpected error: {e}")