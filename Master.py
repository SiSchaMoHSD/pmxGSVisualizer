from GUI_Master import RootGUI, ComGui
from Serial_Com_ctrl import SerialCtrl

MySerial = SerialCtrl()
RootMaster = RootGUI()

ComMaster = ComGui(RootMaster.root, MySerial)

RootMaster.root.mainloop()