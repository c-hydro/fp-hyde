"""
Library Features:

Name:          drv_model_griso_generic
Author(s):     Andrea Libertino (andrea.libertino@cimafoundation.org)
               Flavio Pignone (flavio.pignone@cimafoundation.org)
Date:          '20211026'
Version:       '2.0.0'
"""
# -------------------------------------------------------------------------------------
# Complete library
import numpy as np
from skgstat.models import spherical
from scipy.optimize import curve_fit
from skgstat import Variogram

# -------------------------------------------------------------------------------------
# Average conversion of cellsize from degree to kilometers
def deg2km(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, asin
    R = 6372.8  # Earth radius in kilometers

    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)

    a = sin(dLat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dLon / 2) ** 2
    c = 2 * asin(sqrt(a))

    return R * c
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Matrix coordinates to row indices
def sub2ind(mat, nrow, ncol):
    ind = np.ravel_multi_index(mat, dims=(int(nrow), int(ncol), 1), order='F')

    return ind
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Average rainfall values within cells
def averageCells(rPluvio,cPluvio,values):

    coo = np.vstack([rPluvio, cPluvio]).T
    sortidx = np.lexsort(coo.T)
    sorted_coo =  coo[sortidx]
    # Get mask of start of each unique coo XY
    unqID_mask = np.append(True,np.any(np.diff(sorted_coo,axis=0),axis=1))
    # Tag/ID each coo XY based on their uniqueness among others
    ID = unqID_mask.cumsum()-1
    # Get unique coo XY's
    unq_coo = sorted_coo[unqID_mask]
    # Finally use bincount to get the summation of all coo within same IDs
    # and their counts and thus the average values
    average_values = np.bincount(ID,np.squeeze(values[sortidx]))/np.bincount(ID)
    rPluvio=unq_coo[:,0]
    cPluvio=unq_coo[:,1]

    return rPluvio,cPluvio,average_values
# -------------------------------------------------------------------------------------

# ---------------------------------------------------
# Linear to polar coordinates
def cart2pol(x, y):
    import math

    r = (x ** 2 + y ** 2) ** .5
    theta = np.degrees(np.arctan2(y,x))
    return r, theta
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Function for fit a theoretical variogram to a spherical one with nugget = 0 and sill = 1
def sphericalFit(x,y,range_min,range_max,range_0, c0=0,c1=1):
    def spheric(x,radius):
        return c0 + c1 * (1 - 3 / 2 * x / radius + 1 / 2 * (x / radius) ** 3) * (x < radius)

    x0 = x.flatten('F')[~np.isnan(y.flatten('F'))]
    y0 = y.flatten('F')[~np.isnan(y.flatten('F'))]

    radius_opt, _ = curve_fit(spheric, x0, y0, p0 = range_0, bounds=(range_min, range_max))
    CorrStim = spheric(x,radius_opt)

    return CorrStim, radius_opt
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Function for fit a theoretical variogram to an empirical one
def variogramFit(x, y, range_0, sill_0 , range_lim=None, sill_lim=None, type='spherical'):
    if type=='spherical':
        def f(h, a, b):
            return spherical(h, a, b)
    else:
        raise NotImplementedError('Only spheric variogram is implemented')

    x0=x.flatten('F')[~np.isnan(y.flatten('F'))]
    y0=y.flatten('F')[~np.isnan(y.flatten('F'))]

    if range_lim is None:
        range_lim = np.max(x0)

    if sill_lim is None:
        sill_lim = np.max(1-y0)

    cof, cov = curve_fit(f, x0, 1 - y0, p0=[range_0, sill_0], bounds=(0, (range_lim, sill_lim)))
    y1 = 1 - np.array(list(map(lambda x: spherical(x, *cof), x.flatten('F')))).reshape(y.shape, order='F')
    y1[np.isnan(y)] = 0

    return y1, cof[0]
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------

