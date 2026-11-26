"""Stored signals (SystemExtensionSpecs.md 6.3 to 6.6).

Only the signals the instruction selects are stored. A stored signal
preallocates an array for its sample count when that fits the depth
limit; beyond it the run writes chunks to the results folder and keeps
the last chunk in memory. A stored signal is a name, an x array of
integer master ticks and a y array of values (Specs 6.9.1: the master
tick of every sample is kept as an integer; time is derived from it).
Plot reduction is by bins with minimum and maximum per bin, an
envelope; subsampling hides peaks and is not used.
"""

import os

import numpy as np

# Numbers of the last open item of SystemExtensionSpecs.md section 14:
# a signal longer than DEPTH_LIMIT samples goes to chunk files; the
# envelope reduction uses ENVELOPE_BINS bins. 10 million float64 samples
# are 80 MB in memory.
DEPTH_LIMIT = 10_000_000
ENVELOPE_BINS = 2000


class Record:
    """One stored signal.

    :param name: trace name, ``"<function>.<output>"``
    :param count: number of samples the run will produce
    :param dtype: numpy dtype of the values
    :param folder: results folder for chunk files (needed when *count*
                   exceeds *depth*)
    :param depth: chunk size, default ``DEPTH_LIMIT``
    """

    def __init__(self, name, count, dtype=np.float64, folder=None,
                 depth=DEPTH_LIMIT):
        self.name = name
        self.count = int(count)
        self.dtype = np.dtype(dtype)
        self.folder = folder
        self.depth = int(depth)
        if self.count > self.depth and folder is None:
            raise ValueError(
                "stored signal %s: %d samples exceed the depth limit %d and "
                "no results folder is given for chunk files"
                % (name, count, depth))
        size = min(self.count, self.depth)
        self._x = np.empty(size, dtype=np.int64)        # master ticks
        self._y = np.empty(size, dtype=self.dtype)
        self._n = 0             # samples in the current chunk
        self._chunks = []       # file names of flushed chunks
        self.total = 0

    # ---- recording ----------------------------------------------------------

    def append(self, x, y):
        if self._n == self._x.size:
            self._flush()
        self._x[self._n] = x
        self._y[self._n] = y
        self._n += 1
        self.total += 1

    def extend(self, xs, ys):
        """Append the arrays *xs*, *ys* (a block of samples)."""
        xs = np.asarray(xs)
        ys = np.asarray(ys)
        k = 0
        while k < xs.size:
            if self._n == self._x.size:
                self._flush()
            m = min(xs.size - k, self._x.size - self._n)
            self._x[self._n:self._n + m] = xs[k:k + m]
            self._y[self._n:self._n + m] = ys[k:k + m]
            self._n += m
            self.total += m
            k += m

    def _flush(self):
        k = len(self._chunks)
        path = os.path.join(self.folder, "%s.chunk%03d.npz"
                            % (self.name.replace(".", "_"), k))
        np.savez(path, x=self._x[:self._n], y=self._y[:self._n])
        self._chunks.append(path)
        self._n = 0

    # ---- reading ------------------------------------------------------------

    def values(self):
        """``(ticks, y)`` of the whole signal, chunks included: the integer
        master tick of every sample and its value."""
        xs, ys = [], []
        for path in self._chunks:
            with np.load(path) as f:
                xs.append(f["x"])
                ys.append(f["y"])
        xs.append(self._x[:self._n])
        ys.append(self._y[:self._n])
        return np.concatenate(xs), np.concatenate(ys)

    def envelope(self, bins=ENVELOPE_BINS):
        """``(x, ymin, ymax)`` per bin, see :func:`envelope`."""
        x, y = self.values()
        return envelope(x, y, bins)

    def remove_chunks(self):
        for path in self._chunks:
            try:
                os.remove(path)
            except OSError:
                pass
        self._chunks = []


def envelope(x, y, bins=ENVELOPE_BINS):
    """Reduce ``(x, y)`` to *bins* bins with the minimum and the maximum
    per bin. Returns ``(xb, ymin, ymax)`` with *xb* the bin centres.
    Signals shorter than two samples per bin are returned as they are,
    with ``ymin == ymax == y``.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y)
    n = x.size
    if n == 0:
        return x, y, y
    if n < 2 * bins:
        return x, y, y
    edges = np.linspace(0, n, bins + 1).astype(int)
    xb = np.empty(bins)
    lo = np.empty(bins, dtype=y.dtype)
    hi = np.empty(bins, dtype=y.dtype)
    for i in range(bins):
        a, b = edges[i], edges[i + 1]
        seg = y[a:b]
        xb[i] = 0.5 * (x[a] + x[b - 1])
        lo[i] = seg.min()
        hi[i] = seg.max()
    return xb, lo, hi
