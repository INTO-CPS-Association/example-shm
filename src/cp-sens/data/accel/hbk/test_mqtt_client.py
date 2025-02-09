# This is to test the clinet MQtt code that I extracted from cpsns_pyOMA.py
import time
from accelerometer import mqttc, on_connect, on_message, on_subscribe, on_publish

def test_mqtt_connection():
    # Set up the callbacks
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.on_subscribe = on_subscribe
    mqttc.on_publish = on_publish

    # Connect to the broker (using the port from json)
    mqttc.connect("test.mosquitto.org", 1883, 60)  

    # Start the loop to maintain the connection and handle callbacks
    mqttc.loop_start()

    # test message
    mqttc.publish("topic", "test message", qos=1)
    time.sleep(5)
    mqttc.loop_stop()



test_mqtt_connection()
