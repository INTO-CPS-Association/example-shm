import sys
import matplotlib.pyplot as plt
from functions.plot_sysid import (plot_stabilization_diagram, plot_pre_stabilization_diagram)
from methods import sysid as sysID
from methods.constants import PARAMS
from data.comm.mqtt import (shutdown)

def run_sysid_and_plot(config_path):
    number_of_minutes = 0.2
    data_topic_indexes = [0, 2, 3, 4]
    aligner, data_client, _, fs = sysID.setup_sysid(config_path, data_topic_indexes)

    sysid_results, aligner_time = sysID.wait_for_sysid_output(number_of_minutes, aligner, fs)
    print("Aligned data recieved at:",aligner_time)
    data_client.disconnect()

    _ = plot_pre_stabilization_diagram(sysid_results, PARAMS, fig_ax=None)
    _ = plot_stabilization_diagram(sysid_results, PARAMS, fig_ax=None)
    plt.show(block=True)
    sys.stdout.flush()


def run_sysid_and_print(config_path):
    number_of_minutes = 0.2
    data_topic_indexes = [0, 2, 3, 4]
    aligner, data_client, _, fs = sysID.setup_sysid(config_path, data_topic_indexes)

    sysid_results, _ = sysID.wait_for_sysid_output(number_of_minutes, aligner, fs)
    data_client.disconnect()
    sys.stdout.flush()

    print(f"\n System Frequencies \n {sysid_results['Fn_poles']}")
    print(f"\n Cov \n{sysid_results['Fn_poles_cov']}")
    print(f"\n damping_ratios  \n{sysid_results['Xi_poles']}")
    print(f"\n cov_damping \n{sysid_results['Xi_poles_cov']}")


def run_sysid_and_publish(config_path):
    number_of_minutes = 0.2
    data_topic_indexes = [0, 2, 3, 4]
    aligner, data_client, mqtt_config, fs = sysID.setup_sysid(config_path, data_topic_indexes)

    try:
        sysid_results, aligner_time = sysID.wait_for_sysid_output(number_of_minutes, aligner, fs)
        sysID.publish_sysid_output(data_client, mqtt_config["TopicsToPublish"][0],
                                    sysid_results, aligner_time)
    except KeyboardInterrupt:
        print("\nKeyboard interrupt. Shutting down gracefully")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("Shutting down gracefully")
    finally:
        data_client.disconnect()
        sys.stdout.flush()

def live_sysid_and_publish(config_path):
    number_of_minutes = 0.2
    data_topic_indexes = [0, 2, 3, 4]
    aligner, data_client, mqtt_config, fs = sysID.setup_sysid(config_path, data_topic_indexes)

    try:
        while True:
            sysid_results, aligner_time = sysID.wait_for_sysid_output(number_of_minutes,
                                                                      aligner, fs)
            sysID.publish_sysid_output(data_client, mqtt_config["TopicsToPublish"][0],
                                        sysid_results, aligner_time)
    except KeyboardInterrupt:
        shutdown(data_client,"sysid")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        shutdown(data_client,"sysid")
