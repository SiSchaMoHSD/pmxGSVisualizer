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


# Init the dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id='live-bar-chart', animate=True),
    dcc.Graph(id='time-series', animate=True),
    #dcc.Graph(id='live-map', animate=True),
    dcc.Interval(
        id='interval-component',
        interval=800, # in milliseconds
        n_intervals=0
    ),
    dcc.Dropdown(
        id='time-range',
        options=[
            {'label': '5min', 'value': 5},
            {'label': '15min', 'value': 15},
            # add other options here
        ],
        value=60
    ),
    dcc.Graph(id='live-map',
              config={'uirevision': True},
              figure={'data': [{'type': 'scattermapbox',
                                'lat': [],
                                'lon': [],
                                'mode': 'lines',
                                'line': dict(width=2, color='blue')}],
                      'layout': {
                          'autosize': True,
                          'uirevision': True,
                          'hovermode': 'closest',
                          'mapbox': {
                              'accesstoken': credentials.mapbox_token,
                              'bearing': 0,
                              'center': {'lat': buffers['lat'][-1], 'lon': buffers['lng'][-1]},
                              'pitch': 0,
                              'zoom': 10
                          }
                      }},
              animate=True)
])


@app.callback([Output('live-bar-chart', 'figure'),
              Output('time-series', 'figure')],
              [Input('time-range', 'value'),
              Input('interval-component', 'n_intervals')]
)
def update_graph_live(n, time_range):
    # update bar chart
    with buffer_lock:
        bar_chart = go.Figure(
            data=[
                go.Bar(
                    x=['pm10', 'sumBins', 'temp', 'altitude', 'hum', 'xtra', 'co2'],
                    y=[buffers['pm10'][-1], buffers['sumBins'][-1], buffers['temp'][-1], buffers['altitude'][-1], buffers['hum'][-1], buffers['xtra'][-1], buffers['co2'][-1]]
                )
            ]
        )

    # update time series
    with buffer_lock:
        time_series = go.Figure(
            data=[
                go.Scatter(
                    x=list(buffers['time'])[-time_range*60:], # get last 'time_range' minutes of data
                    y=list(buffers['pm10'])[-time_range*60:],
                    name='PM10'
                ),
                go.Scatter(
                    x=list(buffers['time'])[-time_range*60:], # get last 'time_range' minutes of data
                    y=list(buffers['sumBins'])[-time_range*60:],
                    name='sumBins'
                ),
                go.Scatter(
                    x=list(buffers['time'])[-time_range*60:],
                    y=list(buffers['temp'])[-time_range*60:],
                    name='Temperature'
                ),
                go.Scatter(
                    x=list(buffers['time'])[-time_range*60:],
                    y=list(buffers['altitude'])[-time_range*60:],
                    name='Altitude'
                ),
                go.Scatter(
                    x=list(buffers['time'])[-time_range*60:],
                    y=list(buffers['hum'])[-time_range*60:],
                    name='Humidity'
                ),
                go.Scatter(
                    x=list(buffers['time'])[-time_range*60:],
                    y=list(buffers['xtra'])[-time_range*60:],
                    name='Xtra'
                ),
                go.Scatter(
                    x=list(buffers['time'])[-time_range*60:],
                    y=list(buffers['co2'])[-time_range*60:],
                    name='CO2'
                )
            ]
        )
    # update x-axis range to last 'time_range' minutes
    time_series.update_xaxes(range=[datetime.datetime.now()-datetime.timedelta(minutes=time_range), datetime.datetime.now()])
    #time_series.update_xaxes(rangeslider_visible=True)

    return bar_chart, time_series

@app.callback(Output('live-map', 'extendData'),
              [Input('interval-component', 'n_intervals')])
def update_gps_track(n):
    with buffer_lock:
        return dict(lat=[[buffers['lat'][-1]]], lon=[[buffers['lng'][-1]]])


if __name__ == '__main__':
    app.run_server()
"""     if live_map is None:
        with buffer_lock:
            # create map figure
            live_map = go.Figure(
                data= go.Scattermapbox(
                    lat=list(buffers['lat']),
                    lon=list(buffers['lng']),
                    mode='lines',
                    line=dict(width=2, color='blue'),
                )
            )

            live_map.update_layout(
                autosize=True,
                uirevision=True,
                hovermode='closest',
                mapbox=dict(
                    accesstoken=credentials.mapbox_token,
                    bearing=0,
                    center=dict(
                        lat=buffers['lat'][-1],
                        lon=buffers['lng'][-1],
                    ),
                    pitch=0,
                    zoom=10,
                )
            )
    else:
        with buffer_lock:
            # update map figure
            live_map['data'][0]['lat'] = list(buffers['lat'])
            live_map['data'][0]['lon'] = list(buffers['lng']) """


