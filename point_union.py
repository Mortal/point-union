import time
import subprocess

import numpy as np

from matplotlib.transforms import Affine2D
from matplotlib.path import Path


def run_subprocess(cmdline, input):
    i = ''.join(input)
    # print(i)
    res = subprocess.run(cmdline, input=i,
                         stdout=subprocess.PIPE,
                         universal_newlines=True)
    # print(res.stdout)
    yield from res.stdout.splitlines()


def get_boundary_intersections(points):
    N, d = points.shape
    assert d == 2

    indices = np.argsort(points[:, 0])
    points = points[indices]

    def point_input():
        for x, y in points:
            yield '%s %s\n' % (x, y)

    bi = []
    bj = []
    bx = []
    by = []
    t1 = time.time()
    for line in run_subprocess(('./union',), point_input()):
        i, j, x, y = line.split()
        bi.append(int(i))
        bj.append(int(j))
        bx.append(float(x))
        by.append(float(y))
    t2 = time.time()
    bi = np.asarray(bi)
    bj = np.asarray(bj)
    bx = np.asarray(bx)
    by = np.asarray(by)
    return bi, bj, bx, by


def compress_points(points):
    bi, bj, bx, by = get_boundary_intersections(points)

    f = bi == bj
    alone_points = points[bi[f]]
    alone_paths = [Path.circle(xy, 0.5) for xy in alone_points]

    edge_lists = [[] for i in range(len(points))]
    n = 0
    for i, j, x, y in zip(bi, bj, bx, by):
        if i != j:
            edge_lists[j].append((i, x, y))
            n += 1

    print("%s points in total: %s edges, %s alone points" %
          (len(points), n, len(alone_points)))

    def patan2(dy, dx):
        """
        Return pseudo-arctangent of dy/dx such that
            patan2(y1, x1) < patan2(y2, x2)
            if and only if
            atan2(y1, x1) < atan2(y2, x2)
        """
        if dy > 0 and dx > 0:
            return (0, dy - dx)
        elif dy > 0 and dx <= 0:
            return (1, -dy - dx)
        elif dy <= 0 and dx > 0:
            return (2, dx - dy)
        else:
            return (3, dx + dy)

    def shift(u, v):
        if v < u:
            return (v[0] + 4, v[1])
        else:
            return v

    def pop_next(i, ox, oy):
        def local_patan2(y, x):
            return patan2(y - points[i, 1], x - points[i, 0])
        u = local_patan2(oy, ox)
        j = min(range(len(edge_lists[i])),
                key=lambda j: shift(u, local_patan2(edge_lists[i][j][2],
                                                    edge_lists[i][j][1])))
        return edge_lists[i].pop(j)

    paths = []
    # print("<path fill=\"black\" fillrule=\"wind\">")
    while n > 0:
        assert sum(len(e) for e in edge_lists) == n
        i = 0
        while not edge_lists[i]:
            i += 1
        start = i
        j, ox, oy = edge_lists[i].pop(0)
        startx, starty = ox, oy
        ux, uy = ox, oy
        # path = ['%s %s m' % (startx, starty)]
        path_vert_lists = [[[startx, starty]]]
        path_code_lists = [[Path.MOVETO]]

        n -= 1
        while j != start:
            i = j
            j, vx, vy = pop_next(i, ux, uy)
            n -= 1
            # path.append(
            #     '%s 0 0 %s %s %s %s %s a' %
            #     (R, R, points[i, 0], points[i, 1], ox, oy))
            ox, oy = points[i]
            theta1 = np.arctan2(uy - oy, ux - ox)
            theta2 = np.arctan2(vy - oy, vx - ox)
            a = Path.arc(theta1 * 180 / np.pi, theta2 * 180 / np.pi)
            a = a.transformed(Affine2D().scale(0.5).translate(ox, oy))
            path_vert_lists.append(a._vertices[1:])
            path_code_lists.append(a._codes[1:])
            ux, uy = vx, vy
        # path.append(
        #     '%s 0 0 %s %s %s %s %s a' %
        #     (R, R, points[j, 0], points[j, 1], startx, starty))
        ox, oy = points[j]
        theta1 = np.arctan2(uy - oy, ux - ox)
        theta2 = np.arctan2(starty - oy, startx - ox)
        a = Path.arc(theta1 * 180 / np.pi, theta2 * 180 / np.pi)
        a = a.transformed(Affine2D().scale(0.5).translate(ox, oy))
        path_vert_lists.append(a._vertices[1:])
        path_code_lists.append(a._codes[1:])
        # print('\n'.join(path))
        paths.append(
            Path(np.concatenate(path_vert_lists),
                 np.concatenate(path_code_lists).astype(Path.code_type)))
    # print("</path>")
    return Path.make_compound_path(*(alone_paths + paths))


def compress_markers(marker_path, marker_trans, path, trans):
    ((scale, _),) = marker_trans.transform([[1, 1]])
    if marker_trans != Affine2D().scale(scale):
        return
    t = trans - marker_trans + Affine2D().scale(0.5)
    p = compress_points(path.transformed(t).vertices)
    p = p.transformed(t.inverted())
    return p
