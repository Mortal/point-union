import numpy as np


def main():
    points = np.load('points.npz')['points']
    b = np.load('boundary.npz')
    bx = b['x']
    by = b['y']

    s = 5
    x1 = min(np.min(bx), max(points[:, 0])) - 1
    x2 = max(np.max(bx), max(points[:, 0])) + 1
    y1 = min(np.min(by), max(points[:, 1])) - 1
    y2 = max(np.max(by), max(points[:, 1])) + 1

    print('<?xml version="1.0"?>')
    print('<svg viewBox="%s %s %s %s" ' % (s*x1, s*y1, s*x2, s*y2) +
          'version="1.1" xmlns="http://www.w3.org/2000/svg">')
    for x, y in s * points[:2000]:
        print('<circle cx="%s" cy="%s" r="%s" style="fill:black;opacity:0.5"/>' % (x, y, s / 2))
    for x, y in zip(s * bx, s * by):
        print('<circle cx="%s" cy="%s" r="1" style="fill:red;opacity:0.5"/>' % (x, y))
    print("</svg>")


if __name__ == "__main__":
    main()
