import time
from data.comm.mqtt import load_config
from data.accel.hbk.aligner import Aligner
from methods import sysid as sysID
from methods import mode_clustering as MC
from methods import model_update
from methods.constants import PARAMS, MODEL_PARAMETERS
# pylint: disable=R0914, C0103

def run_model_update_local_sysid(config_path):
    number_of_minutes = 1
    config = load_config(config_path)
    mqtt_config = config["MQTT"]

    # Setting up the client and extracting Fs
    data_client, fs = sysID.setup_client(mqtt_config)

    # Setting up the aligner
    data_topic_indexes = [0, 2, 3, 4]
    selected_topics = [mqtt_config["TopicsToSubscribe"][i] for i in data_topic_indexes]
    aligner = Aligner(data_client, topics=selected_topics)

    aligner_time = None
    while aligner_time is None:
        print("Not enough aligned yet")
        time.sleep(10)
        oma_output, aligner_time = sysID.get_sysid_results(number_of_minutes, aligner, fs)
    data_client.disconnect()

    # Mode clustering
    dictionary_clusters, median_frequencies = MC.cluster_sysid(oma_output,PARAMS)

    # Run model update
    parameters, omegaMU, model_parameters = model_update.estimate_updated_model(dictionary_clusters,MODEL_PARAMETERS,PARAMS)

def run_model_update_remote_sysid(config_path):
    model_update.live_model_update_with_remote_sysid(config_path)

def run_live_model_update_remote_clustering(config_path):
    model_update.live_model_update_with_remote_clustering(config_path)

def run_live_model_update_with_remote_clustering_and_publish(config_path):
    config = load_config(config_path)
    publish_config = config["model_update"]
    publish_client, publish_topic = MC.setup_publish_client(publish_config)
    # publish_topic = publish_config["TopicsToSubscribe"][0]
    model_update.live_model_update_with_remote_clustering_and_publish(config_path,publish_client,publish_topic)