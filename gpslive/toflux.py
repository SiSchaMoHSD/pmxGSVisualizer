import pandas as pd
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient, WriteOptions
#from influxdb_client.client.write_api import SYNCHRONOUS

df = pd.read_csv(r'./gpslive/gpstobfilt.csv')

start_time = datetime(2024, 4, 15, 15)
# specify the time column as integer and add it to the dataframe
df['time'] = [(start_time + timedelta(seconds=i)).timestamp() for i in range(len(df))]
#df['time'] = df['time'].astype(int)
df = df.set_index('time')
# add a new column with the name of the measurement and fill it with the name of the dataframe in every row colum is at the beginning
#df.insert(0, 'measurement', 'gpslive2')

#print(df.head(3))
#save new csv
#df.to_csv(r'./gpslive/gpslive2.csv', index=False)

client = InfluxDBClient.from_config_file(r'./gpslive/config.ini', debug=True)


with client as _client:
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
        _write_client.write("gpslivetest", "roboflex", record=df, data_frame_measurement_name='gpslive4', write_precision='ns')

#pd.set_option('display.float_format', str)
#print first 3 rows of the dataframe
#print(df.head(3))