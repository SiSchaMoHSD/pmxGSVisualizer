import json
import threading

class DataMaster():
    def __init__(self):
        self.serData_lock = threading.Lock()
        self.sync = "sync"
        self.sync_ok = "!"
        self.StartStream = "#A#\n"
        self.StopStream = "#S#\n"
        self.SyncChannel = 0
        self.msg = json.loads('{}')

        self.XData = []
        self.YData = []

        self.FunctionMaster = [
            "RawData",
            "Voltage"
        ]

    def DecodeMsg(self):
        temp = self.RawMsg.decode('utf-8').strip()
        if len(temp) > 0:
            if "{" in temp:
                self.msg = json.loads(temp)
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
    
if __name__ == "__main__":
    DataMaster()