"""
Class Features

Name:          drv_configuration_algorithm
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180521'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging
import json

from src.common.settings.lib_settings import selectDataSettings, setPathRoot, setPathFile
from src.common.default.lib_default_tags import oVarTags as oVarTags_Default

from src.common.utils.lib_utils_op_list import convertList2Dict

# Log
oLogStream = logging.getLogger(__name__)

# Debug
# import matplotlib.pylab as plt
#######################################################################################

# -------------------------------------------------------------------------------------
# Variable(s) definition
oFileKeyDef = dict(sKey1='folder', sKey2='filename')
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
class DataObject(dict):
    pass
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class Tags
class DataAlgorithm:

    # -------------------------------------------------------------------------------------
    # Global Variable(s)
    oDataSettings = None
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method class initialization
    def __init__(self, sFileSettings, sPathDelimiter='$'):

        # -------------------------------------------------------------------------------------
        # Store information in global workspace
        self.sFileSettings = sFileSettings
        self.sPathDelimiter = sPathDelimiter
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to set data tags
    def getDataSettings(self):

        # Get data settings
        sFileSettings = self.sFileSettings
        with open(sFileSettings) as oFileSettings:
            oDataSettings = json.load(oFileSettings)

        # Set root path(s)
        oDataPath = selectDataSettings(oDataSettings, sPathKey='folder')
        setPathRoot(oDataPath, path_delimiter=self.sPathDelimiter, path_noise=['{', '}'])
        # Set file path(s)
        oDataFile = selectDataSettings(oDataSettings, sPathKey='data')
        oDataInfo = findValues(oDataFile, list(oFileKeyDef.values()))
        oDataPath = setPathFile(oDataInfo, oFileKeyDef=oFileKeyDef)
        # Set data flags
        oDataFlags = selectDataSettings(oDataSettings, sPathKey='flags')
        oDataFlags = convertList2Dict(oDataFlags, var_split={'split': True, 'chunk': 2, 'key': 0})
        # Set colormap path(s)
        oColorMapFile = selectDataSettings(oDataSettings, sPathKey='colormap')
        oColorMapInfo = findValues(oColorMapFile, list(oFileKeyDef.values()))
        oColorMapPath = setPathFile(oColorMapInfo, oFileKeyDef=oFileKeyDef)

        return oDataSettings, oDataPath, oDataFlags, oColorMapPath
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to recursively find value of variable(s)
def findValues(oFile, oValueRef=['folder','filename']):

    oVarDict = {}
    for oVar in oFile:

        if isinstance(oFile, list):
            oVarName = oVar[0]
            oVarField = oVar[1]

        elif isinstance(oFile, dict):
            oVarName = oVar
            oVarField = oFile[oVar]

        if isinstance(oVarField, dict):

            if all(sValue in oVarField for sValue in oValueRef):
                sVarName = oVarName
                oVarDict[sVarName] = oVarField
            else:
                oVarDict_Upd = findValues(oVarField, oValueRef)
                if oVarDict:
                    for sKey, oValue in oVarDict_Upd.items():
                        oVarDict[sKey] = oValue
                else:
                    oVarDict = oVarDict_Upd

    return oVarDict
# -------------------------------------------------------------------------------------
