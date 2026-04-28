import numpy as np
import matplotlib.pyplot as plt
from data.comm.mqtt import shutdown
from methods.sysid import setup_sysid
from methods.model_update import load_model_parameters
from examples.aligning_readings import wait_for_data
from methods.virtual_sensing_functions.virtual_sensing_func import displacement_estimation
from methods.virtual_sensing_functions.plot_virtual_sensing import plot_virtual_sensing
from methods.constants import PARAMS

def live_virtual_sensing(config_path):
    """
    Estimate displacement with virtual sensing 
    Args:
        config_path (str): Path to config file
    Returns:
        disp (np.ndarray): Estimated displacement at all DOF
        acc (np.ndarray): Filtered acceleration measurements at all DOF

    """
    aligner, data_client, mqtt_config, fs = setup_sysid(config_path)
    try:
        while True:
            disp, acc = virtual_sensing(mqtt_config['TimeToSample'], aligner, data_client, fs)
            print("Estimated displacements/rotations")
            print("Max and min for every DOF. Max:",np.max(disp,axis=1).tolist(),"Min:",np.min(disp,axis=1).tolist())
    except KeyboardInterrupt as e:
        shutdown(data_client, "Virtual sensing")
        print("PARAMS key error",e)
    except RuntimeError as e:
        shutdown(data_client, "Virtual sensing")
        print("Keyboard interrupt of live mode tracking\n")

def virtual_sensing(number_of_minutes, aligner, data_client, fs):
    """
    Continuously estimate displacement with virtual sensing
    Args:
        number_of_minutes (float): Number og minutes to sample data
        aligner: Aligner
        fs (float): Sample frequency

    """
    _, model_parameters = load_model_parameters()

    try:
        data, aligner_time = wait_for_data(number_of_minutes, aligner, fs)
        try:
            PARAMS['expansion_modes']
            PARAMS['output_type']
            PARAMS['beam_elements']
            PARAMS['sensor_loc']
            disp, acc = displacement_estimation(data,PARAMS,model_parameters)
            return disp, acc
        except KeyError as e:
            shutdown(data_client, "Virtual sensing")
            print("PARAMS key error",e)
    except KeyboardInterrupt as e:
        shutdown(data_client, "Virtual sensing")
        print("Keyboard interrupt of live mode tracking\n")

def virtual_sensing_and_plot(config_path):
    """
    Estimate displacement with virtual sensing 
    Args:
        config_path (str): Path to config file
    Returns:
        disp (np.ndarray): Estimated displacement at all DOF
        acc (np.ndarray): Filtered acceleration measurements at all DOF
    Plots:

    """

    aligner, data_client, mqtt_config, fs = setup_sysid(config_path)
    number_of_minutes = mqtt_config['TimeToSample']
    disp, acc = virtual_sensing(number_of_minutes, aligner, data_client, fs)


    DOFs = [0, 5, 8, 11, 14, 17]
    fig_ax1 = plot_virtual_sensing(disp,DOFs,fig_ax=None,title="Estimated displacements")
    fig_ax2 = plot_virtual_sensing(acc,DOFs,fig_ax=None,title="Estimated accelerations")
    plt.show(block=True)