from genericpath import exists
import json
import threading
import time
import numpy as np
from scipy.signal import savgol_filter
from scipy import signal
from datetime import datetime
import os
import csv

class DataMaster():
    def __init__(self):
        self.serData_lock = threading.Lock()
        self.sync = "sync"
        self.sync_ok = "!"
        self.StartStream = "start"
        self.StopStream = "stop"
        self.SyncChannel = 0
        self.msg = json.loads('{}')

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

    def FileNameFunc(self):
        now = datetime.now()
        # ISO 8601 format
        self.filename = now.strftime("%Y-%m-%dT%H-%M-%S") + ".csv"

    def SaveData(self, gui):
        exists = os.path.isfile(self.filename)
        if gui.save:
            with open(self.filename, mode='a', newline='') as file:
                writer = csv.writer(file)
                if not exists:
                    # write header row
                    writer.writerow(self.Channels)
                # write row with values from the json msg
                writer.writerow([self.msg[ch] for ch in self.Channels])


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