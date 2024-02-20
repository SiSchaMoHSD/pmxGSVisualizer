import json
import threading
import time
import numpy as np

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

        self.FunctionMaster = [
            "RawData",
            "Voltage"
        ]
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

    
if __name__ == "__main__":
    DataMaster()