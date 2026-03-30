from typing import Any, Dict
import numpy as np

from methods.constants import (MODEL_FUNC)
from functions.data_filtering import filter
from methods.virtual_sensing_functions.integration import frequency_based_integration

def displacement_estimation(data: np.ndarray[float], params: Dict[str,Any], model_pars: Dict[str,Any]) -> np.ndarray[float]:
    """
        Apply modal expansion to estimate data at all DOFs.

        Args:
            data (np.ndarray[float]): Measured data
            params (Dict[str,Any]): Parameters for the virtual sensing function
            model_pars (Dict[str,Any]): Model parameters (YaFEM)

        Returns:
            d_hat (np.ndarray[float]): Estimated displacements at all DOFs

    """
    # Experimental data transformation
    y = data
    ms, N = y.shape #Reshape y if it is transposed
    if N < ms:
        y = y.T
        ms, N = y.shape
    if N % 2 == 0: # Needed because of frequency integration?
        N -= 1
        y = y[:, :N]

    y = filter(y,params) #Apply filter

    #Integration:
    disp = frequency_based_integration(y,params,order=params.get('detrend_integration_order',1))
    
    # Find non-measured DOF
    model_pars['modes'] = params['expansion_modes'] #Number of model modes g must be <= to n_m
    model_pars['dofs_sel'] = params['sensor_loc']
    _, __, __, myModel, ____ = MODEL_FUNC(model_pars)
    model_pars['dofs_sel'] = myModel.dofs
    _, __, Phi_selected, myModel2, ___ = MODEL_FUNC(model_pars)
    non_measured_loc, id_no_sensors, id_sensors = find_unique_dofs(myModel2.dofs,params['sensor_loc'])

    #Estimate displacements based on all sensors, even the validation sensor
    Phi_alpha_S = Phi_selected[id_sensors,:] #Mode shapes of the measuremed locations
    Phi_beta_S = Phi_selected[id_no_sensors,:] #Mode shapes of the unmeasuremed locations
    
    # Estimate displacements with modal expansion
    d_alpha = disp
    q_hat = np.linalg.pinv(Phi_alpha_S) @ d_alpha #Find modal coordinates of measured points
    d_beta = Phi_beta_S @ q_hat
    d_hat = np.zeros((myModel2.ndof,N))
    for idx, loc in enumerate(id_sensors):
            d_hat[loc,:] = d_alpha[idx,:]
    for idx, loc in enumerate(id_no_sensors):
            d_hat[loc,:] = d_beta[idx,:]

    # Estimate displacements with modal expansion
    a_alpha = y
    q_hat = np.linalg.pinv(Phi_alpha_S) @ a_alpha #Find modal coordinates of measured points
    a_beta = Phi_beta_S @ q_hat
    a_hat = np.zeros((myModel2.ndof,N))
    for idx, loc in enumerate(id_sensors):
            a_hat[loc,:] = a_alpha[idx,:]
    for idx, loc in enumerate(id_no_sensors):
            a_hat[loc,:] = a_beta[idx,:]

    return d_hat, a_hat

def find_unique_dofs(a: np.ndarray[int], b: np.ndarray[int]) -> tuple[np.ndarray[int], list[int], list[int]]:
    """
    Find the unique DOFs in a that are not in b, and return their indices.
    Args:
        a (np.ndarray[int]): Array of indecies of DOFs for the model
        b (np.ndarray[int]): Array of indecies of DOFs for the sensors
    Returns:
        unqiue_DOF (np.ndarray[int]): Array of indecies of unique DOFs in a that are not in b
        unique_ids (list[int]): List of indices of unique DOFs in a
        non_unique_ids (list[int]): List of indices of DOFs in a that are also in b

    """
    # remove dof from array
    unqiue_DOF = []
    unique_ids = []
    for id, dof in enumerate(a): #Go through the DOFs of a
        add_dof = True
        for dof2 in b: #Go through the DOFs of b
            if np.array_equal(dof,dof2): #If DOF_a is equa to DOF_b
                add_dof = False #Do not add DOF to list of unique DOF
        if add_dof == True: #Add DOF to unique list
            unqiue_DOF.append(dof)
            unique_ids.append(id)
    unqiue_DOF = np.array(unqiue_DOF)

    #Find the non unqiue indices
    non_unique_ids = []
    for ii, dof2 in enumerate(b):
        for jj, dof in enumerate(a):
            if np.array_equal(dof,dof2):
                non_unique_ids.append(jj)



    return unqiue_DOF, unique_ids, non_unique_ids