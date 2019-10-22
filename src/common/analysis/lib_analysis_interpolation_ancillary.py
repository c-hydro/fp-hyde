"""
Library Features:

Name:          lib_analysis_interpolation_ancillary
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180821'
Version:       '1.6.0'
"""

#######################################################################################
# Logging
import logging
import tempfile

from numpy import unique, where, isnan, delete, min, max, nonzero, savetxt, hstack, empty, reshape

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
#######################################################################################

# -------------------------------------------------------------------------------------
# Method to create csv ancillary file
def createPointFile_CSV(sFileName_CSV, a2dVarData, sVarData='values', sVarGeoX='x', sVarGeoY='y',
                        sFileFormat='%10.4f', sFileDelimiter=','):
    oFileCSV = open(sFileName_CSV, 'w')
    oFileCSV.write(sVarGeoX + ',' + sVarGeoY + ',' + sVarData + '\n')
    savetxt(oFileCSV, a2dVarData, fmt=sFileFormat, delimiter=sFileDelimiter, newline='\n')
    oFileCSV.close()
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to create vrt ancillary file
def createPointFile_VRT(sFileName_VRT, sFileName_CSV, sLayerName, sVarData='values', sVarGeoX='x', sVarGeoY='y'):

    oFileVRT = open(sFileName_VRT, 'w')
    oFileVRT.write('<OGRVRTDataSource>\n')
    oFileVRT.write('    <OGRVRTLayer name="' + sLayerName + '">\n')
    oFileVRT.write('        <SrcDataSource>' + sFileName_CSV + '</SrcDataSource>\n')
    oFileVRT.write('    <GeometryType>wkbPoint</GeometryType>\n')
    oFileVRT.write('    <LayerSRS>WGS84</LayerSRS>\n')
    oFileVRT.write(
        '    <GeometryField encoding="PointFromColumns" x="' +
        sVarGeoX + '" y="' + sVarGeoY + '" z="' + sVarData + '"/>\n')
    oFileVRT.write('    </OGRVRTLayer>\n')
    oFileVRT.write('</OGRVRTDataSource>\n')
    oFileVRT.close()

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to filter data over domain
def filterData_Domain(a2dDataValue_IN, a1iDataIdx, dDataNoValue=-9999.0):

    iDataRows, iDataCols = a2dDataValue_IN.shape

    a1dDataValue_OUT = a2dDataValue_IN.ravel()
    a1dDataValue_OUT[a1iDataIdx] = dDataNoValue

    a2dDataValue_OUT = reshape(a1dDataValue_OUT, [iDataRows, iDataCols])

    return a2dDataValue_OUT
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to filter data deleting no data and undefined values
def filterData_ValidRange(a1dData_IN, a1dGeoX_IN=None, a1dGeoY_IN=None, a1dGeoZ_IN=None, oValidRange=None):

    # Valid range definition(s)
    if oValidRange is None:
        oValidRange = [None, None]
    dDataMin_IN = oValidRange[0]
    dDataMax_IN = oValidRange[1]

    if dDataMin_IN is not None:
        a1iIndex_MINDATA = where(a1dData_IN.ravel() < dDataMin_IN)[0]
    else:
        a1iIndex_MINDATA = empty([0])
    if dDataMax_IN is not None:
        a1iIndex_MAXDATA = where(a1dData_IN.ravel() > dDataMax_IN)[0]
    else:
        a1iIndex_MAXDATA = empty([0])

    a1iIndex_VALIDRANGE = unique(hstack((a1iIndex_MINDATA.tolist(), a1iIndex_MAXDATA.tolist())))

    a1dData_FILTER_VALIDRANGE = delete(a1dData_IN.ravel(), a1iIndex_VALIDRANGE)
    if a1dGeoX_IN is not None:
        a1dGeoX_FILTER_VALIDRANGE = delete(a1dGeoX_IN.ravel(), a1iIndex_VALIDRANGE)
        if a1dGeoX_FILTER_VALIDRANGE.size == 0:
            a1dGeoX_FILTER_VALIDRANGE = None
    else:
        a1dGeoX_FILTER_VALIDRANGE = None
    if a1dGeoY_IN is not None:
        a1dGeoY_FILTER_VALIDRANGE = delete(a1dGeoY_IN.ravel(), a1iIndex_VALIDRANGE)
        if a1dGeoY_FILTER_VALIDRANGE.size == 0:
            a1dGeoY_FILTER_VALIDRANGE = None
    else:
        a1dGeoY_FILTER_VALIDRANGE = None
    if a1dGeoZ_IN is not None:
        a1dGeoZ_FILTER_VALIDRANGE = delete(a1dGeoZ_IN.ravel(), a1iIndex_VALIDRANGE)
        if a1dGeoZ_FILTER_VALIDRANGE.size == 0:
            a1dGeoZ_FILTER_VALIDRANGE = None
    else:
        a1dGeoZ_FILTER_VALIDRANGE = None

    # Filter nan values
    a1iIndex_NAN = where(isnan(a1dData_FILTER_VALIDRANGE))

    a1dGeoX_FILTER_NAN = None
    a1dGeoY_FILTER_NAN = None
    a1dGeoZ_FILTER_NAN = None

    a1dData_FILTER_NAN = delete(a1dData_FILTER_VALIDRANGE.ravel(), a1iIndex_NAN)
    if a1dGeoX_FILTER_VALIDRANGE is not None:
        a1dGeoX_FILTER_NAN = delete(a1dGeoX_FILTER_VALIDRANGE.ravel(), a1iIndex_NAN)
    if a1dGeoY_FILTER_VALIDRANGE is not None:
        a1dGeoY_FILTER_NAN = delete(a1dGeoY_FILTER_VALIDRANGE.ravel(), a1iIndex_NAN)
    if a1dGeoZ_FILTER_VALIDRANGE is not None:
        a1dGeoZ_FILTER_NAN = delete(a1dGeoZ_FILTER_VALIDRANGE.ravel(), a1iIndex_NAN)

    # Check data
    if (a1dGeoX_FILTER_NAN is not None) and (a1dGeoY_FILTER_NAN is not None):
        if (a1dGeoX_FILTER_NAN.size > 0) and (a1dGeoY_FILTER_NAN.size > 0):
            a1dData_OUT = a1dData_FILTER_NAN
            a1dGeoX_OUT = a1dGeoX_FILTER_NAN
            a1dGeoY_OUT = a1dGeoY_FILTER_NAN
            a1dGeoZ_OUT = a1dGeoZ_FILTER_NAN
        else:
            a1dData_OUT = None
            a1dGeoX_OUT = None
            a1dGeoY_OUT = None
            a1dGeoZ_OUT = None
    else:
        a1dData_OUT = None
        a1dGeoX_OUT = None
        a1dGeoY_OUT = None
        a1dGeoZ_OUT = None

    return a1dData_OUT, a1dGeoX_OUT, a1dGeoY_OUT, a1dGeoZ_OUT
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to filter data deleting no data and undefined values
def filterData_Undefined(a1dData_IN, a1dGeoX_IN, a1dGeoY_IN, dNoData_IN):

    # Filter no data values
    a1iIndex_NODATA = where(a1dData_IN.ravel() == dNoData_IN)
    a1dData_FILTER_NODATA = delete(a1dData_IN.ravel(), a1iIndex_NODATA)
    a1dGeoX_FILTER_NODATA = delete(a1dGeoX_IN.ravel(), a1iIndex_NODATA)
    a1dGeoY_FILTER_NODATA = delete(a1dGeoY_IN.ravel(), a1iIndex_NODATA)

    # Filter nan values
    a1iIndex_NAN = where(isnan(a1dData_FILTER_NODATA))
    a1dData_FILTER_NAN = delete(a1dData_FILTER_NODATA.ravel(), a1iIndex_NAN)
    a1dGeoX_FILTER_NAN = delete(a1dGeoX_FILTER_NODATA.ravel(), a1iIndex_NAN)
    a1dGeoY_FILTER_NAN = delete(a1dGeoY_FILTER_NODATA.ravel(), a1iIndex_NAN)

    # Check data
    if (a1dGeoX_FILTER_NAN.size > 0) and (a1dGeoY_FILTER_NAN.size > 0):
        a1dData_OUT = a1dData_FILTER_NAN
        a1dGeoX_OUT = a1dGeoX_FILTER_NAN
        a1dGeoY_OUT = a1dGeoY_FILTER_NAN
    else:
        a1dData_OUT = None
        a1dGeoX_OUT = None
        a1dGeoY_OUT = None

    return a1dData_OUT, a1dGeoX_OUT, a1dGeoY_OUT

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to filter data over selected output geographical box
def filterData_GeoBox(a1dData_IN, a1dGeoX_IN, a1dGeoY_IN, a2dGeoX_OUT, a2dGeoY_OUT):

    if (a1dGeoX_IN is not None) and (a1dGeoY_IN is not None):

        dGeoX_OUT_MIN = min(a2dGeoX_OUT)
        dGeoX_OUT_MAX = max(a2dGeoX_OUT)
        dGeoY_OUT_MIN = min(a2dGeoY_OUT)
        dGeoY_OUT_MAX = max(a2dGeoY_OUT)

        # Checking values on selected domain
        a1iIndex_GeoBox = nonzero(((a1dGeoX_IN >= dGeoX_OUT_MIN) & (a1dGeoX_IN <= dGeoX_OUT_MAX)) &
                                  ((a1dGeoY_IN >= dGeoY_OUT_MIN) & (a1dGeoY_IN <= dGeoY_OUT_MAX)))
        a1iIndex_GeoBox = a1iIndex_GeoBox[0]

        if a1iIndex_GeoBox is not None:
            a1dData_OUT = a1dData_IN[a1iIndex_GeoBox]
            a1dGeoX_OUT = a1dGeoX_IN[a1iIndex_GeoBox]
            a1dGeoY_OUT = a1dGeoY_IN[a1iIndex_GeoBox]
        else:
            a1dData_OUT = a1dData_IN
            a1dGeoX_OUT = a1dGeoX_IN
            a1dGeoY_OUT = a1dGeoY_IN

    else:
        a1dData_OUT = None
        a1dGeoX_OUT = None
        a1dGeoY_OUT = None

    return a1dData_OUT, a1dGeoX_OUT, a1dGeoY_OUT
# -------------------------------------------------------------------------------------
