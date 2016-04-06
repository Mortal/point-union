import time
import subprocess

import numpy as np


def main():
    n = 2000
    m = 0.1
    xs = np.linspace(-m, m, n)
    ys = np.random.uniform(-m, m, n)
    s = ' '.join(map(str, np.c_[xs, ys].ravel())).encode()
    p = subprocess.Popen(
        ['./union'],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL)
    t1 = time.time()
    p.communicate(s)
    t2 = time.time()
    print(t2 - t1)


if __name__ == "__main__":
    main()
