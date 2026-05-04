import datetime
import threading
import json
from typing import Any, List, Dict, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from paho.mqtt.client import Client as MQTTClient, MQTTMessage
from data.comm.mqtt import (shutdown,start_mqtt, publish_to_mqtt)
from functions.util import (convert_numpy_to_list, _convert_list_to_dict_or_array)
from methods.model_update_functions.plot_model_update import (plot_parameters,
                                                              plot_model_frequencies)
from methods.mode_clustering import subscribe_and_cluster
from methods.model_update_functions import model_update_func
from methods.constants import (MODEL_DIR, MODEL_PARS_NAME, MODEL_PARAMETERS, MODEL_FUNC)
from methods.mode_clustering import _on_connect

# pylint: disable=C0103, W0603

# Global threading event to wait for cluster data
result_ready = threading.Event()
cluster_global = None  # will store received cluster data inside callback
timestamp_global = None

def _on_message(_client: MQTTClient, _userdata: Dict, msg: MQTTMessage) -> None:
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

def subscribe_cluster_output(config: Dict[str,Any]) -> Tuple[str, Dict[str,Any]]:
    """
    Args:
        config (Dict[str,Any]): Configuration dictionary
    Returns:
        timestamp (str): timestamp string
        clusters (Dict[str,Any]) Dictionary of clusters
    """
    global cluster_global
    global timestamp_global

    cluster_global = None  # Reset in case old data is present
    timestamp_global = None
    result_ready.clear()

    mqtt_client, _, _ = start_mqtt(config["model_update"], _on_connect, _on_message=_on_message)
    print("Waiting for mode clustering data...")


    try:
        # Use timeout to allow keyboard interrupt to work
        while not result_ready.wait(timeout=2.0):
            pass  # Keep checking with timeout

        if cluster_global is None:
            raise RuntimeError("Failed to receive cluster data.")
        clusters = cluster_global
        timestamp = timestamp_global
        print(f"Cluster data received at {timestamp}. Running model update...")

        shutdown(mqtt_client)
        return timestamp, clusters

    except KeyboardInterrupt as exc:
        shutdown(mqtt_client,"model updating")
        raise RuntimeError("Keyboard interrupt") from exc

def publish_model_parameters(config: Dict[str,Any],
                             timestamp: str, model_parameters: Dict[str,Any]) -> None:
    """
    Publish model parameters to MQTT broker

    Args:
        config (Dict[str,Any]): Configuration dictionary
        timestamp (str): Timestamp of data
        model_parameters (Dict[str,Any]): Model parameters
    Returns:
        
    """
    publish_client, _, publish_topics = start_mqtt(config["model_update"], _on_connect)

    payload = {
            "timestamp": timestamp,
            "model_parameters": convert_numpy_to_list(model_parameters)
        }

    publish_to_mqtt(publish_client, publish_topics, payload, "model parameters")
    shutdown(publish_client,"model parameter publish client")

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
         updated_model_parameters) = model_update_func.update_model(clusters, MODEL_FUNC,
                                                                         model_parameters,
                                                                    params['pars_to_update'],
                                                                    params)
        if omega_model is not None:
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
        Path(MODEL_DIR).mkdir(parents=True, exist_ok=True)

        # Thread-safe file locks
        file_locks = {topic: threading.Lock() for topic in config["model_update"]["TopicsToSubscribe"]}

        record = {
            "timestamp": timestamp,
            "parameters": convert_numpy_to_list(model_parameters)
        }
        file_path = Path(MODEL_DIR)/MODEL_PARS_NAME
        with file_locks[config["model_update"]["TopicsToSubscribe"][0]]:
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
        path = Path(MODEL_DIR) / MODEL_PARS_NAME
        if not path.exists():
            print(f"File not found: {path}. Proceed with standard parameters from model and constants.py..")
            _, __, ___, ____, _____ = MODEL_FUNC(MODEL_PARAMETERS) #Adds standard model parameters to variable
            model_parameters = MODEL_PARAMETERS
            timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
            return timestamp, model_parameters
        else:
            with path.open('r') as json_file:
                data = json.loads(json_file.readlines()[-1])
            timestamp = data['timestamp']
            model_parameters = data['parameters']
            if model_parameters is None:
                print("Stored model_parameters are None. Proceed with standard parameters from model and constants.py.")
                _, __, ___, ____, _____ = MODEL_FUNC(MODEL_PARAMETERS)
                model_parameters = MODEL_PARAMETERS
            else:
                print("Model parameters loaded successfully from:", path,"at:", timestamp)

            return timestamp, model_parameters
    except Exception as e:
        print('Could not find previous model data.',e)
        return None, None

def live_model_update_with_remote_sysid(config: Dict[str,Any],
                                        params: Dict[str,Any],
                                        publish: bool = False) -> None:
    fig_axes = [None, None]
    try:
        while True:
            _, model_parameters = load_model_parameters()
            _, clusters, __, timestamp = subscribe_and_cluster(config, params)

            if clusters is not None:
                (_, omega_model, model_parameters) = estimate_updated_model(clusters,
                                                                        model_parameters,
                                                                        params)

                if model_parameters is not None:
                    save_model_parameters(config,timestamp,model_parameters)
                    if publish:
                        publish_model_parameters(config,
                                            timestamp,model_parameters)

                    fig_axes = model_update_plots([1,1], model_parameters,
                                                params['pars_to_update'], omega_model, fig_axes)
    except KeyboardInterrupt:
        print("Keyboard interrupt in live model updating\n")
    except Exception as e:
        print(f"Unexpected error: {e}")

def live_model_update_with_remote_clustering(config: Dict[str,Any],
                                            params: Dict[str,Any],
                                            publish: bool = False) -> None:
    fig_axes = [None, None]

    try:
        while True:
            timestamp, clusters = subscribe_cluster_output(config)

            if clusters is not None:
                _, model_parameters = load_model_parameters()
                (_, omega_model, model_parameters) = estimate_updated_model(clusters,
                                                                model_parameters, params)

                if model_parameters is not None:
                    save_model_parameters(config,timestamp,model_parameters)
                    if publish:
                        publish_model_parameters(config,
                                             timestamp,model_parameters)

                    fig_axes = model_update_plots([1,1], model_parameters,
                                                  params['pars_to_update'], omega_model,
                                                 fig_axes)
    except KeyboardInterrupt:
        print("Keyboard interrupt of live model updating\n")
    except Exception as e:
        print(f"Unexpected error: {e}")
