from datetime import datetime
import os
import threading
import json
from typing import Any, List, Dict, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
from paho.mqtt.client import Client as MQTTClient
from data.comm.mqtt import (load_config, setup_mqtt_client, reconnect_client)
from functions.util import (convert_numpy_to_list, _convert_list_to_dict_or_array)
from methods.mode_clustering import (subscribe_and_cluster)
from methods.model_update_functions import model_update_func as MU
from methods.constants import PARAMS, MODEL_PARAMETERS
from functions.plot_model_update import (plot_parameters,plot_model_frequencies)
# pylint: disable=C0103, W0603

# Global threading event to wait for cluster data
result_ready = threading.Event()
cluster_global = None  # will store received cluster data inside callback

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

def subscribe_cluster_results(config_path) -> Optional[Tuple[datetime, Dict[str,any]]]:
    global cluster_global
    global timestamp_global

    cluster_global = None  # Reset in case old data is present
    result_ready.clear()

    config = load_config(config_path)
    mqtt_client, selected_topic = setup_mqtt_client(config["mode_cluster"], topic_index=0)

    mqtt_client.user_data_set({"topic": selected_topic, "qos": 0})
    mqtt_client.on_connect = _on_connect
    mqtt_client.on_message = _on_message
    mqtt_client.connect(config["mode_cluster"]["host"], config["mode_cluster"]["port"], keepalive=60)
    mqtt_client.loop_start()
    print("Waiting for mode clustering data...")

    while True:
        try:
            result_ready.wait()  # Wait until message arrives
            mqtt_client.loop_stop()
            mqtt_client.disconnect()

            if cluster_global is None:
                raise RuntimeError("Failed to receive cluster data.")
            clusters = cluster_global
            timestamp = timestamp_global
            print(f"Cluster data received at {timestamp}. Running model update...")

            return timestamp, clusters

        except KeyboardInterrupt:
            print("Shutting down gracefully")
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
        
        return None, None


def publish_model_parameters(publish_client,publish_topic,timestamp,model_parameters):
    #Publish updated model
    print(f"Timestamp: {timestamp}")
    payload = {
        "timestamp": timestamp,
        "model_parameters": convert_numpy_to_list(model_parameters)
    }
    try:
        message = json.dumps(payload)

        reconnect_succes = reconnect_client(publish_client)

        publish_client.publish(publish_topic, message, qos=1)
        print(f"[{timestamp}] Published model parameters to {publish_topic}")
    except Exception as e:
        print(f"\nFailed to publish model parameters: {e}")

def estimate_updated_model(cluster_dict: Dict[str,Any], model_parameters: Dict[str,Any], params: Dict[str,Any]) -> Optional[Tuple[np.ndarray[float], List[float], Dict[str,Any]]]:
    try:
        X, omegaMU, updated_model_parameters = MU.update_model(cluster_dict, model_parameters, params['pars_to_update'], params)
        model_parameters = updated_model_parameters
        
        print("Model frequencies:",omegaMU,"[Hz]")
        print("Updated parameters are:")
        for ii, name in enumerate(params['pars_to_update']):
            print(name+":",X[ii])
        return (X, omegaMU, model_parameters)
    except:
        return None

def save_model_parameters(config_path: str, timestamp: str, model_parameters: Dict[str,Any]) -> None:
    config = load_config(config_path)

    # Ensure output directory exists
    os.makedirs("src/methods/packages/models/beam_parameters", exist_ok=True)

    # Thread-safe file locks
    file_locks = {topic: threading.Lock() for topic in config["model_update"]["TopicsToSubscribe"]}

    record = {
        "timestamp": timestamp,
        "parameters": convert_numpy_to_list(model_parameters)
    }
    file_path = "src/methods/packages/models/beam_parameters/beam_pars.jsonl"
    with file_locks["cpsens/d8-3a-dd-37-d2-7e/3050-A-060_sn_106209/1/acc/model_update/data"]:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    print("Model parameters saved to:",file_path)

def load_model_parameters(config_path) -> None:
    RECORDINGS_DIR = "src/methods/packages/models/beam_parameters"
    fname = "beam_pars.jsonl"
    path = os.path.join(RECORDINGS_DIR, fname)
    if not os.path.exists(path):
        print(f"File not found: {path}")
    else:
        with open(path, 'r') as json_file:
            data = json.loads(json_file.readlines()[-1])
        timestamp = data['timestamp']
        model_parameters = data['parameters']
        print("Model parameters loaded succesfully from:", timestamp)
        return timestamp, model_parameters


def live_model_update_with_remote_sysid(config_path: str) -> None:
    model_parameters = MODEL_PARAMETERS
    fig_ax1 = None
    fig_ax2 = None
    while True:
        cluster_results, sysid_output, clusters, median_frequencies, timestamp = subscribe_and_cluster(config_path,PARAMS)

        if cluster_results:
            try:
                timestamp_last_model, model_parameters = load_model_parameters(config_path)
            except:
                print('Could not find previous model data')

            update_results = estimate_updated_model(clusters, model_parameters, PARAMS)

            if update_results is not None:
                X, omegaMU, model_parameters = update_results

                save_model_parameters(config_path,timestamp,model_parameters)      

                fig_ax1 = plot_parameters(model_parameters, PARAMS['pars_to_update'], fig_ax=fig_ax1)
                plt.show(block=False)

                fig_ax2 = plot_model_frequencies(omegaMU,fig_ax=fig_ax2)
                plt.show(block=False)
        else:
            print("Shutting down model updating")
            plt.close()
            break

def live_model_update_with_remote_clustering(config_path: str) -> None:
    model_parameters = MODEL_PARAMETERS
    fig_ax1 = None
    fig_ax2 = None

    while True:
        timestamp, clusters = subscribe_cluster_results(config_path)

        if clusters:
            try:
                timestamp_last_model, model_parameters = load_model_parameters(config_path)
            except:
                print('Could not find previous model data')

            try:
                update_results = estimate_updated_model(clusters, model_parameters, PARAMS)

                if update_results is not None:
                    X, omegaMU, model_parameters = update_results

                    save_model_parameters(config_path,timestamp,model_parameters)

                    fig_ax1 = plot_parameters(model_parameters, PARAMS['pars_to_update'],fig_ax=fig_ax1)
                    plt.show(block=False)

                    fig_ax2 = plot_model_frequencies(omegaMU,fig_ax=fig_ax2)
                    plt.show(block=False)

            except KeyboardInterrupt:
                print("Shutting down modelupdating")
                plt.close()
                break
            except Exception as e:
                print(f"Unexpected error: {e}")


def live_model_update_with_remote_clustering_and_publish(config_path: str, publish_client: MQTTClient, publish_topic: str) -> None:
    model_parameters = MODEL_PARAMETERS
    fig_ax1 = None
    fig_ax2 = None

    while True:
        timestamp, clusters = subscribe_cluster_results(config_path)

        if clusters:
            try:
                timestamp_last_model, model_parameters = load_model_parameters(config_path)
            except:
                print('Could not find previous model data')

            try:
                update_results = estimate_updated_model(clusters, model_parameters, PARAMS)

                if update_results is not None:
                    X, omegaMU, model_parameters = update_results

                    save_model_parameters(config_path,timestamp,model_parameters)
                    publish_model_parameters(publish_client,publish_topic,timestamp,model_parameters)

                    fig_ax1 = plot_parameters(model_parameters, PARAMS['pars_to_update'],fig_ax=fig_ax1)
                    plt.show(block=False)

                    fig_ax2 = plot_model_frequencies(omegaMU,fig_ax=fig_ax2)
                    plt.show(block=False)

            except KeyboardInterrupt:
                print("Shutting down modelupdating")
                plt.close()
                break
            except Exception as e:
                print(f"Unexpected error: {e}")