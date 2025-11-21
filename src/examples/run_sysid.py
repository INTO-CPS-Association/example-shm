import sys
import matplotlib.pyplot as plt
from functions.plot_sysid import (plot_stabilization_diagram, plot_pre_stabilization_diagram)
from methods import sysid as sysID
from methods.constants import PARAMS
from data.comm.mqtt import (shutdown)

def run_sysid_and_plot(config_path):
    number_of_minutes = 0.2

    mqtt_client, sysid_output, _ = sysID.local_sysid(config_path,
                                                              number_of_minutes)
    mqtt_client.disconnect()

    _ = plot_pre_stabilization_diagram(sysid_output, PARAMS, fig_ax=None)
    _ = plot_stabilization_diagram(sysid_output, PARAMS, fig_ax=None)
    plt.show(block=True)


def run_sysid_and_print(config_path):
    number_of_minutes = 0.2
    mqtt_client, sysid_output, _ = sysID.local_sysid(config_path,
                                                              number_of_minutes)

    print(f"\n System Frequencies \n {sysid_output['Fn_poles']}")
    print(f"\n Cov \n{sysid_output['Fn_poles_cov']}")
    print(f"\n damping_ratios  \n{sysid_output['Xi_poles']}")
    print(f"\n cov_damping \n{sysid_output['Xi_poles_cov']}")

    shutdown(mqtt_client,"sysid client")

def run_sysid_and_publish(config_path):
    number_of_minutes = 0.2
    sysID.live_sysid(config_path, number_of_minutes, loop = False)

def live_sysid_and_publish(config_path):
    number_of_minutes = 0.2
    sysID.live_sysid(config_path, number_of_minutes, loop = True)
