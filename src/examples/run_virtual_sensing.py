import numpy as np
from methods.virtual_sensing import virtual_sensing

def run_virtual_sensing(config_path):
    number_of_minutes = 0.2
    disp, acc = virtual_sensing(config_path, number_of_minutes, plot=[0,0,0,0,0])
    print("Estimated displacements/rotations")
    print("Max and min for every DOF. Max:",np.max(disp,axis=1).tolist(),"Min:",np.min(disp,axis=1).tolist())