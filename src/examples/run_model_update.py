import time
from data.comm.mqtt import load_config
from data.accel.hbk.aligner import Aligner
from methods import sysid as sysID
from methods import mode_clustering as MC
from methods import model_update as MU
from methods.constants import PARAMS
# pylint: disable=R0914, C0103

def run_model_update_local_sysid(config_path):
    number_of_minutes = 5
    config = load_config(config_path)
    mqtt_config = config["MQTT"]

    # Setting up the client and extracting Fs
    data_client, fs = sysID.setup_client(mqtt_config)

    # Setting up the aligner
    data_topic_indexes = [0, 2]
    selected_topics = [mqtt_config["TopicsToSubscribe"][i] for i in data_topic_indexes]
    aligner = Aligner(data_client, topics=selected_topics)

    aligner_time = None
    while aligner_time is None:
        print("Not enough aligned yet")
        time.sleep(10)
        oma_output, aligner_time = sysID.get_sysid_results(number_of_minutes, aligner, fs)
    data_client.disconnect()

    # Mode Track
    dictionary_clusters, median_frequencies = MC.cluster_sysid(oma_output,PARAMS)

    # Run model update
    update_result = MU.run_model_update(dictionary_clusters)

    if update_result is not None:
        optimized_parameters = update_result['optimized_parameters']
        omegaN_rad = update_result['omegaN_rad']
        omegaN_Hz = update_result['omegaN_Hz']
        mode_shapes = update_result['mode_shapes']
        damping_matrix = update_result['damping_matrix']
        pars_model = update_result['pars_updated']
        system_up = update_result['System_updated']

        print("\nOptimized parameters (k, m):", optimized_parameters)
        print("\nNatural frequencies (rad/s):", omegaN_rad)
        print("\nNatural frequencies (Hz):", omegaN_Hz)
        print("\nMode shapes (normalized):\n", mode_shapes)
        print("\nDamping matrix:\n", damping_matrix)
        print("\nUpdated model parameters (dictionary):", pars_model)
        print("\nUpdated system:")
        print("\nMass matrix M:", system_up["M"])
        print("\nStiffness matrix K:\n", system_up["K"])
        print("\nDamping matrix C:\n", system_up["C"])

    else:
        print("Model update failed.")



def run_model_update_remote_sysid(config_path):
    config = load_config(config_path)
    sysid_output, clusters, median_frequencies = (
        MC.subscribe_and_cluster(config_path)
    )

    # Run model update
    update_result = MU.run_model_update(clusters)

    if update_result is not None:
        optimized_parameters = update_result['optimized_parameters']
        omegaN_rad = update_result['omegaN_rad']
        omegaN_Hz = update_result['omegaN_Hz']
        mode_shapes = update_result['mode_shapes']
        damping_matrix = update_result['damping_matrix']
        pars_model = update_result['pars_updated']
        system_up = update_result['System_updated']

        print("\nOptimized parameters (k, m):", optimized_parameters)
        print("\nNatural frequencies (rad/s):", omegaN_rad)
        print("\nNatural frequencies (Hz):", omegaN_Hz)
        print("\nMode shapes (normalized):\n", mode_shapes)
        print("\nDamping matrix:\n", damping_matrix)
        print("\nUpdated model parameters (dictionary):", pars_model)
        print("\nUpdated system:")
        print("\nMass matrix M:", system_up["M"])
        print("\nStiffness matrix K:\n", system_up["K"])
        print("\nDamping matrix C:\n", system_up["C"])

    else:
        print("Model update failed.")
