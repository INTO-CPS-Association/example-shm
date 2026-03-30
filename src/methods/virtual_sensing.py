import numpy as np
from methods.model_update import load_model_parameters
from methods.sysid import setup_sysid
from examples.aligning_readings import wait_for_data
from methods.virtual_sensing_functions.virtual_sensing_func import displacement_estimation
from methods.virtual_sensing_functions.plot_virtual_sensing import plot_virtual_sensing

from methods.constants import (PARAMS)

def virtual_sensing(config_path, number_of_minutes, plot: list[bool] = [0,0,0,0,0]):
    """
    Estimate displacement with virtual sensing 
    Args:
        config_path (str): Path to config file
        plot (list[bool]): List of bools to determine what to plot
    Returns:
        disp (np.ndarray): Estimated displacement at all DOF
        acc (np.ndarray): Filtered acceleration measurements at all DOF
    Plots:

    """
    _, model_parameters = load_model_parameters()

    aligner, data_client, mqtt_config, fs = setup_sysid(config_path)
    data, aligner_time = wait_for_data(number_of_minutes, aligner, fs)
    disp, acc = displacement_estimation(data,PARAMS,model_parameters)
    
    print("Shape virtual displacements",disp.shape)

    plot_virtual_sensing(plot, disp, acc, data)

    return disp, acc