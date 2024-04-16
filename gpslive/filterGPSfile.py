import pandas as pd
import csv
df = pd.read_csv(r"./gpslive/gpstob.csv", delimiter='\t')
col2keep = ['latitude', 'longitude', 'altitude', 'total_counts'] 
df = df[col2keep]
df = df.map(lambda x: str(x).replace(',', '.') if isinstance(x, str) else x)
df.to_csv("gpstobfilt.csv", index=False, quoting=csv.QUOTE_NONE, escapechar='\\')