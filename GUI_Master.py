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
        self.label_com = customtkinter.CTkLabel(self.frame, text="Available COM Port(s)", width=15, anchor="w")
        self.label_bd = customtkinter.CTkLabel(self.frame, text="Baud Rate: ", width=15, anchor="w")
        self.publish()
    def publish(self):
        self.frame.grid(row=0,column=0, rowspan=3, columnspan=3, padx=5, pady=5)
        self.label_com.grid(column=1, row=2)
        self.label_bd.grid(column=1, row=3)

if __name__ == "__main__":
    RootGUI()
    ComGui()