"""
Library Features:

Name:          lib_analysis_interpolation
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20150903'
Version:       '1.5.1'
"""

#######################################################################################
# Logging
import logging

from numpy import arange, reshape
from scipy.interpolate import griddata

from lib_default_args import sLoggerName
from drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
#######################################################################################

# --------------------------------------------------------------------------------
# Method to interpolate grid index using NN
def interpGridIndex(oData_IN, oGeoX_IN, oGeoY_IN, oGeoX_OUT, oGeoY_OUT,
                    dNoData_OUT=-9999.0, sInterpMethod='nearest'):

    if oData_IN.shape.__len__() == 1:
        iDataDim_IN = oData_IN.shape[0]
    elif oData_IN.shape.__len__() == 2:
        iDataDim_IN = oData_IN.shape[0] * oData_IN.shape[1]

    a1iIndex_IN = arange(0, iDataDim_IN)

    a1iIndex_OUT = griddata((oGeoX_IN.ravel(), oGeoY_IN.ravel()),
                            a1iIndex_IN,
                            (oGeoX_OUT.ravel(), oGeoY_OUT.ravel()), method=sInterpMethod,
                            fill_value=dNoData_OUT)

    return a1iIndex_OUT

# --------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to interpolate data (using griddata)
def interpGridData(a2dData_IN, a2dGeoX_IN, a2dGeoY_IN, a2dGeoX_OUT, a2dGeoY_OUT,
                   dNoData_OUT=-9999.0, sInterpMethod='nearest',
                   a1iVarIndex_OUT=None):

    if a1iVarIndex_OUT is None:
        a2dData_OUT = griddata((a2dGeoX_IN.ravel(), a2dGeoY_IN.ravel()),
                               a2dData_IN.ravel(),
                               (a2dGeoX_OUT, a2dGeoY_OUT), method=sInterpMethod,
                               fill_value=dNoData_OUT)
    else:
        a1dData_OUT = a2dData_IN.ravel()[a1iVarIndex_OUT]
        a2dData_OUT = reshape(a1dData_OUT, [a2dGeoX_OUT.shape[0], a2dGeoY_OUT.shape[1]])

    return a2dData_OUT
# -------------------------------------------------------------------------------------
