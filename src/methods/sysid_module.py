import time
import json
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from paho.mqtt.client import Client as MQTTClient
from pyoma2.setup.single import SingleSetup
from functions.util import convert_numpy_to_list
from data.accel.metadata import extract_fs_from_metadata
from data.comm.mqtt import setup_mqtt_client
from data.accel.hbk.aligner import Aligner
from methods.packages.pyoma.ssiWrapper import SSIcov
from methods.constants import DEFAULT_FS, PARAMS



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
        ordmin=params['model_order_min'],
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
    }


def setup_client(mqtt_config: Dict[str, Any]) -> Tuple[MQTTClient, float]:
    """
    Sets up and starts the MQTT client for subscribing to sensor data.
    Also extracts sampling frequency from metadata if available.

    Args:
        mqtt_config: Configuration dictionary for the MQTT client.

    Returns:
        A tuple of the connected MQTTClient instance and the extracted sampling frequency.
    """
    try:
        fs = extract_fs_from_metadata(mqtt_config)
        print("Extracted FS from metadata:", fs)
    except Exception:
        print("Failed to extract FS from metadata. Using DEFAULT_FS.")
        fs = DEFAULT_FS

    data_client, _ = setup_mqtt_client(mqtt_config, topic_index=0)
    data_client.connect(mqtt_config["host"], mqtt_config["port"], 60)
    data_client.loop_start()
    return data_client, fs


def get_oma_results(
        sampling_period: int, aligner: Aligner, fs: float
        ) -> Optional[Tuple[Dict[str, Any], datetime]]:
    """
    Extracts aligned sensor data and runs system identification (sysID).

    Args:
        sampling_period: How many minutes of data to pass to sysid.
        aligner: An initialized Aligner object.
        fs: Sampling frequency to use in the OMA algorithm.

    Returns:
        A tuple (OMA_output, timestamp) if successful, or None if data is not ready.
    """

    number_of_samples = int(sampling_period * 60 * fs)
    data, timestamp = aligner.extract(number_of_samples)

    if data.size < number_of_samples:
        return None, None

    try:
        oma_output = sysid(data, PARAMS)
        return oma_output, timestamp
    except Exception as e:
        print(f"sysID failed: {e}")
        return None, None


def publish_oma_results(sampling_period: int, aligner: Aligner,
                        publish_client: MQTTClient, publish_topic: str,
                        fs: float) -> None:
    """
    Repeatedly tries to get aligned data and publish OMA results once.

    Args:
        sampling_period: Duration (in minutes) of data to extract.
        aligner: Aligner object that provides synchronized sensor data.
        publish_client: MQTT client used for publishing results.
        publish_topic: The MQTT topic to publish results to.
        fs: Sampling frequency.
    """
    t1 = time.time()
    loop = True
    while True:
        try:
            time.sleep(0.1)
            t2 = time.time()
            t_text = f"Waiting for data for {round(t2-t1,1)} seconds"
            print(t_text,end="\r")
            oma_output, timestamp = get_oma_results(sampling_period, aligner, fs)


            if oma_output:
                print(f"Timestamp: {timestamp}")
                payload = {
                    "timestamp": timestamp.isoformat(),
                    "OMA_output": convert_numpy_to_list(oma_output)
                }
                try:
                    message = json.dumps(payload)

                    if not publish_client.is_connected():
                        print("Publisher disconnected. Reconnecting...")
                        publish_client.reconnect()

                    publish_client.publish(publish_topic, message, qos=1)
                    print(f"[{timestamp.isoformat()}] Published OMA result to {publish_topic}")
                    loop = True
                    break
                except Exception as e:
                    print(f"\nFailed to publish OMA result: {e}")

        except KeyboardInterrupt:
            print("\nShutting down gracefully")
            aligner.mqtt_client.loop_stop()
            aligner.mqtt_client.disconnect()
            publish_client.disconnect()
            loop = False
            break
        except Exception as e:
            print(f"\nUnexpected error: {e}")

    return loop
