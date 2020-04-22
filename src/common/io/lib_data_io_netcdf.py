"""
Library Features:

Name:          lib_data_io_netcdf
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180521'
Version:       '2.0.7'
"""
#################################################################################
# Library
import logging
import numpy as np

from src.common.default.lib_default_args import sLoggerName

try:
    from src.common.default.lib_default_args import sTimeFormat as sTimeFormat_Default
    from src.common.default.lib_default_args import sTimeCalendar as sTimeCalendar_Default
    from src.common.default.lib_default_args import sTimeUnits as sTimeUnits_Default
except BaseException:
    sTimeFormat_Default = "%Y%m%d%H%M"
    sTimeUnits_Default = 'days since 1970-01-01 00:00'
    sTimeCalendar_Default = 'gregorian'

from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#################################################################################

# ----------------------------------------------------------------------------
# Method to open file
def openFile(sFileName, sFileMode, sFileFormat='NETCDF4'):

    try:
        from netCDF4 import Dataset as Dataset
    except BaseException:
        from scipy.io.netcdf import netcdf_file as Dataset
        Exc.getExc(' =====> WARNING: NetCDF module import from scipy (usually imported from netcdf-python)!', 2, 1)

    try:
        # NetCDF type: NETCDF3_CLASSIC , NETCDF3_64BIT , NETCDF4_CLASSIC , NETCDF4
        oFile = Dataset(sFileName, sFileMode, format=sFileFormat)
        return oFile
    except IOError as oError:
        Exc.getExc(' =====> ERROR: in open file (lib_data_io_netcdf)' + ' [' + str(oError) + ']', 1, 1)

# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Method to close file
def closeFile(oFile):
    oFile.close()
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Method to check variable name
def checkVarName(oFileData, sVarName):
    if sVarName in oFileData.variables:
        bVarExist = True
    else:
        bVarExist = False
    return bVarExist
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Method to check attribute name
def checkAttrName(oFileData, oAttrName):
    a1bAttrKey = np.full(oAttrName.__len__(), False, dtype=bool)
    for iAttrID, (sAttrKey, sAttrName) in enumerate(oAttrName.items()):
        if sAttrKey in oFileData.ncattrs():
            bAttrKey = True
        else:
            bAttrKey = False
        a1bAttrKey[iAttrID] = bAttrKey
    return a1bAttrKey
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Method to check if dimension is already defined
def checkDimName(oFileData, sDimName):
    if sDimName in oFileData.dimensions:
        bDimName = True
    else:
        bDimName = False
    return bDimName
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Method to get variable information
def getVarInfo(oFileData, sVarName):
    
    oVarDim = oFileData.variables[sVarName].dimensions
    oVarType = oFileData.variables[sVarName].dtype
    iVarDim = oFileData.variables[sVarName].ndim
    a1iVarShape = oFileData.variables[sVarName].shape

    return oVarDim, oVarType, iVarDim, a1iVarShape

# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Method to get variable attributes [sVarEncode=None or 'utf-8']
def getVarAttrs(oFileData, sVarName, sVarEncode=None):

    oAttrVar = {}
    for sAttrName_IN in oFileData.variables[sVarName].ncattrs():

        # Get attribute name
        if sVarEncode is None:
            sAttrName_OUT = sAttrName_IN
        elif sVarEncode == 'utf-8':
            sAttrName_OUT = sAttrName_IN.encode('utf-8')
        else:
            Exc.getExc(' =====> WARNING: in reading variable attribute ' + sAttrName_OUT + '. '
                       + 'Attribute encoding unknown or not correctly defined! (lib_data_io_netcdf)', 2, 1)

        # Get attribute value
        oAttrValue_RAW = oFileData.variables[sVarName].getncattr(sAttrName_OUT)

        # Parse attribute value
        if isinstance(oAttrValue_RAW, str):
            if sVarEncode is None:
                oAttrValue_OUT = oAttrValue_RAW
            elif sVarEncode == 'utf-8':
                oAttrValue_OUT = oAttrValue_RAW.encode('utf-8')
            else:
                Exc.getExc(' =====> WARNING: in reading variable attribute' + sAttrName_OUT + '. '
                           + 'Casting value unsing a default encoding! (lib_data_io_netcdf)', 2, 1)
                oAttrValue_OUT = oAttrValue_RAW
        elif isinstance(oAttrValue_RAW, np.float):
            oAttrValue_OUT = np.float32(oAttrValue_RAW)
        elif isinstance(oAttrValue_RAW, np.float32):
            oAttrValue_OUT = np.float32(oAttrValue_RAW)
        elif isinstance(oAttrValue_RAW, np.int32):
            oAttrValue_OUT = np.int32(oAttrValue_RAW)
        elif isinstance(oAttrValue_RAW, np.int64):
            oAttrValue_OUT = np.int32(oAttrValue_RAW)
        else:
            Exc.getExc(
                ' =====> WARNING: in reading variable attribute ' + sAttrName_OUT + '. '
                + 'Attribute type not defined! (lib_data_io_netcdf)', 2, 1)
            oAttrValue_OUT = None

        # Save attribute value
        oAttrVar[sAttrName_OUT] = oAttrValue_OUT

    return oAttrVar

# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Method to get file variable(s)
def getFileVars(oFileData):
    # Get all variable names
    return oFileData.variables
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Method to get file attributes
def getFileAttrs(oFileData, sVarEncode=None):

    oAttrData = oFileData.ncattrs()
    oAttrFile = {}
    for sAttrName in oAttrData:

        # Transform attributes from unicode to utf-8
        if sVarEncode is None:
            oAttrValue = oFileData.getncattr(sAttrName)
        elif sVarEncode == 'utf-8':
            oAttrValue = oFileData.getncattr(sAttrName.encode('utf-8'))
        else:
            Exc.getExc(' =====> WARNING: in reading variable attribute ' + sAttrName + '. '
                       + 'Attribute encoding unknown or not correctly defined! (lib_data_io_netcdf)', 2, 1)

        if isinstance(oAttrValue, str):
            if sVarEncode == 'utf-8':
                oAttrValue = oAttrValue.encode('utf-8')
        elif isinstance(oAttrValue, np.float):
            oAttrValue = np.float32(oAttrValue)
        elif isinstance(oAttrValue, np.float32):
            oAttrValue = np.float32(oAttrValue)
        elif isinstance(oAttrValue, np.int32):
            oAttrValue = np.int32(oAttrValue)
        elif isinstance(oAttrValue, np.int64):
            oAttrValue = np.int32(oAttrValue)
        else:
            Exc.getExc(
                ' =====> WARNING: in reading file attribute ' + sAttrName + '. '
                + 'Attribute type not defined! (lib_data_io_netcdf)', 2, 1)
            oAttrValue = None

        # Save attribute value
        if sVarEncode is None:
            oAttrFile[sAttrName] = oAttrValue
        elif sVarEncode == 'utf-8':
            oAttrFile[sAttrName.encode('utf-8')] = oAttrValue
        else:
            Exc.getExc(' =====> WARNING: in storing variable attribute ' + sAttrName + '. '
                       + 'Attribute encoding unknown or not correctly defined! (lib_data_io_netcdf)', 2, 1)

    return oAttrFile

# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Method to get 1d variable (using variable name)
def get1DVar(oFileData, sVarName):

    try:
        a1dVarName_OUT = oFileData.variables[sVarName][:]
    except RuntimeError:
        a1dVarName_OUT = None
        Exc.getExc(' =====> ERROR: in reading variable 1d. Check variable name! (lib_data_io_netcdf)', 1, 1)
    return a1dVarName_OUT
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Method to get 2d variable (using variable name)
def get2DVar(oFileData, sVarName, bSetAutoMask=True):

    if not bSetAutoMask:
        Exc.getExc(' =====> WARNING: auto_mask is set to false! (lib_data_io_netcdf)', 2, 1)
        oFileData.set_auto_mask(False)

    try:
        a2dVarName_IN = oFileData.variables[sVarName][:]
        a2dVarName_OUT = np.transpose(np.rot90(a2dVarName_IN, -1))
    except RuntimeError:
        a2dVarName_OUT = None
        Exc.getExc(' =====> ERROR: in reading variable 2d. Check variable name! (lib_data_io_netcdf)', 1, 1)

    return a2dVarName_OUT
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Method to get 3d variable (using variable name and t-slice if defined)
def get3DVar(oFileData, sVarName, iVarTSlice=None, bSetAutoMask=True, bSetTranspose=False):

    if not bSetAutoMask:
        Exc.getExc(' =====> WARNING: auto_mask is set to false! (lib_data_io_netcdf)', 2, 1)
        oFileData.set_auto_mask(False)

    a3dVarName_IN = oFileData.variables[sVarName][:]

    if bSetTranspose:
        if iVarTSlice is None:
            oVarName_OUT = np.zeros([a3dVarName_IN.shape[1], a3dVarName_IN.shape[2], a3dVarName_IN.shape[0]])
            for iT in range(0, a3dVarName_IN.shape[0]):
                a2dVarName_IN = np.transpose(np.rot90(a3dVarName_IN[iT, :, :], -1))
                oVarName_OUT[:, :, iT] = a2dVarName_IN

                # a2dVarName_IN[a2dVarName_IN < -900] = np.nan

                # Debug
                # plt.figure(1); plt.imshow(a2dVarName_IN); plt.colorbar(); plt.clim(-10,40);
                # plt.show()

        else:
            oVarName_OUT = np.transpose(np.rot90(a3dVarName_IN[iVarTSlice, :, :], -1))

    else:
        if iVarTSlice is None:
            oVarName_OUT = a3dVarName_IN
        else:
            oVarName_OUT = a3dVarName_IN[:, :, iVarTSlice]
    return oVarName_OUT
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Method to get all variable(s)
def getVars(oFileData):

    # Variable(s) initialization
    oDictData = {}

    # Get all variable names
    a1oFileVariables = oFileData.variables
    for sFileVariableKeys, sFileVariableName in a1oFileVariables.items():
        # Convert variable name from Unicode to ASCII
        sFileVariable = sFileVariableKeys.encode('ascii', 'ignore')
        try:
            # Save variable in a dictionary
            oDataVariable = oFileData.variables[sFileVariableKeys][:]
            oDictData[sFileVariable] = oDataVariable
        except BaseException:
            oDictData[sFileVariable] = None

    return oDictData

# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Method to get dimension field
def getDims(oFileData):

    oFileDims = {}
    for sKeyField, oKeyData in oFileData.dimensions.items():
        sKeyName = oKeyData.name
        iKeyValue = oKeyData.size

        oFileDims[sKeyField] = {}
        oFileDims[sKeyField]['name'] = {}
        oFileDims[sKeyField]['name'] = sKeyName
        oFileDims[sKeyField]['size'] = {}
        oFileDims[sKeyField]['size'] = iKeyValue

    return oFileDims
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Method to write dimension field
def writeDims(oFileData, sDimVar, iDimValue):
    # Dim declaration
    oFileData.createDimension(sDimVar, iDimValue)
    return oFileData

# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Method to write 3d variable
def write3DVar(oFileData, sVarName, a3dVarDataXYT, oVarAttr, sVarFormat, sVarDimT=None, sVarDimY=None, sVarDimX=None):

    # Check dimensions definition
    if not sVarDimY or not sVarDimX or not sVarDimT:
        Exc.getExc(
            ' =====> ERROR: in saving file 3d variable ' + sVarName + '. '
            + 'Dimensions are not correctly defined! (lib_data_io_netcdf)', 2, 1)
    else:
        pass

    # Check Data availability
    if a3dVarDataXYT is not None:

        # Creating variable
        oVar = oFileData.createVariable(sVarName, sVarFormat, (sVarDimT, sVarDimY, sVarDimX,), zlib=True)

        # Saving all variable attribute(s)
        if oVarAttr:
            for sVarAttr in oVarAttr:
                # Retrieving attribute value
                sVarOptValue = oVarAttr[sVarAttr]
                # Saving attribute
                oVar.setncattr(sVarAttr.lower(), str(sVarOptValue))
        else:
            Exc.getExc(
                ' =====> WARNING: in saving file 3d variable ' + sVarName + '. '
                + 'Attributes are null but variable saved correctly! (lib_data_io_netcdf)', 2, 1)

        # Debug to check map orientation
        # if sVarName == 'Terrain':
        #    plt.figure(1)
        #    plt.imshow(np.transpose(np.rot90(a2dVarDataXY,-1))); plt.colorbar()
        #    plt.show()

        # Define 3d field(s)
        a3dVarDataTYX = np.zeros([a3dVarDataXYT.shape[2], a3dVarDataXYT.shape[0], a3dVarDataXYT.shape[1]])
        for iStep in range(0, a3dVarDataXYT.shape[2]):

            # Get Data
            # a2dVarDataXY = np.zeros([a3dVarDataXYT.shape[0], a3dVarDataXYT.shape[1]])
            a2dVarDataXY = a3dVarDataXYT[:, :, iStep]

            # Organize Data
            # a2dVarDataYX = np.zeros([a3dVarDataXYT.shape[0], a3dVarDataXYT.shape[1]])
            a2dVarDataYX = np.transpose(np.rot90(a2dVarDataXY, -1))

            # Store Data
            a3dVarDataTYX[iStep, :, :] = a2dVarDataYX

        # Save Data
        oVar[:, :] = np.transpose(np.rot90(a3dVarDataXYT, -1))

    else:
        Exc.getExc(
            ' =====> WARNING: in saving file 3d variable ' + sVarName + '. '
            + 'Variable is null and not saved! (lib_data_io_netcdf)', 2, 1)

# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Method to write 2d variable
def write2DVar(oFileData, sVarName, a2dVarDataXY, oVarAttr, sVarFormat, sVarDimY=None, sVarDimX=None):

    # Check dimensions definition
    if not sVarDimY or not sVarDimX:
        Exc.getExc(
            ' =====> ERROR: in saving file 2d variable ' + sVarName + '. '
            + 'Dimensions are not correctly defined! (lib_data_io_netcdf)', 2, 1)
    else:
        pass

    # Check Data availability
    if a2dVarDataXY is not None:

        # Creating variable
        oVar = oFileData.createVariable(sVarName, sVarFormat, (sVarDimY, sVarDimX,), zlib=True)

        # Saving all variable attribute(s)
        if oVarAttr:
            for sVarAttr in oVarAttr:
                # Retrieving attribute value
                sVarOptValue = oVarAttr[sVarAttr]
                # Saving attribute
                oVar.setncattr(sVarAttr.lower(), str(sVarOptValue))
        else:
            Exc.getExc(
                ' =====> WARNING: in saving file 2d variable ' + sVarName + '. '
                + 'Attributes are null but variable saved correctly! (lib_data_io_netcdf)', 2, 1)

        # Debug to check map orientation
        # if sVarName == 'Terrain':
        #    plt.figure(1)
        #    plt.imshow(np.transpose(np.rot90(a2dVarDataXY,-1))); plt.colorbar()
        #    plt.show()

        # Saving variable Data
        oVar[:, :] = np.transpose(np.rot90(a2dVarDataXY, -1))

    else:
        Exc.getExc(
            ' =====> WARNING: in saving file 2d variable ' + sVarName + '. '
            + 'Variable is null and not saved! (Lib_Data_IO_NetCDF)', 2, 1)

# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Method to write 1d variable
def write1DVar(oFileData, sVarName, a1dVarData, oVarAttr, sVarFormat, sVarDim=None):

    # Check dimensions definition
    if not sVarDim:
        Exc.getExc(
            ' =====> ERROR: in saving file 1d variable ' + sVarName + '. '
            + 'Dimensions are not correctly defined! (lib_data_io_netcdf)', 2, 1)
    else:
        pass

    # Check Data availability
    if a1dVarData is not None:

        # Creating variable
        oVar = oFileData.createVariable(sVarName, sVarFormat, sVarDim, zlib=True)
        # Saving all variable attribute(s)
        if oVarAttr:
            for sVarAttr in oVarAttr:
                # Retrieving attribute value
                sVarOptValue = oVarAttr[sVarAttr]
                # Saving attribute
                oVar.setncattr(sVarAttr.lower(), str(sVarOptValue))
        else:
            Exc.getExc(
                ' =====> WARNING: in saving file 1d variable ' + sVarName + '. '
                + 'Attributes are null but variable saved correctly! (lib_data_io_netcdf)', 2, 1)

        # Saving variable Data
        oVar[:] = a1dVarData

    else:
        Exc.getExc(
            ' =====> WARNING: in saving file 1d variable ' + sVarName + '. '
            + 'Variable is null and not saved! (lib_data_io_netcdf)', 2, 1)

# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Method to get time information
def getTime(oFileData, sVarName='time'):

    # a1sTime = None
    try:
        from datetime import datetime
        from netCDF4 import num2date, date2num

        oTime = oFileData.variables[sVarName]

        oTimeUnits = oFileData.variables[sVarName].units
        try:
            oTimeCalendar = oFileData.variables[sVarName].calendar
        except AttributeError:  # Attribute doesn't exist
            oTimeCalendar = u"gregorian"  # or standard

        a1oTime = num2date(oTime[:], units=oTimeUnits, calendar=oTimeCalendar)

        a1sTime = []
        for oTime in a1oTime:
            sTime = oTime.strftime(sTimeFormat_Default)
            a1sTime.append(sTime)

    except BaseException:
        a1sTime = None

    return sorted(a1sTime)
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Method to write time information
def writeTime(oFileData, sTimeVar='time', oTime=None, sTimeType='float64', sTimeDim='time',
              sTimeFormat=sTimeFormat_Default,
              sTimeCalendar=sTimeCalendar_Default,
              sTimeUnits=sTimeUnits_Default):

    from datetime import datetime
    from netCDF4 import date2num, num2date

    # Define time dimension
    if isinstance(oTime, str):
        oTime = [oTime]
    iTimeSteps = len(oTime)

    # Define time reference(s)
    oDateFrom = datetime.strptime(oTime[0], sTimeFormat)
    oDateTo = datetime.strptime(oTime[-1], sTimeFormat)

    # Generate datetime from time(s)
    oTimeDates = []
    for iTime, sTime in enumerate(oTime):
        oTimeDates.append(datetime(int(sTime[0:4]), int(sTime[4:6]), int(sTime[6:8]), int(sTime[8:10]), int(sTime[10:12])))

    if not checkDimName(oFileData, sTimeDim):
        oTimeDim = oFileData.createDimension(dimname=sTimeDim, size=iTimeSteps)

    # Write time stamps
    oTimeVar = oFileData.createVariable(varname=sTimeVar, dimensions=(sTimeDim,), datatype=sTimeType)
    oTimeVar.calendar = sTimeCalendar
    oTimeVar.units = sTimeUnits
    oTimeVar.time_date = str(np.array(oTime))
    oTimeVar.time_start = oDateFrom.strftime(sTimeFormat)
    oTimeVar.time_end = oDateTo.strftime(sTimeFormat)
    oTimeVar.axis = 'T'

    oTimeVar[:] = date2num(oTimeDates, units=oTimeVar.units, calendar=oTimeVar.calendar)

    # Debug
    # oDates_Check = num2date(oTimes[:],units=oTimes.units,calendar=oTimes.calendar)
    # print(oDates_Check)

    return oFileData

# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Method to write array in file or variable attribute(s)
def writeArray(oFileData, sAttrName, oAttrArray):

    # Insert parameter(s) information
    a1oAttrValue = []
    for oAttrKeys, oAttrValue in oAttrArray.items():

        a1oAttrValue.append(str(oAttrKeys) + ':' + str(oAttrValue) + ' ')

    oFileData.setncattr(sAttrName.lower(), a1oAttrValue)

    return oFileData

# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Method to write file attribute(s)
def writeFileAttrs(oFileData, oFileAttributes):

    # Library
    import time

    # Cycle on file attribute(s)
    for sFileAttr in oFileAttributes:
        # Retrieve attribute value
        sFileValue = oFileAttributes[sFileAttr]
        # Save attribute
        oFileData.setncattr(sFileAttr, sFileValue)

    # Add file creation date
    oFileData.filedate = 'Created ' + time.ctime(time.time())

    return oFileData

# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Method to get geographical system
def getGeoSystem(oFileData, sGeoVar='crs'):

    oGeoObj = oFileData[sGeoVar]
    oGeoAttrs = oGeoObj.ncattrs()

    oGeoSystem = {}
    for sGeoName in oGeoAttrs:
        oGeoValue = oGeoObj.getncattr(sGeoName)
        oGeoSystem[sGeoName] = oGeoValue
    return oGeoSystem

# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Method to write geographical system
def writeGeoSystem(oFileData, oGeoSystemInfo, sGeoVar='crs'):

    # Open geographical system variable(s)
    if checkVarName(oFileData, sGeoVar) is False:
        oGeoSystem = oFileData.createVariable(sGeoVar, 'i')
    else:
        oGeoSystem = getGeoSystem(oFileData, sGeoVar)

    # Insert geographical system information
    for sGeoSystemKeys, oGeoSystemValue in oGeoSystemInfo.items():
        oGeoSystem.setncattr(sGeoSystemKeys.lower(), oGeoSystemValue)

    return oFileData

# ----------------------------------------------------------------------------
