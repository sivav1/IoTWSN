#!/usr/bin/python

# importing libraries
import paho.mqtt.client as paho
import os
import socket
import ssl
from random import uniform
from grovepi import *
from grove_rgb_lcd import *
from time import sleep
from math import isnan

connflag = False
dht_sensor_port = 7  # connect the DHt sensor to port 7
dht_sensor_type = 0  # use 0 for the blue-colored sensor and 1 for the white-colored sensor
setRGB(0, 255, 0)


def on_connect(client, userdata, flags, rc):                # func for making connection
    global connflag
    print("Connected to AWS")
    connflag = True
    print("Connection returned result: " + str(rc))
    client.subscribe("#", 1)


def on_message(client, userdata, msg):                      # Func for Sending msg
    print("from server " + msg.topic+" "+str(msg.payload))
    retval = msg.payload.split('|')
    if len(retval) == 2:
        t = retval[0]
        h = retval[1]
        setText_norefresh("Temp:" + t + "C\n" + "Humidity :" + h + "%")

# def on_log(client, userdata, level, buf):
#    print(msg.topic+" "+str(msg.payload))


mqttc = paho.Client()                                       # mqttc object
# assign on_connect func
mqttc.on_connect = on_connect
# assign on_message func
mqttc.on_message = on_message
# mqttc.on_log = on_log

#### Change following parameters ####
awshost = "a1mz0kmfnb67b4.iot.ap-southeast-2.amazonaws.com"      # Endpoint
awsport = 8883                                              # Port no.
clientId = "aws_iot"                                     # Thing_Name
thingName = "aws_iot"                                    # Thing_Name
# Root_CA_Certificate_Name
caPath = "root-CA.crt"
# <Thing_Name>.cert.pem
certPath = "1ea25c8bd2-certificate.pem.crt"
keyPath = "1ea25c8bd2-private.pem.key"

mqttc.tls_set(caPath, certfile=certPath, keyfile=keyPath, cert_reqs=ssl.CERT_REQUIRED,
              tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)  # pass parameters

# connect to aws server
mqttc.connect(awshost, awsport, keepalive=60)

mqttc.loop_start()                                          # Start the loop

while 1 == 1:
    sleep(5)
    if connflag == True:
	    [temp, hum] = dht(dht_sensor_port, dht_sensor_type)
	    t = str(temp)
	    h = str(hum)
        mqttc.publish("temperature|humidity", t + "|" + h, qos=1)  
        print("msg sent: temperature " + "%.2f" % temp )
        print("msg sent: humidity " + "%.2f" % hum )
        setText("")
    else:
        print("waiting for connection...")                      
