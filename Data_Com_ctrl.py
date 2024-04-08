from genericpath import exists
import json
import threading
import time
import numpy as np
from scipy.signal import savgol_filter
from scipy import signal
from datetime import datetime, timedelta
import os
import csv
import xml.etree.ElementTree as ET
from collections import deque
from simplekml import Kml, Snippet, Types, AltitudeMode, RefreshMode
import subprocess

class DataMaster():
    def __init__(self):
        self.serData_lock = threading.Lock()
        self.sync = "sync"
        self.sync_ok = "!"
        self.StartStream = "start"
        self.StopStream = "stop"
        self.SyncChannel = 0
        self.msg = json.loads('{}')
        self.lastEpoch = 0
        self.lastEpochKML = 0
        self.Channels = []

        self.XData = []
        self.YData = []

        self.FunctionMaster = {
            "RawData": self.RawData,
            "Voltage(12bit)": self.VoltData,
            "SavgolFilter": self.SavgolFilter,
            "DigitalFilter": self.DigitalFilter
        }
        self.DisplayTimeRange = 5

        self.ChannelColor = [
            "blue",
            "red",
            "green",
            "orange",
            "purple",
            "black",
            "pink",
            "brown",
            "cyan",
            "magenta"
        ]

        # kml
        ET.register_namespace('', 'http://www.opengis.net/kml/2.2')
        ET.register_namespace('gx', 'http://www.google.com/kml/ext/2.2')
        self.namespaces = {'': 'http://www.opengis.net/kml/2.2', 'gx': 'http://www.google.com/kml/ext/2.2'}

        #self.legend = {}

    def FileNameFunc(self):
        now = datetime.now()
        # ISO 8601 format
        self.filename = now.strftime("%Y-%m-%dT%H-%M-%S") + ".csv"
        self.netkmlFilename = now.strftime("%Y-%m-%d-netlink") + ".kml"
        self.kmlFilename = now.strftime("%Y-%m-%d-data") + ".kml"

    def SaveData(self, gui):
        exists = os.path.isfile(self.filename)
        if gui.save:
            with open(self.filename, mode='a', newline='') as file:
                writer = csv.writer(file)
                if not exists:
                    # write header row
                    writer.writerow(self.Channels)
                # write row with values from the json msg
                if self.lastEpoch != self.msg['time']:
                    writer.writerow([self.msg[ch] for ch in self.Channels])
                    self.lastEpoch = self.msg['time']

    def createKML(self, gui):
        if 'lng' not in self.msg.keys() or 'lat' not in self.msg.keys():
            gui.updateKML = False
            gui.noGPSWarning()
            return
        else:
            if not os.path.isfile('./kml/' + self.kmlFilename):
                kml = Kml(name="Tracks", open=1)
                doc = kml.newdocument(name='UMT Drone Track', snippet=Snippet("Created on " + datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')))
                # convert unix time in '%Y-%m-%dT%H:%M:%SZ' format
                GETimeFromEpoch = datetime.fromtimestamp(float(self.msg['time'])).strftime('%Y-%m-%dT%H:%M:%SZ')
                doc.lookat.gxtimespan.begin = GETimeFromEpoch
                doc.lookat.gxtimespan.end = (datetime.fromtimestamp(float(self.msg['time'])) + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
                doc.lookat.longitude = self.msg['lng']
                doc.lookat.latitude = self.msg['lat']
                doc.lookat.range = 1300.000000
                # Create a folder
                # fol = doc.newfolder(name='Track')
                # Create a schema for extended data: sensor values
                schema = kml.newschema()
                for ch in self.Channels:
                    if ch == 'lng' or ch == 'lat':
                        continue
                    schema.newgxsimplearrayfield(name=ch, type=Types.float, displayname=ch)
                # Create a new track
                trk = doc.newgxtrack(name="UMT Drone")
                trk.altitudemode = AltitudeMode.absolute
                # apply the above schema to the track
                trk.extendeddata.schemadata.schemaurl = schema.id
                # add all info for the first point
                trk.newwhen(GETimeFromEpoch)
                trk.newgxcoord([(float(self.msg['lng']), float(self.msg['lat']), float(self.msg['alt']))])
                # add extended data with newgxsimplearraydata
                for ch in self.Channels:
                    if ch == 'lng' or ch == 'lat':
                        continue
                    trk.extendeddata.schemadata.newgxsimplearraydata(ch, [float(self.msg[ch])])
                # styling
                trk.stylemap.normalstyle.iconstyle.icon.href = '../assets/drone.png'
                trk.stylemap.normalstyle.linestyle.color = '99ffac59'
                trk.stylemap.normalstyle.linestyle.width = 6
                trk.stylemap.highlightstyle.iconstyle.icon.href = '../assets/droneHL.png'
                trk.stylemap.highlightstyle.iconstyle.scale = 1.2
                trk.stylemap.highlightstyle.linestyle.color = '99ffac59'
                trk.stylemap.highlightstyle.linestyle.width = 8
                # save the kml to file
                kml.save('./kml/' + self.kmlFilename)

            # check if netlink kml file exists
            if not os.path.isfile('./kml/' + self.netkmlFilename):
                #crete netlink kml file
                netkml = Kml()
                netlink = netkml.newnetworklink(name='UMT Drone Track Update')
                netlink.refreshvisibility = 0
                netlink.gxballoonvisibility = 1
                netlink.link.href = self.kmlFilename
                netlink.link.refreshmode = RefreshMode.oninterval
                netlink.link.refreshinterval = 2
                netkml.save('./kml/' + self.netkmlFilename)
            
            # open GE
            if os.path.isfile('./kml/' + self.netkmlFilename):
                subprocess.run(['start', './kml/' + self.netkmlFilename], shell=True)
            gui.updateKML = True

    def updateKML(self, gui):
        if gui.updateKML:
            if 'lng' not in self.msg.keys() or 'lat' not in self.msg.keys():
                gui.updateKML = False
                gui.noGPSWarning()
                return
            if self.lastEpochKML != self.msg['time']:
                print(self.kmlFilename)
                # open the kml file
                tree = ET.parse('./kml/' + self.kmlFilename)
                root = tree.getroot()
                # find the <gx:Track> tag
                track = root.find('.//gx:Track', self.namespaces)
                if track is None:
                    print('No <gx:Track> tag found in the KML file')
                    return
                # find last <when> and <gx:coord> tags
                last_when = [e for e in track if e.tag == '{http://www.opengis.net/kml/2.2}when'][-1]
                last_coord = [e for e in track if e.tag == '{http://www.google.com/kml/ext/2.2}coord'][-1]
                # get the indices of the last <when> and <gx:coord> elements
                last_when_index = list(track).index(last_when)
                last_coord_index = list(track).index(last_coord)
                # create new <when> and <gx:coord> elements
                new_when = ET.Element('{http://www.opengis.net/kml/2.2}when')
                new_coord = ET.Element('{http://www.google.com/kml/ext/2.2}coord')
                # set the text of the new elements
                GETimeFromEpoch = datetime.fromtimestamp(float(self.msg['time'])).strftime('%Y-%m-%dT%H:%M:%SZ')
                new_when.text = GETimeFromEpoch
                new_coord.text = '{} {} {}'.format(self.msg['lng'], self.msg['lat'], self.msg['alt'])
                # insert the new elements at the correct positions
                track.insert(last_when_index + 1, new_when)
                track.insert(last_coord_index + 2, new_coord) # Add 1 to the index
                # find the <gx:SimpleArrayData> tag with the with the corresponding channel names
                for ch in self.Channels:
                    if ch == 'lng' or ch == 'lat':
                        continue
                    simple_array_data = root.find('.//ExtendedData/SchemaData/gx:SimpleArrayData[@name="' + ch + '"]', self.namespaces)
                    if simple_array_data is None:
                        print('No <gx:SimpleArrayData> tag with name "' + ch + '" found in the KML file')
                        return
                    # create a new <gx:value> elements for each channel
                    new_value = ET.Element('{http://www.google.com/kml/ext/2.2}value')
                    new_value.text = str(self.msg[ch])
                    # append the new <gx:value> element to the <gx:SimpleArrayData> element
                    simple_array_data.append(new_value)
                # write the changes back to the KML file in UTF-8 encoding
                tree.write('./kml/' + self.kmlFilename, encoding='utf-8', xml_declaration=True)
                self.lastEpochKML = self.msg['time']


    def DecodeMsg(self):
        temp = self.RawMsg.decode('utf-8').strip()
        if len(temp) > 0:
            if "{" in temp:
                try:
                    self.msg = json.loads(temp)
                    self.jsonDecoding = True
                except Exception as e:
                    self.jsonDecoding = False
                    print(e)
                # print(f"Temperature: {self.msg['temperature']}, Humidity: {self.msg['humidity']}, Pressure: {self.msg['pressure']}")
                # print("Number of data points: ", len(self.msg))
    
    # Encode the command to be sent to the serial port
    def encode_command(self, command):
        data = {"command": command}
        serialdata = json.dumps(data).encode('utf-8') + b'\n'
        return serialdata
    
    def GenChannels(self):
        self.Channels = [f"{ch}" for ch in self.msg.keys()]
        # generate legend dictionary
        #for i in range(len(self.Channels)):
        #    self.legend[self.Channels[i]] = self.ChannelColor[i]

    def buildYdata(self):
        for _ in range(self.SyncChannel):
            self.YData.append([])

    def ClearData(self):
        self.RawMsg = ""
        self.msg = json.loads('{}')
        self.YData = []

    def StreamDataCheck(self):
        self.StreamData = False
        if self.SyncChannel == len(self.msg):
            if self.jsonDecoding:
                self.StreamData = True

    def SetRefTime(self):
        if len(self.XData) == 0:
            self.RefTime = time.perf_counter()
        else:
            self.RefTime = time.perf_counter() - self.XData[len(self.XData) - 1]
    

    def UpdateXdata(self):
        if len(self.XData) == 0:
            self.XData.append(0)
        else:
            self.XData.append(time.perf_counter() - self.RefTime)

    def UpdateYdata(self):
        for ch in range(self.SyncChannel):
            self.YData[ch].append(self.msg[self.Channels[ch]])

    
    def AdjustData(self):
        lenXdata = len(self.XData)
        if (self.XData[lenXdata -1] - self.XData[0]) > self.DisplayTimeRange:
            del self.XData[0]
            for ydata in self.YData:
                del ydata[0]
        x = np.array(self.XData)
        self.XDisplay = np.linspace(x.min(), x.max(), len(x), endpoint=0)
        self.YDisplay = np.array(self.YData)

    def RawData(self, gui):
        gui.chart.plot(gui.x, gui.y, color=gui.color, dash_capstyle='projecting', linewidth=1)

    def VoltData(self, gui):
        gui.chart.plot(gui.x, (gui.y/4096)*3.3, color=gui.color, dash_capstyle='projecting', linewidth=1)

    def SavgolFilter(self, gui):
        x = gui.x
        y = gui.y
        w = savgol_filter(y, 5, 2)
        gui.chart.plot(x, w, color="#1cbda5", dash_capstyle='projecting', linewidth=2)
    
    def DigitalFilter(self, gui):
        x = gui.x
        y = gui.y
        b, a = signal.ellip(4, 0.01, 120, 0.125)
        fgust = signal.filtfilt(b, a, y, method="gust")
        gui.chart.plot(x, fgust, color="#db2775", dash_capstyle='projecting', linewidth=2)

    
if __name__ == "__main__":
    DataMaster()