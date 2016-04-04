import numpy as np


def main():
    R = 0.5
    points = np.load('points.npz')['points']
    b = np.load('boundary.npz')
    f = b['i'] == b['j']
    alone = b['i'][f]
    print("<group>")
    print("<path fill=\"darkgray\">")
    for i in alone:
        print("%s 0 0 %s %s %s e" % (R, R, points[i, 0], points[i, 1]))
    print("</path>")

    bi = b['i']
    bj = b['j']
    bx = b['x']
    by = b['y']

    edge_lists = [[] for i in range(len(points))]
    n = 0
    for i, j, x, y in zip(bi, bj, bx, by):
        if i != j:
            edge_lists[j].append((i, x, y))
            n += 1
    paths = []

    def patan2(dy, dx):
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

    while n > 0:
        assert sum(len(e) for e in edge_lists) == n
        i = 0
        while not edge_lists[i]:
            i += 1
        start = i
        j, ox, oy = edge_lists[i].pop(0)
        startx, starty = ox, oy
        path = ['%s %s m' % (startx, starty)]
        n -= 1
        while j != start:
            i = j
            j, ox, oy = pop_next(i, ox, oy)
            n -= 1
            path.append(
                '%s 0 0 %s %s %s %s %s a' %
                (R, R, points[i, 0], points[i, 1], ox, oy))
        path.append(
            '%s 0 0 %s %s %s %s %s a' %
            (R, R, points[j, 0], points[j, 1], startx, starty))
        # paths.append('\n'.join(path))
        print("<path fill=\"black\">")
        print('\n'.join(path))
        print("</path>")
    print("</group>")


if __name__ == "__main__":
    main()
