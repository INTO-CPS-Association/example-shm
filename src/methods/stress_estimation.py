from typing import Any, Dict
import threading
import numpy as np
from data.comm.mqtt import (shutdown)
from methods.sysid import setup_aligner
from methods.model_update import load_model_parameters
from methods.stress_estimation_functions.stress_estimation_func import estimate_stress_beam
from methods.stress_estimation_functions.plot_stress import plot_stress
from methods.virtual_sensing import virtual_sensing
from methods.mode_clustering import publish_data
from methods.model_update import subscribe_data
from methods.constants import (MODEL_FUNC, PARAMS)
# pylint: disable=C0103, C0301, W0104

result_ready = threading.Event()
data_global = None  # will store received cluster data inside callback
timestamp_global = None

def stress_estimation_for_beam(displacement: np.ndarray[float],
                        model_parameters: Dict[str,Any] = None
                        ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Estimate stress based on displacements and YAFEM model
    Args:
        displacement (np.ndarray): Array of displacements/rotations (DOF x N)
    Returns:
        Moment (np.ndarray): Array of moment/forces (elements x s)
        stress (np.ndarray): Array of stress (elements x s) [MPa] (s = 3 in the case of a 2D beam: axial, curvature/bending at 1. node (bottom), curvature/bending at 2. node (top))
        strain (np.ndarray): Array of strain (elements x s)
    """
    if model_parameters is None:
        _, model_parameters = load_model_parameters()
    model_parameters["dofs_sel"] = PARAMS["dofs_extract"].copy()
    _, __, __, Model, ____ = MODEL_FUNC(model_parameters)
    try:
        PARAMS['element_type']
        PARAMS['elements']
        PARAMS['y']
        PARAMS["dofs_extract"]
        moment, stress, strain = estimate_stress_beam(Model,displacement,PARAMS)
        return moment, stress, strain
    except KeyError as e:
        print("Missing PARAMS key",e)
        return None, None, None


def live_stress_estimation_subscribe_and_publish(config_path: str) -> None:
    """
    Estimate stress based on displacements and YAFEM model and publish
    Args:
        config_path (str): Path to config file
    Returns:
    """
    _, data_client, config, __ = setup_aligner(config_path, config_name="stress")

    try:
        while True:
            data_dict, timestamp = subscribe_data(config)
            data = data_dict['data']
            model_parameters = data_dict['model_parameters']
            _, stress, __ = stress_estimation_for_beam(data,model_parameters)
            publish_data(config, timestamp, stress)
    except KeyboardInterrupt as e:
        shutdown(data_client, "stress estimation")
        raise RuntimeError("Keyboard interrupt") from e
    except RuntimeError as e:
        shutdown(data_client, "stress estimation")
        print("Runtime error",e)

def live_stress_estimation_for_beam(config_path: str) -> None:
    """
    Estimate stress based on displacements and YAFEM model
    Args:
        config_path (str): Path to config file
    Returns:
    """
    aligner, data_client, mqtt_config, fs = setup_aligner(config_path)

    try:
        while True:
            displacement, _, model_parameters, __ = virtual_sensing(mqtt_config['SamplesToCollect'],
                                                                    aligner, data_client, fs)
            _, stress, __ = stress_estimation_for_beam(displacement,model_parameters)
            print("Max bending stress at all DOFs [MPa]")
            print(np.max(stress[:,1]).tolist())
            print("Min. bending stress at all DOFs [MPa]")
            print(np.min(stress[:,1]).tolist())
    except KeyboardInterrupt as e:
        shutdown(data_client, "stress estimation")
        raise RuntimeError("Keyboard interrupt") from e
    except RuntimeError as e:
        shutdown(data_client, "stress estimation")
        print("Runtime error",e)

def stress_estimation_and_plot(stress: np.ndarray[float]) -> None:
    """
    Estimate stress based on displacements and YAFEM model
    Args:
        stress (np.ndarray): Array of stress/forces (DOF x s x N)
    Returns:
    """
    elements = [0, 1, 2, 3, 4, 5, 6]
    _ = plot_stress(stress,elements,2,fig_ax=None,title="Bending moment [MPa]")
