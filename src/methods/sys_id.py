import time
import json
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
import numpy as np
from paho.mqtt.client import Client as MQTTClient
from pyoma2.setup.single import SingleSetup
from data.comm.mqtt import setup_mqtt_client
from data.accel.hbk.aligner import Aligner
from methods.pyoma.ssiWrapper import SSIcov
from methods.constants import WAIT_METADATA, DEFAULT_FS, MODEL_ORDER, BLOCK_SHIFT


FS = DEFAULT_FS

def sysid(data, params):
    """
    Perform system identification using the Covariance-based
            Stochastic Subspace Identification (SSI-COV) method.

    Args:
        data (numpy.ndarray): Input time-series data, where rows represent time steps and
                              columns represent different sensor channels.
        params (dict): Dictionary containing parameters for the system identification process:
            - 'Fs' (float): Sampling frequency of the input data.
            - 'block_shift' (int): Block shift parameter for the SSI algorithm.
            - 'model_order' (int): Maximum model order for the system identification.

    Returns:
        tuple: Contains identified model parameters (frequencies, cov_freq, damping_ratios,
               cov_damping, mode_shapes, poles_label).
    """
    if data.shape[0]<data.shape[1]:
        data = data.T                           # transpose it if data has more column than rows
    print(f"Data dimensions: {data.shape}")
    print(f"OMA parameters: {params}")

    my_setup = SingleSetup(data, fs=params['Fs'])
    ssi_mode_track = SSIcov(
        name="SSIcovmm_mt",
        method='cov_mm',
        br=params['block_shift'],
        ordmax=params['model_order'],
        calc_unc=True
    )

    my_setup.add_algorithms(ssi_mode_track)
    my_setup.run_by_name("SSIcovmm_mt")

    output = ssi_mode_track.result.model_dump()
    return {
        'Fn_poles': output['Fn_poles'],
        'Fn_poles_cov': output['Fn_poles_cov'],
        'Xi_poles': output['Xi_poles'],
        'Xi_poles_cov': output['Xi_poles_cov'],
        'Phi_poles': output['Phi_poles'],
        'Lab': output['Lab']
    }


def convert_numpy_to_list(obj: Any) -> Any:
    """
    Recursively convert NumPy arrays and complex numbers to JSON-safe types.

    Args:
        obj: Any data type.

    Returns:
        A fully JSON-serializable version of the input.
    """
    if isinstance(obj, dict):
        return {k: convert_numpy_to_list(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_numpy_to_list(item) for item in obj]
    if isinstance(obj, np.ndarray):
        return convert_numpy_to_list(obj.tolist())
    if isinstance(obj, complex):
        return {"real": obj.real, "imag": obj.imag}
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    return obj


def _on_metadata(client: MQTTClient, userdata: Dict[str, str], message) -> None:
    """
    MQTT callback to extract sampling frequency from incoming metadata.

    Args:
        client: MQTT client instance.
        userdata: Dictionary containing metadata topic.
        message: Incoming MQTT message.
    """
    try:
        payload = json.loads(message.payload.decode("utf-8"))
        fs_candidate = payload["Analysis chain"][0]["Sampling"]
        if fs_candidate:
            global FS  # pylint: disable=global-statement
            FS = fs_candidate
            print(f"Extracted Fs from metadata: {FS}")
            client.unsubscribe(userdata["metadata_topic"])
    except Exception as e:
        print(f"Failed to extract Fs: {e}")


def extract_fs_from_metadata(mqtt_config: Dict[str, Any]) -> int:
    """
    Connects to MQTT broker and waits for metadata to extract sampling frequency.

    Args:
        mqtt_config: MQTT connection configuration.
    """
    metadata_topic = mqtt_config["TopicsToSubscribe"][1]
    metadata_client, _ = setup_mqtt_client(mqtt_config, topic_index=1)
    metadata_client.user_data_set({"metadata_topic": metadata_topic})
    metadata_client.message_callback_add(metadata_topic, _on_metadata)

    metadata_client.connect(mqtt_config["host"], mqtt_config["port"], 60)
    metadata_client.subscribe(metadata_topic)
    metadata_client.loop_start()

    initial_fs = FS
    start_time = time.time()
    # Wait until the Metadata arrives
    while FS == initial_fs and (time.time() - start_time) < WAIT_METADATA:
        time.sleep(0.1)

    metadata_client.loop_stop()
    print(f"Sampling frequency FS = {FS}")

    return FS


def setup_client(mqtt_config: Dict[str, Any]) -> MQTTClient:
    """
    Sets up and starts the MQTT client for subscribing to sensor data.

    Args:
        mqtt_config: Configuration dictionary for the MQTT client.

    Returns:
        A connected and loop-started MQTTClient instance.
    """
    if len(mqtt_config.get("topics", [])) > 1:
        extract_fs_from_metadata(mqtt_config)
    data_client, _ = setup_mqtt_client(mqtt_config, topic_index=0)
    data_client.connect(mqtt_config["host"], mqtt_config["port"], 60)
    data_client.loop_start()
    return data_client


def get_oma_results(minutes: int, aligner: Aligner) -> Optional[Tuple[Dict[str, Any], datetime]]:
    """
    Extracts aligned sensor data and runs system identification (sysID).

    Args:
        minuttes: How many minutes of data to pass to sysid.
        aligner: An initialized Aligner object.
        params:  'block_shift', and 'model_order'.

    Returns:
        A tuple (OMA_output, timestamp) if successful, or None if data is not ready.
    """

    oma_params = {
        "Fs": FS,
        "block_shift": BLOCK_SHIFT, 
        "model_order": MODEL_ORDER  
    }


    number_of_samples = int(minutes *60 * FS)
    data, timestamp = aligner.extract(number_of_samples)

    if  data.size < number_of_samples:
        #print("Not enough aligned data yet.")
        return None, None
    try:
        oma_output = sysid(data, oma_params)
        return oma_output, timestamp
    except Exception as e:
        print(f"sysID failed: {e}")
        return None, None


def publish_oma_results(minutes: int,aligner: Aligner,
                        publish_client: MQTTClient, publish_topic: str) -> None:
    """
    Continuously runs system identification on incoming aligned data and publishes results.

    Args:
        aligner: An initialized Aligner object for synchronized sensor data.
        params: Dictionary containing SSI parameters.
        publish_client: MQTT client used for publishing results.
        publish_topic: The MQTT topic where results will be published.
    """
    try:
        while True:
            time.sleep(0.5)
            result = get_oma_results(minutes, aligner)
            if result and result[0] is not None:
                oma_output, timestamp = result
                # Build payload
                payload = {
                    "timestamp": timestamp.isoformat(),
                    "OMA_output": convert_numpy_to_list(oma_output)
                }
                try:
                    message = json.dumps(payload)

                    # Reconnect if needed
                    if not publish_client.is_connected():
                        print("Publisher disconnected. Reconnecting...")
                        publish_client.reconnect()

                    # Publish
                    publish_client.publish(publish_topic, message, qos=1)
                    print(f"[{timestamp.isoformat()}] Published OMA result to {publish_topic}")

                except Exception as e:
                    print(f"Failed to publish OMA result: {e}")
    except KeyboardInterrupt:
        print("Shutting down gracefully")
        aligner.client.loop_stop()
        aligner.client.disconnect()
        publish_client.disconnect()
