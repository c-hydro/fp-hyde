"""
Library Features:

Name:          lib_utils_op_var
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180521'
Version:       '2.0.7'
"""

#######################################################################################
# Library
import logging
import math
import re

from numpy import generic, asscalar, transpose, rot90
import numpy as np

from src.common.default.lib_default_args import sLoggerName

from src.common.driver.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
#######################################################################################

# -------------------------------------------------------------------------------------
# Method to adjust variable from python to fortran
def adjustVarPy2F(a2dVarPy, sVarFormat='float32'):

    # Transpose and rotate 2d array
    a2dVarTemp = transpose(rot90(a2dVarPy, -1))

    # Cast variable to float32 to match real(kind = 4) in fortran routine
    if hasattr(np, sVarFormat):
        oVarFormat = getattr(np, sVarFormat)
    else:
        oVarFormat = None

    if oVarFormat:
        a2dVarF = oVarFormat(a2dVarTemp)
    else:
        a2dVarF = np.float32(a2dVarTemp)

    return a2dVarF

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to adjust variable from fortran to python
def adjustVarF2Py(a2dVarF, sVarFormat='float32'):

    # Transpose and rotate 2d array
    a2dVarTemp = rot90(transpose(a2dVarF), 1)

    # Cast variable to float32 to match real(kind = 4) in fortran routine
    if hasattr(np, sVarFormat):
        oVarFormat = getattr(np, sVarFormat)
    else:
        oVarFormat = None

    if oVarFormat:
        a2dVarPy = oVarFormat(a2dVarTemp)
    else:
        a2dVarPy = np.float32(a2dVarTemp)

    return a2dVarPy

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Convert numpy variable to generic python variable
def convertVarType(obj):
    if isinstance(obj, generic):
        return asscalar(obj)
    else:
        return obj
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to look-up var precision (type format = '{0:.3f}')
def lookupVarPrecision(format_string):
    return int(re.findall(r'\d+', format_string)[1])
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to get variable precision
def getVarPrecision(x):
    max_digits = 14
    int_part = int(abs(x))
    magnitude = 1 if int_part == 0 else int(math.log10(int_part)) + 1
    if magnitude >= max_digits:
        return magnitude, 0

    frac_part = abs(x) - int_part
    multiplier = 10 ** (max_digits - magnitude)
    frac_digits = multiplier + int(multiplier * frac_part + 0.5)
    while frac_digits % 10 == 0:
        frac_digits /= 10
    scale = int(math.log10(frac_digits))
    return magnitude + scale, scale
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to print variable array format
def printVarFormat(a, format_string='{0:.4f}'):
    values = []
    for i, v in enumerate(a):
        [magnitude, scale] = getVarPrecision(v)
        precision_req = lookupVarPrecision(format_string)

        if precision_req >= scale:
            values.append(v)
        else:
            values.append(format_string.format(v, i))

    return values
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to get variable as a string
def retrieveVarName(var):
    import inspect
    callers_local_vars = inspect.currentframe().f_back.f_locals.items()
    return [var_name for var_name, var_val in callers_local_vars if var_val is var]
# -------------------------------------------------------------------------------------
