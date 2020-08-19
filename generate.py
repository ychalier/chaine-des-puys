# pylint: disable=C0103,R0903,R0913
"""Visualization for the "chaîne des Puys".
"""
import xml.etree.ElementTree
import math
import argparse
import codecs
import re
import random
import pandas


class Node:
    """Wrapper for a 2d vector.
    """

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return "Node<%f, %f>" % (self.x, self.y)

    def __str__(self):
        return "%.2f %.2f" % (self.x, self.y)

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __add__(self, other):
        return Node(self.x + other.x, self.y + other.y)

    def __radd__(self, other):
        if other == 0:
            return Node(self.x, self.y)
        raise ValueError(other)

    def __truediv__(self, other):
        return Node(self.x / other, self.y / other)

    def distance(self, other):
        """Euclidian distance between two vectors.
        """
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


class LatLonNode(Node):
    """Node constructor from latitude and longitude (in degrees) using a
    Mercator's projection approximation.
    """

    def __init__(self, lat, lon):
        self.lat = float(lat)
        self.lon = float(lon)
        w = 679.
        h = 724.
        theta = math.pi * self.lat / 180.
        phi = math.pi * self.lon / 180.
        x = w * (phi + math.pi) / (2 * math.pi)
        y = .5 * h - (w / (2 * math.pi))\
            * math.log(math.tan(.25 * math.pi + .5 * theta))
        Node.__init__(self, x, y)


class PuyNode(LatLonNode):
    """Node with metadata.
    """

    def __init__(self, lat, lon, label, visited, elevation=None):
        LatLonNode.__init__(self, lat, lon)
        self.label = label
        self.visited = visited
        self.elevation = elevation

    def full_label(self):
        """Return full label, including elevation is possible.
        """
        if self.elevation is not None:
            return "%s (%dm)" % (self.label, self.elevation)
        return self.label

    def color(self):
        """Node color encoding its visit status.
        """
        if self.visited:
            return "rgba(50, 50, 255, 1)"
        return "rgba(255, 50, 50, 1)"


class Way:
    """Sequence of nodes.
    """

    MIN_ELEVATION = 300
    MID_ELEVATION = 900
    MAX_ELEVATION = 1200

    def __init__(self, elevation=None, is_subway=False):
        self.elevation = elevation
        self.nodes = list()
        self.is_subway = is_subway

    def valid(self):
        """Check if the way is valid to display.
        """
        return self.elevation is not None and len(self.nodes) > 0

    def barycenter(self):
        """Compute the barycenter of all the way's nodes.
        """
        return sum(self.nodes) / len(self.nodes)

    def color(self):
        """Compute the fill color based on its elevation.
        """
        if self.is_subway:
            return "transparent"
        if self.nodes[0].distance(self.nodes[-1]) > 200:
            return "transparent"
        if self.elevation > Way.MID_ELEVATION:
            start, end = (27., 126., 14.), (87., 53., 0.)
            percent = min(1., max(0., (self.elevation - Way.MID_ELEVATION)
                                  / (Way.MAX_ELEVATION - Way.MID_ELEVATION)))
        else:
            start, end = (255., 255., 255.), (27., 126., 14.)
            percent = min(1., max(0., (self.elevation - Way.MIN_ELEVATION)
                                  / (Way.MID_ELEVATION - Way.MIN_ELEVATION)))
        r = percent * end[0] + (1 - percent) * start[0]
        g = percent * end[1] + (1 - percent) * start[1]
        b = percent * end[2] + (1 - percent) * start[2]
        return "rgba(%f, %f, %f, .3)" % (r, g, b)

    def stroke(self):
        """Compute the stroke width based on its elevation.
        """
        if self.elevation % 50 == 0:
            return .6
        return .3

    def sub(self, target_nodes, threshold):
        """Given a set of target nodes, yield parts of its node list, selecting
        nodes close to at least one target node.
        """
        close_nodes = [
            list_distance(self_node, target_nodes) < threshold
            for self_node in self.nodes
        ]
        current_index = 0
        for is_close, length in compress_sequence(close_nodes):
            if is_close and length > 100:
                subway = Way(elevation=self.elevation, is_subway=True)
                left_offset = current_index + random.randint(0, 20)
                right_offset = current_index + length - random.randint(0, 20)
                subway.nodes = self.nodes[left_offset:right_offset]
                yield subway
            current_index += length


def compress_sequence(raw):
    """Given a sequence of symbols, return the list of parts of similar
    consecutive symbols (and the part length).
    """
    sequences = list()
    start_symbol, length = raw[0], 1
    for symbol in raw[1:]:
        if symbol == start_symbol:
            length += 1
        else:
            sequences.append((start_symbol, length))
            start_symbol = symbol
            length = 1
    return sequences


class Scaler:
    """Space transformer.
    """

    def __init__(self, target=1000):
        self.target = target
        self.min_x = None
        self.max_x = None
        self.min_y = None
        self.max_y = None
        self.aspect = None

    def fit(self, nodes):
        """Fit on a set nodes.
        """
        self.min_x = min(map(lambda node: node.x, nodes))
        self.max_x = max(map(lambda node: node.x, nodes))
        self.min_y = min(map(lambda node: node.y, nodes))
        self.max_y = max(map(lambda node: node.y, nodes))
        self.aspect = (self.max_x - self.min_x) / (self.max_y - self.min_y)
        return self

    def transform(self, nodes):
        """Transform a set of nodes from its internal parameters.
        """
        for node in nodes:
            node.x = (node.x - self.min_x) / (self.max_x - self.min_x)\
                * self.target
            node.y = (node.y - self.min_y) / (self.max_y - self.min_y)\
                * self.target / self.aspect


def load_osm(filename):
    """Load the OSM contour file.
    """
    nodes, ways = dict(), list()
    tree = xml.etree.ElementTree.parse(filename)
    root = tree.getroot()
    for element in root:
        if element.tag == "node" and element.attrib.get("action") != "delete":
            node = LatLonNode(element.attrib["lat"], element.attrib["lon"])
            nodes[element.attrib["id"]] = node
        elif element.tag == "way":
            way = Way()
            for subel in element:
                if subel.tag == "nd":
                    way.nodes.append(nodes[subel.attrib["ref"]])
                elif subel.tag == "tag" and subel.attrib["k"] == "ele":
                    way.elevation = int(subel.attrib["v"])
            if way.valid():
                ways.append(way)
    return nodes.values(), ways


def load_csv(filename):
    """Load the CSV puys file.
    """
    nodes = list()
    for _, row in pandas.read_csv(filename).iterrows():
        if str(row["lat"]) == "nan" or str(row["lon"]) == "nan":
            continue
        label = row["label"]
        if str(row["elevation"]) != "nan":
            label += " (%dm)" % row["elevation"]
        nodes.append(PuyNode(
            row["lat"],
            row["lon"],
            row["label"],
            row["visited"] == 1,
            (None if str(row["elevation"]) == "nan" else int(row["elevation"]))
        ))
    return nodes


def list_distance(target, references):
    """Compute the minimum distance from a point to a list of points.
    """
    return min({target.distance(node) for node in references})


class SvgBuilder:
    """Create SVG data.
    """

    HTML_TEMPLATE = ""
    TEMPLATE_SVG = re.sub("^ *", "", """
    <svg
        width="{width}"
        height="{height}"
        viewBox="{min_x} {min_y} {width} {height}"
        xmlns="http://www.w3.org/2000/svg"
        encoding="utf-8"
    >
    <defs>
        <linearGradient id="Gradient1" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stop-color="black" stop-opacity=".3"/>
            <stop offset="50%" stop-color="black"  stop-opacity=".4" />
            <stop offset="100%" stop-color="black"  stop-opacity=".3"/>
        </linearGradient>
    </defs>
    {svg_data}
    </svg>
    """.strip())

    def __init__(self, way_distance_threshold, way_closure_threshold, way_node_distance_threshold):
        self.way_distance_threshold = way_distance_threshold
        self.way_closure_threshold = way_closure_threshold
        self.way_node_distance_threshold = way_node_distance_threshold
        with codecs.open("template.html", "r", "utf8") as infile:
            self.HTML_TEMPLATE = infile.read()

    def _select_ways(self, contour_ways, puy_nodes):
        contour_ways.sort(key=lambda way: way.elevation)
        for way in contour_ways:
            rejected = False
            if list_distance(way.barycenter(), puy_nodes)\
                    > self.way_distance_threshold:
                rejected = True
            elif way.nodes[0].distance(way.nodes[-1])\
                    > self.way_closure_threshold:
                rejected = True
            if not rejected:
                yield way
            else:
                for subway in way.sub(puy_nodes, self.way_node_distance_threshold):
                    yield subway

    def build(self, contour_ways, puy_nodes, department):
        """Output SVG text.
        """
        placed_nodes = set()
        svg_data = """<g id="scene"><g stroke-linejoin="round" >"""
        path_data = "M %s" % str(department.nodes[0])
        for node in department.nodes[1:-1:10]:
            path_data += " L %s" % str(node)
        svg_data += """<path stroke="grey" fill="transparent" stroke-width="1" d="%s" />\n""" % (
            path_data
        )
        svg_data += """</g><g stroke-linejoin="round">"""
        for way in self._select_ways(contour_ways, puy_nodes):
            if way.is_subway:
                path_data = "M %s" % str(way.nodes[0])
            else:
                path_data = "M %s" % str(way.nodes[-1])
            for node in way.nodes:
                path_data += " L %s" % str(node)
                placed_nodes.add(node)
            svg_data += """<path fill="%s" d="%s" stroke="%s" stroke-width="%s" />\n""" % (
                way.color(),
                path_data,
                ("url(#Gradient1)" if way.is_subway else "black"),
                way.stroke())
        svg_data += "</g><g>"
        for node in puy_nodes:
            placed_nodes.add(node)
            svg_data += """<g class="puy">
                <circle cx="%f" cy="%f" r="3" fill="%s" stroke="black" />
                <text x="%f" y="%f" text-anchor="middle" stroke="white" dy="-7">%s</text>
            </g>\n""" % (
                node.x,
                node.y,
                node.color(),
                node.x,
                node.y,
                node.full_label()
            )
        svg_data += "</g></g>"
        scaler = Scaler().fit(placed_nodes)
        return self.TEMPLATE_SVG.format(
            width=scaler.max_x - scaler.min_x,
            height=scaler.max_y - scaler.min_y,
            min_x=scaler.min_x,
            min_y=scaler.min_y,
            svg_data=svg_data,
        )


def load_poly(filename):
    """Load the department contour from a POLY file.
    """
    with open(filename, "r") as infile:
        lines = infile.readlines()
    title = lines[0].strip()
    polygons = dict()
    i = 1
    while i < len(lines):
        polygon = Way()
        polygon_title = lines[i].strip()
        i += 1
        while i < len(lines):
            if lines[i].strip() == "END":
                i += 1
                break
            lon, lat = re.split("[\t ]+", lines[i].strip())
            polygon.nodes.append(LatLonNode(lat, lon))
            i += 1
        polygons[polygon_title] = polygon
    return title, polygons


def main(args):
    """Parse arguments.
    """
    contour_nodes, contour_ways = load_osm(args.osm)
    scaler = Scaler()
    scaler.fit(contour_nodes)
    scaler.transform(contour_nodes)
    puy_nodes = load_csv(args.csv)
    puy_nodes.sort(key=lambda node: node.y)
    visited = len({p for p in puy_nodes if p.visited})
    scaler.transform(puy_nodes)
    department = load_poly(args.poly)[1]["1"]
    scaler.transform(department.nodes)
    builder = SvgBuilder(
        args.way_distance_threshold,
        args.way_closure_threshold,
        args.way_node_distance_threshold,
    )
    svg = builder.build(contour_ways, puy_nodes, department)
    visit_list = ""
    for puy_node in puy_nodes:
        if puy_node.visited:
            visit_list += """<li class="visited">%s</li>\n""" % puy_node.label
        else:
            visit_list += """<li>%s</li>\n""" % puy_node.label
    with codecs.open(args.html, "w", "utf8") as outfile:
        outfile.write(builder.HTML_TEMPLATE.format(
            visit_current=visited,
            visit_total=len(puy_nodes),
            visit_percent=100 * visited / len(puy_nodes),
            svg=svg,
            visit_list=visit_list
        ))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("osm", type=str, help="input OSM file (contours)")
    parser.add_argument("csv", type=str, help="input CSV file (puys)")
    parser.add_argument("poly", type=str, help="input POLY file (department)")
    parser.add_argument("html", type=str, help="output HTML file (map)")
    parser.add_argument("-d", type=int, default=30, dest="way_distance_threshold")
    parser.add_argument("-c", type=int, default=200, dest="way_closure_threshold")
    parser.add_argument("-n", type=int, default=120, dest="way_node_distance_threshold")
    main(parser.parse_args())
