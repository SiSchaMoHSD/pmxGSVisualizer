import pandas as pd
import folium
import time
import os

# Define color function
def get_color(total_counts):
    if total_counts <= 4:
        return 'green'
    elif total_counts <= 9:
        return 'yellow'
    else:
        return 'red'

# Read CSV file
df = pd.read_csv(r'./gpslive/gpstobfilt.csv')

# Initialize folium map centered at the first coordinates
m = folium.Map(location=[df['latitude'][0], df['longitude'][0]], zoom_start=13)
folium.TileLayer(
    tiles='https://{s}.tile.openstreetmap.de/tiles/osmde/{z}/{x}/{y}.png',
    attr='OpenStreetMap.DE',
    name='OpenStreetMap.DE',
).add_to(m)

# Temporary and final HTML files
temp_html = 'temp_map.html'
final_html = 'map.html'

# Add a marker for each coordinate with color based on total_counts
for i in range(len(df)):
    folium.CircleMarker(
        location=[df['latitude'][i], df['longitude'][i]],
        radius=5,
        color=get_color(df['total_counts'][i]),
        fill=True,
        fill_color=get_color(df['total_counts'][i])
    ).add_to(m)
    
    # Save map to HTML string
    html = m.get_root().render()

    # Add meta refresh tag
    html = html.replace('<head>', '<head><meta http-equiv="refresh" content="5">')

    # Write HTML string to temporary HTML file
    with open(temp_html, 'w') as f:
        f.write(html)

    # Save map to temporary HTML file
    #m.save(temp_html)
    
    # Rename temporary HTML file to final HTML file
    os.replace(temp_html, final_html)
    
    time.sleep(1)