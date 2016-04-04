import os
import re
import asyncio
import subprocess

from concurrent.futures import CancelledError

import xml.etree.ElementTree as ET

import numpy as np


def read_svg():
    filename = 'test.svg'
    if os.path.exists(filename):
        print("read_svg: Reading from %s" % filename)
        with open(filename, 'rb') as fp:
            yield from fp
    else:
        print("read_svg: Running pdf2svg")
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


def run_subprocess_alt(cmdline, input):
    loop = asyncio.get_event_loop()

    def sync(co):
        f = asyncio.ensure_future(co)
        loop.run_until_complete(f)
        return f.result()

    print("Starting %s" % (cmdline,))
    process = sync(asyncio.create_subprocess_exec(
        *cmdline, stdin=subprocess.PIPE, stdout=subprocess.PIPE))

    async def writer():
        try:
            for b in input:
                process.stdin.write(b.encode())
                await process.stdin.drain()
        except ConnectionResetError:
            print("Writer caught ConnectionResetError")
            pass
        except CancelledError:
            print("Writer caught CancelledError")
            pass
        finally:
            print("Writer closing stdin")
            process.stdin.write_eof()
            print("Patching _maybe_resume_transport")
            process.stdout._maybe_resume_transport = lambda: None

    print("Starting writer")
    w = asyncio.ensure_future(writer())

    eof = False
    while not eof:
        if process.stdout.at_eof():
            print("stdout.at_eof()")
            break
        try:
            before = str(process.stdout)
            b = sync(process.stdout.readline()).decode()
        except:
            print(process.stdout, before)
            raise
        if b:
            yield b
        else:
            eof = True
    print("Reader got eof, cancelling writer")
    w.cancel()
    loop.run_until_complete(w)
    print("Waiting for process")
    # process.stdin.close()
    sync(process.wait())
    print("Closing loop")
    loop.close()


def run_subprocess(cmdline, input):
    res = subprocess.run(cmdline, input=''.join(input),
                         stdout=subprocess.PIPE,
                         universal_newlines=True)
    yield res.stdout


def get_points():
    svg = read_svg()
    events = read_events(svg)
    points = read_points(events)
    points = np.fromiter((v for p in points for v in p), dtype=np.float)
    points = points.reshape(-1, 2)
    print("get_points: fromiter returned %s points" % len(points))
    indices = np.argsort(points[:, 0])
    points = points[indices]
    return points


def main():
    if os.path.exists('points.npz'):
        print("Loading points from points.npz")
        points = np.load('points.npz')['points']
    else:
        points = get_points()
        print("Saving points to points.npz")
        np.savez_compressed('points.npz', points=points)

    def point_input():
        for x, y in points:
            yield '%s %s\n' % (x, y)

    b_i = []
    b_j = []
    b_x = []
    b_y = []
    for line in run_subprocess(('./union',), point_input()):
        i, j, x, y = line.split()
        b_i.append(int(i))
        b_j.append(int(j))
        b_x.append(float(x))
        b_y.append(float(y))
    b_i = np.asarray(b_i)
    b_j = np.asarray(b_j)
    b_x = np.asarray(b_x)
    b_y = np.asarray(b_y)
    print("Got %d boundary intersections" % len(b_i))
    np.savez_compressed('boundary.npz', i=b_i, j=b_j, x=b_x, y=b_y)


if __name__ == "__main__":
    main()
