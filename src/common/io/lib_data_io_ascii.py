"""
Library Features:

Name:          lib_data_io_ascii
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180521'
Version:       '2.0.7'
"""

#######################################################################################
# Library
import numpy as np
import logging

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#######################################################################################

# -------------------------------------------------------------------------------------
# Method to open ASCII file (in read or write mode)
def openFile(sFileName, sFileMode):
    try:
        oFile = open(sFileName, sFileMode)
        return oFile
    except IOError as oError:
        Exc.getExc(' =====> ERROR: in open file (Lib_Data_IO_Ascii)' + ' [' + str(oError) + ']', 1, 1)
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to close ASCII file
def closeFile(oFile):
    oFile.close()
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to read ASCII tabular file with characters and numbers
def readTable(oFile, iSkiprows=0):

    # Convert to index
    if iSkiprows > 0:
        iIndexRow = iSkiprows - 1
    else:
        iIndexRow = -1

    iNL = None
    for iID, sLine in enumerate(oFile):

        # Control to skip row(s)
        if iID > iIndexRow:

            a1oLine = sLine.split()

            if iNL is None:
                iNL = len(a1oLine)
                a2oDataTable = [[] for iL in range(iNL)]
            else:
                pass

            for iElemID, sElemVal in enumerate(a1oLine):
                a2oDataTable[iElemID].append(sElemVal)
        else:
            pass

    return a2oDataTable

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to read ASCII file line by line
def getLines(oFile):
    oContent = oFile.readlines()
    return oContent
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to read ASCII file with 1 or more columns (default mode)
def getVar(oFile):
    oData = np.array([])
    for sFileLine in oFile.readlines():
        sFileLine = sFileLine.strip()
        sLineCols = sFileLine.split()

        oLineCols = np.asarray(sLineCols)
        oData = np.append(oData, oLineCols)

    return oData
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to write Data to ASCII file (default mode)
def writeVar(oFile, sData):
    oFile.write(sData + '\n')
    return oFile
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Read ArcGrid Data
def readArcGrid(oFile):

    # Check method
    try:

        # Read Header
        a1oVarHeader = {
            "ncols": int(oFile.readline().split()[1]),
            "nrows": int(oFile.readline().split()[1]),
            "xllcorner": float(oFile.readline().split()[1]),
            "yllcorner": float(oFile.readline().split()[1]),
            "cellsize": float(oFile.readline().split()[1]),
            "NODATA_value": float(oFile.readline().split()[1]),
        }

        # Read grid values
        a2dVarData = np.loadtxt(oFile, skiprows=0)

        # Debugging
        # plt.figure(1)
        # plt.imshow(a2dVarData); plt.colorbar();
        # plt.show()

        return a2dVarData, a1oVarHeader

    except RuntimeError:
        # Exit status with error
        Exc.getExc(' =====> ERROR: in readArcGrid function (Lib_Data_IO_Ascii)', 1, 1)

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Write 2dVar
def writeArcGrid(oFile, a2dVarData, a1oVarHeader, sDataFormat=None, dNoData=None):

    # sDataFormat: f, i, None
    # dNoData: 0, -9999
    if dNoData:
        a1oVarHeader["NODATA_value"] = dNoData

    # Check method
    try:

        # Defining max number of digits before comma
        dVarDataMin = np.nanmin(np.unique(a2dVarData))
        dVarDataMax = np.nanmax(np.unique(a2dVarData))
        iVarDataMax = int(dVarDataMax)

        # Get Data format and digits
        if sDataFormat == 'f':
            iDigitNum = len(str(iVarDataMax)) + 3
            sFmt = '%'+str(iDigitNum)+'.2' + sDataFormat
        elif sDataFormat == 'i':
            iDigitNum = len(str(iVarDataMax))
            sFmt = '%'+str(iDigitNum) + sDataFormat
        else:
            Exc.getExc(' =====> WARNING: Data format unknown! Set float type!', 2, 1)
            iDigitNum = len(str(iVarDataMax)) + 3
            sFmt = '%'+str(iDigitNum)+'.2' + sDataFormat

        # Write header
        oFile.write("ncols\t%i\n" % a1oVarHeader["ncols"])
        oFile.write("nrows\t%i\n" % a1oVarHeader["nrows"])
        oFile.write("xllcorner\t%f\n" % a1oVarHeader["xllcorner"])
        oFile.write("yllcorner\t%f\n" % a1oVarHeader["yllcorner"])
        oFile.write("cellsize\t%f\n" % a1oVarHeader["cellsize"])
        if sDataFormat == 'f':
            oFile.write("NODATA_value\t%f\n" % a1oVarHeader["NODATA_value"])
        elif sDataFormat == 'i':
            oFile.write("NODATA_value\t%i\n" % a1oVarHeader["NODATA_value"])
        else:
            Exc.getExc(' =====> WARNING: no Data format set in float type!', 2, 1)
            oFile.write("NODATA_value\t%f\n" % a1oVarHeader["NODATA_value"])

        # Write grid values
        # sDataFormat = '%'+str(iDigitNum)+'.2f';
        np.savetxt(oFile, a2dVarData, delimiter=' ', fmt=sFmt,  newline='\n')

    except RuntimeError:
        # Exit status with error
        Exc.getExc(' =====> ERROR: in writeArcGrid function (Lib_Data_IO_Ascii)', 1, 1)

    # -------------------------------------------------------------------------------------
    
# -------------------------------------------------------------------------------------
