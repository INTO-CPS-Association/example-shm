import time
from data.accel.hbk.accelerometer import Accelerometer
from data.comm.mqtt import setup_mqtt_client, load_config, shutdown  # type: ignore

def read_accelerometers(config_path):
    config = load_config(config_path)
    sysid_config = config["sysid"]
    mqtt_client = setup_mqtt_client(sysid_config, sysid_config['TopicsToSubscribe'][0])
    mqtt_client.connect(sysid_config["host"], sysid_config["port"], 60)
    mqtt_client.loop_start()

    accelerometer = Accelerometer(
        mqtt_client,
        topic=sysid_config['TopicsToSubscribe'],
        map_size=1920
    )

    with accelerometer.acquire_lock():
        accelerometer.data_map.clear()

    time.sleep(1)
    with accelerometer.acquire_lock():
        for key, fifo in sorted(accelerometer.data_map.items()):
            print(f"Key: {key} -> Data: {list(fifo)}\n")
    _, data = accelerometer.read(requested_samples=256)

    print("Data requested", data)
    shutdown(mqtt_client, "Acceleration Reader")
