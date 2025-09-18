import time
import json
import numpy
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from paho.mqtt.client import Client as MQTTClient
from pyoma2.setup.single import SingleSetup
from functions.util import convert_numpy_to_list
from data.accel.metadata import extract_fs_from_metadata
from data.comm.mqtt import setup_mqtt_client
from data.accel.hbk.aligner import Aligner
from methods.packages.pyoma.ssiWrapper import SSIcov
from methods.constants import PARAMS



def sysid(data: numpy.ndarray, Params: dict[str,Any]) -> dict[str,Any]:
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
    # print(f"Data dimensions: {data.shape}")
    # print(f"OMA parameters: {params}")

    my_setup = SingleSetup(data, fs=Params['Fs'])
    ssi_mode_track = SSIcov(
        name="SSIcovmm_mt",
        method='cov_mm',
        br=Params['block_shift'],
        ordmin=Params['model_order_min'],
        ordmax=Params['model_order'],
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
        # 'Lab': output['Lab']
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
        fs = PARAMS["Fs"]

    data_client, _ = setup_mqtt_client(mqtt_config, topic_index=0)
    data_client.connect(mqtt_config["host"], mqtt_config["port"], 60)
    data_client.loop_start()
    return data_client, fs


def get_oma_data(
        sampling_period: int, aligner: Aligner, fs: float
        ) -> Optional[datetime]:
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

    if data.size >= number_of_samples:
        return data, timestamp


def get_oma_results(
        sampling_period: int, aligner: Aligner, fs: float
        ) -> Optional[Tuple[Dict[str, Any], datetime,Dict[str, Any]]]:
    """
    Extracts aligned sensor data and runs system identification (sysID).

    Args:
        sampling_period: How many minutes of data to pass to sysid.
        aligner: An initialized Aligner object.
        fs: Sampling frequency to use in the OMA algorithm.

    Returns:
        A tuple (OMA_output, timestamp) if successful, or None if data is not ready.
    """
    oma_params = {
        "Fs": fs,
        "block_shift": PARAMS['block_shift'],
        "model_order_min": PARAMS['model_order_min'],
        "model_order": PARAMS['model_order']  
    }

    number_of_samples = int(sampling_period * 60 * fs)
    data, timestamp = aligner.extract(number_of_samples)

    if data.size < number_of_samples:
        return None, None, None

    try:
        oma_output = sysid(data, oma_params)

        # for ii,x in enumerate(data):
        #     plt.plot(x,label=f"Data: {ii}")
        # plt.legend()
        # plt.title(timestamp)
        # plt.grid()
        # plt.show()

        return (oma_output, timestamp, oma_params)
    except Exception as e:
        print(f"sysID failed: {e}")
        return (None, None, None)


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
    while True:
        try:
            time.sleep(0.5)
            oma_output, timestamp, _ = get_oma_results(sampling_period, aligner, fs)
            print(f"OMA result: {oma_output}")
            print(f"Timestamp: {timestamp}")

            if oma_output:
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
                    break

                except Exception as e:
                    print(f"Failed to publish OMA result: {e}")
        except KeyboardInterrupt:
            print("Shutting down gracefully")
            aligner.client.loop_stop()
            aligner.client.disconnect()
            publish_client.disconnect()
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
