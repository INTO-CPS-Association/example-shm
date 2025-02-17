import json
from datetime import datetime
import queue
from threading import Thread
from time import sleep
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import paho.mqtt.client as mqtt
import json
import paho.mqtt.client as mqtt

with open('config.json', 'r') as f:
    config = json.load(f)
    host = config['mqtt']['host']
    port = config['mqtt']['port']
    username = config['mqtt']['username']
    password = config['mqtt']['password']
    topic = config['mqtt']['topic']

samples = 30
time_step=1 #seconds
accel_queue = queue.Queue()

# TODO: Adopt dynamic plotting from
# other CP-Sens demo code
# because this plotting is too slow

def update_graph(fig,ax,x_values,accel_x,accel_y,accel_z):
    ax.clear()
    ax.plot(x_values, accel_x, c='r', label='x-axis')
    ax.plot(x_values, accel_y, c='b', label='y-axis')
    ax.plot(x_values, accel_z, c='g', label='z-axis')
    ax.set_title('Acceleration Values')
    ax.set_ylabel(r'$x10^{-3} g$')
    ax.set_xticks(x_values)
    labels = [x-(samples-1) for x in x_values]
    labels[0] = 'oldest'
    labels[-1] = 'latest'
    ax.set_xticklabels(labels, rotation=90)
    ax.legend(loc=2)
    ax.grid(True)
    fig.canvas.draw()
    fig.canvas.flush_events()


def plot_graph() -> None:
    gs = gridspec.GridSpec(1,1)
    plt.ion()
    fig = plt.figure()
    ax = plt.subplot(gs[0,0])
    ax.clear()
    x_values = range(0,samples)
    accel_x = [0  for x in range(0,samples)]
    accel_y = [0  for y in range(0,samples)]
    accel_z = [0  for z in range(0,samples )]
    update_graph(fig,ax,x_values,accel_x,accel_y,accel_z)

    while True:
      if not accel_queue.empty():
          #print(f'accessing queue: queue size {accel_queue.qsize()}')
          accel = accel_queue.get()
          del accel_x[0]
          del accel_y[0]
          del accel_z[0]
          accel_x.append(1000*accel['x'])
          accel_y.append(1000*accel['y'])
          accel_z.append(1000*accel['z'])
          print(f'received accelerometer sample: {accel}')
          update_graph(fig,ax,x_values,accel_x,accel_y,accel_z)

      #matplotlib is too slow
      #throw out old values and use only the latest one
      #with accel_queue.mutex:
      #     accel_queue.queue.clear()
      sleep(time_step/100)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    client.subscribe(topic)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    #print(msg.topic+" "+str(msg.payload))
    accel_queue.put(json.loads(str(msg.payload.decode("utf-8","ignore"))))

if __name__ == "__main__":
  mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
  mqttc.username_pw_set(username, password)

  mqttc.on_connect = on_connect
  mqttc.on_message = on_message

  mqttc.connect(host, port)
  mqttc.loop_start()
  plot_graph()
