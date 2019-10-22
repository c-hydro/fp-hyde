"""
Library Features:

Name:          lib_analysis_filtering
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20150903'
Version:       '1.5.1'
"""

#######################################################################################
# Logging
import logging
import re

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
#######################################################################################

# -------------------------------------------------------------------------------------
# Method to define look up table
def defineLookUpTable(a1oLUTValues, a1oLUTMasks, a1oLUTMeanings):

    oLUT = {}
    for oValue, oMask, sMeaning in zip(a1oLUTValues, a1oLUTMasks, a1oLUTMeanings):

        oLUT[sMeaning] = {}
        oLUT[sMeaning]['in'] = {}
        oLUT[sMeaning]['out'] = {}

        if isinstance(oValue, str):
            oValue = [oValue]
        if isinstance(oMask, str):
            oMask = [oMask]

        if oValue.__len__() == 2:
            if oValue[0] is not None:
                dValMin = float(oValue[0])
            else:
                dValMin = None
            if oValue[1] is not None:
                dValMax = float(oValue[1])
            else:
                dValMax = None
        elif oValue.__len__() == 1:
            if oValue[0] is not None:
                dValMin = float(oValue[0])
                dValMax = float(oValue[0])
            else:
                dValMin = None
                dValMax = None

        if oMask.__len__() == 2:
            if oMask[0] is not None:
                dMaskMin = float(oMask[0])
            else:
                dMaskMin = None
            if oMask[1] is not None:
                dMaskMax = float(oMask[1])
            else:
                dMaskMax = None
        elif oMask.__len__() == 1:
            if oMask[0] is not None:
                dMaskMin = float(oMask[0])
                dMaskMax = float(oMask[0])
            else:
                dMaskMin = None
                dMaskMax = None

        if (dValMin == dMaskMin) and (dValMax == dMaskMax):
            oLUT[sMeaning]['in']['min'] = dValMin
            oLUT[sMeaning]['in']['max'] = dValMax
            oLUT[sMeaning]['out'] = None
        elif (dValMin != dMaskMin) and (dValMax != dMaskMax):
            oLUT[sMeaning]['in']['min'] = dValMin
            oLUT[sMeaning]['in']['max'] = dValMax
            if oMask.__len__() == 2:
                oLUT[sMeaning]['out']['min'] = dMaskMin
                oLUT[sMeaning]['out']['max'] = dMaskMax
            elif oMask.__len__() == 1:
                oLUT[sMeaning]['out'] = dMaskMin

    return oLUT

# -------------------------------------------------------------------------------------
