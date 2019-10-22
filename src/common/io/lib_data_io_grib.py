"""
Library Features:

Name:          lib_data_io_grib
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20170512'
Version:       '2.0.1'
"""
#################################################################################
# Library
import logging
import pygrib
import inspect
import numpy as np
import numpy.ma as ma

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#################################################################################

# --------------------------------------------------------------------------------
# Method to open grib file
def openFile(sFileName, sFileMode='r'):

    # Open file
    try:

        if sFileMode == 'r':
            oFile = pygrib.open(sFileName)
            return oFile
        else:
            Exc.getExc(' -----> WARNING: open file in write/append mode not available (lib_data_io_grib)', 2, 1)
            return None

    except IOError as oError:
        Exc.getExc(' -----> ERROR: in open file (lib_data_io_grib)' + ' [' + str(oError) + ']', 1, 1)

# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to close grib file
def closeFile(oFile):
    pass
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to check messages in file
def checkFileMessage(oFile=None, iAttMessage=0):
    if oFile:
        iFileMessages = oFile.messages

        if iAttMessage == iFileMessages:
            bFileCheck = True
        else:
            bFileCheck = False
    else:
        bFileCheck = False
    return bFileCheck
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to get file messages
def getFileMessage(oFile):

    try:
        iFM = oFile.messages
        if iFM == 0:
            a1iFM = None
            Exc.getExc(' -----> WARNING: no message in GRIB file! Check your input file!', 2, 1)
        else:
            a1iFM = np.linspace(1, iFM, iFM, endpoint=True)

    except BaseException:

        a1iFM = None
        Exc.getExc(' -----> WARNING: no message in GRIB file! Check your input file!', 2, 1)

    return a1iFM

# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to get 2d variable data using a box
def getVar2D_BOX(oFile, iIndex=None,
                 oGeoBox=None):

    if oGeoBox is None:
        oGeoBox = [-90, 90, -180, 180]

    if iIndex is None:
        oVarHandle = oFile
    else:
        oVarHandle = oFile[iIndex]
    a2dVarData, a2dVarLat, a2dVarLon = oVarHandle.data(lat1=oGeoBox[3], lat2=oGeoBox[1],
                                                       lon1=oGeoBox[0], lon2=oGeoBox[2])
    return a2dVarData, a2dVarLat, a2dVarLon
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to get 2d variable all domain
def getVar2D_ALL(oFile, iIndex=None):

    # Check method
    try:

        if iIndex:
            # Read variable using Data index
            oVar = oFile[iIndex]
        else:
            oVar = oFile

        a2dVarData_Raw = oVar.values
        if ma.is_masked(a2dVarData_Raw):
            a2dVarData = a2dVarData_Raw.data
        else:
            a2dVarData = a2dVarData_Raw

        return a2dVarData

    except BaseException:

        # Exit status with error
        Exc.getExc(' -----> WARNING: in getting 2d variable function (lib_data_io_grib)', 2, 1)

# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to get 3d variable all domain
def getVar3D_ALL(oFile, sVarComp=None):

    # Check method
    try:
        bVarWarn = False
        oVarData = {}
        for oVar in oFile:

            # Get variable name
            sVarName = oVar.name
            #if not isinstance(sVarName, str):
            #    sVarName = sVarName.encode('UTF-8')
            #sVarName = sVarName.replace(' ', '_').lower()

            if (sVarComp == sVarName) or (sVarComp is None):

                if sVarName not in oVarData:
                    oVarData[sVarName] = None

                a2dVarData_Raw = oVar.values
                if ma.is_masked(a2dVarData_Raw):
                    a2dVarData = a2dVarData_Raw.data
                else:
                    a2dVarData = a2dVarData_Raw

                if oVarData[sVarName] is None:
                    a3dVarData = np.reshape(a2dVarData, [a2dVarData.shape[0], a2dVarData.shape[1], 1])
                else:
                    a3dVarData = oVarData[sVarName]
                    a3dVarData = np.dstack((a3dVarData, a2dVarData))

                oVarData[sVarName] = a3dVarData

            else:
                # Exit status with warning
                if bVarWarn is False:
                    Exc.getExc(
                        ' -----> WARNING: selected variable [' + sVarComp +
                        '] is not in grib message (lib_data_io_grib)', 2, 1)
                    bVarWarn = True
        return oVarData

    except BaseException:

        # Exit status with warning
        Exc.getExc(' -----> WARNING: in getting 3d variable function (lib_data_io_grib)', 2, 1)

# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to get time(s) for every variables
def getVarTime(oFile, sVarComp=None):

    # Get file message(s)
    iFM = oFile.messages
    a1iFM = np.linspace(1, iFM, iFM, endpoint=True)

    # Cycle(s) over message(s)
    bVarWarn = False
    a1oTime = {}
    for iMS_STEP, iMS_IDX in enumerate(a1iFM):

        # Cast index to integer format
        iMS_IDX = int(iMS_IDX)

        # Get variable data
        oVar = oFile[iMS_IDX]

        # Get time information
        sFM_Year = str(oVar['year']).zfill(4)
        sFM_Month = str(oVar['month']).zfill(2)
        sFM_Day = str(oVar['day']).zfill(2)
        sFM_HH = str(oVar['hour']).zfill(2)
        sFM_MM = str(oVar['minute']).zfill(2)
        iFM_UTR = int(oVar['unitOfTimeRange'])
        iFM_P1 = int(oVar['P1'])
        iFM_P2 = int(oVar['P2'])
        iFM_TRI = int(oVar['timeRangeIndicator'])
        oTimeAnalysis = oVar.analDate
        oTimeValid = oVar.validDate

        # Get variable name
        sVarName = oVar.name
        #if not isinstance(sVarName, str):
        #    sVarName = sVarName.encode('UTF-8')
        #sVarName = sVarName.replace(' ', '_').lower()

        if (sVarComp == sVarName) or (sVarComp is None):

            # Define variable in dictionary
            if sVarName not in a1oTime:
                a1oTime[sVarName] = {}
            else:
                pass

            # Define dictionary for each step
            oTime = {'Year': sFM_Year, 'Month': sFM_Month, 'Day': sFM_Day, 'Hour': sFM_HH, 'Minute': sFM_MM,
                     'TimeRangeUnit': iFM_UTR, 'TimeRangeIndicator': iFM_TRI,
                     'P1': iFM_P1, 'P2': iFM_P2,
                     'TimeAnalysis': oTimeAnalysis, 'TimeValidation': oTimeValid}

            # Store time information
            a1oTime[sVarName][iMS_IDX] = oTime
        else:
            # Exit status with warning
            if bVarWarn is False:
                Exc.getExc(
                    ' -----> WARNING: selected variable [' + sVarComp +
                    '] is not in grib message (lib_data_io_grib)', 2, 1)
                bVarWarn = True

    # Return variable(s)
    return a1oTime

# -------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to get data variable
def getVarData(oFile, oGeoData=None):

    # Get file message(s)
    iFM = oFile.messages
    a1iFM = np.linspace(1, iFM, iFM, endpoint=True)

    # Cycle(s) over message(s)
    a1oVar = {}
    for iMS_STEP, iMS_IDX in enumerate(a1iFM):

        # Cast index to integer format
        iMS_IDX = int(iMS_IDX)

        # Get variable data
        oVar = oFile[iMS_IDX]
        oVarData = oVar.values
        # Get variable name
        sVarName = oVar.name

        #if not isinstance(sVarName, str):
        #    sVarName = sVarName.encode('UTF-8')
        #sVarName = sVarName.replace(' ', '_').lower()

        # Define variable in dictionary
        if sVarName not in a1oVar:
            a1oVar[sVarName] = {}
        else:
            pass

        # Store variable data
        if oGeoData is None:
            a1oVar[sVarName][iMS_IDX] = oVarData
        else:
            if oGeoData['CorrOrient'] is True:
                a1oVar[sVarName][iMS_IDX] = np.flipud(oVarData)
            else:
                a1oVar[sVarName][iMS_IDX] = oVarData

    # Return variable(s)
    return a1oVar

# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to get geographical variable
def getVarGeo(oFile, iIndex=1):

    # Get geographical information
    try:

        # Get geographical data
        [a2dGeoY, a2dGeoX] = oFile[iIndex].latlons()
        # Check geographical orientation
        [a2dVarGeoX, a2dVarGeoY, bVarCorrOrient] = checkVarOrient(a2dGeoX, a2dGeoY)

        # Store geographical information
        a1oVarGeo = {'Longitude': a2dGeoX, 'Latitude': a2dGeoY, 'CorrOrient': bVarCorrOrient}

    except BaseException:

        Exc.getExc(' -----> WARNING: error in extracting file geographical data! Check input file!', 2, 1)
        a1oVarGeo = None

    # Return variable(s)
    return a1oVarGeo

# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to check variable(s) orientation (O-E, S-N)
def checkVarOrient(a2dVarGeoX, a2dVarGeoY):

    dVarGeoY_LL = a2dVarGeoY[a2dVarGeoY.shape[0] - 1, 0]
    dVarGeoY_UL = a2dVarGeoY[0, 0]
    # dVarGeoY_UR = a2dVarGeoY[0, a2dVarGeoY.shape[1] - 1]
    # dVarGeoY_LR = a2dVarGeoY[a2dVarGeoY.shape[0] - 1, a2dVarGeoY.shape[1] - 1]

    # Debug
    # print(dVarGeoY_LL, dVarGeoY_UL, dVarGeoY_UR, dVarGeoY_LR)
    # plt.figure(1); plt.imshow(a2dVarGeoY); plt.colorbar(); plt.show()

    if dVarGeoY_LL > dVarGeoY_UL:
        a2dVarGeoY = np.flipud(a2dVarGeoY)
        bVarCorrOrient = True
    else:
        bVarCorrOrient = False

    return a2dVarGeoX, a2dVarGeoY, bVarCorrOrient

# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Check variable name in file attributes
def checkVarName(oFileHandle, oVarValue, sVarKey='nameECMF', iVarMsg=2):

    bVarCheck = False
    for iFileIdx, oFileMsg in enumerate(oFileHandle()):

        if iFileIdx > iVarMsg - 1:
            break

        for sFileKey in oFileMsg.keys():
            try:
                oFileValue = oFileMsg[sFileKey]

                if sVarKey == sFileKey:
                    if oVarValue == oFileValue:
                        bVarCheck = True

            except BaseException:
                pass

        if bVarCheck is True:
            break

    return bVarCheck
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to print file attributes
def printFileAttrs(oFile):
    for oData in oFile:
        print(oData.typeOfLevel, oData.level, oData.name, oData.validDate, oData.analDate, oData.forecastTime)
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to get file attributes
def getFileAttr(oFile, iIndex=None, oVarKeyNA=None):

    # Default argument
    if oVarKeyNA is None:
        oVarKeyNA = ['distinctLatitudes', 'distinctLongitudes',
                  'values', 'latLonValues',
                  'latitudes', 'longitudes']

    if iIndex is None:
        oVarHandle = oFile
    else:
        oVarHandle = oFile[iIndex]

    # Attributes
    oVarAttrs = {}
    for sVarKey in oVarHandle.keys():

        sVarKey = sVarKey.strip().encode('UTF-8')
        sVarKey = sVarKey.decode('utf-8')

        if sVarKey not in oVarKeyNA:

            try:
                if sVarKey == 'validDate':
                    oVarValue = oVarHandle.validDate
                elif sVarKey == 'analDate':
                    oVarValue = oVarHandle.analDate
                else:
                    oVarValue = oVarHandle[sVarKey]
                oVarAttrs.update({sVarKey: oVarValue})
            except BaseException:
                Exc.getExc(' -----> WARNING: file key ' +
                           sVarKey + ' not correctly retrieved Check input file!', 2, 1)
        else:
            pass

    return oVarAttrs

# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to get geographical reference
def getVarGeo_LAMI_2i(oFileHandle, iIdx=0):

    # Check method
    a2dGeoY = None
    a2dGeoX = None
    try:
        # Get file message at index [iIdx]
        oFileMsg = oFileHandle()[iIdx]

        # Get geographical data
        try:
            # Method to get lats and lons
            [a2dGeoY, a2dGeoX] = oFileMsg.latlons()

        except BaseException:

            # Get data dimension(s)
            if oFileMsg.has_key('Ni') and oFileMsg.has_key('Nj'):
                iRows = oFileMsg.Ni
                iCols = oFileMsg.Nj
            else:
                [iCols, iRows] = oFileMsg.values.shape
            # Get lats and lons using key(s)
            a2dGeoX = np.reshape(oFileMsg['longitudes'], [iCols, iRows])
            a2dGeoY = np.reshape(oFileMsg['latitudes'], [iCols, iRows])

    except BaseException:

        # Exit status with warning
        Exc.getExc(' -----> WARNING: in getVarAttr_LAMI_2i an exception occurred (lib_data_io_grib)', 2, 1)

    return a2dGeoX, a2dGeoY

# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Get variable(s) attribute(s) for LAMI 2i
def getVarAttr_LAMI_2i(oFileHandle, oVarComp=None, oVarKeyNA=None):

    # Check method
    oVarAttrs = None
    try:

        # Default argument
        if oVarKeyNA is None:
            oVarKeyNA = ['distinctLatitudes', 'distinctLongitudes',
                         'values', 'latLonValues',
                         'latitudes', 'longitudes']

        # List conversion for string arguments of variable component(s)
        if isinstance(oVarComp, str) and (oVarComp is not None):
            oVarComp = [oVarComp]
        if oVarComp is None:
            oVarComp = [None]

        # Iterate over variable(s) component(s)
        oVarAttrs = {}
        for sVarComp in oVarComp:

            if sVarComp is None:
                oFileMsg = oFileHandle()
            else:
                try:
                    oFileMsg = oFileHandle.select(nameECMF=sVarComp)
                except BaseException:
                    Exc.getExc(
                        ' -----> WARNING: selected variable [' +
                        sVarComp + '] is not in grib message (lib_data_io_grib)', 2, 1)
                    oFileMsg = None

            # Iterate over message(s)
            for iVarID, oVarMsg in enumerate(oFileMsg):

                # Get variable name
                sVarName = oVarMsg.nameECMF

                # Selection of variable based on selected variables and variable admitted attribute(s)
                if sVarName in oVarComp:
                    if sVarName not in oVarAttrs:

                        # Initialization of attributes workspace for each variable(s)
                        oVarAttrs[sVarName] = {}

                        # Iterate over key(s)
                        for sVarKey in oVarMsg.keys():

                            # Sanitation of string
                            sVarKey = sVarKey.strip().encode('UTF-8')
                            sVarKey = sVarKey.decode('utf-8')

                            # Check of admitted key(s)
                            if sVarKey not in oVarKeyNA:

                                try:
                                    if sVarKey == 'validDate':
                                        oVarValue = oVarMsg.validDate
                                    elif sVarKey == 'analDate':
                                        oVarValue = oVarMsg.analDate
                                    else:
                                        oVarValue = oVarMsg[sVarKey]

                                    # Attributes workspace
                                    oVarAttrs[sVarName][sVarKey] = {}
                                    oVarAttrs[sVarName][sVarKey] = oVarValue

                                except BaseException:
                                    Exc.getExc(' -----> WARNING: file key ' +
                                               sVarKey + ' not correctly retrieved Check input file!', 2, 1)
                            else:
                                pass
                    else:
                        pass
                else:
                    pass

    except BaseException:

        # Exit status with warning
        Exc.getExc(' -----> WARNING: in getVarAttr_LAMI_2i an exception occurred (lib_data_io_grib)', 2, 1)

    return oVarAttrs
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to get time variable from LAMI 2i model
def getVarTime_LAMI_2i(oFileHandle, oVarComp):

    # Check method
    oVarTime = None
    try:

        # List conversion for string arguments of variable component(s)
        if isinstance(oVarComp, str) and (oVarComp is not None):
            oVarComp = [oVarComp]
        if oVarComp is None:
            oVarComp = [None]

        # Iterate over variable(s) component(s)
        oVarTime = {}
        for sVarComp in oVarComp:

            if sVarComp is None:
                oFileMsg = oFileHandle()
            else:
                try:
                    oFileMsg = oFileHandle.select(nameECMF=sVarComp)
                except BaseException:
                    Exc.getExc(
                        ' -----> WARNING: selected variable [' +
                        sVarComp + '] is not in grib message (lib_data_io_grib)', 2, 1)
                    oFileMsg = None

            # Iterate over message(s)
            for iVarID, oVarMsg in enumerate(oFileMsg):

                # Get variable name
                sVarName = oVarMsg.nameECMF

                if sVarName not in oVarTime:
                    oVarTime[sVarName] = None

                # Get time information
                sFM_Year = str(oVarMsg['year']).zfill(4)
                sFM_Month = str(oVarMsg['month']).zfill(2)
                sFM_Day = str(oVarMsg['day']).zfill(2)
                sFM_HH = str(oVarMsg['hour']).zfill(2)
                sFM_MM = str(oVarMsg['minute']).zfill(2)
                iFM_UTR = int(oVarMsg['unitOfTimeRange'])
                iFM_P1 = int(oVarMsg['P1'])
                iFM_P2 = int(oVarMsg['P2'])
                iFM_TRI = int(oVarMsg['timeRangeIndicator'])
                dFM_JDay = float(oVarMsg.julianDay)
                oTimeAnalysis = oVarMsg.analDate
                oTimeValid = oVarMsg.validDate

                # Define dictionary for each step
                oTime = {'Year': sFM_Year, 'Month': sFM_Month, 'Day': sFM_Day, 'Hour': sFM_HH, 'Minute': sFM_MM,
                         'TimeRangeUnit': iFM_UTR, 'TimeRangeIndicator': iFM_TRI,
                         'P1': iFM_P1, 'P2': iFM_P2, 'JulianDay': dFM_JDay,
                         'TimeAnalysis': oTimeAnalysis, 'TimeValidation': oTimeValid}

                # Store time information
                if oVarTime[sVarName] is None:
                    oVarTime[sVarName] = {}
                oVarTime[sVarName][iVarID] = oTime

    except BaseException:

        # Exit status with warning
        Exc.getExc(' -----> WARNING: in getVarTime_LAMI_2i an exception occurred (lib_data_io_grib)', 2, 1)

    return oVarTime
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to get 3d variable from LAMI 2i model
def getVar3D_LAMI_2i(oFileHandle, oVarComp=None):

    # Check method
    oVarData = None
    try:

        # List conversion for string arguments of variable component(s)
        if isinstance(oVarComp, str) and (oVarComp is not None):
            oVarComp = [oVarComp]
        if oVarComp is None:
            oVarComp = [None]

        # Iterate over variable(s) component(s)
        oVarData = {}
        for sVarComp in oVarComp:

            if sVarComp is None:
                oFileMsg = oFileHandle()
            else:
                try:
                    oFileMsg = oFileHandle.select(nameECMF=sVarComp)
                except BaseException:
                    Exc.getExc(
                        ' -----> WARNING: selected variable [' +
                        sVarComp + '] is not in grib message (lib_data_io_grib)', 2, 1)
                    oFileMsg = None

            # Iterate over message(s)
            for iVarID, oVarMsg in enumerate(oFileMsg):

                # Get variable name
                sVarName = oVarMsg.nameECMF

                if sVarName not in oVarData:
                    oVarData[sVarName] = None

                a2dVarData_Raw = oVarMsg.values
                if ma.is_masked(a2dVarData_Raw):
                    a2dVarData = a2dVarData_Raw.data
                else:
                    a2dVarData = a2dVarData_Raw

                if oVarData[sVarName] is None:
                    a3dVarData = np.reshape(a2dVarData, [a2dVarData.shape[0], a2dVarData.shape[1], 1])
                else:
                    a3dVarData = oVarData[sVarName]
                    a3dVarData = np.dstack((a3dVarData, a2dVarData))

                oVarData[sVarName] = a3dVarData

    except BaseException:

        # Exit status with warning
        Exc.getExc(' -----> WARNING: in getVar3D_LAMI_2i an exception occurred (lib_data_io_grib)', 2, 1)

    return oVarData

# --------------------------------------------------------------------------------
