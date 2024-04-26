import pandas as pd
#from datetime import datetime, timedelta, timezone
import time
from influxdb_client import InfluxDBClient, WriteOptions, WritePrecision, Point
from influxdb_client.client.write_api import SYNCHRONOUS

df = pd.read_csv(r'./gpslive/gpstobfilt.csv')

current_epoch = time.time_ns()
df['time'] = [current_epoch + int(i*1e9) for i in range(len(df))]
#start_time = datetime(2024, 4, 22, 15)
# specify the time column as integer and add it to the dataframe
#df['time'] = [int((start_time + timedelta(seconds=i)).timestamp()*1e9) for i in range(len(df))]
#df['time'] = df['time'].astype(int)
#df = df.set_index('time')
# add a new column with the name of the measurement and fill it with the name of the dataframe in every row colum is at the beginning
#df.insert(0, 'measurement', 'gpslive2')

#print(df.head(3))
#save new csv
#df.to_csv(r'./gpslive/gpslive2.csv', index=False)

client = InfluxDBClient.from_config_file(r'./gpslive/config.ini', debug=True)

# Print total counts column only first row
print(df['total_counts'].iloc[0])
print(df.columns[3])
data = Point("Testground").field(df.columns[0], df['latitude'].iloc[0]).field(df.columns[1], df['longitude'].iloc[0]).field(df.columns[2], df['altitude'].iloc[0]).field(df.columns[3], df['total_counts'].iloc[0]).time(df['time'].iloc[0])
write_api = client.write_api(write_options=SYNCHRONOUS)
write_api.write("gpslivetest", "roboflex", record=data)
""" with client as _client:
    with _client.write_api(write_options=WriteOptions(
        batch_size=500,
        flush_interval=10_000,
        jitter_interval=2_000,
        retry_interval=5_000,
        max_retries=5,
        max_retry_delay=30_000,
        max_close_wait= 300_000,
        exponential_base=2
    
    )) as _write_client:
        #_write_client.write("gpslivetest", "roboflex", record=data, data_frame_measurement_name='gpslive5', write_precision=WritePrecision.S)
        _write_client.write("gpslivetest", "roboflex", record=data, write_precision=WritePrecision.NS) """

#pd.set_option('display.float_format', str)
#print first 3 rows of the dataframe
#print(df.head(3))

""" # Create a new QueryApi object
query_api = client.query_api()

# Flux query to filter data
flux_query = '''
from(bucket: "gpslivetest")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "gpslive5")
  |> filter(fn: (r) => r._field == "latitude" or r._field == "longitude" or r._field == "total_counts")
'''

# Execute the Flux query
result = query_api.query(flux_query)

data = []
for table in result:
    for record in table.records:
        data.append(record.values)

df = pd.DataFrame(data)

# Write the DataFrame to a CSV file
df.to_csv('influxdata.csv', index=False) """