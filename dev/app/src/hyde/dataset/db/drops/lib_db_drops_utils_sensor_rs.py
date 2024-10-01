"""
Library Features:

Name:          lib_db_drops_utils_sensor_rs
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20171114'
Version:       '1.0.0'

Octave and oct2py installation steps:
    sudo apt-get install octave
    sudo -E pip install oct2py
Example:
    from oct2py import octave
    octave.addpath(sPathRatCurve)
    d = octave.teverepierantonioRatingCurve(float(5), '201310091200')
"""
#######################################################################################
# Logging
import logging

from re import match, IGNORECASE
from os.path import join, splitext
from csv import writer, reader
from copy import deepcopy
from numpy import array

from oct2py import octave

from Lib_Op_System_Apps import getFileName2FxObj, getModule2FxObj

oLogStream = logging.getLogger('sLogger')

# Global libraries
from Drv_Exception import Exc
#######################################################################################

# -------------------------------------------------------------------------------------
# Method to write station water level data on disk (using csv format)
def writeSectionWaterLevel(sFileName, a1oStationData, a1oStationName, a2oStation_DB, sFileDelimiter=','):

    # Open, handle and initialize CSV writer
    with open(sFileName, "wb") as oFileHandle:
        oWriter = writer(oFileHandle, delimiter=sFileDelimiter)

        # Cycle(s) over DB station(s)
        for iStationID_DB, oStationRegistry_DB in enumerate(a2oStation_DB):

            # Parse and control DB station name
            sStationName_DB = oStationRegistry_DB[8].strip()

            # Find DB name in registry name
            if sStationName_DB in a1oStationName:
                iStationIdx_DB = [i for i, s in enumerate(a1oStationName) if sStationName_DB in s][0]
            else:
                iStationIdx_DB = None

            # Check station idx
            if iStationIdx_DB:
                # Get section data
                dStationData = float(a1oStationData[iStationIdx_DB])
                # Define data format
                oRowFormat = '.3f'
                sRowFormat = "{:" + oRowFormat + "}"
                sStationData = str(sRowFormat.format(dStationData))
            else:
                sStationData = '-9999.0'

            # Copy information from DB registry
            oStationRow = deepcopy(oStationRegistry_DB)

            # Define line to dump data to csv file
            oStationRow.extend([sStationData])

            # Write row in file handle
            oWriter.writerow(oStationRow)

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to read station water level data from disk (using csv format)
def readStationWaterLevel(sFileName, sFileDelimiter=','):
    with open(sFileName, 'rb') as oFileHandle:
        oFileReader = reader(oFileHandle, delimiter=sFileDelimiter, quotechar='|')
        oFileData = []
        for oRow in oFileReader:
            oFileData.append(oRow)
    return oFileData
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to select station information
def selectStationInfo(sDomainName_SEL, sStationName_SEL, oDrops_DB):

    oStationInfo = []
    for iDrops_ID, oDrops_Line in enumerate(oDrops_DB):

        sDomainName_DB = str(oDrops_Line[2]).lower().replace(' ', '')
        sStationName_DB = str(oDrops_Line[3]).lower().replace(' ', '')

        sDomainName_RE = r'(\s|^|$)'
        bDomainName_CHECK = bool(match(sDomainName_RE + sDomainName_SEL + sDomainName_RE, sDomainName_DB,
                                       flags=IGNORECASE))

        sStationName_RE = r'(\s|^|$)'
        bStationName_CHECK = bool(match(sStationName_RE + sStationName_SEL + sStationName_RE, sStationName_DB,
                                        flags=IGNORECASE))

        if (bDomainName_CHECK is True) and (bStationName_CHECK is True):
            oStationInfo = [oDrops_DB[iDrops_ID]]
            break

    return oStationInfo
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to select water level data for a given name
def computeStationDischargeByName(a2oStationData, sStationDomain, sStationName, sStationTime, sPathRatCurve=None):

    # -------------------------------------------------------------------------------------
    # Define station reference domain and name
    sStationDomain_REF = sStationDomain.strip().lower().replace(' ', '')
    sStationName_REF = sStationName.strip().lower().replace(' ', '')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Find station idx
    for iStationIdx_STEP, a1oStationData_STEP in enumerate(a2oStationData):
        sStationDomain_STEP = a1oStationData_STEP[2].lower().replace(' ', '')
        sStationName_STEP = a1oStationData_STEP[3].lower().replace(' ', '')

        if (sStationDomain_REF == sStationDomain_STEP) and (sStationName_REF == sStationName_STEP):
            iStationIdx = iStationIdx_STEP
            break
        else:
            iStationIdx = None
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Select data based on idx
    if iStationIdx is not None:
        a1oStationData = a2oStationData[iStationIdx]
        # Get data and rating curve
        dStationDataWL = float(a1oStationData[-1])
        sStationRatCurve = a1oStationData[15].strip()
    else:
        dStationDataWL = None
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Compute discharge using rating curve and water level data
    if dStationDataWL is not None:
        dStationDataQ = convertWLevel2Discharge(dStationDataWL, sStationTime, sStationRatCurve, sPathRatCurve)
    else:
        dStationDataQ = -9999.0
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Define data format
    sStationDataFormat = '.2f'
    sStationDataFormat = "{:" + sStationDataFormat + "}"
    dStationDataQ = float(sStationDataFormat.format(dStationDataQ))

    # Return variable(s)
    return dStationDataQ, iStationIdx
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to select water level data for a given time step
def computeStationDischargeByTime(a2oStationData_WL, sStationTime_WL, sPathRatCurve=None):

    # -------------------------------------------------------------------------------------
    # Cycle(s) over section(s) information
    a2oStationData_Q = []
    for iStationData_ID, oStationData_WL in enumerate(a2oStationData_WL):

        # -------------------------------------------------------------------------------------
        # Get rating curve name and water level data
        sStationDomain = oStationData_WL[2].strip()
        sStationName = oStationData_WL[3].strip()
        sStationRatCurve = oStationData_WL[15].strip()
        dStationData_WL = float(oStationData_WL[-1])

        # Info
        oLogStream.info(
            ' ----> Domain: ' + sStationDomain + ' Section: ' + sStationName +
            ' RatingCurve: ' + sStationRatCurve + ' WaterLevel Value: ' + str(dStationData_WL))
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Compute discharge value
        dStationData_Q = convertWLevel2Discharge(dStationData_WL, sStationTime_WL, sStationRatCurve, sPathRatCurve)

        # Define data format
        sStationData_Format = '.2f'
        sStationData_Format = "{:" + sStationData_Format + "}"
        dStationData_Q = float(sStationData_Format.format(dStationData_Q))
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Add data to section info
        oStationData_WL.extend([str(dStationData_Q)])
        # Add data to outcome workspace
        a2oStationData_Q.append(oStationData_WL)
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Return variable(s)
    return a2oStationData_Q
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to compute discharge value
def convertWLevel2Discharge(dStationData_WL, sStationTime_WL, sStationRatCurve, sPathRatCurve):

    # -------------------------------------------------------------------------------------
    # Check interpreter for rating curve file (m = octave; py = python)
    if splitext(sStationRatCurve)[1].replace('.', '') == 'm':

        # -------------------------------------------------------------------------------------
        # Add rating curve path to octave workspace
        octave.addpath(sPathRatCurve)

        # Find rating curve function (if available) in a module
        oFunctionObj = getModule2FxObj(octave, sStationRatCurve.split('.')[0])

        # Select rating curve to transform water level in discharge
        if oFunctionObj:

            # Call function to convert water level to discharge (for octave interpreter)
            try:
                # Set octave interpreter and cast input to float
                dStationData_WL = array([dStationData_WL], dtype=float)
                # Compute discharge applying rating curve function
                dStationData_Q = oFunctionObj(dStationData_WL, sStationTime_WL)
            except:
                # Info warning if rating curve failed
                Exc.getExc(' ------> WARNING: ' + sStationRatCurve + ' FAILED in computing discharge!', 2, 1)
                dStationData_Q = -9997.0
        else:
            # Exit with none rating curve available
            Exc.getExc(' ------> WARNING: ' + sStationRatCurve + ' NOT FOUND in RatingCurve path!', 2, 1)
            dStationData_Q = -9998.0
            # -------------------------------------------------------------------------------------

    elif splitext(sStationRatCurve)[1].replace('.', '') == 'py':

        # -------------------------------------------------------------------------------------
        # Find rating curve function (if available) in a file
        oFunctionObj = getFileName2FxObj(join(sPathRatCurve, sStationRatCurve), sStationRatCurve.split('.')[0])

        # Select rating curve to transform water level in discharge
        if oFunctionObj:

            # Call function to convert water level to discharge (for python interpreter)
            try:
                # Compute discharge applying rating curve function
                dStationData_Q = oFunctionObj(dStationData_WL, sStationTime_WL)[0]
            except:
                # Info warning if rating curve failed
                Exc.getExc(' ------> WARNING: ' + sStationRatCurve + ' FAILED in computing discharge!', 2, 1)
                dStationData_Q = -9997.0
        else:
            # Exit with none rating curve available
            Exc.getExc(' ------> WARNING: ' + sStationRatCurve + ' NOT FOUND in RatingCurve path!', 2, 1)
            dStationData_Q = -9998.0
            # -------------------------------------------------------------------------------------

    else:

        # -------------------------------------------------------------------------------------
        # Exit with interpreter issue
        Exc.getExc(' ------> WARNING: ' + sStationRatCurve + ' interpreter NOT CORRECTLY DEFINED!', 2, 1)
        dStationData_Q = -9996.0
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Return variable
    return dStationData_Q
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
