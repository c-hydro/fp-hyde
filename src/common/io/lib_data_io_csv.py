"""
Library Features:

Name:          lib_data_io_csv
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180914'
Version:       '1.7.0'
"""
#################################################################################
# Library
import logging

import csv
from pandas import read_csv
from os.path import exists

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#################################################################################


# --------------------------------------------------------------------------------
# Initialize dictionary object
class ObjCSV(object):
    pass
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to open csv file
def openFile(sFileName, sFileMode=None, sFileDelimiter=','):

    # Method to open an object to store features of csv dataset
    try:
        oFile = ObjCSV()

        if exists(sFileName):
            oFile.bFileData = True
        else:
            oFile.bFileData = False

        oFile.sFileMode = sFileMode
        oFile.sFileName = sFileName
        oFile.sFileDelimiter = sFileDelimiter

        return oFile

    except IOError as oError:
        Exc.getExc(' -----> ERROR: in open file (lib_data_io_csv)' + ' [' + str(oError) + ']', 1, 1)

# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to read csv file
def readFile2Data(sFileName, sFileDelimiter=',', sFileMode='rb'):
    with open(sFileName, sFileMode) as oFile:
        oFileReader = csv.reader(oFile, delimiter=sFileDelimiter, quotechar='|')
        oFileData = []
        for oRow in oFileReader:
            a1sRow = sFileDelimiter.join(oRow)
            oFileData.append(a1sRow)
    return oFileData
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to write csv file
def writeFile(sFileName, sFileMode='w'):
    with open(sFileName, sFileMode) as oFileHandle:
        oFile = csv.writer(oFileHandle, quoting=csv.QUOTE_NONNUMERIC)
    return oFile
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to close csv file
def closeFile():
    Exc.getExc(' -----> Warning: no close method defined (lib_data_io_csv)', 2, 1)
    pass
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to read file to data frame
def readFile2DataFrame(sFileName, sFileDelimiter=','):
    oDataFrame = read_csv(sFileName, delimiter=sFileDelimiter)
    return oDataFrame
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to write dataframe to csv file
def writeDataFrame2File(sFileName, oDataFrame, sDataSeparetor=',',
                        sDataEncoding='utf-8', bDataIndex=False, bDataHeader=True):

    oVarName = list(oDataFrame.columns.values)
    oDataFrame.to_csv(sFileName, sep=sDataSeparetor, encoding=sDataEncoding,
                      index=bDataIndex, index_label=False, header=bDataHeader,
                      columns=oVarName)
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to parse file in csv format
def parseFile(oFile, sDelimiter=',', iSkipRows=0):

    if iSkipRows > 0:
        iSkipRows = iSkipRows - 1

    iNL = None
    a2oDataTable = []
    a2oFileTable = []
    for iRowID, oRowData in enumerate(oFile):

        if iRowID > iSkipRows:
            a1oRowData = oRowData.split(sDelimiter)
            a2oFileTable.append(a1oRowData)

            # Arrange data in table format
            if iNL is None:
                iNL = a1oRowData.__len__()
                a2oDataTable = [[] for iL in range(iNL)]
            else:
                pass

            for iElemID, sElemVal in enumerate(a1oRowData):
                a2oDataTable[iElemID].append(sElemVal)
        else:
            pass

    return a2oDataTable, a2oFileTable
# --------------------------------------------------------------------------------
