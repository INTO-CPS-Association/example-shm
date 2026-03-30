from typing import Any
import numpy as np
from yafem import model

def estimate_stress_beam(Model: model, displacement : np.ndarray, extraction_dict: dict[str,Any]):
    """
    Args:
        Model (yafem.model): Yafem model
        displacement (np.ndarray): Array of displacement (DOF x N)
        extraction_dict (Dict[str,Any]): Dictionary of stress/strain extraction parameters
    Returns:
        moment (np.ndarray): Array of bending moment/ force [Nm or N]
        stress (np.ndarray): Array of stress (elements x s) [MPa] (s = 3 in the case of a 2D beam: axial, curvature/bending at 1. node (bottom), curvature/bending at 2. node (top))
        strain (np.ndarray): Array of strain (elements x s)
    """
    N = np.max(displacement.shape)
    
    s = Model.my_elements[extraction_dict['elements'][0]].s_phi.shape[0]
    stress = np.zeros((len(extraction_dict['elements']),s,N)) # s x m
    strain = np.zeros((len(extraction_dict['elements']),s,N)) # s x m
    moment = np.zeros((len(extraction_dict['elements']),s,N)) # s x m

    for idx, element in enumerate(extraction_dict['elements']):
        I = Model.my_elements[element].I
        moment[idx,:] = (Model.my_elements[element].s_phi @ displacement) # [Nm]
        stress[idx,:] = (Model.my_elements[element].s_phi @ displacement) * - extraction_dict['y'][idx] / I / 10**6 # [MPa]
        strain[idx,:] = (Model.my_elements[element].e_phi @ displacement)
    
    return moment, stress, strain