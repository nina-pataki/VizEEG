import h5py
import numpy as np

def createMinMax(h5File, h5Path):
    f = h5py.File(h5File, 'a')
    indset = f[h5Path]

    shape = indset.shape
    dtype = indset.dtype
    n_chan = shape[1]
    n_sample = shape[0]

    n_levels = int(np.log10(n_sample)) -2 # last level magnitude 10**2


    gh = f.create_group('minmax')
    g_min = gh.create_group('h_min')
    g_max = gh.create_group('h_max')


    n_hsamp = n_sample
    d_min0 = indset
    d_max0 = indset
    for l in range(n_levels):
        n_hsamp = int(np.ceil(n_hsamp / 10.0))
        d_min = g_min.create_dataset(str(l),(n_hsamp,n_chan))
        d_max = g_max.create_dataset(str(l),(n_hsamp,n_chan))
        for i in xrange(n_hsamp):
            d_min[i,:] = np.min(d_min0[i*10:(i+1)*10,:],axis=0)
            d_max[i,:] = np.max(d_max0[i*10:(i+1)*10,:],axis=0)
        d_min0 = d_min
        d_max0 = d_max


    f.close()
