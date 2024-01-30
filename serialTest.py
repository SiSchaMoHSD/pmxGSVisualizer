import serial
import json
import time
import sys
from GracefulExiter import GracefulExiter

# get user input string "ON" or "OFF"
# input_str = input("Enter ON or OFF: ")

n = 0
ser = serial.Serial('COM3', 115200, timeout=1)
time.sleep(2)

def send_command(command):
    data = {"command": command}
    ser.write(json.dumps(data).encode('utf-8'))
    time.sleep(1)

flag = GracefulExiter()

starttime = time.time()

while True:
    if ser.in_waiting > 0 and ser.read() == b'<':
        line = ser.readline().decode().strip()
        try:
            data = json.loads(line)
            print(f"Temperature: {data['temperature']}, Humidity: {data['humidity']}, Pressure: {data['pressure']}")
        except json.decoder.JSONDecodeError:
            print("JSONDecodeError")
            print(f"Couldn't decode line: {line}")

    if (time.time() - starttime) > 5:
        if n % 2 == 0:
            send_command("ON")
        else:
            send_command("OFF")
        n += 1
        starttime = time.time()

    if flag.exit():
        ser.close()
        sys.exit()

