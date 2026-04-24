import numpy as np
from methods.sysid import setup_sysid
from methods.virtual_sensing import virtual_sensing, live_virtual_sensing, virtual_sensing_and_plot

def run_virtual_sensing(config_path):
    number_of_minutes = 0.2
    aligner, data_client, _, fs = setup_sysid(config_path)
    displacement, _ = virtual_sensing(number_of_minutes, aligner, data_client, fs)
    print("Estimated displacements/rotations")
    print("Max and min for every DOF. Max:",np.max(displacement,axis=1).tolist(),"Min:",np.min(displacement,axis=1).tolist())

def run_live_virtual_sensing(config_path):
    number_of_minutes = 0.2
    live_virtual_sensing(config_path, number_of_minutes)

def run_plot_virtual_sensing(config_path):
    number_of_minutes = 0.2
    virtual_sensing_and_plot(config_path, number_of_minutes)