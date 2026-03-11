from typing import Dict, Any, Optional, List
from collections.abc import Callable
import numpy as np
from scipy.optimize import minimize
from methods.model_update_functions.mode_pairing import pair_modes
# pylint: disable=C0103

def update_model(cluster_dict: Dict[str,Any], model_func: Callable[[Dict[str,Any]],Any], model_pars: Dict[str,Any],
                 pars_to_update: List[str], params: Dict[str,Any]) -> Optional[Any]:
    """
    Estimate updated model parameters

    Args:
        cluster_dict (Dict[str,Any]): Dictionary of clustered modes
        model_func (Callable[[Dict[str,Any]],Any]): YAFEM model function
        model_parameters (Dict[str,Any]): Model parameters (YaFEM)
        parameters_to_update (List[str]): String of keys to update in model_parameters
        params (Dict[str,Any]): Update parameters

    Returns:
        X (np.ndarray[float]): Updated values
        omegaMU (np.ndarray[float]): Eigenfrequencies in Hertz of the updated model
        updated_model_parameters (Dict[str,Any]): Updated model parameters

    """
    X = None
    pars_to_update = params['pars_to_update']
    try:
        res = minimize(lambda x: estimate_parameters(x, cluster_dict, model_func, model_pars,
                                                     pars_to_update, params),
                       params['MU_start_values'], bounds=params['MU_bounds'],
                       options={'maxiter': 1000})
        # Get the optimized parameter values
        X = res.x

        # Updated model parameter
        idx = 0
        for key in model_pars:
            if str(key) in pars_to_update:
                model_pars[key] = X[idx]
                idx += 1
        updated_model_parameters = model_pars
        omegaMU, _, __, ___, ____ = model_func(updated_model_parameters)

    except ValueError as e:
        print(f"Skipping model updating due to error: {e}")

    if X is not None:
        print("Updated parameters are:")
        for ii, name in enumerate(params['pars_to_update']):
            print(name+":",X[ii])
        return X, omegaMU, updated_model_parameters
    return None, None, None

def estimate_parameters(theta_star: List[float], cluster_dict: Dict[str,Any],
                        model_func: Callable[[Dict[str,Any]],Any], model_parameters: Dict[str,Any],
                        parameters_to_update: List[str],params: Dict[str,Any]) -> float:
    """
    Estimate updated parameters and return the objective function result

    Args:
        theta_star (np.ndarray[float]): The parameters to update
        cluster_dict (Dict[str,Any]): Dictionary of clustered modes
        model_func (Callable[[Dict[str,Any]],Any]): YAFEM model function
        model_parameters (Dict[str,Any]): Model parameters (YaFEM)
        parameters_to_update (List[str]): String of keys to update in model_parameters
        params (Dict[str,Any]): Update parameters

    Returns:
        X (float): Resulting value from objective function

    Raises:
    ValueError:
        The number of updating parameters more than than the number of features. 
        One should re-try after reducing the number of updating parameters 

    """
    idx = 0
    for key in model_parameters:
        if str(key) in parameters_to_update:
            model_parameters[key] = theta_star[idx]
            idx += 1
    # Call FE solver to get model frequencies and mode shapes
    omegaM, _, PhiM, __, ___ = model_func(model_parameters)

    # Mode Pairing Start
    (paired_frequencies, paired_mode_shapes, omegaM, PhiM
     ) = pair_modes(omegaM, PhiM, cluster_dict, params)
    omegaM = omegaM.reshape(paired_frequencies.shape)

    # Error message if the number of updating parameters
    # are more than double of the paired frequencies
    if len(theta_star) > 2 * len(paired_frequencies):
        raise ValueError("The problem becomes undetermined." \
        " The number of updated parameters should not be more than the number of features")

    # Compute MAC
    MACn = np.abs(np.diag(np.conj(paired_mode_shapes).T @ PhiM))**2 #Nominator
    MACd = np.diag(np.conj(paired_mode_shapes).T @
                   paired_mode_shapes) * np.diag(np.conj(PhiM).T @ PhiM) #Denominator
    MAC = MACn / MACd

    # Objective function
    resOM = (omegaM - paired_frequencies)/omegaM #Frequency desqrepancy
    resPhi = MAC
    X = np.dot(resOM.T, resOM) + 1 / np.dot(resPhi.T, resPhi)

    return np.real(X)
