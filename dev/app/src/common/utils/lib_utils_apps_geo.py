"""
Library Features:

Name:          lib_utils_apps_geo
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180521'
Version:       '2.0.7'
"""

#################################################################################
# Libraries
import logging

import numpy as np

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
#################################################################################

# --------------------------------------------------------------------------------
# Method to create meshgrid (from 1d to 2d coordinates arrays)
def createMeshGrid(a1dGeoX, a1dGeoY):

    [a2dGeoX, a2dGeoY] = np.meshgrid(a1dGeoX, a1dGeoY, sparse=False, indexing='xy')
    a2dGeoY = np.flipud(a2dGeoY)
    return a2dGeoX, a2dGeoY
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to find XY geographical indexes
def findGeoIndex(a2dGeoX_REF, a2dGeoY_REF, a2dGeoX_VAR, a2dGeoY_VAR, dGeoCellSize_VAR):

    # Get geographical information
    dYU_REF = np.max(a2dGeoY_REF)
    dXL_REF = np.min(a2dGeoX_REF)
    # Compute index
    a1dIndexY_VAR = np.ceil((dYU_REF - a2dGeoY_VAR.ravel()) / dGeoCellSize_VAR)
    a1dIndexX_VAR = np.ceil((a2dGeoX_VAR.ravel() - dXL_REF) / dGeoCellSize_VAR)
    # From double to integer
    a1iIndexX_VAR = np.int32(a1dIndexX_VAR)
    a1iIndexY_VAR = np.int32(a1dIndexY_VAR)

    return a1iIndexX_VAR, a1iIndexY_VAR
# --------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Method to check domains are equal feature(s)
def checkGeoDomain(oGeoHeader_VAR=None, oGeoHeader_REF=None):

    a1bVarCheck = {}
    for sVarName_VAR, oVarValue_VAR in oGeoHeader_VAR.iteritems():
        if sVarName_VAR in oGeoHeader_REF:
            oVarValue_REF = oGeoHeader_REF[sVarName_VAR]
            if oVarValue_VAR == oVarValue_REF:
                a1bVarCheck[sVarName_VAR] = True
            else:
                a1bVarCheck[sVarName_VAR] = False
        else:
            a1bVarCheck[sVarName_VAR] = False

    if all(a1bVarCheck.values()):
        bVarCheck = True
    else:
        bVarCheck = False

    return bVarCheck

# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Method to read geographical box
def readGeoBox(a1oGeoBox):

    dGeoXMin = a1oGeoBox['xllcorner']
    dGeoYMin = a1oGeoBox['yllcorner']
    dGeoXMax = a1oGeoBox['xurcorner']
    dGeoYMax = a1oGeoBox['yurcorner']
    dGeoXStep = a1oGeoBox['xcellsize']
    dGeoYStep = a1oGeoBox['ycellsize']

    if 'nrows' in a1oGeoBox:
        iRows = a1oGeoBox['nrows']
    else:
        iRows = int(np.round((dGeoYMax - dGeoYMin) / dGeoYStep + 1))

    if 'ncols' in a1oGeoBox:
        iCols = a1oGeoBox['ncols']
    else:
        iCols = int(np.round((dGeoXMax - dGeoXMin) / dGeoXStep + 1))

    return iRows, iCols, dGeoXMin, dGeoYMin, dGeoXMax, dGeoYMax, dGeoXStep, dGeoYStep

# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Method to define geographical box
def defineGeoBox(dGeoXMin, dGeoYMin, dGeoXMax, dGeoYMax, dGeoXStep, dGeoYStep):

    iCols = int(np.round((dGeoXMax - dGeoXMin) / dGeoXStep + 1))
    iRows = int(np.round((dGeoYMax - dGeoYMin) / dGeoYStep + 1))

    a1oGeoBox = {'xllcorner': dGeoXMin, 'xurcorner': dGeoXMax, 'yllcorner': dGeoYMin, 'yurcorner': dGeoYMax,
                 'xcellsize': dGeoXStep, 'ycellsize': dGeoYStep, 'nrows': iRows, 'ncols': iCols}

    return a1oGeoBox

# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Method to read header of geographical Data
def readGeoHeader(a1oGeoHeader):

    iRows = a1oGeoHeader['nrows']
    iCols = a1oGeoHeader['ncols']
    dGeoXMin = a1oGeoHeader['xllcorner']
    dGeoYMin = a1oGeoHeader['yllcorner']
    dGeoXStep = a1oGeoHeader['cellsize']
    dGeoYStep = a1oGeoHeader['cellsize']
    try:
        dNoData = a1oGeoHeader['NODATA_value']
    except BaseException:
        dNoData = a1oGeoHeader['nodata_value']

    return iRows, iCols, dGeoXMin, dGeoYMin, dGeoXStep, dGeoYStep, dNoData

# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Method to define header of geographical Data
def defineGeoHeader(iRows, iCols, dGeoXMin, dGeoYMin, dGeoXStep, dGeoYStep, dNoData):

    a1oGeoHeader = {'nrows': iRows, 'ncols': iCols, 'xllcorner': dGeoXMin,
                    'cellsize': dGeoXStep, 'yllcorner': dGeoYMin,
                    'NODATA_value': dNoData}

    return a1oGeoHeader
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Method to define goegraphical corners (geox min, geox max, geoy min and geoy max)
def defineGeoCorner(dGeoXMin, dGeoYMin, dGeoXStep, dGeoYStep, iCols, iRows, iGeoDecimal=3):

    # Define geographical cell center
    dGeoXMin = dGeoXMin + dGeoXStep / 2.
    dGeoYMin = dGeoYMin + dGeoYStep / 2.

    # Compute
    dGeoXMax = dGeoXMin + (iCols - 1) * dGeoXStep
    dGeoYMax = dGeoYMin + (iRows - 1) * dGeoYStep

    if iGeoDecimal is not None:
        dGeoXMax = np.around(dGeoXMax, decimals=iGeoDecimal)
        dGeoYMax = np.around(dGeoYMax, decimals=iGeoDecimal)
        dGeoXMin = np.around(dGeoXMin, decimals=iGeoDecimal)
        dGeoYMin = np.around(dGeoYMin, decimals=iGeoDecimal)

    return dGeoXMin, dGeoXMax, dGeoYMin, dGeoYMax

# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Method to define geographical information (geox, geoy, geobox)
def defineGeoGrid(dGeoYMin, dGeoXMin, dGeoYMax, dGeoXMax, dGeoYStep, dGeoXStep, iGeoDecimal=3):

    # -------------------------------------------------------------------------------------
    # Creating geox and geoy references
    a1dGeoX = np.arange(dGeoXMin, dGeoXMax + np.abs(dGeoXStep / 2), np.abs(dGeoXStep), float)
    a1dGeoY = np.arange(dGeoYMin, dGeoYMax + np.abs(dGeoYStep / 2), np.abs(dGeoYStep), float)

    a2dGeoX, a2dGeoY = np.meshgrid(a1dGeoX, a1dGeoY)
    a2dGeoY = np.flipud(a2dGeoY)

    dGeoXMin = np.nanmin(a2dGeoX)
    dGeoXMax = np.nanmax(a2dGeoX)
    dGeoYMax = np.nanmax(a2dGeoY)
    dGeoYMin = np.nanmin(a2dGeoY)
    oGeoBox = [dGeoXMin, dGeoYMax, dGeoXMax, dGeoYMin]

    a1dGeoBox = np.around(oGeoBox, decimals=iGeoDecimal)

    return a2dGeoX, a2dGeoY, a1dGeoBox
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to define finite and undefined geographical indexes
def defineGeoIndex(a2dGeoData, dNoData=-9999):

    # Define Data, finite and nan value(s)
    a2dGeoData = np.asarray(a2dGeoData, dtype=np.float32)
    a2bGeoDataFinite = (a2dGeoData != dNoData)
    a2bGeoDataNaN = (a2dGeoData == dNoData)
    a1iGeoIndexNaN = np.where(a2bGeoDataFinite.ravel() == False)[0]
    a1iGeoIndexFinite = np.where(a2bGeoDataFinite.ravel() == True)[0]

    return a2bGeoDataNaN, a2bGeoDataFinite, a1iGeoIndexNaN, a1iGeoIndexFinite

# -------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to convert curve number to maximum volume
def computeCN2VMax(a2dDataCN):

    # Initialize VMax 2D array
    a2dDataVMax = np.zeros([a2dDataCN.shape[0], a2dDataCN.shape[1]])
    a2dDataVMax[:, :] = np.nan

    # Compute VMax starting from Curve Number values
    a2dDataVMax = (1000/a2dDataCN - 10) * 25.4

    #a2dMapVMax(a1iIndexNanCN) = NaN;

    return a2dDataVMax

# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to convert decimal degrees to km
def Deg2Km_2(deg, lat=None):
    if lat is None:
        km = deg * 110.54
    else:
        km = deg * 111.32 * np.cos(np.deg2rad(lat))
    return km
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to convert decimal degrees to km (2)
def Deg2Km(deg):
    # Earth radius
    dRE = 6378.1370
    km = deg * (np.pi * dRE) / 180;
    return km
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to convert km to decimal degrees
def Km2Deg(km):
    # Earth radius
    dRE = 6378.1370
    deg = 180 * km / (np.pi * dRE)
    return deg
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to correct GeoHeader key(s) to lower character(s)
def correctGeoHeader(a1oGeoHeader):

    a1oGeoHeaderUpd = {}
    for sK, oV in iter(a1oGeoHeader.items()):
        sKUpd = sK.lower()
        a1oGeoHeaderUpd[sKUpd] = oV

    return a1oGeoHeaderUpd
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to get pixel using coordinates
def world2Pixel(geoMatrix, x, y):
    # from osgeo import gdal
    # src = gdal.Open("/qgis_data/rasters/satimage.tif")
    # geoTrans = src.GetGeoTransform()
    # world2Pixel(geoTrans, -89.59486002580364, 30.510227817850406)

    ulX = geoMatrix[0]
    ulY = geoMatrix[3]
    xDist = geoMatrix[1]
    yDist = geoMatrix[5]
    rtnX = geoMatrix[2]
    rtnY = geoMatrix[4]

    pixel = int((x - ulX) / xDist)
    line = int((y - ulY) / yDist)

    return pixel, line
# --------------------------------------------------------------------------------
