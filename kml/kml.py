# This is a recreation of the example found in the KML Reference:
# http://code.google.com/apis/kml/documentation/kmlreference.html#gxtrack
import os
import csv
import time
from os.path import abspath, dirname, join
from datetime import datetime, timedelta
from collections import deque
import simplekml
from simplekml import Kml, Snippet, Types, AltitudeMode
import xml.etree.ElementTree as ET
import subprocess

# register the namespaces
ET.register_namespace('', 'http://www.opengis.net/kml/2.2')
ET.register_namespace('gx', 'http://www.google.com/kml/ext/2.2')
namespaces = {'': 'http://www.opengis.net/kml/2.2', 'gx': 'http://www.google.com/kml/ext/2.2'}

#create deques
headings = deque(maxlen=60*60)
when = deque(maxlen=60*60)
coord = deque(maxlen=60*60)
kmlfilepath = join(dirname(abspath(__file__)), 'gpsdata.kml')
csvfilepath = join(dirname(abspath(__file__)), 'GPS_filtered.csv')
dronePNGfilepath = join(dirname(abspath(__file__)), 'drone.png')
filedate = str(datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
init_values = []

# Create the KML document
kml = Kml(name="Tracks", open=1)
doc = kml.newdocument(name='PMX Track', snippet=Snippet(filedate))
if os.path.exists(kmlfilepath): open(kmlfilepath, 'w').close()
# only read header and first row and put data in init_values
with open(csvfilepath, 'r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        init_values.append(row)
        curr_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ') 
        # append time to key TIME in init_values
        init_values[0]['TIME'] = curr_time
        break
file.close()
print(init_values)
# Set the document properties with init_values
doc.lookat.gxtimespan.begin = init_values[0]['TIME']
# add one hour to the begin time
end_time = datetime.now() + timedelta(hours=1)
print(end_time.strftime('%Y-%m-%dT%H:%M:%SZ'))
doc.lookat.gxtimespan.end = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
doc.lookat.longitude = init_values[0]['LONGITUDE']
doc.lookat.latitude = init_values[0]['LATITUDE']
doc.lookat.range = 1300.000000

# Create a folder
fol = doc.newfolder(name='Track')

# Create a schema for extended data: heart rate, cadence and power
schema = kml.newschema()
schema.newgxsimplearrayfield(name='heading', type=Types.float, displayname='heading')

# Create a new track in the folder
trk = fol.newgxtrack(name=filedate)
trk.altitudemode = AltitudeMode.absolute

# Apply the above schema to this track
trk.extendeddata.schemadata.schemaurl = schema.id

# Add all the information to the track
trk.newwhen(init_values[0]['TIME']) # Each item in the give nlist will become a new <when> tag
trk.newgxcoord([(float(init_values[0]['LONGITUDE']),float(init_values[0]['LATITUDE']),float(init_values[0]['ALTITUDE']))]) # Ditto
trk.extendeddata.schemadata.newgxsimplearraydata('heading', [float(init_values[0]['HEADING'])])

# Styling
trk.stylemap.normalstyle.iconstyle.icon.href = dronePNGfilepath
trk.stylemap.normalstyle.linestyle.color = '99ffac59'
trk.stylemap.normalstyle.linestyle.width = 6
trk.stylemap.highlightstyle.iconstyle.icon.href = 'http://earth.google.com/images/kml-icons/track-directional/track-0.png'
trk.stylemap.highlightstyle.iconstyle.scale = 1.2
trk.stylemap.highlightstyle.linestyle.color = '99ffac59'
trk.stylemap.highlightstyle.linestyle.width = 8

# Save the kml to file
kml.save(kmlfilepath)

# create network link
netkml = Kml()
netlink = netkml.newnetworklink(name='PMX Track')
netlink.refreshvisibility = 0
netlink.gxballoonvisibility = 1
netlink.link.href = kmlfilepath
netlink.link.refreshmode = simplekml.RefreshMode.oninterval
netlink.link.refreshinterval = 2
netkml.save(join(dirname(abspath(__file__)), 'netlink.kml'))

# Function to update the KML file using xml library --------------------------------------------------------------------------------
def updateKML():
    tree = ET.parse(kmlfilepath)
    root = tree.getroot()

    # Find the <gx:Track> tag
    track = root.find('.//gx:Track', namespaces)
    if track is None:
        print('No <gx:Track> tag found in the KML file')
        return
        
    # Find last <when> and <gx:coord> tags
    last_when = [e for e in track if e.tag == '{http://www.opengis.net/kml/2.2}when'][-1]
    last_coord = [e for e in track if e.tag == '{http://www.google.com/kml/ext/2.2}coord'][-1]

    # Get the indices of the last <when> and <gx:coord> elements
    last_when_index = list(track).index(last_when)
    last_coord_index = list(track).index(last_coord)

    # Create new <when> and <gx:coord> elements
    new_when = ET.Element('{http://www.opengis.net/kml/2.2}when')
    new_coord = ET.Element('{http://www.google.com/kml/ext/2.2}coord')

    # Set the text of the new elements
    new_when.text = when[-1]
    new_coord.text = '{} {} {}'.format(coord[-1][0], coord[-1][1], coord[-1][2])

    # Insert the new elements at the correct positions
    track.insert(last_when_index + 1, new_when)
    track.insert(last_coord_index + 2, new_coord)  # Add 1 to the index

    # Find the <gx:SimpleArrayData> tag with the name 'heading'
    simple_array_data = root.find('.//ExtendedData/SchemaData/gx:SimpleArrayData[@name="heading"]', namespaces)
    if simple_array_data is None:
        print('No <gx:SimpleArrayData> tag with name "heading" found in the KML file')
        return
    
    # Create a new <gx:value> element
    new_value = ET.Element('{http://www.google.com/kml/ext/2.2}value')
    new_value.text = headings[-1]

    # Append the new <gx:value> element to the <gx:SimpleArrayData> element
    simple_array_data.append(new_value)

    # Write the changes back to the KML file in UTF-8 encoding
    tree.write(kmlfilepath, encoding='utf-8', xml_declaration=True)
# End of updateKML function ---------------------------------------------------------------------------------------------

# open kml file
subprocess.run(['start', join(dirname(abspath(__file__)), 'netlink.kml')], shell=True)

# open csv file
with open(csvfilepath, 'r') as file:
    reader = csv.DictReader(file)
    for index, row in enumerate(reader):
        if index == 0:
            continue
        headings.append(row['HEADING'])
        curr_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        coord.append((float(row['LONGITUDE']), float(row['LATITUDE']), float(row['ALTITUDE'])))
        when.append(curr_time)
        updateKML()
        time.sleep(2) # sleep for 1 second
file.close()


# Data for the track
#when = ["2010-05-28T02:02:09Z",
#    "2010-05-28T02:02:35Z",
#    "2010-05-28T02:02:44Z",
#    "2010-05-28T02:02:53Z",
#    "2010-05-28T02:02:54Z",
#    "2010-05-28T02:02:55Z",
#    "2010-05-28T02:02:56Z"]

#coord = [(-122.207881,37.371915,156.000000),
#    (-122.205712,37.373288,152.000000),
#    (-122.204678,37.373939,147.000000),
#    (-122.203572,37.374630,142.199997),
#    (-122.203451,37.374706,141.800003),
#    (-122.203329,37.374780,141.199997),
#    (-122.203207,37.374857,140.199997)]

#cadence = [86, 103, 108, 113, 113, 113, 113]
#heartrate = [181, 177, 175, 173, 173, 173, 173]
#power = [327.0, 177.0, 179.0, 162.0, 166.0, 177.0, 183.0]
