import sys
import datetime
import os
import threading
import json
from typing import Any, List, Dict, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
from paho.mqtt.client import Client as MQTTClient
from data.comm.mqtt import (reconnect_client,shutdown)
from functions.util import (convert_numpy_to_list, _convert_list_to_dict_or_array)
from functions.plot_model_update import (plot_parameters,plot_model_frequencies)
from methods.mode_clustering import (subscribe_and_cluster)
from methods.model_update_functions import model_update_func
from methods.constants import MODEL_PARAMETERS
from methods.mode_clustering import _on_connect

# pylint: disable=C0103, W0603

# Global threading event to wait for cluster data
result_ready = threading.Event()
cluster_global = None  # will store received cluster data inside callback
timestamp_global = None

def _on_message(_client: mqtt.Client, _userdata: dict, msg: mqtt.MQTTMessage) -> None:
    """Callback when a message is received."""
    global cluster_global
    global timestamp_global
    print(f"Message received on topic: {msg.topic}")
    try:
        raw = json.loads(msg.payload.decode("utf-8"))
        clusters = _convert_list_to_dict_or_array(raw["cluster_dictionary"])
        timestamp = raw["timestamp"]
        print(f"Received cluster data at timestamp: {timestamp}")
        cluster_global = clusters
        timestamp_global = timestamp
        result_ready.set()

    except Exception as e:
        print(f"Error processing sysid message: {e}")

def subscribe_cluster_results(mqtt_client: mqtt.Client, config: Dict[str,Any],
                              subscribe_topic) -> Optional[Tuple[str, Dict[str,Any]]]:
    """
    Args:
        publish_client (mqtt.Client): MQTT client
        config (Dict[str,Any]): Configuration dictionary
        subscribe_topic (str): Topic to subscribe to
    Returns:
        timestamp (str): timestamp string
        clusters (Dict[str,Any]) Dictionary of clusters
    """
    global cluster_global
    global timestamp_global

    cluster_global = None  # Reset in case old data is present
    timestamp_global = None
    result_ready.clear()

    mqtt_client.user_data_set({"topic": subscribe_topic, "qos": 1})
    mqtt_client.on_connect = _on_connect
    mqtt_client.on_message = _on_message
    mqtt_client.connect(config["model_update"]["host"],
                        config["model_update"]["port"], keepalive=60)
    mqtt_client.loop_start()
    print("Waiting for mode clustering data...")

    while True:
        try:
            result_ready.wait() # Wait until message arrives
            mqtt_client.loop_stop()
            mqtt_client.disconnect()

            if cluster_global is None:
                raise RuntimeError("Failed to receive cluster data.")
            clusters = cluster_global
            timestamp = timestamp_global
            print(f"Cluster data received at {timestamp}. Running model update...")

            return timestamp, clusters

        except KeyboardInterrupt as exc:
            raise RuntimeError("Keyboard interrupt") from exc


def publish_model_parameters(publish_client: mqtt.Client, publish_topic: str,
                             timestamp: str, model_parameters: Dict[str,Any]):
    """
    Publish model parameters to MQTT broker

    Args:
        publish_client (mqtt.Client): MQTT client
        publish_topic (str): Topic to publish to
        timestamp (str): Timestamp of data
        model_parameters (Dict[str,Any]): Model parameters
    Returns:
        
    """
    if publish_topic is not None:
        print(f"Timestamp: {timestamp}")
        payload = {
            "timestamp": timestamp,
            "model_parameters": convert_numpy_to_list(model_parameters)
        }
        try:
            message = json.dumps(payload)

            _ = reconnect_client(publish_client)

            publish_client.publish(publish_topic, message, qos=1)
            print(f"[{timestamp}] Published model parameters to {publish_topic}")
        except Exception as e:
            print(f"\nFailed to publish model parameters: {e}")

def estimate_updated_model(clusters: Dict[str,Any], model_parameters: Dict[str,Any],
                           params: Dict[str,Any]) -> Optional[Tuple[List[float],
                                                                    List[float], Dict[str,Any]]]:
    """
    Estimate model parameters based on clusters

    Args:
        clusters (Dict[str,Any]): Dictionary of clsuters
        model_parameters (Dict[str,Any]): Model parameters
        params (Dict[str,Any]): Model update parameters
    Returns:
        X (List[float]): Updated values
        omega_model (List[float]): Eigenfrequency of model
        updated_model_parameters (Dict[str,Any]): Model parameters

    """
    try:
        (X, omega_model,
         updated_model_parameters) = model_update_func.update_model(clusters, model_parameters,
                                                                    params['pars_to_update'],
                                                                    params)
        print("Model frequencies:",omega_model,"[Hz]")

        return (X, omega_model, updated_model_parameters)
    except Exception as e:
        print('Model update is not succesful.', e)
        return None

def model_update_plots(plot: List[bool], model_parameters: Dict[str,Any],
                       pars_to_update: List[str], omega_updated_model: np.ndarray[float],
                       fig_axes: List[Tuple[plt.Figure,plt.Axes]],
                       hold: bool = False) -> List[Tuple[plt.Figure,plt.Axes]]:
    """
    Plot clusters and stabilization diagram

    Args:
        plot (List[bool]): List of bools to state what plots should be made/updated
        model_parameters (Dict[str,Any]): Dictionary of model parameters
        pars_to_update (List[str]): Updated parameters, keys of model_parameters dict.
        omega_updated_model (np.ndarray[float]): Eigenfrequencies of model
        fig_axes (List[plt.Fig,plt.Axes]): List of figure and axes of plots
        hold (bool): To show graph until it is closed, plt.show(block=False)

    Returns:
        fig_axes (List[plt.Fig,plt.Axes]): List of figure and axes of plots
    """
    if plot[0] == 1:
        fig_ax1 = plot_parameters(model_parameters, pars_to_update, fig_ax=fig_axes[0])
    else:
        fig_ax1 = None
    if plot[1] == 1:
        fig_ax2 = plot_model_frequencies(omega_updated_model, fig_ax=fig_axes[1])
    else:
        fig_ax2 = None
    plt.show(block=hold)
    return [fig_ax1,fig_ax2]


def save_model_parameters(config: Dict[str,Any], timestamp: str,
                          model_parameters: Dict[str,Any]) -> None:
    """
    Save model parameters based on config.

    Args:
        config (Dict[str,Any]):
        timestamp (Str): Timestamp of the latest data
        model_parameters (Dict[str,Any]): Updated model parameters
    Returns:

    """
    if model_parameters is not None:
        # Ensure output directory exists
        os.makedirs("src/methods/packages/models/beam_parameters", exist_ok=True)

        # Thread-safe file locks
        file_locks = {topic: threading.Lock() for topic in config["model_update"]["TopicsToSubscribe"]}

        record = {
            "timestamp": timestamp,
            "parameters": convert_numpy_to_list(model_parameters)
        }
        file_path = "src/methods/packages/models/beam_parameters/beam_pars.jsonl"
        with file_locks["cpsens/d8-3a-dd-37-d2-7e/3050-A-060_sn_106209/1/acc/mode_cluster/data"]:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")

        print("Model parameters saved to:",file_path)

def load_model_parameters() -> Optional[Tuple[str, Dict[str,Any]]]:
    """
    Load model parameters based on config.

    Args:

    Returns:
        timestamp (str): Timestamp of the last updated parameters
        model_parameters (Dict[str,Any]): Updated model parameters

    """
    try:
        RECORDINGS_DIR = "src/methods/packages/models/beam_parameters"
        fname = "beam_pars.jsonl"
        path = os.path.join(RECORDINGS_DIR, fname)
        if not os.path.exists(path):
            print(f"File not found: {path}")
            model_parameters = MODEL_PARAMETERS
            timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
            return timestamp, MODEL_PARAMETERS
        else:
            with open(path, 'r') as json_file:
                data = json.loads(json_file.readlines()[-1])
            timestamp = data['timestamp']
            model_parameters = data['parameters']
            if model_parameters is None:
                print("Stored model_parameters are None. Proceed with standard parameters.")
                model_parameters = MODEL_PARAMETERS
            print("Model parameters loaded successfully from:", timestamp)

            return timestamp, model_parameters
    except Exception as e:
        print('Could not find previous model data.',e)
        return None, None



def live_model_update_with_remote_sysid(mqtt_client: mqtt.Client, config: Dict[str,Any],
                                        publish_topic: str,
                                        params: Dict[str,Any]) -> None:
    fig_axes = [None, None]
    try:
        while True:
            _, clusters, __, timestamp = subscribe_and_cluster(mqtt_client, config, params)

            if clusters is not None:
                _, model_parameters = load_model_parameters()
                _, omega_model, model_parameters = estimate_updated_model(clusters,
                                                                          model_parameters,
                                                                          params)

                if model_parameters is not None:
                    save_model_parameters(config,timestamp,model_parameters)
                    publish_model_parameters(mqtt_client,publish_topic,
                                            timestamp,model_parameters)

                    fig_axes = model_update_plots([1,1], model_parameters, params['pars_to_update'],
                                                omega_model, fig_axes)
    except KeyboardInterrupt:
        shutdown(mqtt_client,"model updating")
    except Exception as e:
        print(f"Unexpected error: {e}")
        shutdown(mqtt_client,"model updating")

def live_model_update_with_remote_clustering(mqtt_client: MQTTClient, config: Dict[str,Any],
                                            subscribe_topic: str, publish_topic: str,
                                            params: Dict[str,Any]) -> None:
    model_parameters = MODEL_PARAMETERS
    fig_axes = [None, None]

    try:
        while True:
            timestamp, clusters = subscribe_cluster_results(mqtt_client, config, subscribe_topic)

            if clusters is not None:
                _, model_parameters = load_model_parameters()
                _, omega_model, model_parameters = estimate_updated_model(clusters,
                                                                          model_parameters,
                                                                          params)

                if model_parameters is not None:
                    save_model_parameters(config,timestamp,model_parameters)
                    publish_model_parameters(mqtt_client,publish_topic,
                                             timestamp,model_parameters)

                    fig_axes = model_update_plots([1,1], model_parameters,
                                                  params['pars_to_update'], omega_model, fig_axes)

    except KeyboardInterrupt:
        plt.close()
        shutdown(mqtt_client,"model updating")
    except Exception as e:
        print(f"Unexpected error: {e}")
        shutdown(mqtt_client,"model updating")
