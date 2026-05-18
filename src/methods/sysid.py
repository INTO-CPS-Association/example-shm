import time
from typing import Any, Dict, Optional, Tuple, List
from datetime import datetime
import numpy as np
from paho.mqtt.client import Client as MQTTClient
from pyoma2.setup.single import SingleSetup
from data.comm.mqtt import (shutdown,publish_to_mqtt)
from data.accel.hbk.aligner import Aligner
from functions.util import convert_numpy_to_list
from methods.packages.pyoma.ssiWrapper import SSIcov
from methods.constants import PARAMS
from examples.aligning_readings import get_data, setup_aligner

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
    print(f"sysid parameters: Sample frequency [Hz]: {params['Fs']}, Model order: {params['model_order']}, Block shift: {params['block_shift']}")

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

def wait_for_sysid_output(samples: int, aligner: Aligner,
                          fs: float) -> Optional[Tuple[Dict[str, Any],str]]:
    """
    Extract system identidication results while printing elapsed time

    Args:
        sampling_period (float): How many minutes of data to pass to sysid.
        aligner (Aligner): An initialized Aligner object.
        fs (float): Sampling frequency to use in the sysid algorithm.

    Returns:
        sysid_output (Dict[str, Any]): System identification output data.
        aligner_time (str): Timestamp of the aligned data.
    """
    aligner_time = None
    PARAMS['Fs'] = fs
    t1 = time.time()
    try:
        while aligner_time is None:
            time.sleep(0.1)
            t2 = time.time()
            t_text = f"Waiting for data for {round(t2-t1,1)} seconds"
            print(t_text,end="\r")
            data, aligner_time = get_data(samples, aligner)
        sysid_output = sysid(data, PARAMS)
        print("Aligned data received at:",aligner_time)
        return sysid_output, aligner_time
    except KeyboardInterrupt as exc:
        raise RuntimeError("Keyboard interrupt") from exc

def publish_sysid_output(publish_client: MQTTClient, publish_topics: List[str],
                        sysid_output: Dict[str, Any], aligner_time: str) -> None:
    """
    Publish sysid results once.

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

def local_sysid(config_path: str, topic_indexes: List[int] = None):
    """
    Perform local sysid using specified configuration and topic indexes.
    Args:
        config_path (str): Configuration path.
        topic_indexes (List[int]): Indexes of topics to subscribe to.
    Returns:
        mqtt_client (MQTTClient): MQTT client used for publishing results.
        sysid_output (Dict[str, Any]): System identification output data.
        aligner_time (str): Sampling frequency.
    """
    aligner, mqtt_client, mqtt_config, fs = setup_aligner(config_path, config_name="sysid",
                                                          data_topic_indexes=topic_indexes)

    sysid_output, aligner_time = wait_for_sysid_output(mqtt_config['SamplesToCollect'], aligner, fs)
    print("Aligned data received at:",aligner_time)

    return mqtt_client, sysid_output, aligner_time

def live_sysid(config_path: str, topic_indexes: List[int] = None, loop: bool = True):
    """
    Perform live sysid using specified configuration and topic indexes.
    Args:
        config_path (str): Configuration path.
        topic_indexes (List[int]): Indexes of topics to subscribe to.
        loop (bool): Whether to loop the sysid process continuously.
    Returns:
    """
    aligner, mqtt_client, mqtt_config, fs = setup_aligner(config_path,
                                                          data_topic_indexes=topic_indexes)
    samples = mqtt_config['SamplesToCollect']
    try:
        aligner_time_last = datetime.fromisoformat("2025-01-01 01:01:00.00000")
        while True:
            sysid_output, aligner_time = wait_for_sysid_output(samples,
                                                                      aligner, fs)
            publish_sysid_output(mqtt_client, mqtt_config["TopicsToPublish"],
                                        sysid_output, aligner_time)

            dt = datetime.fromisoformat(aligner_time)-aligner_time_last
            print("Time passed",dt)
            aligner_time_last = datetime.fromisoformat(aligner_time)

            if loop is False:
                break
    except KeyboardInterrupt:
        print("\nKeyboard interrupt. Shutting down gracefully")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    shutdown(mqtt_client,"sysid")
