import json
import threading
from typing import Any, List, Dict, Tuple, Optional
import numpy as np
import paho.mqtt.client as mqtt
from scipy.optimize import minimize
from scipy.linalg import eigh
from methods.constants import PARAMS
from methods.packages.clustering import (cluster_func)
from methods.packages.cantilever_beam.eval_yafem_model import eval_yafem_model
from methods.packages import model_update
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


def _on_connect(client: mqtt.Client, userdata: dict, flags: dict,
                reason_code: int, properties: mqtt.Properties) -> None:
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


def run_mode_clustering(oma_output: Any) -> Dict[str, Dict]:
    """
    Runs the mode tracking algorithm.

    Args:
        oma_output (Any): OMA output from subscription or elsewhere.
    Returns:
        cleaned_values (List[Dict]), 
        median_frequencies (np.ndarray), 
        confidence_intervals (np.ndarray)
    """

    cluster_dict_before, cluster_dict_allignment, cluster_dict = cluster_func(oma_output,
                                                                              PARAMS, plot=False)

    return cluster_dict_before, cluster_dict


# pylint: disable=R0914
def run_model_update(cluster_dict: Dict[str, Dict], model_pars={}) -> Optional[Dict[str, Any]]:
    """
    Runs model updating based on cleaned OMA clusters.

    Args:
        cleaned_values (Dict[str, Dict]): Cleaned cluster results.

    Returns:
        Updated model details or None if error.
    """
    comb = {'cluster': cluster_dict}
    try:
        res = minimize(lambda x: model_update.par_est(x, comb, PARAMS, model_pars),
                       PARAMS['MU_start_values'], bounds=PARAMS["MU_bounds"],
                       options={'maxiter': 1000})
        X = res.x
        print(f'Updated parameters: {X}')

        idx = 0
        pars_updated = {}
        for key in model_pars:
            if str(key) in PARAMS['pars_to_update']:
                pars_updated[key] = PARAMS['updated_values'][idx]
                idx += 1
            else:
                pars_updated[key] = model_pars[key]

        omegaMU, phi, PhiMU, myModel = eval_yafem_model(pars_updated)
        print("\nomegaMU:",omegaMU)
        # print("\nphi:",phi)
        # print("\nPhiMU:",PhiMU)

        M = myModel.M.todense()
        K = myModel.K.todense()

        eigenvalues, eigenvectors = eigh(K, M)
        omegaN = np.sqrt(eigenvalues)
        omegaN_pi = omegaN / (2 * np.pi)

        return {
            'optimized_parameters': X,
            'omegaN_rad': omegaN,
            'omegaN_Hz': omegaN_pi,
            'pars_updated': pars_updated,
        }

    except ValueError as e:
        print(f"Skipping model updating due to error: {e}")
        return None


def subscribe_and_get_cleaned_values(config_path: str,
            num_clusters: int = 2) -> Tuple[List[Dict], np.ndarray, np.ndarray]:
    """
    Subscribes to MQTT broker, receives one OMA message, runs mode tracking, and returns results.

    Args:
        config_path (str): Path to config JSON.
        num_clusters (int): Number of clusters to keep after mode tracking.

    Returns:
        cleaned_values (List[Dict]), 
        median_frequencies (np.ndarray), 
        confidence_intervals (np.ndarray)
    """
    global oma_output_global
    oma_output_global = None  # Reset in case old data is present
    result_ready.clear()

    config = load_config(config_path)
    mqtt_client, selected_topic = setup_mqtt_client(config["MQTT"], topic_index=0)
    #mqtt_client, selected_topic = setup_mqtt_client(config["sysID"], topic_index=0)

    mqtt_client.user_data_set({"topic": selected_topic, "qos": 0})
    mqtt_client.on_connect = _on_connect
    mqtt_client.on_message = _on_message
    mqtt_client.connect(config["MQTT"]["host"], config["MQTT"]["port"], keepalive=60)
    #mqtt_client.connect(config["sysID"]["host"], config["sysID"]["port"], keepalive=60)
    mqtt_client.loop_start()
    print("Waiting for OMA data...")
    result_ready.wait()  # Wait until message arrives
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

    if oma_output_global is None:
        raise RuntimeError("Failed to receive OMA data.")

    print("OMA data received. Running mode tracking...")
    return cluster_func(oma_output_global,PARAMS)
