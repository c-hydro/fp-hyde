"""
Library Features:

Name:          Lib_Data_IO_Binary
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20161114'
Version:       '2.0.6'
"""
#################################################################################
# Library
import logging
import numpy as np

from Lib_HMC_Struct_Args import sLoggerFormat
from Drv_HMC_Exception import Exc

# Log
oLogStream = logging.getLogger(sLoggerFormat)

# Debug
import matplotlib.pylab as plt
#################################################################################

# --------------------------------------------------------------------------------
# Method to open binary file
def openFile(sFileName, sFileMode):
    try:  # Read = 'rb: Write = 'wb'
        oFile = open(sFileName, sFileMode + 'b')
        return oFile
    except IOError as oError:
        Exc.getExc(' =====> ERROR: in open file (Lib_Data_IO_Binary)' + ' [' + str(oError) + ']', 1, 1)
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to close binary file
def closeFile(oFile):
    oFile.close()
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to write 2d variable in binary format (saved as 1d integer array)
def write2DVar(oFileData, a2dVarData, sVarFormat='i', iVarScaleFactor=10):
    # Import library
    import struct

    # Define nodata value
    dNoData = -9999.0
    dNoData = dNoData / iVarScaleFactor

    # Values shape (1d)
    iNVals = a2dVarData.shape[0] * a2dVarData.shape[1]
    # Values format sVarFormat = 'i'
    sDataFormat = sVarFormat * iNVals

    # Define nodata value (instead of NaN values)
    a2dVarData[np.where(np.isnan(a2dVarData))] = dNoData

    # NOTA BENE:
    # NON OCCORRE FARE IL FLIPUD SE LE VAR SONO ORIENTATE IN MODO CORRETTO partendo da angolo
    # IN BASSO A SX [sud-->nord ovest --> est]
    # a1iVarData = np.int32((numpy.flipud(a2dVarData)).reshape(iNVals, order='F') * iScaleFactor)

    a1iVarData = np.int32(((a2dVarData)).reshape(iNVals, order='F') * iVarScaleFactor)
    oBinData = struct.pack(sDataFormat, *(a1iVarData))

    oFileData.write(oBinData)

    return oFileData

# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to read 2d variable in binary format (saved as 1d integer array)
def get2DVar(oFileData, iRows, iCols, iVarScaleFactor=10):
    import struct

    # Values shape (1d)
    iNVals = iRows * iCols
    # Values format
    sDataFormat = 'i' * iNVals
    # Open and read binary file
    oFileCheck = oFileData.read(-1)
    a1dVarDataCheck = struct.unpack(sDataFormat, oFileCheck)

    # Reshape binary file in Fortran order and scale Data (float32)
    a2dVarDataCheck = np.reshape(a1dVarDataCheck, (iRows, iCols), order='F')
    a2dVarDataCheck = np.float32(a2dVarDataCheck / iVarScaleFactor)

    # Debug
    # plt.figure(1)
    # plt.imshow(a2dVarDataCheck); plt.colorbar()
    # plt.show()

    return a2dVarDataCheck

# --------------------------------------------------------------------------------
