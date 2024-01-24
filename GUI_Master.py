from CTkMessagebox import CTkMessagebox
import customtkinter
import tkinter
from tkinter import ttk

class RootGUI:
    def __init__(self):
        self.root = customtkinter.CTk()
        self.root.title("PMX Live Visualizer")
        self.root.geometry("1200x600")


class ComGui():
    def __init__(self, root, serial):
        # initialize widgets
        self.root = root
        self.serial = serial
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
            self.serial.SerialOpen(self)
            if self.serial.ser.status:
                self.btn_connect.configure(text="Disconnect")
                self.btn_refresh.configure(state="disabled")
                self.drop_com.configure(state="disabled")
                self.drop_baud.configure(state="disabled")
                InfoMsg = f"Connection established to {self.clicked_com.get()}"
                CTkMessagebox(title="Connection Established", message=InfoMsg, icon="check")
                self.conn = ConnGUI(self.root, self.serial)
            else:
                ErrorMsg = f"Failure to establish connection to {self.clicked_com.get()}"
                CTkMessagebox(title="Connection Error", message=ErrorMsg, icon="cancel")
        else:
            self.conn.ConnGUIClose()
            # start closing serial port
            self.serial.SerialClose()
            self.btn_connect.configure(text="Connect")
            self.btn_refresh.configure(state="normal")
            self.drop_com.configure(state="normal")
            self.drop_baud.configure(state="normal")

class ConnGUI():
    def __init__(self, root, serial):
        self.root = root
        self.serial = serial
        self.frame = tkinter.LabelFrame(
            root, text="Connection Manager", padx=5, pady=5, bg="#2b2b2b", fg="white", width=60
            )
        self.sync_label = customtkinter.CTkLabel(
            self.frame, text="Sync Status: ", width=15, anchor="w"
        )
        self.sync_status = customtkinter.CTkLabel(
            self.frame, text="...Sync...", fg_color="#ff4a00", width=5
        )
        self.ch_label = customtkinter.CTkLabel(
            self.frame, text="Active Channels: ", width=15, anchor="w"
        )
        self.ch_status = customtkinter.CTkLabel(
            self.frame, text="...", fg_color="#ff4a00", width=46
        )
        self.btn_start_stream = customtkinter.CTkButton(
            self.frame, text="Start", state="disabled", width=15, command=self.start_stream
        )
        self.btn_stop_stream = customtkinter.CTkButton(
            self.frame, text="Stop", state="disabled", width=15, command=self.stop_stream
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
        pass
    def stop_stream(self):
        pass
    def new_chart(self):
        pass
    def kill_chart(self):
        pass
    def save_data(self):
        pass


if __name__ == "__main__":
    RootGUI()
    ComGui()
    ConnGUI()