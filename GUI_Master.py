from CTkMessagebox import CTkMessagebox
import customtkinter
import tkinter
from tkinter import ttk
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from functools import partial

class RootGUI:
    def __init__(self, serial, data):
        self.root = customtkinter.CTk()
        self.root.title("PMX Live Visualizer")
        self.root.geometry("1200x600")
        self.serial = serial
        self.data = data

        self.root.protocol("WM_DELETE_WINDOW", self.close_window)

    def close_window(self):
        print("Closing the window and exiting the program...")
        self.root.destroy()
        self.serial.SerialClose()
        self.serial.threading = False


class ComGui():
    def __init__(self, root, serial, data):
        # initialize widgets
        self.root = root
        self.serial = serial
        self.data = data
        self.frame = customtkinter.CTkFrame(root, width=140, corner_radius=0)
        self.label_com = customtkinter.CTkLabel(self.frame, text="Available COM Port(s):", width=15, anchor="w")
        self.label_bd = customtkinter.CTkLabel(self.frame, text="Baud Rate: ", width=15, anchor="w")
        self.ComOptionMenu()
        self.BaudOptionMenu()

        self.btn_refresh = customtkinter.CTkButton(
            self.frame, text="Refresh", width=15, command=self.com_refresh
            )
        self.btn_connect = customtkinter.CTkButton(
            self.frame, text="Connect", width=15, state="disabled", command=self.serial_connect
            )

        self.publish()

    def ComOptionMenu(self):
        # generate list of available COM ports
        self.serial.getCOMList()
        self.clicked_com = customtkinter.StringVar()
        self.clicked_com.set(self.serial.com_list[0])
        self.drop_com = customtkinter.CTkOptionMenu(
            self.frame, values=self.serial.com_list, variable=self.clicked_com, command=self.connect_ctrl
            )
        self.drop_com.configure(width=15)

    def BaudOptionMenu(self):
        self.clicked_bd = customtkinter.StringVar()
        bds = [
            "-", "9600", "14400", "19200", "28800", "38400", "56000", "57600", "115200", "128000", "256000"
        ]
        self.clicked_bd.set(bds[0])
        self.drop_baud = customtkinter.CTkOptionMenu(
            self.frame, values=bds, variable=self.clicked_bd, command=self.connect_ctrl
            )
        self.drop_baud.configure(width=15)

    def publish(self):
        self.frame.grid(row=0,column=0, rowspan=3, columnspan=3, padx=5, pady=5)
        self.label_com.grid(column=1, row=2)
        self.drop_com.grid(column=2, row=2, padx=10, pady=5)
        self.label_bd.grid(column=1, row=3)
        self.drop_baud.grid(column=2, row=3, padx=10, pady=5)
        self.btn_refresh.grid(column=3, row=2)
        self.btn_connect.grid(column=3, row=3)

    def connect_ctrl(self, event=None):
        print("Connect Control")
        if "-" not in self.clicked_com.get() and "-" not in self.clicked_bd.get():
            self.btn_connect.configure(state="normal")
        else:
            self.btn_connect.configure(state="disabled")

    def com_refresh(self):
        self.drop_com.destroy()
        self.ComOptionMenu()
        self.drop_com.grid(column=2, row=2, padx=10, pady=5)
        logic = []
        self.connect_ctrl(logic)

    def serial_connect(self):
        if self.btn_connect.cget("text") == "Connect":
            # start the serial communication
            self.serial.SerialOpen(self)
            
            # if connection is established move on
            if self.serial.ser.status:
                # Update the COM manager
                self.btn_connect.configure(text="Disconnect")
                self.btn_refresh.configure(state="disabled")
                self.drop_com.configure(state="disabled")
                self.drop_baud.configure(state="disabled")
                InfoMsg = f"Connection established to {self.clicked_com.get()}"
                CTkMessagebox(title="Connection Established", message=InfoMsg, icon="check")
                # Display the Channel Manager
                self.conn = ConnGUI(self.root, self.serial, self.data)

                self.serial.t1 = threading.Thread(
                    target=self.serial.SerialSync, args=(self,), daemon=True
                )
                self.serial.t1.start()
            else:
                ErrorMsg = f"Failure to establish connection to {self.clicked_com.get()}"
                CTkMessagebox(title="Connection Error", message=ErrorMsg, icon="cancel")
        else:
            self.serial.threading = False
            # Closing the Serial COM
            # Close the Serial communication
            self.serial.SerialClose()
            # Closing the Conn Manager
            # Destroy the channel manager
            self.conn.ConnGUIClose()
            self.data.ClearData()
            
            self.btn_connect.configure(text="Connect")
            self.btn_refresh.configure(state="normal")
            self.drop_com.configure(state="normal")
            self.drop_baud.configure(state="normal")

class ConnGUI():
    def __init__(self, root, serial, data):
        self.root = root
        self.serial = serial
        self.data = data
        self.frame = tkinter.LabelFrame(
            root, text="Connection Manager", padx=5, pady=5, bg="#2b2b2b", fg="white", width=60
            )
        self.sync_label = customtkinter.CTkLabel(
            self.frame, text="Sync Status: ", width=15, anchor="w"
        )
        self.sync_status = customtkinter.CTkLabel(
            self.frame, text="...Sync...", fg_color="#ff4a00", width=46
        )
        self.ch_label = customtkinter.CTkLabel(
            self.frame, text="Active Channels: ", width=15, anchor="w"
        )
        self.ch_status = customtkinter.CTkLabel(
            self.frame, text="...", fg_color="#ff4a00", width=46
        )
        self.btn_start_stream = customtkinter.CTkButton(
            self.frame, text="Start", state="disabled", width=50, command=self.start_stream
        )
        self.btn_stop_stream = customtkinter.CTkButton(
            self.frame, text="Stop", state="disabled", width=50, command=self.stop_stream
        )

        self.btn_add_chart = customtkinter.CTkButton(
            self.frame, text="+", state="disabled", width=40, fg_color="#098577", command=self.new_chart
        )
        self.btn_kill_chart = customtkinter.CTkButton(
            self.frame, text="-", state="disabled", width=40, fg_color="#CC252C", command=self.kill_chart
        )

        self.save = False
        self.SaveVar = tkinter.IntVar()
        self.save_check = customtkinter.CTkCheckBox(
            self.frame, text="Save Data", variable=self.SaveVar, onvalue=1, offvalue=0, state="disabled", command=self.save_data
        )

        self.seperator = ttk.Separator(self.frame, orient="vertical")

        self.ConnGUIOpen()
        self.chartMaster = DisGUI(self.root,self.serial,self.data)


    def ConnGUIOpen(self):
        # self.root.geometry("800x120")
        self.frame.grid(row=0, column=4, rowspan=3, columnspan=5, padx=5, pady=5)
        self.sync_label.grid(column=1, row=1)
        self.sync_status.grid(column=2, row=1, padx= 5)
        self.ch_label.grid(column=1, row=2)
        self.ch_status.grid(column=2, row=2, padx=5, pady=5)
        self.btn_start_stream.grid(column=3, row=1, padx=5, pady=5)
        self.btn_stop_stream.grid(column=3, row=2, padx=5, pady=5)
        self.btn_add_chart.grid(column=4, row=1, padx=5, pady=5)
        self.btn_kill_chart.grid(column=5, row=1, padx=5, pady=5)

        self.save_check.grid(column=4, row=2, columnspan=2, padx=5, pady=5)

        self.seperator.place(relx=0.65, rely=0, relwidth=0.001, relheight=1)

    def ConnGUIClose(self):
        for widget in self.frame.winfo_children():
            widget.destroy()
        self.frame.destroy()

    def start_stream(self):
        self.btn_start_stream.configure(state="disabled")
        self.btn_stop_stream.configure(state="normal")

        self.serial.t1 = threading.Thread(target=self.serial.SerialDataStream, args=(self,), daemon=True)
        self.serial.t1.start()

    def stop_stream(self):
        self.btn_start_stream.configure(state="normal")
        self.btn_stop_stream.configure(state="disabled")
        self.serial.threading = False
        # own temporarly exit command ########################################################################
        try:
            self.serial.ser.write(self.data.encode_command(self.data.StopStream))
        except Exception as e:
            print(e)
        # own exit command ########################################################################

    def new_chart(self):
        self.chartMaster.AddChannelMaster()

    def kill_chart(self):
        try:
            if len(self.chartMaster.frames) > 0:
                totalFrames = len(self.chartMaster.frames)-1
                self.chartMaster.frames[totalFrames].destroy()
                self.chartMaster.frames.pop()
                self.chartMaster.figs.pop()
                self.chartMaster.controlFrames[totalFrames][0].destroy()
                self.chartMaster.controlFrames.pop()

                self.chartMaster.channelFrame[totalFrames][0].destroy()
                self.chartMaster.channelFrame.pop()

                self.chartMaster.viewVar.pop()
                self.chartMaster.optionVar.pop()
                self.chartMaster.funcVar.pop()
                self.chartMaster.AdjustRootFrame()
        except:
            pass

    def save_data(self):
        pass

class DisGUI():
    def __init__(self, root, serial, data):
        self.root = root
        self.serial = serial
        self.data = data

        self.frames = []
        self.framesCol = 0
        self.framesRow = 4
        self.totalFrames = 0

        self.figs = []

        self.controlFrames = []

        # adding new data channels
        self.channelFrame = []
        self.viewVar = []
        self.optionVar = []
        self.funcVar = []
    
    def AddChannelMaster(self):
        self.AddMasterFrame()
        self.AdjustRootFrame()
        self.AddGraph()
        self.AddChannelFrame()
        self.AddBtnFrame()

    def AddMasterFrame(self):
        self.frames.append(customtkinter.CTkFrame(self.root))
        self.totalFrames = len(self.frames)-1

        if self.totalFrames % 2 == 0:
            self.framesCol = 0
        else:
            self.framesCol = 9
        
        self.framesRow = 4 + 4 * int(self.totalFrames / 2)
        self.frames[self.totalFrames].grid(padx=5, pady=5, column=self.framesCol, row=self.framesRow, columnspan=9, sticky="nw")

    
    def AdjustRootFrame(self):
        self.totalFrames = len(self.frames)-1
        if self.totalFrames > 0:
            RootW = 800 * 2
        else:
            RootW = 800
        if self.totalFrames+1 == 0:
            RootH = 120
        else:
            RootH = 120 + 430 * (int(self.totalFrames / 2)+1)

        self.root.geometry(f"{RootW}x{RootH}")

    def AddGraph(self):
        self.figs.append([])
        self.figs[self.totalFrames].append(plt.Figure(figsize=(7,5), dpi=80))
        self.figs[self.totalFrames].append(self.figs[self.totalFrames][0].add_subplot(111))
        self.figs[self.totalFrames].append(
            FigureCanvasTkAgg(self.figs[self.totalFrames][0], self.frames[self.totalFrames])
        )
        self.figs[self.totalFrames][2].get_tk_widget().grid(column=1, row=0, rowspan=17, columnspan=4, sticky="n")

    def AddBtnFrame(self):
        btnH = 8
        btnW = 30
        self.controlFrames.append([])
        self.controlFrames[self.totalFrames].append(
            customtkinter.CTkFrame(self.frames[self.totalFrames])
        )
        self.controlFrames[self.totalFrames][0].grid(
            column=0, row=0, padx=5, pady=5, sticky="n"
        )
        self.controlFrames[self.totalFrames].append(
            customtkinter.CTkButton(
                self.controlFrames[self.totalFrames][0], text="+", width=btnW, height=btnH,
                command=partial(self.AddChannel, self.channelFrame[self.totalFrames]))
        )
        self.controlFrames[self.totalFrames][1].grid(column=0, row=0, padx=5, pady=5)
        self.controlFrames[self.totalFrames].append(
            customtkinter.CTkButton(
                self.controlFrames[self.totalFrames][0], text="-", width=btnW, height=btnH,
                command=partial(self.DeleteChannel, self.channelFrame[self.totalFrames]))
        )
        self.controlFrames[self.totalFrames][2].grid(column=1, row=0, padx=5, pady=5)
    
    def AddChannelFrame(self):
        # method to add the channel frame
        self.channelFrame.append([])
        self.viewVar.append([])
        self.optionVar.append([])
        self.funcVar.append([])
        self.channelFrame[self.totalFrames].append(
            customtkinter.CTkFrame(self.frames[self.totalFrames])
        )

        self.channelFrame[self.totalFrames].append(self.totalFrames)

        self.channelFrame[self.totalFrames][0].grid(
            column=0, row=1, padx=5, pady=5, rowspan=16, sticky="n"
        )
        self.AddChannel(self.channelFrame[self.totalFrames])

    def AddChannel(self, channelFrame):
        # method that adds options & controls to the channel frame
        if len(channelFrame[0].winfo_children()) < 8:
            newFrameChannel = customtkinter.CTkFrame(channelFrame[0])

            newFrameChannel.grid(column=0, row=len(channelFrame[0].winfo_children())-1)
            self.viewVar[channelFrame[1]].append(customtkinter.IntVar())
            ch_btn = customtkinter.CTkCheckBox(newFrameChannel, text='', variable=self.viewVar[channelFrame[1]][len(self.viewVar[channelFrame[1]])-1],
                                               onvalue=1, offvalue=0)
            ch_btn.grid(column=0, row=0, padx=1)
            self.ChannelOption(newFrameChannel, channelFrame[1])
            self.ChannelFunc(newFrameChannel, channelFrame[1])

    def ChannelOption(self, frame, channelFrameNumber):
        self.optionVar[channelFrameNumber].append(customtkinter.StringVar())

        bds = self.data.Channels

        self.optionVar[channelFrameNumber][len(self.optionVar[channelFrameNumber])-1].set(bds[0])
        drop_ch = customtkinter.CTkOptionMenu(frame, values=bds, variable=self.optionVar[channelFrameNumber][len(self.optionVar[channelFrameNumber])-1])
        drop_ch.configure(width=15)
        drop_ch.grid(column=1, row=0, padx=1)

    def ChannelFunc(self, frame, channelFrameNumber):
        self.funcVar[channelFrameNumber].append(customtkinter.StringVar())

        bds = self.data.FunctionMaster

        self.funcVar[channelFrameNumber][len(self.optionVar[channelFrameNumber])-1].set(bds[0])
        drop_ch = customtkinter.CTkOptionMenu(frame, values=bds, variable=self.funcVar[channelFrameNumber][len(self.optionVar[channelFrameNumber])-1])
        drop_ch.configure(width=15)
        drop_ch.grid(column=2, row=0, padx=1)

    def DeleteChannel(self, channelFrame):
        if len(channelFrame[0].winfo_children()) > 1:
            channelFrame[0].winfo_children()[len(channelFrame[0].winfo_children())-1].destroy()
            self.viewVar[channelFrame[1]].pop()
            self.optionVar[channelFrame[1]].pop()
            self.funcVar[channelFrame[1]].pop()




if __name__ == "__main__":
    RootGUI()
    ComGui()
    ConnGUI()
    DisGUI()