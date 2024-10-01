"""
Class Features

Name:          drv_configuration_tags
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180521'
Version:       '2.0.7'
"""

#######################################################################################
# Library
import logging
from copy import deepcopy

from src.common.utils.lib_utils_apps_tags import updateTags
from src.common.utils.lib_utils_op_string import defineString

from src.common.default.lib_default_tags import oVarTags as oVarTags_Default

# Log
oLogStream = logging.getLogger(__name__)

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
class DataObject(dict):
    pass
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class Tags
class DataTags:

    # -------------------------------------------------------------------------------------
    # Global Variable(s)
    oVarTags_OUT = None
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method class initialization
    def __init__(self, oVarTags_IN):

        # -------------------------------------------------------------------------------------
        # Store information in global workspace
        self.oVarTags_IN = oVarTags_IN
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to set data tags
    def setDataTags(self):

        oVarTags_DEF = deepcopy(oVarTags_Default)
        oVarTags_OUT = updateTags(oVarTags_DEF, self.oVarTags_IN)

        return oVarTags_OUT
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    @staticmethod
    def defineDataTags(sString, oTags):
        return defineString(sString, oTags)
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
