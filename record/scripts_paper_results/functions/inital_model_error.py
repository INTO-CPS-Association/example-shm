import numpy as np
import pickle as pk
import os
import matplotlib.pyplot as plt
from functions.model_update import (par_est,pair_calculate)
from functions import fun_cantilever_beam_new as beam_new


def calculate_inital_model_error(updated_parameters,cluster_dict,Params):
    dirname = os.path.dirname(__file__)

    pars_before={'modes': Params['MU_initial_modes'],
            'dofs_sel': Params['sensor_loc'],
            'k_rot': Params['MU_initial_start_values'][0], 
            'l4': Params['MU_initial_start_values'][1],
            'm': 0,
            }
    
    omegaM, phi, PhiM, myModel, _ = beam_new.eval_yafem_model(pars_before)
    paired_frequencies_1, paired_mode_shapes_1, omegaM_1, PhiM_1 = pair_calculate(omegaM, PhiM, cluster_dict, Params)

    pars_after = {'modes': Params['MU_initial_modes'],
                  'dofs_sel': Params['sensor_loc'],
                  'k_rot': updated_parameters[0],
                  'l4': updated_parameters[1],
                  'm': 0
                }
    omegaM, phi, PhiM, myModel, _ = beam_new.eval_yafem_model(pars_after)
    paired_frequencies_2, paired_mode_shapes_2, omegaM_2, PhiM_2 = pair_calculate(omegaM, PhiM, cluster_dict, Params)

    freq_error_before = 100 * np.abs(omegaM_1 - paired_frequencies_1) / paired_frequencies_1
    freq_error_after = 100 * np.abs(omegaM_2 - paired_frequencies_2) / paired_frequencies_2

    # Compute MAC_1
    MACn = np.abs(np.diag(np.conj(paired_mode_shapes_1).T @ PhiM_1))**2
    MACd = np.diag(np.conj(paired_mode_shapes_1).T @ paired_mode_shapes_1) * np.diag(np.conj(PhiM_1).T @ PhiM_1)
    MAC_1 = MACn / MACd

    # Compute MAC_2
    MACn = np.abs(np.diag(np.conj(paired_mode_shapes_2).T @ PhiM_2))**2
    MACd = np.diag(np.conj(paired_mode_shapes_2).T @ paired_mode_shapes_2) * np.diag(np.conj(PhiM_2).T @ PhiM_2)
    MAC_2 = MACn / MACd

    initial_model_update_results = (freq_error_before,freq_error_after,MAC_1,MAC_2)

    filename = os.path.join(Params['path'], 'data/initial_model_update_comparisson.pkl')
    with open(filename, "wb") as f:
        pk.dump(initial_model_update_results, f)