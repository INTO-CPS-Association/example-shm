import numpy as np
from methods.sysid import setup_aligner
from methods.virtual_sensing import (virtual_sensing,
                                     live_virtual_sensing,
                                     virtual_sensing_and_plot,
                                     live_virtual_sensing_publish)

def run_virtual_sensing(config_path):
    aligner, data_client, mqtt_config, fs = setup_aligner(config_path)
    number_of_samples = mqtt_config['SamplesToCollect']
    displacement, _, __, ___ = virtual_sensing(number_of_samples, aligner, data_client, fs)
    print("Estimated displacements/rotations")
    print("Max and min for every DOF. Max:",np.max(displacement,axis=1).tolist(),"Min:",np.min(displacement,axis=1).tolist())

def run_live_virtual_sensing(config_path):
    live_virtual_sensing(config_path)

def run_live_virtual_sensing_and_publish(config_path):
    live_virtual_sensing_publish(config_path)

def run_plot_virtual_sensing(config_path):
    virtual_sensing_and_plot(config_path)