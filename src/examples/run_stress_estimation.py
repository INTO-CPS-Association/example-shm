import numpy as np
from methods.sysid import setup_sysid
from methods.virtual_sensing import virtual_sensing
from methods.stress_estimation import (stress_estimation_for_beam,
                                       live_stress_estimation_for_beam,
                                       stress_estimation_and_plot)

def run_stress_and_strain_estimation_beam(config_path):
    number_of_minutes = 0.2
    aligner, data_client, _, fs = setup_sysid(config_path)
    displacement, _ = virtual_sensing(number_of_minutes, aligner, data_client, fs)
    stress, strain = stress_estimation_for_beam(displacement)
    print("Max bending stress at all DOFs [MPa]")
    print(np.max(stress[:,1]).tolist())
    print("Min. bending stress at all DOFs [MPa]")
    print(np.min(stress[:,1]).tolist())

def run_live_stress_and_strain_estimation_beam(config_path):
    number_of_minutes = 0.5
    live_stress_estimation_for_beam(config_path, number_of_minutes)

def run_stress_estimation_and_plot(config_path):
    number_of_minutes = 0.2
    displacement, _ = virtual_sensing(config_path, number_of_minutes)
    stress, strain = stress_estimation_for_beam(displacement)
    stress_estimation_and_plot(stress)
