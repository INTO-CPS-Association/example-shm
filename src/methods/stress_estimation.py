import numpy as np
from data.comm.mqtt import shutdown
from methods.sysid import setup_sysid
from methods.model_update import load_model_parameters
from methods.stress_estimation_functions.stress_estimation_func import estimate_stress_beam
from methods.stress_estimation_functions.plot_stress import plot_stress
from methods.virtual_sensing import virtual_sensing
from methods.constants import (MODEL_FUNC, PARAMS)


def stress_estimation_for_beam(displacement: np.ndarray[float]):
    """
    Estimate stress based on displacements and YAFEM model
    Args:
        displacement (np.ndarray): Array of displacements/rotations (DOF x N)
    Returns:
        stress (np.ndarray): Array of stress (elements x s) [MPa] (s = 3 in the case of a 2D beam: axial, curvature/bending at 1. node (bottom), curvature/bending at 2. node (top))
        strain (np.ndarray): Array of strain (elements x s)
    """
    _, model_parameters = load_model_parameters()
    model_parameters["dofs_sel"] = PARAMS["dofs_extract"].copy()
    _, __, __, Model, ____ = MODEL_FUNC(model_parameters)
    try:
        PARAMS['element_type']
        PARAMS['elements']
        PARAMS['y']
        PARAMS["dofs_extract"]
        moment, stress, strain = estimate_stress_beam(Model,displacement,PARAMS)
    except KeyError as e:
        print("Missing PARAMS key",e)

    return stress, strain

def live_stress_estimation_for_beam(config_path: str, number_of_minutes: float):
    """
    Estimate stress based on displacements and YAFEM model
    Args:
        displacement (np.ndarray): Array of displacements/rotations (DOF x N)
    Returns:
        stress (np.ndarray): Array of stress (elements x s) [MPa] (s = 3 in the case of a 2D beam: axial, curvature/bending at 1. node (bottom), curvature/bending at 2. node (top))
        strain (np.ndarray): Array of strain (elements x s)
    """
    aligner, data_client, _, fs = setup_sysid(config_path)

    _, model_parameters = load_model_parameters()
    model_parameters["dofs_sel"] = PARAMS["dofs_extract"].copy()
    _, __, __, Model, ____ = MODEL_FUNC(model_parameters)
    
    try:
        PARAMS['element_type']
        PARAMS['elements']
        PARAMS['y']
        PARAMS["dofs_extract"]
        while True:
            displacement, accreleration = virtual_sensing(number_of_minutes, aligner, data_client, fs)
            moment, stress, strain = estimate_stress_beam(Model,displacement,PARAMS)
            print("Max bending stress at all DOFs [MPa]")
            print(np.max(stress[:,1]).tolist())
            print("Min. bending stress at all DOFs [MPa]")
            print(np.min(stress[:,1]).tolist())
    except KeyboardInterrupt as e:
        shutdown(data_client, "Virtual sensing")
        raise RuntimeError("Keyboard interrupt") from e
    except KeyError as e:
        shutdown(data_client, "Virtual sensing")
        print("Missing PARAMS key",e)

    return stress, strain

def stress_estimation_and_plot(stress: np.ndarray[float]):
    """
    Estimate stress based on displacements and YAFEM model
    Args:
        stress (np.ndarray): Array of stress/forces (DOF x s x N)
    Returns:
    """
    elements = [0, 1, 2, 3, 4, 5, 6]
    fig_ax = plot_stress(stress,elements,2,fig_ax=None,title="Bending moment [MPa]")
