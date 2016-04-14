# -*- coding: utf-8 -*-
#
#  abvio_kml2gpx
#  Author: Simone Cingano (simonecingano@gmail.com)
#  Web: http://simonecingano.it
#  Repository: https://github.com/yupswing/abvio_kml2gpx
#  Licence: GNU GPL v2

# ---

# This tool converts ABVIO KML files to GPX files

# Use it from shell

# place your KML files in the input folder

#  python abvio_kml2gpx.py

# get your GPX files in the output folder

import re
import os
import pytz
from datetime import datetime, timedelta
from os import listdir
from os.path import isfile, join

INPUT_PATH = "input"
OUTPUT_PATH = "output"


def main():
    """
    Main process
    """
    # DELETE ALL GPX IN OUTPUT
    for f in listdir(OUTPUT_PATH):
        if isfile(join(OUTPUT_PATH, f)) and f.endswith(".gpx"):
            os.remove(join(OUTPUT_PATH, f))

    # CONVERT ALL KML IN INPUT
    for f in listdir(INPUT_PATH):
        if isfile(join(INPUT_PATH, f)) and f.endswith(".kml"):
            convert(f)
            print "-----------------------------------------------------------------------"


def tofloat(v):
    """Convert to float (sometimes there is an error in the file)"""
    v = v.replace('..', '.')
    return float(v)


def convert(f):
    """Main conversion function"""
    print "- Conversion started for %s" % join(INPUT_PATH, f)

    # ORIGINAL FORMAT
    # ...
    # <abvio:startTime>2011-07-10 07:19:48.622</abvio:startTime>
    # <abvio:startTimeZone>Europe/Rome</abvio:startTimeZone>
    # ...
    # <abvio:coordinateTable>
    # 17089.451,44.4060463,8.9280751,12.1,6.5
    # 17089.451,44.4060463,8.9280751,12.1,6.5
    # 17089.451,44.4060463,8.9280751,12.1,6.5
    # </abvio:coordinateTable>
    # ...
    # <abvio:altitudeTable>
    # 17099.102,40.7,0.0,-0.033
    # 17099.102,40.7,0.0,-0.033
    # 17099.102,40.7,0.0,-0.033
    # </abvio:altitudeTable>
    # ...

    f_gpx = open(join(OUTPUT_PATH, f.replace(".kml", ".gpx")), 'w')

    f_gpx.write("""<?xml version="1.0" encoding="us-ascii"?>
<gpx
    creator="abvio_kml2gpx.py"
    version="1.1"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd http://www.garmin.com/xmlschemas/TrackPointExtension/v1 http://www.garmin.com/xmlschemas/TrackPointExtensionv1.xsd"
    xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
    xmlns="http://www.topografix.com/GPX/1/1">
    <metadata>
        <time>%s</time>
    </metadata>
    <trk>
        <trkseg>
""" % datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))

    mode_start_time = True
    mode_start_timezone = False
    mode_coordinate = False
    mode_altitude = False

    start_time_re = re.compile('<abvio:startTime>([^<]+)</abvio:startTime>')
    start_timezone_re = re.compile('<abvio:startTimeZone>([^<]+)</abvio:startTimeZone>')
    coordinate_start_re = re.compile('<abvio:coordinateTable>')
    # 17089.451,44.4060463,8.9280751,12.1,6.5
    coordinate_data_re = re.compile('([0-9.\-]+),([0-9.\-]+),([0-9.\-]+),([0-9.\-]+),([0-9.\-]+)')
    coordinate_end_re = re.compile('</abvio:coordinateTable>')
    altitude_start_re = re.compile('<abvio:altitudeTable>')
    # 17099.102,40.7,0.0,-0.033
    altitude_data_re = re.compile('([0-9.\-]+),([0-9.\-]+),([0-9.\-]+),([0-9.\-]+)')
    altitude_end_re = re.compile('</abvio:altitudeTable>')

    start_time_string = "2011-07-10 07:19:48.622"
    start_time_zone_string = "Europe/Rome"
    start_time = None

    coordinate_points = []
    coordinate_points_len = 0
    last_coordinate_altitude = -1
    altitude_points_len = 0
    last_altitude = 0

    with open(join(INPUT_PATH, f), 'r') as fp:
        for line in fp:
            if mode_start_time:  # look for start time
                m = start_time_re.search(line)
                if m:
                    start_time_string = m.group(1)
                    mode_start_time = False  # Done!
                    mode_start_timezone = True  # Todo
            elif mode_start_timezone:  # look for start timezone
                m = start_timezone_re.search(line)
                if m:
                    start_time_zone_string = m.group(1)
                    mode_start_timezone = False  # Done!
                    start_time_unaware = datetime.strptime(start_time_string.split('.')[0], '%Y-%m-%d %H:%M:%S')
                    localtz = pytz.timezone(start_time_zone_string)
                    start_time = localtz.localize(start_time_unaware).astimezone(pytz.timezone('UTC'))
                    print "Start date: '%s' (original timezone '%s')" % \
                        (start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z"), start_time_zone_string)
            elif mode_coordinate:
                if coordinate_end_re.match(line):
                    mode_coordinate = False
                    coordinate_points_len = len(coordinate_points)
                    continue
                else:
                    m = coordinate_data_re.search(line)
                    if m:
                        coordinate_points.append({"moment": tofloat(m.group(1)),
                                                  "date": start_time+timedelta(seconds=tofloat(m.group(1))),
                                                  "lat": tofloat(m.group(2)),
                                                  "el": None,
                                                  "lon": tofloat(m.group(3))})
            elif mode_altitude:
                if altitude_end_re.match(line):
                    mode_altitude = False
                    print "Coordinates: %d points, Altitude: %d points" % (coordinate_points_len, altitude_points_len)
                    for track in coordinate_points:
                        f_gpx.write("""            <trkpt lat="%s" lon="%s">
                <ele>%s</ele>
                <time>%s</time>
                <extensions>
                    <gpxtpx:TrackPointExtension/>
                </extensions>
            </trkpt>
""" % (track['lat'],track['lon'],track['el'] or last_altitude,track['date'].strftime("%Y-%m-%dT%H:%M:%S.")+str(track['date'].microsecond)[:3]+'Z'))
                    break
                    #FINISH!
                else:
                    m = altitude_data_re.search(line)
                    if m:
                        moment = tofloat(m.group(1))
                        altitude = tofloat(m.group(2))
                        last_altitude = altitude
                        altitude_points_len += 1
                        for i in range(last_coordinate_altitude+1,coordinate_points_len):
                            c = coordinate_points[i]
                            if (moment>=c['moment']):
                                c['el'] = altitude
                                last_coordinate_altitude = i
                            else:
                                break
            else:  # look for altitude or coordinate start
                if coordinate_start_re.match(line):
                    mode_coordinate = True
                    continue
                if altitude_start_re.match(line):
                    mode_altitude = True

    f_gpx.write("""        </trkseg>
    </trk>
</gpx>""")

    f_gpx.close()

    if (mode_start_time or mode_start_timezone or mode_coordinate or mode_altitude):
        os.remove(join(OUTPUT_PATH, f.replace(".kml", ".gpx")))
        print "- Conversion FAILED for %s" % join(INPUT_PATH, f)
    else:
        print "- Conversion ended to %s" % join(OUTPUT_PATH, f.replace(".kml", ".gpx"))

if __name__ == "__main__":
    main()
