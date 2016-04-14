This simple scripts converts a KML file (created from an Abvio APP like Cyclemeter) to a GPX file.

The exported data will be importable to most websites (like SmashRun) correctly.

I created this tool to port my data from Abvio to a more flexible system.

(It keeps elevation, gps position and correct dates and interval)

Hope it could be useful to someone else.

# How to use

Just place your Abvio KML files in the input folder execute in your command line

````sh
python abvio_kml2gpx.py
````

You will find the GPX exported files in the output folder ready to be uploaded wherever you want
