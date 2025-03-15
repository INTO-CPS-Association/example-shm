from data.accel.accelerometer import IAccelerometer # type: ignore
from data.accel.random import RandomSource # type: ignore
import time
from data.accel.hbk.Accelerometer import Accelerometer  # type: ignore
from data.accel.constants import MIN_SAMPLES_NEEDED   # type: ignore
from data.sources.mqtt import setup_mqtt_client, load_config # type: ignore
from methods.sysID import sysid # type: ignore
import numpy as np
import logging




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
        "block_shift": 30,  
        "model_order": 20  
    }

    while True:
        time.sleep(2)

        status, data = accelerometer.read(requested_samples=2000)
        print(f"FIFO contains {data.shape[0]} samples.")



        if data.shape[0] < MIN_SAMPLES_NEEDED:
              print(f" Not enough samples in FIFO ({data.shape[0]} < {MIN_SAMPLES_NEEDED}). Waiting for more data...")
              time.sleep(0.5)
              continue  

        data = data.T
        
        # logging data and sysid output 
        log_file_path = r"C:\Users\derki\Desktop\sysID_log.txt"
        logging.basicConfig(filename=log_file_path, level=logging.INFO, format="%(asctime)s - %(message)s")
        logging.info("data before passing them to sysID %s", data[:, :50])
        logging.info("data shape  %s", data.shape)
        logging.info("\n The params: %s", Params)



        sysid_output = sysid(data, Params)

        # extract results
        frequencies = sysid_output['Fn_poles']
        cov_freq    = sysid_output['Fn_poles_cov']
        damping_ratios = sysid_output['Xi_poles']
        cov_damping    = sysid_output['Xi_poles_cov']
        mode_shapes    = sysid_output['Phi_poles']

        logging.info(" System Identification frequencies: %s", frequencies)
        print("System Identification frequencies:", frequencies)
        logging.info(" System Identification cov_freq: %s", cov_freq)
        print("System Identification cov_freq:", cov_freq)
        logging.info(" damping_ratios: %s", damping_ratios)
        print("damping_ratios:", damping_ratios)
        logging.info("  cov_damping: %s", cov_damping)
        print(" cov_damping:", cov_damping)
        logging.info("  mode_shapes: %s", mode_shapes)
        print("mode_shapes:", mode_shapes)

        break  


if __name__ == '__main__':
    main()