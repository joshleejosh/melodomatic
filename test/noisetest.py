#!/usr/bin/env python
"""
A script that exercises the noise function used in the $noise value generator.

Visualizes various samples, and compares with a packaged noise function.
"""
import sys, os.path, math, time

# https://github.com/caseman/noise (or just `pip install noise`)
import noise

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'melodomatic'))
import generators

# ---------------------------------------------------------

START = int(time.time())%10000
ITERATIONS = 300
STEPSIZE = 0.01
ITERATIONSIZE = 1000
DISTRIBUTION_BUCKETS = 64

pdist=list(0 for i in range(DISTRIBUTION_BUCKETS))
qdist=list(0 for i in range(DISTRIBUTION_BUCKETS))

# ---------------------------------------------------------

def _rmap(n, minn, maxn, maxw):
    return int(round(generators._map(n, minn, maxn, 0.0, maxw)))

def _bar(w):
    s = ''
    for i in range(w):
        s += '-'
    return s

# ---------------------------------------------------------

BARWIDTH = 20
def _fmt(n):
    s = _bar(_rmap(abs(n), 0.0, 1.0, BARWIDTH))
    if n < 0:
        s = str.rjust(s, BARWIDTH) + str.ljust(' ', BARWIDTH)
    else:
        s = str.rjust(' ', BARWIDTH) + str.ljust(s, BARWIDTH)
    return s

def test_noise(base, step, viz=False):
    global pdist, qdist
    for i in range(ITERATIONSIZE):
        p = noise.pnoise1(base + step * i)
        q = generators._noise1(base + step * i)
        if viz:
            print '%+0.4f | %s | %s | %+0.4f'%(p, _fmt(p), _fmt(q), q)
        pdist[_rmap(p, -1.0, 1.0, DISTRIBUTION_BUCKETS)] += 1
        qdist[_rmap(q, -1.0, 1.0, DISTRIBUTION_BUCKETS)] += 1

# ---------------------------------------------------------

if __name__ == '__main__':
    #test_noise(START, STEPSIZE, True)

    for i in range(START, START+ITERATIONS):
        test_noise(i, STEPSIZE, False)
    for i in range(len(pdist)):
        maxval = max(max(pdist), max(qdist))
        print '%03d | %07d %-40s | %07d %-40s |'%(i,
                pdist[i], _bar(_rmap(pdist[i], 0.0, maxval, 40)),
                qdist[i], _bar(_rmap(qdist[i], 0.0, maxval, 40)))


