import socket
import json
import paho.mqtt.client as paho
import os
import ssl
from time import sleep
from grovepi import *
from grove_rgb_lcd import *
from time import sleep
from math import isnan

UDP_IP = "127.0.0.1"
UDP_PORT = 5005
connflag = False

with open('config.json') as config_file:
    config = json.load(config_file)
    UDP_IP = config["ip"]
    UDP_PORT = config["port"]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))
print "listening to : ", UDP_IP + " : " + str(UDP_PORT)

def on_connect(client, userdata, flags, rc):                # func for making connection
    global connflag
    print "Connected to AWS"
    connflag = True
    print("Connection returned result: " + str(rc) )
    client.subscribe("#" , 1 )
 
def on_message(client, userdata, msg):                      # Func for Sending msg
    print("from server " + msg.topic+" "+str(msg.payload))
    retval = msg.payload.split('|')

mqttc = paho.Client()                                 
mqttc.on_connect = on_connect
mqttc.on_message = on_message   

awshost = "a1mz0kmfnb67b4.iot.ap-southeast-2.amazonaws.com"      # Endpoint
awsport = 8883                                              # Port no.   
clientId = "aws_iot"                                     # Thing_Name
thingName = "aws_iot"                                    # Thing_Name
caPath = "root-CA.crt"                                      # Root_CA_Certificate_Name
certPath = "1ea25c8bd2-certificate.pem.crt"                            # <Thing_Name>.cert.pem
keyPath = "1ea25c8bd2-private.pem.key" 

mqttc.tls_set(caPath, certfile=certPath, keyfile=keyPath, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)  # pass parameters
mqttc.connect(awshost, awsport, keepalive=60)               # connect to aws server
mqttc.loop_start()  

while True:
    data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    payload = ''
    topic = ''#'deviceuid|devicename|'
    print "received message:", data
    json_obj = json.loads(data)
    #for sensor in SENSORTYPES:
        #if(sensor in json_obj):
            #topic += sensor
            #payload += str(json_obj[sensor])
    if connflag == True:
        #if payload != '':
        topic = str(json_obj['deviceuid']) + '/' + str(json_obj['devicename'])
        payload = json.dumps(json_obj) #json_obj['deviceuid'] + "|" + json_obj['devicename'] + "|" + payload
        print 'Payload : ', payload
        print 'topic :' , topic
        mqttc.publish(topic, payload, qos=1)