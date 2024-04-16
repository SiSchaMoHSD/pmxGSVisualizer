import csv
import json
import folium
from folium import JsCode
from folium.plugins import Realtime
import time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import threading
import atexit



# Read CSV file
#df = pd.read_csv(r'./gpslive/gpstobfilt.csv')
initloc = {}
with open(r'./gpslive/gpstobfilt.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    initloc = next(reader)

# Initialize folium map centered at the first coordinates
m = folium.Map(location=[float(initloc['latitude']), float(initloc['longitude'])], zoom_start=13)
folium.TileLayer(
    tiles='https://{s}.tile.openstreetmap.de/tiles/osmde/{z}/{x}/{y}.png',
    attr='OpenStreetMap.DE',
    name='OpenStreetMap.DE',
).add_to(m)

source = "http://localhost:8877/data.geojson"

Realtime(
    source,
    get_feature_id=JsCode("(f) => { return f.properties.id}"),
    point_to_layer=JsCode("""
        (f, latlng) => {
            var color = 'red';
            if (f.properties.total_counts < 5) {
                color = 'green';
            } else if (f.properties.total_counts < 10) {
                color = 'yellow';
            }
            var marker = L.circleMarker(latlng, {radius: 8, fillOpacity: 0.2, color: color});
            marker.bindPopup(
                'ID: ' + f.properties.id + '<br>' +
                'Total Counts: ' + f.properties.total_counts + '<br>' +
                'Altitude: ' + f.properties.altitude
            );
            return marker;
        }
        """),
    interval=1000,
).add_to(m)

m.save(r'./gpslive/realtime.html')

def create_geojson():
    with open(r'./gpslive/gpstobfilt.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)

        # init an empty list to store GeoJSON features
        features = []

        # loop through each row in the CSV
        for index, row in enumerate(reader):
            # create a GeoJSON feature
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row['longitude']), float(row['latitude'])]
                },
                "properties": {
                    "id": index,
                    "total_counts": float(row['total_counts']),
                    "altitude": float(row['altitude'])
                }
            }

            # add the feature to the list
            features.append(feature)

            # write the features to a new GeoJSON file
            with open(r'./gpslive/data.geojson', 'w') as geojsonfile:
                json.dump({'type': 'FeatureCollection', 'features': features}, geojsonfile)

            #wait for 1 second
            time.sleep(1)

class MapHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        f = open(r'./gpslive/data.geojson', 'rb').read()
        #Set the referrer policy header
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(f)

def run_server(server_class=ThreadingHTTPServer, handler_class=MapHTTPRequestHandler, port=8877):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}')
    httpd.serve_forever()

# run both functions in separate threads
t_geo = threading.Thread(target=create_geojson)
#tserver = threading.Thread(target=run_server)

t_geo.start()
#tserver.start()

# stop the server when the main thread exits
atexit.register(t_geo.join)
#atexit.register(tserver.join)
run_server()