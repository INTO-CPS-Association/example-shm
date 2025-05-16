import json
import threading
from typing import Any, List, Dict, Tuple, Optional
import numpy as np
import paho.mqtt.client as mqtt
from scipy.optimize import minimize
from scipy.linalg import eigh
from methods.constants import MODEL_ORDER, MSTAB_FACTOR, TMAC
from methods.packages.mode_track import mode_allingment
from methods.packages.eval_yafem_model import eval_yafem_model
from methods.packages import model_update
from methods.constants import X0, BOUNDS
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


def run_mode_track(oma_output: Any) -> Tuple[List[Dict], np.ndarray, np.ndarray]:
    """
    Runs the mode tracking algorithm.

    Args:
        oma_output (Any): OMA output from subscription or elsewhere.
    Returns:
        cleaned_values (List[Dict]), 
        median_frequencies (np.ndarray), 
        confidence_intervals (np.ndarray)
    """
    mstab = MODEL_ORDER * MSTAB_FACTOR
    cleaned_values = mode_allingment(oma_output, mstab, TMAC)
    median_frequencies = np.array([cluster["median"] for cluster in cleaned_values])
    confidence_intervals = np.array([
        cluster["original_cluster"]["confidence_interval"]
        for cluster in cleaned_values
    ])
    return cleaned_values, median_frequencies, confidence_intervals


# pylint: disable=R0914
def run_model_update(cleaned_values: List[Dict]) -> Optional[Dict[str, Any]]:
    """
    Runs model updating based on cleaned OMA clusters.

    Args:
        cleaned_values (List[Dict]): Cleaned cluster results.

    Returns:
        Updated model details or None if error.
    """
    comb = {'cluster': cleaned_values}
    try:
        res = minimize(lambda x: model_update.par_est(x, comb),
                       X0, bounds=BOUNDS, options={'maxiter': 1000})
        X = res.x
        print(f'Updated parameters: {X}')

        pars_updated = {'k': X[0], 'Lab': X[1]}
        omegaMU, phi, PhiMU, myModel = eval_yafem_model(pars_updated)
        print("\nomegaMU:",omegaMU)
        print("\nphi:",phi)
        print("\nPhiMU:",PhiMU)

        M = myModel.M.todense()
        K = myModel.K.todense()

        eigenvalues, eigenvectors = eigh(K, M)
        omegaN = np.sqrt(eigenvalues)
        omegaN_pi = omegaN / (2 * np.pi)

        dd = np.sqrt(np.diag(eigenvectors.T @ M @ eigenvectors))
        aa = eigenvectors @ np.diag(1.0 / dd)

        zeta = np.zeros(len(omegaN))
        zeta_medians = np.array([np.median(cluster['z_values']) for cluster in cleaned_values])
        zeta[:len(zeta_medians)] = zeta_medians

        Cmodal = np.diag(2 * zeta * omegaN)
        C = np.linalg.inv(aa).T @ Cmodal @ np.linalg.inv(aa)
        system_updated = {
            "M": M,
            "K": K,
            "C": C
        }
        return {
            'optimized_parameters': X,
            'omegaN_rad': omegaN,
            'omegaN_Hz': omegaN_pi,
            'mode_shapes': aa,
            'damping_matrix': C,
            'pars_updated': pars_updated,
            'System_updated': system_updated
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
    mqtt_client, selected_topic = setup_mqtt_client(config["sysID"], topic_index=0)

    mqtt_client.user_data_set({"topic": selected_topic, "qos": 0})
    mqtt_client.on_connect = _on_connect
    mqtt_client.on_message = _on_message
    mqtt_client.connect(config["sysID"]["host"], config["sysID"]["port"], keepalive=60)
    mqtt_client.loop_start()
    print("Waiting for OMA data...")
    result_ready.wait()  # Wait until message arrives
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

    if oma_output_global is None:
        raise RuntimeError("Failed to receive OMA data.")

    print("OMA data received. Running mode tracking...")
    return run_mode_track(oma_output_global)
