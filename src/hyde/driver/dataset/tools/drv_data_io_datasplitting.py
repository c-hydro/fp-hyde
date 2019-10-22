"""
Library Features:

Name:          drv_data_io_datasplitting
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20181010'
Version:       '1.0.0'
"""
#################################################################################
# Library
import logging

from datetime import datetime
from os import remove
from os.path import exists
from copy import deepcopy
from numpy import full

from fp.utils.lib_utils_op_string import defineString
from fp.utils.lib_utils_op_list import mergeList
from fp.utils.lib_utils_apps_file import handleFileData, selectFileDriver, zipFileData
from fp.utils.lib_utils_apps_time import getTimeFrom, getTimeTo, getTimeSteps

from fp.default.lib_default_args import sZipExt as sZipExt_Default
from fp.default.lib_default_args import sTimeFormat as sTimeFormat_Default
from fp.default.lib_default_args import sTimeCalendar as sTimeCalendar_Default
from fp.default.lib_default_args import sTimeUnits as sTimeUnits_Default
from fp.default.lib_default_conventions import oVarConventions as oVarConventions_Default
from fp.default.lib_default_conventions import oFileConventions as oFileConventions_Default

from fp.default.lib_default_args import sLoggerName

from fp.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
#################################################################################

# -------------------------------------------------------------------------------------
# Algorithm definition(s)
oVarKey_Ancillary = ['longitude', 'latitude', 'crs', 'time', 'attributes', 'dimensions']
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Class data object
class DataObj(dict):
    pass
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Class to compute time product
class DataProductTime:

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, **kwargs):
        self.sVarTime = kwargs['time']
        self.oVarTime = kwargs['settings']['data']['dynamic']['time']
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute data time
    def computeDataTime(self):

        sVarTime = self.sVarTime
        oVarTime = self.oVarTime

        if 'time_observed_step' in oVarTime and 'time_observed_delta' in oVarTime:
            iVarTimeObsStep = oVarTime['time_observed_step']
            iVarTimeObsDelta = oVarTime['time_observed_delta']
        else:
            iVarTimeObsStep = 0
            iVarTimeObsDelta = 0

        if 'time_forecast_step' in oVarTime and 'time_forecast_delta' in oVarTime:
            iVarTimeForStep = oVarTime['time_forecast_step']
            iVarTimeForDelta = oVarTime['time_forecast_delta']
        else:
            iVarTimeForStep = 0
            iVarTimeForDelta = 0

        sVarTimeFrom = getTimeFrom(sVarTime, iVarTimeObsDelta, iVarTimeObsStep)[0]
        sVarTimeTo = getTimeTo(sVarTime, iVarTimeForDelta, iVarTimeForStep)[0]

        a1oVarTimeObs = getTimeSteps(sVarTimeFrom, sVarTime, iVarTimeObsDelta)
        a1oVarTimeFor = getTimeSteps(sVarTime, sVarTimeTo, iVarTimeForDelta)

        a1oVarTime = mergeList(a1oVarTimeObs, a1oVarTimeFor)
        a1oVarTime.sort()

        return a1oVarTime

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Class to clean data product
class DataProductCleaner:

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, **kwargs):
        self.a1oFile = kwargs['file']
        self.a1bFlag = kwargs['flag']
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to clean selected file(s)
    def cleanDataProduct(self):

        if isinstance(self.a1bFlag, bool):
            self.a1bFlag = [self.a1bFlag]
        if isinstance(self.a1oFile, str):
            self.a1oFile = [self.a1oFile]

        if self.a1bFlag.__len__() < self.a1oFile.__len__():
            self.a1bFlag = full(self.a1oFile.__len__(),  self.a1bFlag[0], dtype=bool)

        for bFlag, oFile in zip(self.a1bFlag, self.a1oFile):
            if isinstance(oFile, str):
                oFile = [oFile]
            for sFile in oFile:
                if exists(sFile):
                    if bFlag:
                        remove(sFile)
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Class to finalize data product
class DataProductFinalizer:

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, **kwargs):

        self.sAlgTime = kwargs['time']
        self.oVarSetting = kwargs['settings']
        self.oVarData = kwargs['data']
        self.sVarFile = kwargs['data_product_file']
        self.oAlgConventions = kwargs['settings']['algorithm']

        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to save data
    def saveDataProduct(self, oDataGeo=None, bDataUpdate=False):

        # -------------------------------------------------------------------------------------
        # Get time step information
        sAlgTime = self.sAlgTime
        oVarData = self.oVarData
        sVarFile = self.sVarFile

        # Info start
        oLogStream.info(' ---> Save data at time: ' + sAlgTime + ' ... ')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Check data availability
        if oVarData:

            # -------------------------------------------------------------------------------------
            # Get file dimension(s)
            if 'dimensions' in oVarData:
                oFileDims = oVarData['dimensions']
                oVarData.pop('dimensions')
            else:
                Exc.getExc(
                    ' ---> WARNING: file dimension(s) not found! Use X,Y of grid reference and time equal to 1', 2, 1)
                oFileDims = {'X': {'size': oDataGeo.a2dGeoY.shape[1]},
                             'Y': {'size': oDataGeo.a2dGeoX.shape[0]},
                             'time': {'size': 1}}
            # Get file attribute(s)
            if 'attributes' in oVarData:
                oFileAttributes = oVarData['attributes']
                oVarData.pop('attributes')
            else:
                Exc.getExc(' ---> WARNING: file attribute(s) not found! Use default attributes', 2, 1)
                oFileAttributes = oFileConventions_Default['general']
            # Get file time(s)
            if 'time' in oVarData:
                oFileTime = oVarData['time']
                oVarData.pop('time')
            else:
                Exc.getExc(' ---> WARNING: file times(s) not found! Use general time with step equal to 1', 2, 1)
                oFileTime = [sVarTime]
            # Get file geographical system
            if 'crs' in oVarData:
                oFileCRS = oVarData['crs']
                oVarData.pop('crs')
            else:
                Exc.getExc(' ---> WARNING: file geographical system not found! Use default geographical system', 2, 1)
                oFileCRS = oFileConventions_Default['geosystem']
            # Get data longitude
            if 'longitude' in oVarData:
                a2dVarGeoX = oVarData['longitude']
                oVarData.pop('longitude')
            else:
                Exc.getExc(' ---> WARNING: data longitude not found! Use grid reference', 2, 1)
                a2dVarGeoX = oDataGeo.a2dGeoX
            # Get data latitude
            if 'latitude' in oVarData:
                a2dVarGeoY = oVarData['latitude']
                oVarData.pop('latitude')
            else:
                Exc.getExc(' ---> WARNING: data longitude not found! Use grid reference', 2, 1)
                a2dVarGeoY = oDataGeo.a2dGeoY
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Iterate over data time steps
            for iVarTime, sVarTime in enumerate(oFileTime):

                # -------------------------------------------------------------------------------------
                # Define time tags
                oTimeTags = {'$yyyy': sVarTime[0:4],
                             '$mm': sVarTime[4:6], '$dd': sVarTime[6:8], '$HH': sVarTime[8:10],
                             '$MM': sVarTime[10:12]}
                # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Get filename from file definition(s) using file tag in outcome variable(s)
                sVarFileName = defineString(deepcopy(sVarFile), oTimeTags)
                # Info start about selected file
                oLogStream.info(' ----> Save file: ' + sVarFileName + ' (Time: ' + sVarTime + ') ... ')
                # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Activate data updating (for common period between different runs)
                if bDataUpdate:
                    oAlgTime = datetime.strptime(sAlgTime, sTimeFormat_Default)
                    oVarTime = datetime.strptime(sVarTime, sTimeFormat_Default)
                    if oVarTime > oAlgTime:
                        if exists(sVarFileName):
                            oLogStream.info(
                                ' -----> Update file using a newest run [ ' + sAlgTime + ' ] for time ' + sVarTime)
                            remove(sVarFileName)
                # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Check file saved on disk
                if not exists(sVarFileName):

                    # -------------------------------------------------------------------------------------
                    # Info create file
                    oLogStream.info(' -----> Create file ' + sVarFileName + ' ... ')

                    # Get file driver (according with filename extensions
                    [oFileDriver, sFileUnzip, sFileZip] = selectFileDriver(sVarFileName, sZipExt_Default)

                    # Open file outcome
                    oFileData = oFileDriver.oFileLibrary.openFile(sFileUnzip, 'w')

                    # Write file attributes
                    oFileDriver.oFileLibrary.writeFileAttrs(oFileData, oFileAttributes)
                    # Write geo system information
                    oFileDriver.oFileLibrary.writeGeoSystem(oFileData, oFileCRS)
                    # Write X, Y, time, nsim, ntime and nens
                    oFileDriver.oFileLibrary.writeDims(oFileData, 'X', oFileDims['X']['size'])
                    oFileDriver.oFileLibrary.writeDims(oFileData, 'Y', oFileDims['Y']['size'])
                    oFileDriver.oFileLibrary.writeDims(oFileData, 'time', 1)
                    oFileDriver.oFileLibrary.writeDims(oFileData, 'nsim', 1)
                    oFileDriver.oFileLibrary.writeDims(oFileData, 'ntime', 2)
                    oFileDriver.oFileLibrary.writeDims(oFileData, 'nens', 1)

                    # Get file dimension(s)
                    oFileDims = oFileDriver.oFileLibrary.getDims(oFileData)

                    # Write time information
                    oFileDriver.oFileLibrary.writeTime(oFileData, 'time', sVarTime, 'float64', 'time',
                                                       sTimeFormat_Default, sTimeCalendar_Default,
                                                       sTimeUnits_Default)

                    # Write longitude information
                    sVarNameX = 'longitude'
                    a2VarDataX = a2dVarGeoX
                    oVarAttrsX = oVarConventions_Default[sVarNameX]
                    sVarFormatX = oVarConventions_Default[sVarNameX]['Format']
                    oFileDriver.oFileLibrary.write2DVar(oFileData, sVarNameX,
                                                        a2VarDataX, oVarAttrsX, sVarFormatX,
                                                        sVarDimY=oFileDims['Y']['name'],
                                                        sVarDimX=oFileDims['X']['name'])
                    # Write latitude information
                    sVarNameY = 'latitude'
                    a2VarDataY = a2dVarGeoY
                    oVarAttrsY = oVarConventions_Default[sVarNameY]
                    sVarFormatY = oVarConventions_Default[sVarNameY]['Format']
                    oFileDriver.oFileLibrary.write2DVar(oFileData, sVarNameY,
                                                        a2VarDataY, oVarAttrsY, sVarFormatY,
                                                        sVarDimY=oFileDims['Y']['name'],
                                                        sVarDimX=oFileDims['X']['name'])

                    # Info create file
                    oLogStream.info(' -----> Create file ' + sVarFileName + ' ... OK')
                    # -------------------------------------------------------------------------------------
                else:
                    # -------------------------------------------------------------------------------------
                    # Info get file
                    oLogStream.info(' -----> Get file ' + sVarFileName + ' previously created ... ')
                    # Get file driver (according with filename extensions
                    [oFileDriver, sFileUnzip, sFileZip] = selectFileDriver(sVarFileName, sZipExt_Default)

                    # Open file outcome
                    oFileData = oFileDriver.oFileLibrary.openFile(sFileUnzip, 'a')
                    # Get file dimension(s)
                    oFileDims = oFileDriver.oFileLibrary.getDims(oFileData)

                    # Info get file
                    oLogStream.info(' -----> Get file ' + sVarFileName + ' previously created ... OK')
                    # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Info start saving variable
                for sVarName, oVarWS in oVarData.items():

                    # Info start
                    oLogStream.info(' ----> Save variable ' + sVarName + ' ... ')

                    # Check variable in file handle
                    if oFileDriver.oFileLibrary.checkVarName(oFileData, sVarName) is False:

                        # -------------------------------------------------------------------------------------
                        # Get file dimensions
                        sVarDimX = oFileDims['X']['name']
                        sVarDimY = oFileDims['Y']['name']
                        sVarDimT = oFileDims['time']['name']

                        # Get var structure
                        oVarValues = oVarWS['values']
                        oVarAttributes = oVarWS['attributes']

                        # Get variable format
                        if 'Format' in oVarAttributes:
                            sVarFormat = oVarAttributes['Format']
                        else:
                            sVarFormat = 'f4'

                        oFileDriver.oFileLibrary.write2DVar(oFileData,
                                                            sVarName, oVarValues[:, :, iVarTime],
                                                            oVarAttributes, sVarFormat,
                                                            sVarDimY=sVarDimY, sVarDimX=sVarDimX)

                        # Info end saving variable
                        oLogStream.info(' ----> Save variable ' + sVarName + ' ... OK ')
                        # -------------------------------------------------------------------------------------
                    else:
                        # -------------------------------------------------------------------------------------
                        # Info skip saving variable
                        oLogStream.info(' ----> Save variable ' + sVarName +
                                        ' ... SKIPPED! Variable is already saved in selected file ')
                        # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Info start closing and zipping file
                oLogStream.info(' -----> Close and zip file ' + sVarFileName + ' ... ')
                # Close file
                oFileDriver.oFileLibrary.closeFile(oFileData)
                # Zip file
                zipFileData(sFileUnzip, sZipExt_Default)
                # Info end closing and zipping file
                oLogStream.info(' -----> Close and zip file ' + sVarFileName + ' ... OK')

                # Info end about selected file
                oLogStream.info(' ----> Save file: ' + sVarFileName + ' (Time: ' + sVarTime + ') ... OK')
                # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Info end
            oLogStream.info(' ---> Save data at time: ' + sAlgTime + ' ... OK')
            # -------------------------------------------------------------------------------------

        else:

            # -------------------------------------------------------------------------------------
            # Info end
            oLogStream.info(' ---> Save data at time: ' + sAlgTime + ' ... SKIPPED')
            Exc.getExc(' ---> WARNING: data are not available at this time step!', 2, 1)
            # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Class to build data product
class DataProductBuilder:

    # -------------------------------------------------------------------------------------
    # Class declaration(s)
    oVarData = DataObj()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, **kwargs):
        self.oVarTime = kwargs['time']
        self.oVarSetting = kwargs['settings']
        self.oVarFile = kwargs['source_data_file']
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to get data
    def getDataProduct(self):

        # -------------------------------------------------------------------------------------
        # Initialize workspace
        oVarWS = {}

        # Initialize time step
        sVarTime = self.oVarTime
        sVarFile = self.oVarFile

        # Define time tags
        oTimeTags = {'$yyyy': sVarTime[0:4],
                     '$mm': sVarTime[4:6], '$dd': sVarTime[6:8], '$HH': sVarTime[8:10],
                     '$MM': sVarTime[10:12]}
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Get filename from file definition(s) using file tag in outcome variable(s)
        sVarFileName = defineString(deepcopy(sVarFile), oTimeTags)
        # Info start about selected file
        oLogStream.info(' ---> Get file: ' + sVarFileName + ' (Time: ' + sVarTime + ') ... ')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Check file saved on disk
        if exists(sVarFileName):

            # -------------------------------------------------------------------------------------
            # Get data
            [oFileHandle, oFileDriver, bFileOpen] = handleFileData(sVarFileName)
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Check file opening
            if bFileOpen is True:

                # -------------------------------------------------------------------------------------
                # Get file attribute(s)
                oVarWS['attributes'] = oFileDriver.oFileLibrary.getFileAttrs(oFileHandle)
                # Get file dimension(s)
                oVarWS['dimensions'] = oFileDriver.oFileLibrary.getDims(oFileHandle)

                # Iterate over data variable(s)
                oFileVariable = oFileDriver.oFileLibrary.getFileVars(oFileHandle)
                for sVarName, oVarHandle in oFileVariable.items():

                    # -------------------------------------------------------------------------------------
                    # Info start about getting variable
                    oLogStream.info(' ---> Get variable: ' + sVarName + ' ...')

                    # Check variable data in workspace
                    if sVarName not in oVarWS:

                        # -------------------------------------------------------------------------------------
                        # Check variable data in file handle
                        if oFileDriver.oFileLibrary.checkVarName(oFileHandle, sVarName):

                            # -------------------------------------------------------------------------------------
                            # Init variable workspace
                            oVarWS[sVarName] = {}

                            # Check variable dynamic or ancillary
                            if sVarName not in oVarKey_Ancillary:

                                # -------------------------------------------------------------------------------------
                                # Get variable data
                                a3dVarData = oFileDriver.oFileLibrary.get3DVar(oFileHandle, sVarName)
                                # Get variable parameter(s)
                                oVarAttributes = oFileDriver.oFileLibrary.getVarAttrs(oFileHandle, sVarName)
                                # Store variable information
                                oVarWS[sVarName]['values'] = a3dVarData
                                oVarWS[sVarName]['attributes'] = oVarAttributes
                                # -------------------------------------------------------------------------------------

                            else:

                                # -------------------------------------------------------------------------------------
                                # Get variable time(s)
                                if sVarName == 'time':
                                    oVarTimes = oFileDriver.oFileLibrary.getTime(oFileHandle, sVarName)
                                    # Store variable information
                                    oVarWS[sVarName] = oVarTimes
                                # Get variable longitude
                                if sVarName == 'longitude':
                                    a2dVarGeoX = oFileDriver.oFileLibrary.get2DVar(
                                        oFileHandle, sVarName, bSetAutoMask=False)
                                    # Store variable information
                                    oVarWS[sVarName] = a2dVarGeoX
                                # Get variable latitude
                                if sVarName == 'latitude':
                                    a2dVarGeoY = oFileDriver.oFileLibrary.get2DVar(
                                        oFileHandle, sVarName, bSetAutoMask=False)
                                    # Store variable information
                                    oVarWS[sVarName] = a2dVarGeoY
                                if sVarName == 'crs':
                                    oVarGeoSystem = oFileDriver.oFileLibrary.getGeoSystem(oFileHandle, sVarName)
                                    oVarWS[sVarName] = oVarGeoSystem
                                # -------------------------------------------------------------------------------------

                            # -------------------------------------------------------------------------------------
                            # Info end about getting data variable
                            oLogStream.info(' ---> Get variable: ' + sVarName + ' ... OK')
                            # -------------------------------------------------------------------------------------
                        else:
                            # -------------------------------------------------------------------------------------
                            # Info end about getting data variable
                            oLogStream.info(' ---> Get variable: ' + sVarName + ' ... FAILED!')
                            Exc.getExc(' ---> WARNING: variable is not available in selected file!', 2, 1)
                            # -------------------------------------------------------------------------------------
                    else:
                        # -------------------------------------------------------------------------------------
                        # Info end about getting data variable
                        oLogStream.info(' ---> Get variable: ' + sVarName +
                                        ' ... SKIPPED! Variable already set in workspace!')
                        # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Close file handle
                oFileDriver.oFileLibrary.closeFile(oFileHandle)
                oLogStream.info(' ---> Get file: ' + sVarFileName + ' (Time: ' + sVarTime + ') ... OK')
                # -------------------------------------------------------------------------------------
            else:
                # -------------------------------------------------------------------------------------
                # Exit file not in workspace
                oLogStream.info(' ---> Get file: ' + sVarFileName + ' (Time: ' + sVarTime + ') ... FAILED!')
                Exc.getExc(' ---> WARNING: file not correctly opened!', 2, 1)
                # -------------------------------------------------------------------------------------
        else:
            # -------------------------------------------------------------------------------------
            # Exit file not in workspace
            oLogStream.info(' ---> Get file: ' + sVarFileName + ' (Time: ' + sVarTime + ') ... FAILED')
            Exc.getExc(' ---> WARNING: file does not exist!', 2, 1)
            # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Return workspace
        return oVarWS
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
