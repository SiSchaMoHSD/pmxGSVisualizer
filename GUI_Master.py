import tkinter as tk
import customtkinter

class RootGUI:
    def __init__(self):
        self.root = customtkinter.CTk()
        self.root.title("PMX Live Visualizer")
        self.root.geometry("1200x600")


class ComGui():
    def __init__(self, root):
        self.root = root
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
        coms = ["-", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9"]
        self.clicked_com = customtkinter.StringVar()
        self.clicked_com.set(coms[0])
        self.drop_com = customtkinter.CTkOptionMenu(
            self.frame, values=coms, variable=self.clicked_com, command=self.connect_ctrl
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

    def com_refresh(self):
        print("Refresh COM Ports")

    def serial_connect(self):
        print("Connect to Serial Port")

if __name__ == "__main__":
    RootGUI()
    ComGui()