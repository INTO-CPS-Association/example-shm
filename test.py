"""
This program will
1. Get the configuration from private and public JSON configuration files
1. read CP-SENS MQTT messages v.2, both data and metadata
2. plot the data
"""

import matplotlib.pyplot as plt
import numpy as np
import ssl
from paho.mqtt.client import Client as MQTTClient
from paho.mqtt.client import CallbackAPIVersion
from paho.mqtt.client import MQTTv311
import queue
import struct
import time
import argparse
import json
import sys
import os


HOST_DEFAULT = "dtl-server-2.st.lab.au.dk"
PORT_DEFAULT = 8090
USERNAME_DEFAULT = "hbk1"
PASSWORD_DEFAULT = "hbk1shffd"
MQTT_TOPIC_DEFAULT = "cpsens/+/+/1/acc/raw/+" # "cpsens/+/+/1/+/+/data"
YLIM_DEFAULT = 3 # MATLAB's ylim([-3 3])
BUFFER_TO_DRAW_DEFAULT = 3 # seconds

# Default configuration files
PRIVATE_CONFIG_FILE_DEFAULT = "private_config.json" # locate this file in the private folder and chmod 600 it.
PUBLIC_CONFIG_FILE_DEFAULT = "public_config.json" # this file can be located in a public folder 


myDict = {}
bReadingMyDict = False
bWritingMyDict = False
strMQTTTopic = MQTT_TOPIC_DEFAULT


def on_connect(mqttc_in, userdata, flags, rc, properties=None):
    global json_config_public
    print("MQTT_IN: Connected with response code %s" % rc)
    for topic in json_config_public["MQTT_IN"]["TopicsToSubscribe"]:
    print(f"MQTT_IN: Subscribing to the topic {topic}...")
    mqttc_in.subscribe(topic, qos=json_config_public["MQTT_IN"]["QoS"])


def on_subscribe(self, mqttc, userdata, msg, granted_qos):
p   rint("Subscribed. Message: " + str(msg))


def on_message(client, userdata, msg): 
    global myDict, bReadingMyDict, bWritingMyDict
    topic = msg.topic
    print(f"topic = {topic}")
    substrings = topic.split('/')
    bIsMetadata = True
    if substrings[-1] == "data":
        bIsMetadata = False
    elif substrings[-1] == "metadata":
        bIsMetadata = True
    else:
        raise Exception("Unknown topic: " + substrings[-1])

    # Create a tuple made of the topic string without the last element (data/metadata)
    myKey = tuple(substrings[:-1])

    while bReadingMyDict:
        # make the thread sleep
        # print("Waiting for bReadingMyDict")
        time.sleep(0.0001)
        bWritingMyDict = True
        if bIsMetadata:
            # Process JSON metadata
            # Add the key to the dictionary
            if myKey not in myDict:
                # Parse the payload
                json_metadata = json.loads(msg.payload)
                nSamples = json_metadata['Data']['Samples']
                cType = json_metadata['Data']['Type'][0]
                Fs = json_metadata["Analysis chain"][-1]["Sampling"] # take the sampling freq. from the last element of the analysis chain!
                # Need to know: physical quantity, units
                strPhysQuantity = json_metadata["Analysis chain"][-1]["Output"]
                strUnits = json_metadata["Data"]["Unit"]
                # Only for metadata ver.>=2
                try:
                    secAtAcqusitionStart = json_metadata["TimeAtAquisitionStart"]["Seconds"]
                    nanosec = json_metadata["TimeAtAquisitionStart"]["Nanosec"]
                except Exception as e:
                    print("Incompatible version. Use earlier version of cpsns_LifePlot!", file=sys.stderr)

                usTimeStamp = 0
                # 0 1 2 3 4 5 6 7 8
                #myDict[myKey] = [nSamples, cType, Fs, strPhysQuantity, strUnits, queue.Queue(), None, secAtAcqusitionStart, usTimeStamp]
                myDict[myKey] = {
                "SamplesInPayload": nSamples, 
                "DataType": cType, 
                "SampleRate": Fs, 
                "PhysicalQuantity": strPhysQuantity, 
                "Units": strUnits, 
                "PayloadQueue": queue.Queue(), 
                "SecAtAcqusiitionStart": secAtAcqusitionStart, 
                "Nanosec": nanosec,
                "SampleWhenEntryCreated": 0,
                "Data": None,
                "PlotLine": None
                }
                print(f"Key added: {myKey}.")

            else:
                if myKey in myDict:
                    # Parse the payload
                    payload = msg.payload
                    # descriptorLength, metadataVer = struct.unpack_from('HH', payload) # assumes "default", which is little endian here

                    # Trying to load in big-endian and little-endian ways
                    char_LE, char_BE = '<','>'
                    temp, metadataVer_LE = struct.unpack_from(char_LE+'HH', payload) # assumes little endian here
                    temp, metadataVer_BE = struct.unpack_from(char_BE+'HH', payload) # assumes big endian here
                    char_Endian = char_LE if metadataVer_LE < metadataVer_BE else char_BE

                    # re-read the descriptor
                    descriptorLength, metadataVer = struct.unpack_from(char_Endian+'HH', payload)
                    print(f"Descriptor length {descriptorLength}, metadata version {metadataVer}") 

                    # how many samples and what's its type, float or double?
                    cType = myDict[myKey]["DataType"]
                    #cType = "d"
                    nSamples = myDict[myKey]["SamplesInPayload"]
                    #nSamples = -1
                    if nSamples == -1: # unknown or variable
                        # calculate nSamples from the payload length
                        payload_len = len(payload)
                        nSamples = round((payload_len-descriptorLength)/struct.calcsize(cType))

                        # Data
                        strBinFormat = char_Endian + str(nSamples) + str(cType) # e.g., '>640f' for 640 floats, big-endian
                        print(f"strBinFormat = {strBinFormat}")
                        # data
                        data = np.array(struct.unpack_from(strBinFormat, payload, descriptorLength))
                        print(f"data = {data[0:10]}")
                        print(f"size of data = {data.shape}")
                        # time stamp of the payload
                        secFromEpoch = struct.unpack_from(char_Endian + 'Q', payload, 4)[0]
                        nanosec = struct.unpack_from(char_Endian + 'Q', payload, 12)[0]
                        # nSamples
                        nSamplesFromDAQStart = 0

                        if metadataVer >= 2:
                            nSamplesFromDAQStart = struct.unpack_from(char_Endian + 'Q', payload, 20)[0]
                        else:
                            raise Exception("Incompatible version. Use earlier version of cpsns_LifePlot!")
                        print(f"secFromEpoch = {secFromEpoch}, nSamplesFromDAQStart = {nSamplesFromDAQStart}")

                    if myDict[myKey]["SampleWhenEntryCreated"] == 0:
                        # First time
                        myDict[myKey]["SampleWhenEntryCreated"] = nSamplesFromDAQStart

                        myDict[myKey]["PayloadQueue"].put({"SampleFromDAQStart": nSamplesFromDAQStart, "PayloadData": data})
                    else:
                        print("Waiting for the metadata...")

                        bWritingMyDict = False




def main():
    global json_config_private, json_config_public
    global myDict, bReadingMyDict, bWritingMyDict
    # Parse command line parameters
    # Create the parser
    parser = argparse.ArgumentParser(description="This Python script reads the time data from MQTT and outputs it on a life graph.")
    parser.add_argument('--config_private', type=str, help='Specify the JSON configuration file for PRIVATE data. Defaults to ' + PRIVATE_CONFIG_FILE_DEFAULT, default=PRIVATE_CONFIG_FILE_DEFAULT)
    parser.add_argument('--config_public', type=str, help='Specify the JSON configuration file for PUBLIC data. Defaults to ' + PUBLIC_CONFIG_FILE_DEFAULT, default=PUBLIC_CONFIG_FILE_DEFAULT)

    # Parse the arguments
    args = parser.parse_args()
    # Parsing the configuration files..
    # Name of the private configuration file
    strConfigFile = args.config_private
    # Read the configuration file
    print(f"Reading private configuration from {strConfigFile}...")
    if os.path.exists(strConfigFile):
        try:
            # Open and read the JSON file
            with open(strConfigFile, 'r') as file:
                json_config_private = json.load(file)
        except json.JSONDecodeError:
            print(f"Error: The file {strConfigFile} exists but could not be parsed as JSON.", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Error: The file {strConfigFile} does not exist.", file=sys.stderr) 
        sys.exit(1)

        # Name of the public configuration file
        strConfigFile = args.config_public
        # Read the configuration file
        print(f"Reading public configuration from {strConfigFile}...")
        if os.path.exists(strConfigFile):
            try:
                # Open and read the JSON file
                with open(strConfigFile, 'r') as file:
                    json_config_public = json.load(file)
            except json.JSONDecodeError:
                print(f"Error: The file {strConfigFile} exists but could not be parsed as JSON.", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"Error: The file {strConfigFile} does not exist.", file=sys.stderr) 
            sys.exit(1)
            # MQTT_IN stuff
            mqttc_in = MQTTClient(callback_api_version=CallbackAPIVersion.VERSION2, protocol=MQTTv311)

            # Set username and password
        if json_config_private["MQTT_IN"]["userId"] != "":
            mqttc_in.username_pw_set(json_config_private["MQTT_IN"]["userId"], json_config_private["MQTT_IN"]["password"])

            # TLS configuration (ONLY if enabled)
            if json_config_private["MQTT_IN"].get("useTLS", False):
                mqttc_in.tls_set(
                ca_certs=json_config_private["MQTT_IN"]["caFile"],
                certfile=None,
                keyfile=None,
                tls_version=ssl.PROTOCOL_TLS_CLIENT
                )


    # Optional but recommended
    mqttc_in.tls_insecure_set(False)
    mqttc_in.on_connect = on_connect
    mqttc_in.on_message = on_message
    mqttc_in.on_subscribe = on_subscribe
    mqttc_in.connect(json_config_private["MQTT_IN"]["host"], json_config_private["MQTT_IN"]["port"], 60) # we subscribe to the topics in on_connect callback

    mqttc_in.loop_start()
    # MQTT_IN done

# plot params, from public configuration
TimeToCover = json_config_public["Graph"]["TimeToCover"] # seconds
ylim = json_config_public["Graph"]["ylim"] # Y axis limits

# initiate the plt
plt.ion()
fig, ax = plt.subplots()
# New: grid lines
ax.grid(True)
# Labels
ax.set_xlabel('Time, s')

# common time axis
tAxisCommon = None

last_redraw_time = time.time()
while True:
    bNeedToReset = False
    # Dima 18-Dec
    current_time = time.time()
    if current_time-last_redraw_time >= 0.1:
        bNeedToRedraw = True
        last_redraw_time=current_time
    else:
        bNeedToRedraw = False

    if bNeedToRedraw:
        while bWritingMyDict:
            # make the thread sleep
            # print("Waiting for bWritingMyDict")
            time.sleep(0.0001)
            bReadingMyDict = True 

    for key, val in myDict.items():
        if val["PayloadQueue"].empty():
            continue

        # Define the global time axis
        if tAxisCommon is None:
            tAxisCommon = {"Fs": val["SampleRate"], "AxisStartsAtSample": val["SampleWhenEntryCreated"], "AxisLength": int(round(TimeToCover * val["SampleRate"]))}
            #print(f'AxisLength = {tAxisCommon["AxisLength"]}')

        if val["Data"] is None:
            # allocate
            val["Data"] = np.full(tAxisCommon["AxisLength"], 0, dtype=np.float32)

            while not val["PayloadQueue"].empty():
            # place the data where it is suposed to be
            payload = val["PayloadQueue"].get()
            inx = payload["SampleFromDAQStart"]
            inxToPlaceData = inx - tAxisCommon["AxisStartsAtSample"]
            print(f"inxToPlaceData = {inxToPlaceData}")
        if inxToPlaceData<0:
            ## ignore this payload...
            #print(f"key={key}. Negative index: {inxToPlaceData}. The payload is ignored!") 
            #continue
            # need to reset!
            bNeedToReset = True
            break

data = payload["PayloadData"]
print(data.shape)
if inxToPlaceData+len(data) < tAxisCommon["AxisLength"]:
# okay
val["Data"][inxToPlaceData:inxToPlaceData+len(data)] = data
else:
# need to "scroll"... by 
scrl = 1 + inxToPlaceData+len(data) - tAxisCommon["AxisLength"]
print(f"key={key}. Scrolling by {scrl} elements") 
# scroll the time axis
tAxisCommon["AxisStartsAtSample"] += scrl
if scrl < tAxisCommon["AxisLength"]:
# scroll all other dataset
for kk in myDict:
if myDict[kk]["Data"] is None:
continue
myDict[kk]["Data"] = np.roll(myDict[kk]["Data"], -scrl)
if kk == key:
print(f"inxToPlaceData = {inxToPlaceData}")
print(f"inxToPlaceData-scrl = {inxToPlaceData-scrl}")
print(f"inxToPlaceData+len(data)-scrl = {inxToPlaceData+len(data)-scrl}")
myDict[kk]["Data"][inxToPlaceData-scrl:inxToPlaceData+len(data)-scrl] = data
else:
myDict[kk]["Data"][-scrl:] = np.full(scrl, 0, dtype=np.float32) 
else:
# need to reset!
bNeedToReset = True
break

# add a line if it is not here
if val["PlotLine"] is None:
ta = np.linspace(0, tAxisCommon["AxisLength"]/tAxisCommon["Fs"], tAxisCommon["AxisLength"])
line, = ax.plot(ta, val["Data"], label=str(key))
plt.legend(loc="upper left")
plt.ylim(ylim[0], ylim[1])
val["PlotLine"] = line

line = val["PlotLine"]
line.set_ydata(val["Data"])

if bNeedToReset:
print("Long break in the data detected. Resetting the plot", file=sys.stderr)
bNeedToReset = False
# remove the lines
for kk in myDict:
if myDict[kk]["PlotLine"] is not None:
myDict[kk]["PlotLine"].remove()

# reset the dictionary
myDict = {}
tAxisCommon = None

# remove the legend
plt.legend().remove()
plt.show()

bReadingMyDict = False

fig.canvas.draw()
fig.canvas.flush_events()

time.sleep(0.1) # Dima 16-Dec



if __name__ == "__main__":
main()