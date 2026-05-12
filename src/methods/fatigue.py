from typing import Dict, Any, Optional, List
import numpy as np
from datetime import datetime
from data.comm.mqtt import (shutdown, load_config)
from methods.sysid import setup_aligner
from methods.stress_estimation import stress_estimation_for_beam
from methods.virtual_sensing import virtual_sensing
from methods.fatigue_functions.fatigue_calculation import fatigue_analysis
from methods.fatigue_functions.fatigue_plots import (plot_damage, plot_histogram, plot_sn_curve, plot_eol_rul, plot_cld)
from methods.constants import FATIGUE_DOF, DAMAGE_SUM
from methods.stress_estimation import subscribe_data

def fatigue_local(config_path: str, SN_curve: Dict[str,Any]) -> fatigue_analysis | None:
    """
    Apply a single fatigue calculation to estimated stress and estimated displacements.
    Args:
        config_path (str): path to config file
        SN_curve (Dict[str,Any]): Dictionary with SN curve parameters
    Returns:
        fatigue_object (fatigue object):

    """
    aligner, data_client, mqtt_config, fs = setup_aligner(config_path)
    fatigue_object = fatigue_analysis(SN_curve)
    try:
        displacement, _, model_parameters, __ = virtual_sensing(mqtt_config['SamplesToCollect'], aligner, data_client, fs)
        _, stress, __ = stress_estimation_for_beam(displacement,model_parameters)
        dof_stress = stress[FATIGUE_DOF[0],FATIGUE_DOF[1]]
        print(f"Stress shape:{dof_stress.shape}")
        fatigue_object.run(dof_stress)
        return fatigue_object
    except KeyboardInterrupt as e:
        shutdown(data_client, "fatigue analysis")
        raise RuntimeError("Keyboard interrupt") from e
    except RuntimeError as e:
        shutdown(data_client, "fatigue analysis")
        print("Runtime error",e)
        return None

def live_fatigue_local(config_path: str, SN_curve: Dict[str,Any]) -> fatigue_analysis | None:
    """
    Apply continuously fatigue calculation to estimated stress and estimated displacements.
    Args:
        config_path (str): path to config file
        SN_curve (Dict[str,Any]): Dictionary with SN curve parameters
    Returns:
        fatigue_object (fatigue object):

    """
    aligner, data_client, mqtt_config, fs = setup_aligner(config_path)
    fatigue_object = fatigue_analysis(SN_curve)
    fig_ax1 = None
    fig_ax2 = None
    fig_ax3 = None
    fig_ax4 = None
    fig_ax5 = None
    hist = None
    SN_data = None
    try:
        while True:
            displacement, _, model_parameters, aligner_time = virtual_sensing(mqtt_config['SamplesToCollect'], aligner, data_client, fs)
            _, stress, __ = stress_estimation_for_beam(displacement,model_parameters)
            dof_stress = stress[FATIGUE_DOF[0],FATIGUE_DOF[1]]
            print(f"Stress shape:{dof_stress.shape}")
            fatigue_object.run(dof_stress)
            fig_ax1 = plot_damage(fatigue_object.result,fig_ax=fig_ax1)
            fig_ax2, hist = plot_histogram(fatigue_object.result,fig_ax=fig_ax2,bin_width=0.25,hist_data=hist,static_mean=0)
            fig_ax3, SN_data = plot_sn_curve(SN_curve, fatigue_object.result, hist_data=SN_data, fig_ax=fig_ax3, bin_width=0.25, hist_type="stair")
            current_time = datetime.fromisoformat(aligner_time)
            if fig_ax4 is None:
                inital_time = current_time
            fig_ax4 = plot_eol_rul(fatigue_object.result, inital_time, current_time, output_time_unit = "hrs", damage_sum = DAMAGE_SUM, x_length = 50, fig_ax = fig_ax4)
            fig_ax5 = plot_cld(SN_curve,250,300,fatigue_object.result, fig_ax=fig_ax5)
    except KeyboardInterrupt as e:
        shutdown(data_client, "fatigue analysis")
        raise RuntimeError("Keyboard interrupt") from e
    except RuntimeError as e:
        shutdown(data_client, "fatigue analysis")
        print("Runtime error",e)

def live_fatigue_remote(config_path: str, SN_curve: Dict[str,Any]) -> fatigue_analysis | None:
    """
    Apply continuously fatigue calculation to estimated stress and estimated displacements.
    Args:
        config_path (str): path to config file
        SN_curve (Dict[str,Any]): Dictionary with SN curve parameters
    Returns:
        fatigue_object (fatigue object):

    """
    config = load_config(config_path)
    fatigue_object = fatigue_analysis(SN_curve)
    fig_ax1 = None
    fig_ax2 = None
    fig_ax3 = None
    fig_ax4 = None
    fig_ax5 = None
    hist = None
    SN_data = None
    try:
        while True:
            stresses, timestamp = subscribe_data(config['fatigue'])
            dof_stress = stresses[FATIGUE_DOF[0],FATIGUE_DOF[1]]
            print(f"Stress shape:{dof_stress.shape}")
            fatigue_object.run(dof_stress)
            fig_ax1 = plot_damage(fatigue_object.result,fig_ax=fig_ax1)
            fig_ax2, hist = plot_histogram(fatigue_object.result,fig_ax=fig_ax2,bin_width=0.25,hist_data=hist,static_mean=0)
            fig_ax3, SN_data = plot_sn_curve(SN_curve, fatigue_object.result, hist_data=SN_data, fig_ax=fig_ax3, bin_width=0.25, hist_type="stair")
            current_time = datetime.fromisoformat(timestamp)
            if fig_ax4 is None:
                inital_time = current_time
            fig_ax4 = plot_eol_rul(fatigue_object.result, inital_time, current_time, output_time_unit = "hrs", damage_sum = DAMAGE_SUM, x_length = 50, fig_ax = fig_ax4)
            fig_ax5 = plot_cld(SN_curve,250,300,fatigue_object.result, fig_ax=fig_ax5)
    except KeyboardInterrupt as e:
        raise RuntimeError("Keyboard interrupt") from e
    except RuntimeError as e:
        print("Runtime error",e)

def plot_rainflow_counting(config_path: str, SN_curve: Dict[str,Any]) -> fatigue_analysis | None:
    """
    Apply a single fatigue calculation to estimated stress and estimated displacements.
    Args:
        config_path (str): path to config file
        SN_curve (Dict[str,Any]): Dictionary with SN curve parameters
    Returns:
        fatigue_object (fatigue object):

    """
    aligner, data_client, mqtt_config, fs = setup_aligner(config_path)
    fatigue_object = fatigue_analysis(SN_curve)
    try:
        displacement, _, model_parameters, _ = virtual_sensing(mqtt_config['SamplesToCollect'], aligner, data_client, fs)
        _, stress, __ = stress_estimation_for_beam(displacement,model_parameters)
        dof_stress = stress[FATIGUE_DOF[0],FATIGUE_DOF[1]]
        print(f"Stress shape:{dof_stress.shape}")
        fatigue_object.run(dof_stress,plot_rainflow=True)
    except KeyboardInterrupt as e:
        shutdown(data_client, "fatigue analysis")
        raise RuntimeError("Keyboard interrupt") from e
    except RuntimeError as e:
        shutdown(data_client, "fatigue analysis")
        print("Runtime error",e)