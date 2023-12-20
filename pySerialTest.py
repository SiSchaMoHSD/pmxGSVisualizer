import serial
import struct

# open the serial port
ser = serial.Serial('COM7', 115200, timeout=1)

# Define the format of the struct
struct_format = '<9fH5B3d'

while True:
    # Read until we find a start marker
    while ser.read() != b'<':
        pass
    # Read the size of the struct
    struct_size = struct.calcsize(struct_format)

    # Read struct_size bytes from the serial port
    data = ser.read(struct_size)

    # Check for the end marker
    if ser.read() != b'>':
        # If we didn't find an end marker discard the data and continue
        continue

    if len(data) == struct_size:
        # If we received the correct amount of bytes, unpack them
        unpacked_data = struct.unpack(struct_format, data)

        # Now you can access the fields of the struct:
        pm1, pm25, pm10, sumBins, temp, altitude, hum, xtra, co2, year, month, day, hour, minute, second, lat, lng, heading = unpacked_data

        print(f'pm1: {pm25}', f'pm2.5: {pm25}', f'pm10: {pm10}, sumBins: {sumBins}, temp: {temp}, altitude: {altitude}, hum: {hum}, xtra: {xtra}, co2: {co2}, year: {year}, month: {month}, day: {day}, hour: {hour}, minute: {minute}, second: {second}, lat: {lat}, lng: {lng}', f'heading: {heading}')
