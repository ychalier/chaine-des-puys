# Chaîne des Puys

A visualization for the geographical data of the [Chaîne des Puys](https://en.wikipedia.org/wiki/Cha%C3%AEne_des_Puys).

I wanted to keep track of my progress in hiking over the whole chain, and came up with a 2D visualization of the summits surrounded by minimal contours. The department (the 'Puy de Dôme') outline is also shown for giving an idea of the chain location. Summit names and elevations are plotted if available. Visited ones are marked with blue dots, not yet visited ones with red dots.

## Getting Started

### Prerequisites

You'll need Python 3, and a small program called [Srtm2Osm](https://wiki.openstreetmap.org/wiki/Srtm2Osm).

### Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/ychalier/chaine-des-puys
    cd chaine-des-puys/
    ```

2. Install the Python requirements:
    ```bash
    pip install -r requirements.txt
    ```

3. Use Srtm2Osm to get the contours in a OSM format:
    ```bash
    [path to Srtm2Osm] -bounds1 45.556211 2.826316 46.093789 3.184321 -o contours.osm
    ```
    This should generate a file of about 36Mb. Note: if you want to reuse this script for another location, you want to change the boundaries expressed here; I found a great tool for doing so: [BoundingBox](https://boundingbox.klokantech.com/).

### Usage

Use the Python script `generate.py` to generate your HTML file:
```
usage: generate.py [-h] [-l WAY_LENGTH_THRESHOLD] [-d WAY_DISTANCE_THRESHOLD]
                   [-c WAY_CLOSURE_THRESHOLD]
                   osm csv poly html

positional arguments:
  osm                   input OSM file (contours)
  csv                   input CSV file (puys)
  poly                  input POLY file (department)
  html                  output HTML file (map)

optional arguments:
  -h, --help            show this help message and exit
  -l WAY_LENGTH_THRESHOLD    (default: 1000)
  -d WAY_DISTANCE_THRESHOLD  (default: 30)
  -c WAY_CLOSURE_THRESHOLD   (default: 200)
```

To serve the result as a static files, you'll need to upload the generated HTML, as well as `style.css` and `script.js` to your hosting server.

## Built With

- Contours are extracted from [NASA's SRTM data](https://www2.jpl.nasa.gov/srtm/) using [Srtm2Osm](https://wiki.openstreetmap.org/wiki/Srtm2Osm)
- Department [POLY file](https://wiki.openstreetmap.org/wiki/Osmosis/Polygon_Filter_File_Format) is queried from [OpenStreetMap](https://www.openstreetmap.org/) using this [portal](http://polygons.openstreetmap.fr/?id=7406)
- Information about the Chaîne des Puys (location, elevation, etc.) is extracted from [Wikipedia](https://fr.wikipedia.org/wiki/Cha%C3%AEne_des_Puys), [Google Maps](https://www.google.fr/maps), [OpenStreetMap](https://www.openstreetmap.org/) and [OpenTopoMap](https://opentopomap.org/)
- Map navigation feature is done with [panzoom](https://github.com/anvaka/panzoom)

![](https://i.imgur.com/6ceSnPM.png)
