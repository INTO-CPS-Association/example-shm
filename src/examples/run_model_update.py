from data.comm.mqtt import load_config
from methods import mode_clustering as MC
from methods import model_update as MU
from settings import PARAMS, MODEL_PARAMETERS
# pylint: disable=R0914, C0103

def run_model_update_local_sysid(config_path):
    _, clusters, _ = MC.cluster_from_local_sysid(config_path, PARAMS)

    # Run model update
    _, omega_model, model_parameters = MU.estimate_updated_model(clusters,MODEL_PARAMETERS,PARAMS)
    if omega_model is not None:
        _ = MU.model_update_plots([1,1], model_parameters, PARAMS['pars_to_update'],
                                omega_model,
                                fig_axes=[None,None], hold=True)

def run_model_update_remote_sysid(config_path):
    print("Beware live-model-update-with-remote-sysid requires live-sysid-publish to run in parallel")
    config = load_config(config_path)
    MU.live_model_update_with_remote_sysid(config,PARAMS,publish=False)

def run_model_update_remote_sysid_and_publish(config_path):
    print("Beware live-model-update-remote-sysid-and-publish requires live-sysid-publish to run in parallel")
    config = load_config(config_path)
    MU.live_model_update_with_remote_sysid(config,PARAMS,publish=True)

def run_live_model_update_remote_clustering(config_path):
    print("Beware live-model-update-remote-clustering requires live-clustering-with-remote-sysid-and-publish to run in parallel")
    config = load_config(config_path)
    MU.live_model_update_with_remote_clustering(config,PARAMS,publish=False)
