import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go
# import pandas as pd
import datetime
from time import sleep
from collections import deque
import serial
import struct
import threading
import credentials


# Open the serial port
ser = serial.Serial('COM7', 115200, timeout=1)
sleep(5)  # wait for COM port
# Define the format for the data structure
struct_format = '<9fH5B3d'
# Create a DataFrame to store the data
# df = pd.DataFrame(columns=['pm10', 'sumBins', 'temp', 'altitude', 'hum', 'xtra', 'co2', 'year', 'month', 'day', 'hour', 'minute', 'second', 'lat', 'lng'])

# create buffers for each value (FiFo)
buffer_size = 60*60  # 1 hour
buffers = {
    'pm1': deque(maxlen=buffer_size),
    'pm25': deque(maxlen=buffer_size),
    'pm10': deque(maxlen=buffer_size),
    'sumBins': deque(maxlen=buffer_size),
    'temp': deque(maxlen=buffer_size),
    'altitude': deque(maxlen=buffer_size),
    'hum': deque(maxlen=buffer_size),
    'xtra': deque(maxlen=buffer_size),
    'co2': deque(maxlen=buffer_size),
    'time': deque(maxlen=buffer_size),
    'lat': deque(maxlen=buffer_size),
    'lng': deque(maxlen=buffer_size)
}


# Create a lock for the buffers
buffer_lock = threading.Lock()


# Threaded function to read data from the serial port
def read_serial_data():
    while True:
        # Read until start marker
        while ser.read() != b'<':
            pass
        # Read the size of the struct
        struct_size = struct.calcsize(struct_format)
        # Read the data from the serial port
        data = ser.read(struct_size)
        # Check for the end marker
        if ser.read() != b'>':
            # If we didn't find the end marker, discard the data and continue
            continue
        if len(data) == struct_size:
            # If we received the correct amount of bytes, unpack the data
            unpacked_data = struct.unpack(struct_format, data)
            # fill buffers with data
            time = datetime.datetime.now()
            with buffer_lock:
                buffers['pm1'].append(unpacked_data[0])
                buffers['pm25'].append(unpacked_data[1])
                buffers['pm10'].append(unpacked_data[2])
                buffers['sumBins'].append(unpacked_data[3])
                buffers['temp'].append(unpacked_data[4])
                buffers['altitude'].append(unpacked_data[5])
                buffers['hum'].append(unpacked_data[6])
                buffers['xtra'].append(unpacked_data[7])
                buffers['co2'].append(unpacked_data[8])
                buffers['lat'].append(unpacked_data[15])
                buffers['lng'].append(unpacked_data[16])
                buffers['time'].append(time)


# Start the thread
serial_thread = threading.Thread(target=read_serial_data)
serial_thread.start()

# Initialize the app
app = dash.Dash(__name__)

# Layout of the app
app.layout = html.Div([
    dcc.Graph(id='live-update-graph'),
    dcc.Interval(
        id='interval-component',
        interval=1*1000,  # in milliseconds
        n_intervals=0
    ),
    dcc.RangeSlider(
        id='time-slider',
        min=0,
        max=60,
        step=1,
        marks={i: f'{-(i-60)} min' for i in range(60, -1, -5)},
        value=[0, 60]
    )
])


# Callback to update the graph
@app.callback(Output('live-update-graph', 'figure'),
              [Input('interval-component', 'n_intervals')],
              [State('time-slider', 'value')])
def update_graph(n_intervals, time_slider):
    # Get the latest data point
    current_time = datetime.datetime.now()
    
    # Create traces for each line
    traces = []
    for key in buffers.keys():
        traces.append(go.Scatter(
            x=list(buffers['time']),
            y=list(buffers[key]),
            mode='lines',
            name=key
        ))

    # Calculate x-axis range
    end_time = current_time - datetime.timedelta(minutes=60 - time_slider[1])
    start_time = current_time - datetime.timedelta(minutes=60 - time_slider[0])

    # Define layout
    layout = go.Layout(
        title='Live Update Graph',
        xaxis=dict(title='Time', range=[start_time, end_time]),
        yaxis=dict(title='Values'),
        showlegend=True,
        legend=dict(traceorder='reversed'),
        uirevision='legend'
    )


    return {'data': traces, 'layout': layout}


# Run the app
if __name__ == '__main__':
    app.run_server()