from GUI_Master import RootGUI, ComGui
from Serial_Com_ctrl import SerialCtrl
from Data_Com_ctrl import DataMaster

# Initiate the Root class that will manage the other classes
MySerial = SerialCtrl()
MyData = DataMaster()
RootMaster = RootGUI()

# Initiate the Communication Master class that will manage all the GUI classes
ComMaster = ComGui(RootMaster.root, MySerial, MyData)

# Start the GUI
RootMaster.root.mainloop()