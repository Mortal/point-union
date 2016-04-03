import os
import re
import subprocess

import xml.etree.ElementTree as ET

import numpy as np


def read_svg():
    if os.path.exists('test.svg'):
        with open('test.svg', 'rb') as fp:
            yield from fp
    else:
        cmdline = ('pdf2svg', 'bachelormain.pdf', '/dev/stdout', '20')
        kwargs = dict(
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE)
        with subprocess.Popen(cmdline, **kwargs) as p:
            yield from p.stdout


def read_events(svg):
    parser = ET.XMLPullParser(['start', 'end'])
    for line in svg:
        parser.feed(line)
        yield from parser.read_events()
    parser.close()
    yield from parser.read_events()


def parse_style(elem):
    matches = re.finditer(r'([a-z-]+):([^;]+)', elem.attrib.get('style', ''))
    return dict((mo.group(1), mo.group(2)) for mo in matches)


def is_circle(elem):
    NS = 'http://www.w3.org/2000/svg'
    PATH = '{%s}path' % NS
    if elem.tag != PATH:
        return False
    style = parse_style(elem)
    stroke = style.get('stroke', 'none')
    if stroke == 'none' or 'stroke-width' not in style:
        return False

    path = elem.attrib['d'].split()
    tpl = """
        M 0.00102178 -0.249553 C 0.067428 -0.249553 0.129928 -0.222209 0.176803
        -0.175334 C 0.223678 -0.128459 0.251022 -0.0659589 0.251022 0.000447374
        C 0.251022 0.0668536 0.223678 0.129354 0.176803 0.176229 C 0.129928
        0.223104 0.067428 0.250447 0.00102178 0.250447 C -0.0653845 0.250447
        -0.131791 0.223104 -0.178666 0.176229 C -0.225541 0.129354 -0.248978
        0.0668536 -0.248978 0.000447374 C -0.248978 -0.0659589 -0.225541
        -0.128459 -0.178666 -0.175334 C -0.131791 -0.222209 -0.0653845
        -0.249553 0.00102178 -0.249553 Z M 0.00102178 -0.249553""".split()
    return all(x == y or len(x) > 1 for x, y in zip(tpl, path))


def parse_matrix(elem):
    pattern = r'matrix\(1,0,0,-1,(-?[\d.]+),(-?[\d.]+)\)'
    mo = re.match(pattern, elem.attrib['transform'])
    return float(mo.group(1)), float(mo.group(2))


def read_points(events):
    crumb = []
    for event, elem in events:
        if event == 'start':
            crumb.append(elem)
        # print(' > '.join(e.tag for e in crumb))
        if event == 'start' and is_circle(elem):
            style = parse_style(elem)
            width = float(style.get('stroke-width'))
            x, y = parse_matrix(elem)
            yield x, y
        if event == 'end':
            crumb.pop()


def print_points(points):
    print('<?xml version="1.0"?>')
    print('<svg viewBox="0 0 120 120" version="1.1" ' +
          'xmlns="http://www.w3.org/2000/svg">')
    for x, y in points:
        print('<circle cx="%s" cy="%s" r="0.5"/>' % (x, y))
    print("</svg>")


def main():
    svg = read_svg()
    events = read_events(svg)
    points = read_points(events)
    points = np.fromiter((v for p in points for v in p), dtype=np.float)
    points = points.reshape(-1, 2)
    indices = np.argsort(points[:, 0])
    points = points[indices]
    print_points(points)


if __name__ == "__main__":
    main()
