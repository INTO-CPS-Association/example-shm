"This file is taken from the DTaaS-platform"
import numpy as np
import sys
import os
from methods.packages import fun_cantilever_beam_new as beam_new
import json
from methods.packages.mode_pairs import pair_calculate


def par_est(x, comb):
    """
    

    Parameters
    ----------
    x : numpy array
        The parameters to update
    comb : Dictionary
        Results from mode tracking

    Raises
    ------
    ValueError
        The number of updating parameters more than than the number of features. 
        One should re-try after reducing the number of updating parameters 

    Returns
    -------
    TYPE
        Optimized value message

    """
    # Cluster from mode tracking 
    cleaned_clusters = comb['cluster']
    # median frequencies of each clusters
    median_frequencies = np.array([cluster["median"] for cluster in cleaned_clusters])
    
    # Estimate the frequency range to make pairing with finite element model
    frequency_range = [0.2*min(median_frequencies), 5.0*max(median_frequencies)]
    # print(f'frequency range: {frequency_range}')
     
    pars={'modes': 9,
      'dofs_sel': np.array([[5,1],[4,1]]),
      'k': x[0], 
      'Lab': x[1],
     }
    # print(f'parameters: {x}')
    
    # Call FE solver to get model frequencies and mode shapes
    omegaM, phi, PhiM, myModel = beam_new.eval_yafem_model(pars)
     # Compute the index which fall within the frequency bounds
    interested_frequency_index = np.where((omegaM >= frequency_range[0]) & (omegaM[:, None] <= frequency_range[1]).any(axis=1))[0]
    # print(f'interested frequency index: {interested_frequency_index}')
    # Interested frequencies and mode shapes from the finite elelment model
    omegaM = omegaM[interested_frequency_index]
    PhiM = PhiM[:, interested_frequency_index]
    # print(f'YaFEM fn: {omegaM}')
    # print(f'YaFEM phi: {PhiM}')
    
    # Mode Pairing Start 
    paired_frequencies, paired_mode_shapes, omegaM, PhiM = pair_calculate(omegaM, PhiM, cleaned_clusters, median_frequencies)
    
    # print(f'x: {len(x)}')
    # print(f'2 * paired frequency length: {2 * len(paired_frequencies)}')
    # Error message if the number of updating parameters is more than double of the paired frequencies
    if len(x) > 2 * len(paired_frequencies):
        raise ValueError("The problem becomes undetermined. The number of updated parameters should not be more than the number of features")
    
    # Compute MAC
    MACn = np.abs(np.diag(np.conj(paired_mode_shapes).T @ PhiM))**2
    MACd = np.diag(np.conj(paired_mode_shapes).T @ paired_mode_shapes) * np.diag(np.conj(PhiM).T @ PhiM)
    MAC = MACn / MACd
    
    # Objective function
    resOM = (omegaM - paired_frequencies)/omegaM
    resPhi = MAC
    # print(f'MAC: {MAC}')
    # print(f'X 1st part: {np.dot(resOM.T, resOM)}')
    # print(f'X 2nd part: {np.dot(resPhi.T, resPhi)}')
    X = np.dot(resOM.T, resOM) + 1 / np.dot(resPhi.T, resPhi)
    
    # # Display Results
    # print(f'omegaM: {omegaM}')
    print(f'paired frequencies: {paired_frequencies}')
    # print(f'resOM: {resOM}')
    # print(f'resPhi: {resPhi}')
    # print(f'X: {np.real(X)}')
   
    return np.real(X)


