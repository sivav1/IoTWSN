import bluepy
import threading
import time
import re
import argparse
import sys
import os
import socket
import json, ast

gworg = ''
gwdevtype = ''
gwdevid = ''
gwtoken = ''

BTNAME = 'Complete Local Name'

MAXDEVICES = 16

FAST = 0.2
MEDIUM = 1.0
SLOW = 5.0

SENSORTYPES = [
    'accelerometer', 'barometer'  
    , 'gyroscope', 'humidity', 'IRtemperature'  
    , 'lightmeter', 'magnetometer'
]


devicenames = {}
DEVICENAMESFILE = 'devices.txt'


def is_float(text):
    try:
        float(text)
        if str(text).isalpha():
            return False
        return True
    except ValueError:
        return False
    except TypeError:
        return False


class _paireddevice():
    def __init__(self, dev, devdata):
        print "devdata=", devdata
        self.devdata = devdata
        self.name = self.devdata[BTNAME]
        if dev.addr not in devicenames:
            devicenames[dev.addr] = args["name"] + chr(48+len(devicenames)+1)
        self.friendlyname = devicenames[dev.addr]
        self.addr = dev.addr
        self.addrType = dev.addrType
        self.rssi = dev.rssi
        self.report("status", "found")
        print "created _paireddevice"

    def unpair(self):
        print "unpairing", self
        self.running = False
        for thread in self.threads:
            thread.join()
        pass

    def _sensorlookup(self, sensorname):
        if not hasattr(self.tag, sensorname):
            print "not found", sensorname
            return None
        return getattr(self.tag, sensorname)

    def start(self, f, m, s):
        """
        f,m,s are list of sensor names to run at FAST, MEDIUM and SLOW read rates
        """
        print "starting", f, m, s
        self.running = True
        self.threads = []
        for sensors, interval in zip([f, m, s], [FAST, MEDIUM, SLOW]):
            if sensors:
                self.threads.append(threading.Thread(
                    target=self.runner, args=(sensors, interval)))
                self.threads[-1].daemon = True
                self.threads[-1].start()

    def runinit(self, sensors):
        print "initializing for run", sensors
        return False

    def runread(self, sensors):
        print('Doing something important in the background', self, sensors)
        return False

    def runner(self, sensors, interval):
        """ Method that runs forever """
        if not self.runinit(sensors):
            return
        while self.running:
            if not self.runread(sensors):
                break
            time.sleep(interval)
        print "Aborting"

    def report(self, tag, value=None):
        reading = ''
        if is_float(value):
            reading = '{"deviceuid":"'+self.addr+'","devicename":"' + \
                self.friendlyname+'","'+tag+'":'+str(value)+'}'
        else:
            if not isinstance(value, basestring):
                reading = '{"deviceuid":"'+self.addr+'","devicename":"'+self.friendlyname + \
                    '","'+tag+'":' + \
                    "["+",".join([str(x) for x in value])+"]"+'}'
            else:
                reading = '{"deviceuid":"'+self.addr+'","devicename":"' + \
                    self.friendlyname+'","'+tag+'":"'+str(value)+'"}'

        UDP_IP = args["ip"]

        UDP_Port = args["port"] #5005

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP

        print "Sending Data to ", UDP_IP + " : " + str(UDP_Port)

        sock.sendto(reading, (UDP_IP, UDP_Port))

        sys.stdout.flush()

class _SensorTag(_paireddevice):
    def __init__(self, dev, devdata):
        print "creating _SensorTag"
        self.tag = bluepy.sensortag.SensorTag(dev.addr)
        _paireddevice.__init__(self, dev, devdata)
        self.devicetype = "SensorTag generic"
        print "created _SensorTag"
        return True

    def runinit(self, sensors):
        print "_Sensortag runinit", sensors
        self.report("status", "enabled "+repr(sensors))
        for sensor in sensors:
            print "enabling", sensor
            tagfn = self._sensorlookup(sensor)
            if tagfn:
                tagfn.enable()
#        time.sleep( 1.0 )
        return True

    def runread(self, sensors):
        try:
            for sensor in sensors:
                tagfn = self._sensorlookup(sensor)
                if tagfn:
                    self.report(sensor, tagfn.read())
        except bluepy.btle.BTLEException:
            self.report("status", "lost")
            return False
        return True

class _ST2650(_SensorTag):
    def __init__(self, dev, devdata):
        print "creating _ST2650"
        _SensorTag.__init__(self, dev, devdata)
        self.devicetype = "Sensortag CC2650"
        self.report("status", "started")
        print "created _ST2650"

class _ST(_SensorTag):
    def __init__(self, dev, devdata):
        print "creating _ST"
        _SensorTag.__init__(self, dev, devdata)
        self.devicetype = "Sensortag CC2540"
        self.report("status", "started")
        print "created _ST"



def paireddevicefactory(dev):
    devdata = {}
    for (adtype, desc, value) in dev.getScanData():
        devdata[desc] = value
    if BTNAME not in devdata.keys():
        devdata[BTNAME] = 'Unknown!'
    print "Found", devdata[BTNAME]
    if devdata[BTNAME] == 'SensorTag':
        return _ST(dev, devdata)
    elif devdata[BTNAME] == 'CC2650 SensorTag':
        return _ST2650(dev, devdata)
    return None


class ScanDelegate(bluepy.btle.DefaultDelegate):
    def __init__(self):
        os.system('sudo hciconfig hci0 reset')
        bluepy.btle.DefaultDelegate.__init__(self)
        self.activedevlist = []

    def handleDiscovery(self, dev, isNewDev, isNewData):
        global args
        if isNewDev:
            print "found", dev.addr
            #print "only", dev.addr, devicenames
            if dev.addr not in devicenames:
                # ignore it!
                #print "ignoring only", dev.addr
                return
            if len(self.activedevlist) < MAXDEVICES:
                thisdev = paireddevicefactory(dev)
                print "thisdev=", thisdev
                if thisdev:
                    self.activedevlist.append(thisdev)
                    thisdev.start(args["fast"], args["medium"], args["slow"])
                print "activedevlist=", self.activedevlist
            else:
                print "TOO MANY DEVICES - IGNORED", dev.addr
        elif isNewData:
            print "Received new data from", dev.addr
            pass

    def shutdown(self):
        print "My activedevlist=", self.activedevlist
        for dev in self.activedevlist:
            print "dev=", dev
            dev.unpair()

def loadConfig():
    with open('config.json') as config_file:
        config = json.load(config_file)
        return config

args = loadConfig() 

if not args["name"]:
    args["name"] = "ST-"

if not args["fast"]:
    args["fast"] = ['IRtemperature', 'gyroscope']

if not args["medium"]:
    args["medium"] = []

if not args["slow"]:
    args["slow"] = []

print args["fast"]
print args["medium"]
print args["slow"]

if args["devices"]:
    devicenames = {}
    for dev in args["devices"]:
        (uid, devname) = dev.split("=", 2)
        if not uid or not devname:
            print "could not split device", dev
            burp
        devicenames[uid.lower()] = devname

print "specified devices:", devicenames

scandelegate = ScanDelegate()
scanner = bluepy.btle.Scanner().withDelegate(scandelegate)

try:
    while True:
        try:
            devices = scanner.scan(timeout=30.0)
        except bluepy.btle.BTLEException:
            print "Aargh BTLE execption. Not panicing. Carrying on."
except KeyboardInterrupt:
    pass

print "finishing"

scandelegate.shutdown()

print "finished"
