import time
import numpy as np
import matplotlib.pyplot as plt
from data.comm.mqtt import setup_mqtt_client, load_config, shutdown  # type: ignore
from data.accel.hbk.aligner import Aligner
from data.accel.metadata import extract_metadata
from methods.setup_data import setup_aligner, wait_for_data
from functions.plot_aligned_readings import plot_timeseries
# pylint: disable=C0103

def align_acceleration_readings(config_path):
    config = load_config(config_path)
    sysid_config = config["sysid"]

    all_topics = sysid_config["TopicsToSubscribe"]
    metadata = extract_metadata(sysid_config)
    mqtt_client = setup_mqtt_client(sysid_config, sysid_config["TopicsToSubscribe"])
    mqtt_client.connect(sysid_config["host"], sysid_config["port"], 60)
    mqtt_client.loop_start()

    aligner = Aligner(mqtt_client, topics=all_topics, metadata=metadata)

    while True:
        time.sleep(1)
        data, utime = aligner.extract(16)
        if data.shape[0] == 0:
            print("Not enough aligned data yet.")
        else:
            print(f"Collected this batch at: {utime}")
            print(f"Extracted aligned data shape: {data.shape}\n{data}")
            break
        time.sleep(1)
    shutdown(mqtt_client, "aligner example")

def live_align_readings_plot(config_path):
    number_of_samples = 2560

    fig_ax = None
    aligner, mqtt_client, _, params = setup_aligner(config_path)
    try:
        while True:
            data, _ = wait_for_data(number_of_samples,
                                        aligner, params['Fs'])
            if data is not None:
                if fig_ax is None:
                    N = 20000
                    xdata = np.zeros(N)
                    ydata = np.zeros((data.shape[0],N))
                t1 = time.perf_counter()
                fig_ax, xdata, ydata = plot_timeseries(data, xdata, ydata, x_length=N, fig_ax=fig_ax)
                t2 = time.perf_counter()
                print("time to plot",t2-t1,"s")
    except KeyboardInterrupt:
        print("\nKeyboard interrupt. Shutting down gracefully")
        plt.show(block=True)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    shutdown(mqtt_client,"sysid")
