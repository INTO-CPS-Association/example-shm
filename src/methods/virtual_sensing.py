from typing import Dict, Any
import numpy as np
import matplotlib.pyplot as plt
from paho.mqtt.client import Client as MQTTClient
from data.accel.hbk.aligner import Aligner
from data.comm.mqtt import (shutdown)
from methods.sysid import setup_aligner
from methods.model_update import load_model_parameters
from methods.mode_clustering import publish_data
from methods.virtual_sensing_functions.virtual_sensing_func import displacement_estimation
from methods.virtual_sensing_functions.plot_virtual_sensing import plot_virtual_sensing
from methods.constants import PARAMS
from examples.aligning_readings import wait_for_data
# pylint: disable=C0103, C0301, W0104

def virtual_sensing(number_of_samples: int, aligner: Aligner, data_client: MQTTClient, fs: float) -> tuple[np.ndarray[float, Any], np.ndarray[float, Any], Dict[str,Any], str] :
    """
    Continuously estimate displacement with virtual sensing
    Args:
        number_of_samples (int): Number og minutes to sample data
        aligner (Aligner): Aligner to align data
        data_client (MQTTClient): MQTT client
        fs (float): Sample frequency

    Returns:
        disp (np.ndarray[float]): Displacements
        acc (np.ndarray[float]): Accelerations
        model_parameters (Dict[str,Any]): Latest model parameters
        aligner_time (str): Time of alignment

    """
    _, model_parameters = load_model_parameters()
    try:
        data, aligner_time = wait_for_data(number_of_samples, aligner, fs)
        try:
            PARAMS['expansion_modes']
            PARAMS['output_type']
            PARAMS['beam_elements']
            PARAMS['sensor_loc']
            disp, acc = displacement_estimation(data,PARAMS,model_parameters)
            return disp, acc, model_parameters, aligner_time
        except KeyError as e:
            shutdown(data_client, "Virtual sensing")
            print("PARAMS key error",e)
            return None, None, None, None
    except KeyboardInterrupt:
        shutdown(data_client, "Virtual sensing")
        print("Keyboard interrupt of virtual sensing\n")
        return None, None, None, None

def live_virtual_sensing(config_path: str) -> None:
    """
    Estimate displacement with virtual sensing 
    Args:
        config_path (str): Path to config file
    Returns:
        disp (np.ndarray): Estimated displacement at all DOF
        acc (np.ndarray): Filtered acceleration measurements at all DOF

    """
    aligner, data_client, mqtt_config, params = setup_aligner(config_path, config_name="virtual_sensing")
    try:
        while True:
            disp, _, _, _ = virtual_sensing(mqtt_config['SamplesToCollect'], aligner, data_client, params['Fs'])
            print("Estimated displacements/rotations")
            print("Max and min for every DOF. Max:",np.max(disp,axis=1).tolist(),"Min:",np.min(disp,axis=1).tolist())
    except KeyboardInterrupt as e:
        shutdown(data_client, "Virtual sensing")
        print("PARAMS key error",e)
    except RuntimeError:
        shutdown(data_client, "Virtual sensing")
        print("Keyboard interrupt ofvVirtual sensing\n")

def live_virtual_sensing_publish(config_path: str) -> None:
    """
    Estimate displacement with virtual sensing 
    Args:
        config_path (str): Path to config file
    Returns:
        disp (np.ndarray): Estimated displacement at all DOF
        acc (np.ndarray): Filtered acceleration measurements at all DOF

    """
    aligner, data_client, config, params = setup_aligner(config_path, config_name="virtual_sensing")
    try:
        while True:
            disp, _, model_parameters, timestamp = virtual_sensing(config['SamplesToCollect'], aligner, data_client, params['Fs'])
            data = {"data": disp,
                    "model_parameters": model_parameters}
            # data = {"model_parameters": model_parameters}
            publish_data(config, timestamp, data)
    except KeyboardInterrupt as e:
        shutdown(data_client, "Virtual sensing")
        print("PARAMS key error",e)
    except RuntimeError:
        shutdown(data_client, "Virtual sensing")
        print("Keyboard interrupt of virtual sensing\n")

def virtual_sensing_and_plot(config_path: str) -> None:
    """
    Estimate displacement with virtual sensing 
    Args:
        config_path (str): Path to config file
    Returns:
        disp (np.ndarray): Estimated displacement at all DOF
        acc (np.ndarray): Filtered acceleration measurements at all DOF
    Plots:

    """

    aligner, data_client, mqtt_config, params = setup_aligner(config_path)
    number_of_samples = mqtt_config['SamplesToCollect']
    disp, acc, _, __ = virtual_sensing(number_of_samples, aligner, data_client, params['Fs'])

    DOFs = [0, 5, 8, 11, 14, 17]
    _ = plot_virtual_sensing(disp,DOFs,fig_ax=None,title="Estimated displacements")
    _ = plot_virtual_sensing(acc,DOFs,fig_ax=None,title="Estimated accelerations")
    plt.show(block=True)
