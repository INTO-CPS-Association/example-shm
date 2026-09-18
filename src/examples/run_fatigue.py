from settings import SN_CURVE
from methods.fatigue import (fatigue_local,
                             live_fatigue_local,
                             live_fatigue_remote,
                             plot_rainflow_counting)

def run_fatigue_with_local_stress_estimation(config_path):
    fatigue_object = fatigue_local(config_path, SN_CURVE)
    print(f"Damage: {fatigue_object.result['D_t']}")

def run_live_fatigue_with_local_stress_estimation(config_path):
    live_fatigue_local(config_path, SN_CURVE)

def run_live_fatigue_with_remote_stress_estimation(config_path):
    print("Beware live-fatigue-with-remote-stress-estimation requires live-stress-estimation-subscribe-and-publish to run in parallel")
    live_fatigue_remote(config_path, SN_CURVE)

def run_plot_rainflow_counting(config_path):
    plot_rainflow_counting(config_path, SN_CURVE)
