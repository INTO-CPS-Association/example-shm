import time
import numpy as np

# Project imports
from data.accel.hbk.Accelerometer import Accelerometer  # type: ignore
from data.accel.constants import MIN_SAMPLES_NEEDED  # type: ignore
from data.sources.mqtt import setup_mqtt_client, load_config  # type: ignore
from methods.sysID import sysid  # type: ignore


def main():
    config = load_config("src/config/mqtt.json")
    mqtt_config = config["MQTT"]["real_server"]

    topic_index = 0
    mqtt_client, selected_topic = setup_mqtt_client(mqtt_config, topic_index)
    mqtt_client.connect(mqtt_config["host"], mqtt_config["port"], 60)
    mqtt_client.loop_start()

    # Initialize Accelerometer w
    accelerometer = Accelerometer(mqtt_client, topic=selected_topic, fifo_size=10000)

    # System Identification parameters
    Params = {
        "Fs": 100,  
        "block_shift": 15,  
        "model_order": 10  
    }
    accelerometer._fifo.clear()
    accelerometer._timestamps.clear()
    while True:
        time.sleep(2)

        status, data = accelerometer.read(requested_samples=2000)
        print(f"FIFO contains {data.shape[0]} samples.")

        if data.shape[0] < MIN_SAMPLES_NEEDED:
            print(" Not enough samples in FIFO",
                  f"({data.shape[0]} < {MIN_SAMPLES_NEEDED}).",
                  "Waiting for more data...")
            time.sleep(0.5)
            continue

        print(f"Data shape before sysid: {data.shape}")

        sysid_output = sysid(data, Params)

        # extract results
        frequencies = sysid_output['Fn_poles']
        cov_freq    = sysid_output['Fn_poles_cov']
        damping_ratios = sysid_output['Xi_poles']
        cov_damping    = sysid_output['Xi_poles_cov']
        mode_shapes    = sysid_output['Phi_poles']

        print("System Identification frequencies:", frequencies)
        print("System Identification cov_freq:", cov_freq)
        print("damping_ratios:", damping_ratios)
        print(" cov_damping:", cov_damping)
        print("mode_shapes:", mode_shapes)

        break


if __name__ == '__main__':
    main()