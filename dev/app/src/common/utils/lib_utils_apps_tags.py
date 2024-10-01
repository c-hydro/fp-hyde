"""
Library Features:

Name:          lib_utils_apps_tag
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180521'
Version:       '2.0.7'
"""

#######################################################################################
# Library
from __future__ import print_function
import logging

from src.common.default.lib_default_args import sLoggerName

from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to merge tags
def mergeTags(oTags1, oTags2):

    oTagsComplete = {}
    for sKey1, oValue1 in iter(oTags1.items()):
        oTagsComplete[sKey1] = oValue1
    for sKey2, oValue2 in iter(oTags2.items()):
        if sKey2 in oTagsComplete:
            if oTagsComplete[sKey2] is None:
                if oValue2:
                    oTagsComplete[sKey2] = oValue2
                else:
                    pass
            else:
                pass
        else:
            oTagsComplete[sKey2] = oValue2

    return oTagsComplete
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to update tags
def updateTags(oDict, oTags):

    for sDictKey, oDictValue in oDict.items():

        sDictSubKey = list(oDictValue.keys())[0]

        if sDictSubKey in oTags.keys():
            oValue = oTags[sDictSubKey]
            oTagUpd = {sDictSubKey: oValue}
            oDict[sDictKey] = oTagUpd

        else:
            pass

    return oDict
# -------------------------------------------------------------------------------------
