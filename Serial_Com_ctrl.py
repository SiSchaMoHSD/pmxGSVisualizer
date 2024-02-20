import serial.tools.list_ports
import time


# secure the UART serial communication with the MCU
class SerialCtrl():
    def __init__(self):
        self.com_list = []
        self.sync_cnt = 200

    def getCOMList(self):
        ports = serial.tools.list_ports.comports()
        self.com_list = [com[0] for com in ports]
        self.com_list.insert(0, "-")

    def SerialOpen(self, gui):
        try:
            self.ser.is_open
        except:
            PORT = gui.clicked_com.get()
            BAUD = gui.clicked_bd.get()
            self.ser = serial.Serial()
            self.ser.baudrate = BAUD
            self.ser.port = PORT
            self.ser.timeout = 0.1

        try:
            if self.ser.is_open:
                self.ser.status = True
            else:
                PORT = gui.clicked_com.get()
                BAUD = gui.clicked_bd.get()
                self.ser = serial.Serial()
                self.ser.baudrate = BAUD
                self.ser.port = PORT
                self.ser.timeout = 0.1
                self.ser.open()
                self.ser.status = True
        except:
            self.ser.status = False

    def SerialClose(self):
        try:
            if self.ser.is_open:
                self.ser.close()
                self.ser.status = False
        except:
            self.ser.status = False

    def SerialSync(self, gui):
        self.threading = True
        cnt=0
        while self.threading:
            with gui.data.serData_lock:
                try:
                    self.ser.write(gui.data.encode_command(gui.data.sync))
                    gui.conn.sync_status.configure(text="..Sync..")
                    gui.conn.sync_status.configure(fg_color="orange")
                    gui.data.RawMsg = self.ser.readline()
                    # print(f"RawMsg: {gui.data.RawMsg}")
                    gui.data.DecodeMsg()
                    if gui.data.msg['syncStatus'] == gui.data.sync_ok:
                        gui.data.msg.pop('syncStatus', None)
                        if len(gui.data.msg) > 0:
                            gui.conn.btn_start_stream.configure(state="normal")
                            gui.conn.btn_add_chart.configure(state="normal")
                            gui.conn.btn_kill_chart.configure(state="normal")
                            gui.conn.save_check.configure(state="normal")
                            gui.conn.sync_status.configure(text="OK")
                            gui.conn.sync_status.configure(fg_color="green")
                            gui.conn.ch_status.configure(text=len(gui.data.msg))
                            gui.conn.ch_status.configure(fg_color="green")
                            gui.data.SyncChannel = len(gui.data.msg)
                            gui.data.GenChannels()
                            gui.data.buildYdata()
                            print(gui.data.Channels, gui.data.YData) 
                            self.threading = False
                            break
                    if self.threading == False:
                        break
                except Exception as e:
                    print(e)
                cnt += 1
                if self.threading == False:
                    break

                if cnt > self.sync_cnt:
                    cnt = 0
                    gui.conn.sync_status.configure(text="failed")
                    gui.conn.sync_status.configure(fg_color="red")
                    time.sleep(0.5)
                    if self.threading == False:
                        break

    def SerialDataStream(self, gui):
        self.threading = True

        while self.threading:
            with gui.data.serData_lock:
                try:
                    self.ser.write(gui.data.encode_command(gui.data.StartStream))
                    gui.data.RawMsg = self.ser.readline()
                    gui.data.DecodeMsg()
                    gui.data.StreamDataCheck()
                    if gui.data.StreamData:
                        gui.data.SetRefTime()
                        break
                except Exception as e:
                    print(e)

        while self.threading:
            with gui.data.serData_lock:
                try:
                    gui.data.RawMsg = self.ser.readline()
                    gui.data.DecodeMsg()
                    gui.data.StreamDataCheck()
                    if gui.data.StreamData:
                        gui.data.UpdateXdata()
                        gui.data.UpdateYdata()
                        gui.data.AdjustData()
                        print(f"Xdata: {len(gui.data.XData)}, Ydata: {len(gui.data.YData[0])}")
                except Exception as e:
                    print(e)


if __name__ == "__main__":
    SerialCtrl()