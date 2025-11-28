from data.comm.mqtt import load_config
from methods import mode_clustering as MC
from methods import model_update as MU
from methods.constants import PARAMS, MODEL_PARAMETERS
# pylint: disable=R0914, C0103

def run_model_update_local_sysid(config_path):
    number_of_minutes = 0.2

    _, clusters, _ = MC.cluster_from_local_sysid(config_path, number_of_minutes, PARAMS)

    # Run model update
    _, omega_model, model_parameters = MU.estimate_updated_model(clusters,MODEL_PARAMETERS,PARAMS)
    _ = MU.model_update_plots([1,1], model_parameters, PARAMS['pars_to_update'],
                              omega_model,
                              fig_axes=[None,None], hold=True)

def run_model_update_remote_sysid(config_path):
    config = load_config(config_path)
    MU.live_model_update_with_remote_sysid(config,PARAMS,publish=False)

def run_model_update_remote_sysid_and_publish(config_path):
    config = load_config(config_path)
    MU.live_model_update_with_remote_sysid(config,PARAMS,publish=True)

def run_live_model_update_remote_clustering(config_path):
    config = load_config(config_path)
    MU.live_model_update_with_remote_clustering(config,PARAMS,publish=False)
