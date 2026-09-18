import numpy as np
from methods.sysid import setup_aligner
from methods.virtual_sensing import virtual_sensing
from methods.stress_estimation import (stress_estimation_for_beam,
                                       live_stress_estimation_for_beam,
                                       live_stress_estimation_subscribe_and_publish,
                                       stress_estimation_and_plot)
from settings import PARAMS

def run_stress_and_strain_estimation_beam(config_path):
    aligner, data_client, sysid_config, params = setup_aligner(config_path)
    number_of_samples = sysid_config['SamplesToCollect']
    displacement, _, __, ___ = virtual_sensing(number_of_samples, aligner, data_client, params['Fs'])
    _, stress, __ = stress_estimation_for_beam(displacement)
    print("Max bending stress at all DOFs [MPa]")
    print(np.max(stress[:,1]).tolist())
    print("Min. bending stress at all DOFs [MPa]")
    print(np.min(stress[:,1]).tolist())

def run_live_stress_and_strain_estimation_beam(config_path):
    live_stress_estimation_for_beam(config_path)

def run_live_stress_estimation_subscribe_and_publish(config_path):
    print("Beware live-stress-estimation-subscribe-and-publish requires live-virtual-sensing-and-publish to run in parallel")
    live_stress_estimation_subscribe_and_publish(config_path)

def run_stress_estimation_and_plot(config_path):
    aligner, data_client, sysid_config, params = setup_aligner(config_path)
    number_of_samples = sysid_config['SamplesToCollect']
    displacement, _, model_parameters, __ = virtual_sensing(number_of_samples,
                                                            aligner, data_client, params['Fs'])
    stress, _, __ = stress_estimation_for_beam(displacement,model_parameters)
    stress_estimation_and_plot(stress)
