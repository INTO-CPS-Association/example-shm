import numpy as np
from methods.model_update import load_model_parameters
from methods.stress_estimation_functions.stress_estimation_func import estimate_stress_beam
from methods.constants import (MODEL_FUNC, STRESS_EXTRACTION)


def stress_estimation_for_beam(displacement):
    """
    Estimate stress based on displacements and YAFEM model
    Args:
        displacement (np.ndarray): Array of displacements/rotations (DOF x N)
    Returns:
        stress (np.ndarray): Array of stress (elements x s) [MPa] (s = 3 in the case of a 2D beam: axial, curvature/bending at 1. node (bottom), curvature/bending at 2. node (top))
        strain (np.ndarray): Array of strain (elements x s)
    """
    _, model_parameters = load_model_parameters()
    model_parameters["dofs_sel"] = STRESS_EXTRACTION["dofs_sel"]
    _, __, __, Model, ____ = MODEL_FUNC(model_parameters)
    moment, stress, strain = estimate_stress_beam(Model,displacement,STRESS_EXTRACTION)

    return stress, strain