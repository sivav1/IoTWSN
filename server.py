import socket
import json

UDP_IP = "127.0.0.1"
UDP_PORT = 5005

SENSORTYPES = [
    'accelerometer'
    ,'barometer'
    ,'gyroscope'
    ,'humidity'
    ,'IRtemperature'
    ,'lightmeter'
    ,'magnetometer'
]

with open('config.json') as config_file:
    config = json.load(config_file)
    UDP_IP = config["ip"]
    UDP_PORT = config["port"]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))
print "listening to : ", UDP_IP + " : " + str(UDP_PORT)

while True:
    data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    print "received message:", data
    json_obj = json.load(data)