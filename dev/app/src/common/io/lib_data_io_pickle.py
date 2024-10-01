"""
Library Features:

Name:          lob_data_io_pickle
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20171219'
Version:       '1.6.0'
"""
#################################################################################
# Logging
import logging
import pickle

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#################################################################################

# --------------------------------------------------------------------------------
# Method to open pickle file
def openFile(sFileName, sFileMode):

    try:
        if 'r' in sFileMode:
            oFile = open(sFileName, sFileMode + 'b')
        elif 'w' in sFileMode:
            oFile = open(sFileName, sFileMode + 'b')
        return oFile

    except IOError as oError:
        Exc.getExc(' -----> ERROR: in open file (lib_data_io_pickle)' + ' [' + str(oError) + ']', 1, 1)

# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to close pickle file
def closeFile(oFile):
    oFile.close()
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Get data using file handle
def getData(oFile):
    oData = pickle.load(oFile)
    return oData
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Save data using file handle
def writeData(oFile, oData):
    pickle.dump(oData, oFile, protocol=pickle.HIGHEST_PROTOCOL)
    return oFile
# --------------------------------------------------------------------------------
