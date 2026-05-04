import time
import datetime
import numpy as np
from typing import Any, Dict, Optional, Tuple
from data.comm.mqtt import setup_mqtt_client, load_config, shutdown  # type: ignore
from data.accel.hbk.aligner import Aligner


def align_acceleration_readings(config_path):
    config = load_config(config_path)
    sysid_config = config["sysid"]

    all_topics = sysid_config["TopicsToSubscribe"]

    mqtt_client = setup_mqtt_client(sysid_config, sysid_config["TopicsToSubscribe"][0])
    mqtt_client.connect(sysid_config["host"], sysid_config["port"], 60)
    mqtt_client.loop_start()

    aligner = Aligner(mqtt_client, topics=all_topics)

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

def get_data(
        samples: int, aligner: Aligner, fs: float
        ) -> Optional[Tuple[Dict[str, Any], str]]:
    """
    Extracts aligned sensor data and runs system identification (sysID).

    Args:
        sampling_period: How many minutes of data to pass to sysid.
        aligner: An initialized Aligner object.
        fs: Sampling frequency to use in the sysid algorithm.

    Returns:
        A tuple (sysid_output, timestamp) if successful, or None if data is not ready.
    """

    data, timestamp = aligner.extract(int(samples))

    if data.size < samples:
        return None, None

    return data, timestamp.isoformat()

def wait_for_data(samples: int, aligner: Aligner,
                          fs: float) -> Optional[Tuple[Dict[str, Any],str]]:
    aligner_time = None
    t1 = time.time()
    try:
        while aligner_time is None:
            time.sleep(0.05)
            t2 = time.time()
            t_text = f"Waiting for data for {round(t2-t1,1)} seconds"
            print(t_text,end="\r")
            data, aligner_time = get_data(samples, aligner, fs)

            if (t2-t1) > 100*samples/fs:
                raise RuntimeError("Aligned data not received in time")

        return data, aligner_time
    except KeyboardInterrupt as exc:
        raise RuntimeError("Keyboard interrupt") from exc

from methods import sysid as sysID

def live_align_readings_plot(config_path):
    number_of_samples = 2560
    
    import numpy as np
    from functions.plot_aligned_readings import plot_timeseries, plot_timeseries_1

    fig_ax = None
    aligner, mqtt_client, mqtt_config, fs = sysID.setup_sysid(config_path)
    # try:
    prev_aligner_time = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    prev_key = 0
    try:
        while True:
            data, aligner_time = wait_for_data(number_of_samples,
                                                        aligner, fs)
            if data is not None:
                # print("Aligned data time difference:", (datetime.datetime.fromisoformat(aligner_time)-prev_aligner_time).total_seconds(),". Key difference:",key-prev_key)
                prev_aligner_time = datetime.datetime.fromisoformat(aligner_time)
                if fig_ax is None:
                    N = 20000
                    xdata = np.zeros(N)
                    ydata = np.zeros((data.shape[0],N))
                t1 = time.perf_counter()
                fig_ax, xdata, ydata = plot_timeseries_1(data, xdata, ydata, aligner_time, fs, x_length=N, fig_ax=fig_ax)
                t2 = time.perf_counter()
                print("time to plot",t2-t1,"s")
    except KeyboardInterrupt:
        print("\nKeyboard interrupt. Shutting down gracefully")
        import matplotlib.pyplot as plt
        plt.show(block=True)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    shutdown(mqtt_client,"sysid")