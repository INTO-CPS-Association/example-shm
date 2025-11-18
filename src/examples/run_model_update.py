from data.comm.mqtt import load_config
from methods import mode_clustering as MC
from methods import model_update as MU
from methods.constants import PARAMS, MODEL_PARAMETERS
# pylint: disable=R0914, C0103

def run_model_update_local_sysid(config_path):
    number_of_minutes = 1
    data_topic_indexes = [0, 2, 3, 4]

    _, clusters, _ = MC.cluster_of_local_sysid(config_path, number_of_minutes, data_topic_indexes)

    # Run model update
    _, omega_model, model_parameters = MU.estimate_updated_model(clusters,MODEL_PARAMETERS,PARAMS)
    _ = MU.model_update_plots([1,1], model_parameters, PARAMS['pars_to_update'],
                              omega_model, fig_axes=[None,None], hold=True)

def run_model_update_remote_sysid(config_path):
    config = load_config(config_path)
    mqtt_client, _, _ = MC.setup_client(config["model_update"])
    MU.live_model_update_with_remote_sysid(mqtt_client,config,None,PARAMS)

def run_live_model_update_remote_clustering(config_path):
    config = load_config(config_path)
    mqtt_client, subscrube_topic, publish_topic = MC.setup_client(config["model_update"])
    MU.live_model_update_with_remote_clustering(mqtt_client,config,subscrube_topic,
                                                publish_topic,PARAMS)
