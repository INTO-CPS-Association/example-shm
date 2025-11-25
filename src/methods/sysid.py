import time
import json
from typing import Any, Dict, Optional, Tuple, List
from datetime import datetime
import numpy as np
from paho.mqtt.client import Client as MQTTClient
from pyoma2.setup.single import SingleSetup
from data.accel.aligner import IAligner
from data.comm.mqtt import (load_config,setup_mqtt_client,shutdown,publish_to_mqtt)
from data.accel.metadata import extract_fs_from_metadata
from data.accel.hbk.aligner import Aligner
from functions.util import convert_numpy_to_list
from methods.packages.pyoma.ssiWrapper import SSIcov
from methods.constants import DEFAULT_FS, PARAMS

def sysid(data: np.ndarray[float], params: Dict[str,Any]) -> Dict[str, Any]:
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
    print(f"sysid parameters: {params}")

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
        (Tuple[MQTTClient, float]): A tuple of the connected MQTTClient instance and the extracted sampling frequency.
    """
    try:
        fs = extract_fs_from_metadata(mqtt_config)
    except Exception:
        print("Failed to extract FS from metadata. Using DEFAULT_FS.")
        fs = DEFAULT_FS

    data_client = setup_mqtt_client(mqtt_config, mqtt_config["TopicsToSubscribe"][0])
    data_client.connect(mqtt_config["host"], mqtt_config["port"], 60)
    data_client.loop_start()
    return data_client, fs

def setup_sysid(config_path, data_topic_indexes: List[int] = None) -> Tuple[IAligner, MQTTClient,
                                                          Dict[str,Any], float]:
    """
    Helper function to set up sysid (Operational Modal Analysis).

    Parameters:
        config_path (str): Path to the configuration file.
        data_topic_indexes (list): Indexes of topics to subscribe to.

    Returns:
        Aligner (IAligner): The aligner object for data alignment.
        data_client (MQTTClient): The MQTT client used for data subscription.
        mqtt_config (Dict[str,Any]): Configuration dictionary for the MQTT client.
        fs (float): Sampling frequency.
    """
    config = load_config(config_path)
    mqtt_config = config["sysid"]

    # Setting up the client and extracting Fs
    data_client, fs = setup_client(mqtt_config)

    # Setting up the aligner
    if data_topic_indexes is None:
        data_topic_indexes = list(range(len(mqtt_config["TopicsToSubscribe"])))
    selected_topics = [mqtt_config["TopicsToSubscribe"][i] for i in data_topic_indexes]
    aligner = Aligner(data_client, topics=selected_topics)
    return aligner, data_client, mqtt_config, fs

def get_sysid_output(
        sampling_period: int, aligner: Aligner, fs: float
        ) -> Optional[Tuple[Dict[str, Any], str]]:
    """
    Extracts aligned sensor data and runs system identification (sysID).

    Args:
        sampling_period: How many minutes of data to pass to sysid.
        aligner: An initialized Aligner object.
        fs: Sampling frequency to use in the sysid algorithm.

    Returns:
        sysid_output (Dict[str, Any]): System identification output data.
        aligner_time (str): Timestamp of the aligned data.
    """

    number_of_samples = int(sampling_period * 60 * fs)
    data, aligner_time = aligner.extract(number_of_samples)

    if data.size < number_of_samples:
        return None, None

    try:
        sysid_output = sysid(data, PARAMS)
        return sysid_output, aligner_time.isoformat()
    except Exception as e:
        print(f"sysID failed: {e}")
        return None, None

def wait_for_sysid_output(number_of_minutes: float, aligner: Aligner,
                          fs: float) -> Optional[Tuple[Dict[str, Any],str]]:
    """
    Extract system identidication results while printing elapsed time

    Args:
        sampling_period (float): How many minutes of data to pass to sysid.
        aligner (IAligner): An initialized Aligner object.
        fs (float): Sampling frequency to use in the sysid algorithm.

    Returns:
        sysid_output (Dict[str, Any]): System identification output data.
        aligner_time (str): Timestamp of the aligned data.
    """
    aligner_time = None
    t1 = time.time()
    try:
        while aligner_time is None:
            time.sleep(0.1)
            t2 = time.time()
            t_text = f"Waiting for data for {round(t2-t1,1)} seconds"
            print(t_text,end="\r")
            sysid_output, aligner_time = get_sysid_output(number_of_minutes, aligner, fs)

            if (t2-t1) > 20*number_of_minutes*60:
                raise RuntimeError("Aligned data not recieved in time")

        print("Aligned data recieved at:",aligner_time)
        return sysid_output, aligner_time
    except KeyboardInterrupt as exc:
        raise RuntimeError("Keyboard interrupt") from exc

def publish_sysid_output(publish_client: MQTTClient, publish_topics: List[str],
                        sysid_output: Dict[str, Any], aligner_time: str) -> None:
    """
    Ppublish sysid results once.

    Args:
        publish_client (MQTTClient): MQTT client used for publishing results.
        publish_topics (str): The MQTT topic to publish results to.
        sysid_output (Dict[str, Any]): System identification output data.
        aligner_time (str): Sampling frequency.
    Returns:
    """
    
    payload = {
        "timestamp": aligner_time,
        "sysid_output": convert_numpy_to_list(sysid_output)
    }
    
    publish_to_mqtt(publish_client, publish_topics, payload, "sysid output")

def local_sysid(config_path: str, number_of_minutes: float, topic_indexes: List[int] = None):
    """
    Perform local sysid using specified configuration and topic indexes.
    Args:
        config_path (str): Configuration path.
        number_of_minutes (float): How many minutes of data to sample.
        topic_indexes (List[int]): Indexes of topics to subscribe to.
    Returns:
        mqtt_client (MQTTClient): MQTT client used for publishing results.
        sysid_output (Dict[str, Any]): System identification output data.
        aligner_time (str): Sampling frequency.
    """
    aligner, mqtt_client, _, fs = setup_sysid(config_path, topic_indexes)

    sysid_output, aligner_time = wait_for_sysid_output(number_of_minutes, aligner, fs)
    print("Aligned data recieved at:",aligner_time)

    return mqtt_client, sysid_output, aligner_time

def live_sysid(config_path: str, number_of_minutes: float, topic_indexes: List[int] = None, loop: bool = True):
    """
    Perform live sysid using specified configuration and topic indexes.
    Args:
        config_path (str): Configuration path.
        number_of_minutes (float): How many minutes of data to sample.
        topic_indexes (List[int]): Indexes of topics to subscribe to.
        loop (bool): Whether to loop the sysid process continuously.
    Returns:
    """
    aligner, mqtt_client, mqtt_config, fs = setup_sysid(config_path, topic_indexes)
    try:
        aligner_time_last = datetime.fromisoformat("2025-01-01 01:01:00.00000")
        while True:
            sysid_output, aligner_time = wait_for_sysid_output(number_of_minutes,
                                                                      aligner, fs)
            publish_sysid_output(mqtt_client, mqtt_config["TopicsToPublish"],
                                        sysid_output, aligner_time)
            
            dt = datetime.fromisoformat(aligner_time)-aligner_time_last
            print(dt)
            aligner_time_last = datetime.fromisoformat(aligner_time)
            
            if loop is False:
                break
    except KeyboardInterrupt:
        print("\nKeyboard interrupt. Shutting down gracefully")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    shutdown(mqtt_client,"sysid")