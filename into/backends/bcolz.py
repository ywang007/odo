from __future__ import absolute_import, division, print_function

import bcolz
import os
from bcolz import ctable, carray
import numpy as np
from toolz import keyfilter
import datashape
from ..append import append
from ..convert import convert
from ..create import create
from ..resource import resource
from ..chunks import chunks, Chunks

keywords = ['rootdir']


@append.register((ctable, carray), np.ndarray)
def numpy_append_to_bcolz(a, b, **kwargs):
    a.append(b)
    return a


@append.register((ctable, carray), object)
def numpy_append_to_bcolz(a, b, **kwargs):
    return append(a, convert(np.ndarray, b), **kwargs)


@convert.register(ctable, np.ndarray)
def convert_numpy_to_bcolz_ctable(x, **kwargs):
    return ctable(x, **keyfilter(keywords.__contains__, kwargs))


@convert.register(carray, np.ndarray)
def convert_numpy_to_bcolz_carray(x, **kwargs):
    return carray(x, **keyfilter(keywords.__contains__, kwargs))


@convert.register(np.ndarray, (carray, ctable))
def convert_bcolz_to_numpy(x, **kwargs):
    return x[:]


@append.register((carray, ctable), chunks(np.ndarray))
def append_carray_with_chunks(a, c, **kwargs):
    for chunk in c:
        append(a, chunk)
    return a


@convert.register(chunks(np.ndarray), (ctable, carray))
def bcolz_to_numpy_chunks(x, chunksize=2**20, **kwargs):
    def load():
        for i in range(0, x.shape[0], chunksize):
            yield x[i: i + chunksize]
    return chunks(np.ndarray)(load)


@resource.register('.*\.bcolz/?')
def resource_bcolz(uri, dshape=None, **kwargs):
    if os.path.exists(uri):
        return ctable(rootdir=uri)
    else:
        if not dshape:
            raise ValueError("Must specify either existing bcolz directory or"
                    "valid datashape")
        dshape = datashape.dshape(dshape)

        dt = datashape.to_numpy_dtype(dshape)
        x = np.empty(shape=(0,), dtype=dt)

        if datashape.predicates.isrecord(dshape.measure):
            return ctable(x, rootdir=uri, **keyfilter(keywords.__contains__, kwargs))
        else:
            return carray(x, rootdir=uri, **keyfilter(keywords.__contains__, kwargs))
