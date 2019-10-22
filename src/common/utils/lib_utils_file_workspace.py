"""
Library Features:

Name:          lib_debug
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190913'
Version:       '2.1.0'
"""
#######################################################################################
# Library
import logging

import shelve
import pickle
import scipy.io as sio

from src.common.utils.lib_utils_op_system import createFolderByFile

# Log
log_stream = logging.getLogger(__name__)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to save variable(s) workspace
def saveWorkspace(sFileName, **kwargs):
    oShelf = shelve.open(sFileName, 'n')
    for oKey, oValue in iter(kwargs.items()):
        try:
            oShelf[oKey] = oValue
        except TypeError:
            log_stream.error(' =====> ERROR saving: {0}'.format(oKey))
    oShelf.close()
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to restore variable(s) workspace
def restoreWorkspace(sFileName):
    oShelf = shelve.open(sFileName)
    oDictArgs = {}
    for oKey in oShelf:
        try:
            oDictArgs[oKey] = oShelf[oKey]
        except TypeError:
            log_stream.error(' =====> ERROR saving: {0}'.format(oKey))
    oShelf.close()
    return oDictArgs
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to save pickle file
def savePickle(sFileName, oVarData):

    createFolderByFile(sFileName)

    oFile = open(sFileName, 'wb')
    pickle.dump(oVarData, oFile, protocol=pickle.HIGHEST_PROTOCOL)
    oFile.close()
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to restore pickle file
def restorePickle(sFileName):

    createFolderByFile(sFileName)

    oFile = open(sFileName, 'rb')
    oVarData = pickle.load(oFile)
    oFile.close()
    return oVarData
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to save mat file
def saveMat(sFileName, oVarData, sVarName):
    oData = {sVarName: oVarData}
    sio.savemat(sFileName, oData)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to restore mat file
def restoreMat(sFileName):
    return sio.loadmat(sFileName)
# -------------------------------------------------------------------------------------
