"""
Library Features:

Name:          drv_model_griso_generic
Author(s):     Andrea Libertino (andrea.libertino@cimafoundation.org)
Date:          '20210311'
Version:       '1.0.0'
"""
# -------------------------------------------------------------------------------------
# Complete library
import numpy as np

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

# ---------------------------------------------------
# Linear to polar coordinates
def cart2pol(x, y):
    import math

    r = (x ** 2 + y ** 2) ** .5
    theta = np.degrees(np.arctan2(y,x))
    return r, theta

