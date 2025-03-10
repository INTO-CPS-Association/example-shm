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
    config = load_config("src/cp-sens/config/mqtt.json")
    mqtt_config = config["MQTT"]["real_server"]

    topic_index = 3  
    mqtt_client, selected_topic = setup_mqtt_client(mqtt_config, topic_index)
    mqtt_client.connect(mqtt_config["host"], mqtt_config["port"], 60)  
    mqtt_client.loop_start()

    # Initialize Accelerometer w
    accelerometer = Accelerometer(mqtt_client, topic=selected_topic, fifo_size=100)

    
    # System Identification parameters
    Params = {
        "Fs": 10,  
        "block_shift": 15,  
        "model_order": 10  
    }

    while True:
        time.sleep(2)

        status, data = accelerometer.read(requested_samples=100)
        print(f"FIFO contains {data.shape[0]} samples.")



        if data.shape[0] < MIN_SAMPLES_NEEDED:
              print(f" Not enough samples in FIFO ({data.shape[0]} < {MIN_SAMPLES_NEEDED}). Waiting for more data...")
              time.sleep(0.5)
              continue  


        # logging data and sysid output 
        log_file_path = r"C:\Users\....\Desktop\sysid5_log.txt"
        logging.basicConfig(filename=log_file_path, level=logging.INFO, format="%(asctime)s - %(message)s")
        #logging.info("data before passing them to sysID %s", data)
        #logging.info("\n The params: %s", Params)



        print("data before passing them to sysID ",data)
        sysid_output = sysid(data, Params)
        #logging.info("✅ System Identification Output: %s", sysid_output)
        print("✅ System Identification Output:", sysid_output)
        break  


if __name__ == '__main__':
    main()