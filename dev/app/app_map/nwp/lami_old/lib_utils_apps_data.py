"""
Library Features:

Name:          lib_utils_apps_data
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180711'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging
from copy import deepcopy
from numpy import squeeze

from lib_default_args import sLoggerName
from drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
#######################################################################################

# -------------------------------------------------------------------------------------
#  Method to squeeze data array
def squeezeDataArray(oVarData_IN, iVarAxis=None):

    if iVarAxis:
        iVarDims_IN = oVarData_IN.ndim
        if iVarDims_IN - 1 >= iVarAxis:
            oVarData_OUT = squeeze(oVarData_IN, axis=(iVarAxis,))
        else:
            oVarData_OUT = oVarData_IN
    else:
        oVarData_OUT = oVarData_IN

    return oVarData_OUT
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to update data stored in a dict stucture
def updateDictStructure(oDictDefault, oDictDef, sDictTag=None):

    if sDictTag is not None:
        if sDictTag in oDictDefault:
            oDictDefault = deepcopy(oDictDefault[sDictTag])
        if sDictTag in oDictDef:
            oDictDef = deepcopy(oDictDef[sDictTag])

    for sDictKey, oDictValue in oDictDef.items():
        if sDictKey in oDictDefault.keys():
            oDictDefault[sDictKey] = oDictValue

    return oDictDefault
# -------------------------------------------------------------------------------------
