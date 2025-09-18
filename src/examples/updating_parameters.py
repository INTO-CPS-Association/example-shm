import time
from data.comm.mqtt import load_config
from data.accel.hbk.aligner import Aligner
from methods.packages import sys_id as sysID
from methods import model_update_module as MT
# pylint: disable=R0914, C0103

def run_model_update(config_path):
    number_of_minutes = 2
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
        oma_output, aligner_time, _ = sysID.get_oma_results(number_of_minutes, aligner, fs)
    data_client.disconnect()

    # Mode Track
    cluster_dict_before, cluster_dict_allignment, cluster_dict = MT.run_mode_clustering(oma_output)

    # Run model update
    model_pars = {'l4': 0.129}
    update_result = MT.run_model_update(cluster_dict,model_pars)

    if update_result is not None:
        optimized_parameters = update_result['optimized_parameters']
        omegaN_rad = update_result['omegaN_rad']
        omegaN_Hz = update_result['omegaN_Hz']
        pars_model = update_result['pars_updated']

        print("\nOptimized parameters (k, m):", optimized_parameters)
        print("\nNatural frequencies (rad/s):", omegaN_rad)
        print("\nNatural frequencies (Hz):", omegaN_Hz)
        print("\nUpdated model parameters (dictionary):", pars_model)

    else:
        print("Model update failed.")
