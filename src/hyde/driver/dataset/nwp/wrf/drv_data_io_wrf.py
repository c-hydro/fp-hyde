"""
Library Features:

Name:          drv_data_io_wrf
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190916'
Version:       '1.1.0'
"""
#################################################################################
# Library
import logging
import progressbar

from os import remove
from os.path import exists, isfile
from copy import deepcopy
from numpy import where, reshape, full, empty, nan, zeros

from src.common.analysis.lib_analysis_interpolation_grid import interpGridData, interpGridIndex

from src.common.utils.lib_utils_apps_geo import createMeshGrid
from src.common.utils.lib_utils_op_string import defineString
from src.common.utils.lib_utils_op_dict import mergeDict
from src.common.utils.lib_utils_op_list import mergeList
from src.common.utils.lib_utils_apps_data import updateDictStructure, squeezeDataArray
from src.common.utils.lib_utils_apps_file import handleFileData, selectFileDriver, zipFileData
from src.common.utils.lib_utils_file_workspace import savePickle, restorePickle
from src.common.utils.lib_utils_apps_time import getTimeFrom, getTimeTo, getTimeSteps

from src.common.default.lib_default_args import sZipExt as sZipExt_Default
from src.common.default.lib_default_args import sTimeFormat as sTimeFormat_Default
from src.common.default.lib_default_args import sTimeCalendar as sTimeCalendar_Default
from src.common.default.lib_default_args import sTimeUnits as sTimeUnits_Default
from src.common.default.lib_default_conventions import oVarConventions as oVarConventions_Default
from src.common.default.lib_default_conventions import oFileConventions as oFileConventions_Default

from src.common.default.lib_default_args import sLoggerName

from src.hyde.driver.dataset.nwp.wrf.cpl_data_variables_wrf import DataVariables

from src.hyde.driver.configuration.generic.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
#################################################################################

# -------------------------------------------------------------------------------------
# Algorithm definition(s)
oVarKey_Valid = {'time': 'Time', 'longitude': 'lon', 'latitude': 'lat'}
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

        oTimeObj = DataObj
        oTimeObj.time_step = sVarTime
        oTimeObj.time_range = a1oVarTime
        oTimeObj.time_from = sVarTimeFrom
        oTimeObj.time_to = sVarTimeTo
        oTimeObj.time_period_obs = iVarTimeObsStep
        oTimeObj.time_period_for = iVarTimeForStep
        oTimeObj.time_freq_obs = iVarTimeObsDelta
        oTimeObj.time_freq_for = iVarTimeForDelta

        return oTimeObj

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
# Class to analyze data product
class DataProductAnalyzer:

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, **kwargs):
        self.oVarTime = kwargs['time']
        self.oVarDef = kwargs['settings']['variables']['input']
        self.oVarData = kwargs['data']
        self.oVarFile = {'grid_ref': kwargs['grid_ref_file']}
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute data
    def computeDataProduct(self, oDataGeo=None):

        # -------------------------------------------------------------------------------------
        # Iterate over file variable(s)
        oVarWS = self.oVarData
        oTimeWS = self.oVarTime
        oVarSel = DataObj()
        for sVarKey, oVarDef in self.oVarDef.items():

            # DEBUG START
            # sVarKey = 'rain_data'
            # oVarDef = self.oVarDef[sVarKey]
            # DEBUG END

            # -------------------------------------------------------------------------------------
            # Get input variable information
            oVarType = oVarDef['id']['var_type']
            oVarName = oVarDef['id']['var_name']
            sVarFile = oVarDef['id']['var_file']
            sVarMethod = oVarDef['id']['var_method_compute']

            oVarAttrs = oVarDef['attributes']

            # Info start about computing variable
            oLogStream.info(' ---> Compute variable: ' + sVarKey + ' ... ')
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Check dictionary data
            if oVarWS:

                # -------------------------------------------------------------------------------------
                # Create workspace for each variable and ancillary data
                oVarSel[sVarKey] = {}
                for sVarName in oVarName:
                    oVarSel[sVarKey][sVarName] = {}
                    if oVarWS[sVarName]:
                        if 'values' in oVarWS[sVarName] \
                                and 'attributes' in oVarWS[sVarName] \
                                and 'parameters' in oVarWS[sVarName] \
                                and 'times' in oVarWS[sVarName]:
                            oVarSel[sVarKey][sVarName]['values'] = {}
                            oVarSel[sVarKey][sVarName]['values'] = oVarWS[sVarName]['values']
                            oVarSel[sVarKey][sVarName]['parameters'] = {}
                            oVarSel[sVarKey][sVarName]['parameters'] = oVarWS[sVarName]['parameters']
                            oVarSel[sVarKey][sVarName]['attributes'] = {}
                            oVarSel[sVarKey][sVarName]['attributes'] = oVarWS[sVarName]['attributes']
                            oVarSel[sVarKey][sVarName]['times'] = {}
                            oVarSel[sVarKey][sVarName]['times'] = oVarWS[sVarName]['times']

                            if 'longitude' not in oVarSel:
                                oVarSel[sVarKey]['longitude'] = oVarWS[sVarName]['longitude']
                            if 'latitude' not in oVarSel:
                                oVarSel[sVarKey]['latitude'] = oVarWS[sVarName]['latitude']

                        else:
                            oVarSel[sVarKey][sVarName] = None
                    else:
                        oVarSel[sVarKey][sVarName] = None

                # Check data available for all selected ancillary variable(s)
                for sVarName in oVarSel[sVarKey]:
                    if oVarSel[sVarKey][sVarName] is None:
                        oVarSel[sVarKey] = None
                        break
                # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Check data field(s) availability to compute results
                if oVarSel[sVarKey]:

                    # -------------------------------------------------------------------------------------
                    # Get method to compute variable
                    oDrv_Data_Cmp = DataVariables(data=oVarSel[sVarKey], component=oVarName, method=sVarMethod)

                    # Define index start and end in relationship with variable type
                    iIndexStart = None
                    iIndexEnd = None
                    if oVarType[1] == 'istantaneous':
                        iIndexStart = 1
                        iIndexEnd = oDrv_Data_Cmp.oVarTimes[0].__len__()
                    elif oVarType[1] == 'accumulated':
                        iIndexStart = 0
                        iIndexEnd = oDrv_Data_Cmp.oVarTimes[0].__len__()
                    else:
                        Exc.getExc(' ---> Variable type definition is not allowed! Check your settings!', 1, 1)

                    # Get values, time(s) and attribute(s)
                    a3dVarValue_CMP, oVarTimes_CMP, oVarAttrs_CMP = oDrv_Data_Cmp.computeVarData(
                        type=oVarType[1], index_start=iIndexStart, index_end=iIndexEnd)
                    oVarSel[sVarKey]['values'] = {}
                    oVarSel[sVarKey]['values'] = a3dVarValue_CMP
                    oVarSel[sVarKey]['times'] = {}
                    oVarSel[sVarKey]['times'] = oVarTimes_CMP
                    oVarSel[sVarKey]['attributes'] = {}
                    oVarSel[sVarKey]['attributes'] = mergeDict(oVarAttrs_CMP, oVarAttrs)

                    # Remove component field(s)
                    for sVarComp in oVarName:
                        oVarSel[sVarKey].pop(sVarComp, None)
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Check all variables are not none
                    if all(oVarCheck is not None for oVarCheck in [a3dVarValue_CMP, oVarTimes_CMP, oVarAttrs_CMP]):

                        # -------------------------------------------------------------------------------------
                        # Check fields definition in variable workspace
                        if ('values' in oVarSel[sVarKey]) and ('attributes' in oVarSel[sVarKey]) and ('times' in oVarSel[sVarKey]):

                            # -------------------------------------------------------------------------------------
                            # Get data and attributes
                            a3dVarValue = deepcopy(oVarSel[sVarKey]['values']).astype(float)
                            a2dVarGeoX = deepcopy(oVarSel[sVarKey]['longitude']).astype(float)
                            a2dVarGeoY = deepcopy(oVarSel[sVarKey]['latitude']).astype(float)
                            oVarAttrs = deepcopy(oVarSel[sVarKey]['attributes'])
                            oVarTime = deepcopy(oVarSel[sVarKey]['times'])
                            # -------------------------------------------------------------------------------------

                            # -------------------------------------------------------------------------------------
                            # Apply filter to avoid no data values
                            if 'Missing_value' in oVarAttrs:
                                iVarMissValue = oVarAttrs['Missing_value']
                            else:
                                iVarMissValue = -9999.0
                            # Apply scale factor to geographical array(s)
                            if 'ScaleFactor' in oVarAttrs:
                                iScaleFactor = oVarAttrs['ScaleFactor']
                            else:
                                iScaleFactor = 1
                            # Filter variable over grid reference points
                            if '_FillValue' in oVarAttrs:
                                dVarFillValue = oVarAttrs['_FillValue']
                            else:
                                dVarFillValue = -9999.0
                            # -------------------------------------------------------------------------------------

                            # -------------------------------------------------------------------------------------
                            # Get expected time period
                            oVarTime_EXP = oTimeWS.time_range[1:]

                            # Check lengths of time lists
                            if oVarTime.__len__() == oVarTime_EXP.__len__():
                                for sTimeCMP, sTimeEXP in zip(oVarTime, oVarTime_EXP):
                                    if sTimeCMP != sTimeEXP:
                                        oVarTime = oVarTime_EXP
                                        oVarSel[sVarKey]['times'] = oVarTime_EXP

                                        Exc.getExc(' ---> Correction of time range. '
                                                   'Variable time(s) and expected time(s) are different! '
                                                   'Set expected time(s) as reference', 2, 1)
                                        break
                            else:
                                # Exit if lists of time have different length
                                Exc.getExc(' ---> Variable time and expected time have a different lenght. '
                                           'Check your settings!', 1, 1)
                            # -------------------------------------------------------------------------------------

                            # -------------------------------------------------------------------------------------
                            # Initialize variable to store results
                            a3dVarValue_FILTER = zeros([oDataGeo.a2dGeoX.shape[0], oDataGeo.a2dGeoY.shape[1],
                                                        oVarTime.__len__()])
                            a3dVarValue_FILTER[:, :, :] = nan

                            # Info start interpolating variable
                            oLogStream.info(' ----> Interpolate and filter variable over domain ... ')

                            # Iterate over time step(s)
                            oPBar = progressbar.ProgressBar()
                            for iTimeStep, sTimeStep in enumerate(oPBar(oVarTime)):

                                # -------------------------------------------------------------------------------------
                                # Create grid reference(s)
                                if not exists(self.oVarFile['grid_ref']):
                                    a1iVarIndex_INTERP = interpGridIndex(a3dVarValue[:, :, iTimeStep],
                                                                         a2dVarGeoX, a2dVarGeoY,
                                                                         oDataGeo.a2dGeoX, oDataGeo.a2dGeoY)

                                    savePickle(self.oVarFile['grid_ref'], a1iVarIndex_INTERP)
                                else:
                                    a1iVarIndex_INTERP = restorePickle(self.oVarFile['grid_ref'])

                                # Interpolate variable over grid reference
                                a2dVarValue_INTERP = interpGridData(a3dVarValue[:, :, iTimeStep],
                                                                    a2dVarGeoX, a2dVarGeoY,
                                                                    oDataGeo.a2dGeoX, oDataGeo.a2dGeoY,
                                                                    a1iVarIndex_OUT=a1iVarIndex_INTERP)
                                # Filter variable over domain reference
                                a1dVarValue_INTERP = deepcopy(a2dVarValue_INTERP.ravel())
                                a1dVarValue_INTERP[oDataGeo.a1iGeoIndexNaN] = dVarFillValue
                                a2dVarValue_FILTER = reshape(a1dVarValue_INTERP,
                                                             [oDataGeo.a2dGeoX.shape[0], oDataGeo.a2dGeoY.shape[1]])
                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Debug
                                # plt.figure()
                                # plt.imshow(a3dVarValue[:, :, iTimeStep]); plt.colorbar(); plt.clim(0, 10)
                                # plt.figure()
                                # plt.imshow(a2dVarValue_INTERP); plt.colorbar(); plt.clim(0, 10)
                                # plt.figure()
                                # plt.imshow(a2dVarValue_FILTER); plt.colorbar(); plt.clim(0, 10)
                                # plt.show()
                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Store results
                                a3dVarValue_FILTER[:, :, iTimeStep] = a2dVarValue_FILTER
                                # -------------------------------------------------------------------------------------

                            # -------------------------------------------------------------------------------------
                            # Info end interpolating variable
                            oLogStream.info(' ----> Interpolate and filter variable over domain ... OK')

                            # Add attributes to workspace
                            if not hasattr(oVarSel, 'iRows'):
                                oVarSel.iRows = a3dVarValue_FILTER.shape[0]
                            if not hasattr(oVarSel, 'iCols'):
                                oVarSel.iCols = a3dVarValue_FILTER.shape[1]
                            if not hasattr(oVarSel, 'iTime'):
                                oVarSel.iTime = a3dVarValue_FILTER.shape[2]
                            if not hasattr(oVarSel, 'oDataTime'):
                                oVarSel.oDataTime = oVarTime

                            # Save data
                            oVarSel[sVarKey]['results'] = a3dVarValue_FILTER
                            # Info end computing variable
                            oLogStream.info(' ---> Compute variable: ' + sVarKey + ' ... OK')
                            # -------------------------------------------------------------------------------------

                        else:

                            # -------------------------------------------------------------------------------------
                            # Exit variable key not in workspace
                            Exc.getExc(' ---> Compute variable: ' + sVarKey +
                                       ' ... FAILED! Values and/or attributes field(s) is/are not defined!', 2, 1)
                            oVarSel[sVarKey] = None
                            # -------------------------------------------------------------------------------------

                    else:

                        # -------------------------------------------------------------------------------------
                        # Exit variable key not in workspace
                        Exc.getExc(' ---> Compute variable: ' + sVarKey +
                                   ' ... FAILED! Computing method exited with none values!', 2, 1)
                        oVarSel[sVarKey] = None
                        # -------------------------------------------------------------------------------------

                else:

                    # -------------------------------------------------------------------------------------
                    # Exit variable key not in workspace
                    Exc.getExc(' ---> Compute variable: ' + sVarKey +
                               ' ... FAILED! One or more data field(s) is/are not defined!', 2, 1)
                    oVarSel[sVarKey] = None
                    # -------------------------------------------------------------------------------------

            else:

                # -------------------------------------------------------------------------------------
                # Exit variable key not in workspace
                Exc.getExc(' ---> Compute variable: ' + sVarKey +
                           ' ... FAILED! Dictionary data are empty!', 2, 1)
                oVarSel[sVarKey] = None
                # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Return workspace
        return oVarSel
        # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class to finalize data product
class DataProductFinalizer:

    # -------------------------------------------------------------------------------------
    # Class declaration(s)
    oVarCM = None
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, **kwargs):

        self.sVarTime = kwargs['time']
        self.oVarDef = kwargs['settings']['variables']['outcome']
        self.oVarData = kwargs['data']
        self.oVarFile = {'wrf_product': kwargs['wrf_product_file']}
        self.oVarColorMap = kwargs['wrf_colormap_file']
        self.oAlgConventions = kwargs['settings']['algorithm']
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to get variable colormap
    @staticmethod
    def __getColorMap(sFileCM):

        # Get file driver (according with filename extensions
        if isfile(sFileCM):
            oFileDriver = selectFileDriver(sFileCM, sFileMode='r')[0]
            oFileCM = oFileDriver.oFileLibrary.openFile(sFileCM, 'r')
            oFileLines = oFileDriver.oFileLibrary.getLines(oFileCM)
        else:
            oFileLines = ''

        return oFileLines

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to save data
    def saveDataProduct(self, oDataGeo=None):

        # -------------------------------------------------------------------------------------
        # Get time step information
        sVarTime = self.sVarTime

        # Define general and geo-system information
        oFileGeneralInfo = updateDictStructure(oFileConventions_Default, self.oAlgConventions, 'general')
        oFileGeoSystemInfo = updateDictStructure(oFileConventions_Default, self.oAlgConventions, 'geosystem')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Iterate over outcome variable(s)
        for sVarKey, oVarDef in self.oVarDef.items():

            # -------------------------------------------------------------------------------------
            # Info start saving variable
            oLogStream.info(' ---> Save workspace: ' + sVarKey + ' ... ')

            # Get outcome variable information
            oVarType = oVarDef['id']['var_type']
            sVarName = oVarDef['id']['var_name']
            sVarFile = oVarDef['id']['var_file']
            sVarMethod = oVarDef['id']['var_method_save']
            sVarColormap = oVarDef['id']['var_colormap']

            # Get outcome variable colormap
            oVarCM = {}
            if sVarKey in self.oVarData:
                oVarCM['colormap'] = self.__getColorMap(self.oVarColorMap[sVarColormap])
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Check variable workspace
            if self.oVarData[sVarKey]:

                # -------------------------------------------------------------------------------------
                # Check file tag in file definition(s)
                if sVarFile in self.oVarFile:

                    # -------------------------------------------------------------------------------------
                    # Get filename from file definition(s) using file tag in outcome variable(s)
                    sVarFileName = self.oVarFile[sVarFile]
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Check file saved on disk
                    if not exists(sVarFileName):

                        # -------------------------------------------------------------------------------------
                        # Info create file
                        oLogStream.info(' ----> Create file ' + sVarFileName + ' ... ')

                        # Get file driver (according with filename extensions
                        [oFileDriver, sFileUnzip, sFileZip] = selectFileDriver(sVarFileName, sZipExt_Default)

                        # Open file outcome
                        oFileData = oFileDriver.oFileLibrary.openFile(sFileUnzip, 'w')

                        # Write file attributes
                        oFileDriver.oFileLibrary.writeFileAttrs(oFileData, oFileGeneralInfo)
                        # Write geo system information
                        oFileDriver.oFileLibrary.writeGeoSystem(oFileData, oFileGeoSystemInfo)
                        # Write X, Y, time, nsim, ntime and nens
                        oFileDriver.oFileLibrary.writeDims(oFileData, 'X', self.oVarData.iCols)
                        oFileDriver.oFileLibrary.writeDims(oFileData, 'Y', self.oVarData.iRows)
                        oFileDriver.oFileLibrary.writeDims(oFileData, 'time', self.oVarData.iTime)
                        oFileDriver.oFileLibrary.writeDims(oFileData, 'nsim', 1)
                        oFileDriver.oFileLibrary.writeDims(oFileData, 'ntime', 2)
                        oFileDriver.oFileLibrary.writeDims(oFileData, 'nens', 1)

                        # Get file dimension(s)
                        oFileDims = oFileDriver.oFileLibrary.getDims(oFileData)

                        # Write time information
                        oFileDriver.oFileLibrary.writeTime(oFileData, 'time', self.oVarData.oDataTime, 'float64', 'time',
                                                           sTimeFormat_Default, sTimeCalendar_Default,
                                                           sTimeUnits_Default)

                        # Write longitude information
                        sVarNameX = 'longitude'
                        a2VarDataX = oDataGeo.a2dGeoX
                        oVarAttrsX = oVarConventions_Default[sVarNameX]
                        sVarFormatX = oVarConventions_Default[sVarNameX]['Format']
                        oFileDriver.oFileLibrary.write2DVar(oFileData, sVarNameX,
                                                            a2VarDataX, oVarAttrsX, sVarFormatX,
                                                            sVarDimY=oFileDims['Y']['name'],
                                                            sVarDimX=oFileDims['X']['name'])
                        # Write latitude information
                        sVarNameY = 'latitude'
                        a2VarDataY = oDataGeo.a2dGeoY
                        oVarAttrsY = oVarConventions_Default[sVarNameY]
                        sVarFormatY = oVarConventions_Default[sVarNameY]['Format']
                        oFileDriver.oFileLibrary.write2DVar(oFileData, sVarNameY,
                                                            a2VarDataY, oVarAttrsY, sVarFormatY,
                                                            sVarDimY=oFileDims['Y']['name'],
                                                            sVarDimX=oFileDims['X']['name'])

                        # Info create file
                        oLogStream.info(' ----> Create file ' + sVarFileName + ' ... OK')
                        # -------------------------------------------------------------------------------------
                    else:
                        # -------------------------------------------------------------------------------------
                        # Info get file
                        oLogStream.info(' ----> Get file ' + sVarFileName + ' previously created ... ')
                        # Get file driver (according with filename extensions
                        [oFileDriver, sFileUnzip, sFileZip] = selectFileDriver(sVarFileName, sZipExt_Default)

                        # Open file outcome
                        oFileData = oFileDriver.oFileLibrary.openFile(sFileUnzip, 'a')
                        # Get file dimension(s)
                        oFileDims = oFileDriver.oFileLibrary.getDims(oFileData)

                        # Info get file
                        oLogStream.info(' ----> Get file ' + sVarFileName + ' previously created ... OK')
                        # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Info start saving variable
                    oLogStream.info(' -----> Save variable ' + sVarName + ' ... ')
                    # Check variable in file handle
                    if oFileDriver.oFileLibrary.checkVarName(oFileData, sVarName) is False:

                        # -------------------------------------------------------------------------------------
                        # Get file dimensions
                        sVarDimX = oFileDims['X']['name']
                        sVarDimY = oFileDims['Y']['name']
                        sVarDimT = oFileDims['time']['name']

                        # Get var structure
                        oVarData = self.oVarData[sVarKey]
                        # Define var attribute(s)
                        oVarAttrs = deepcopy(oVarConventions_Default[oVarType[0]])
                        oVarAttrs = updateDictStructure(oVarAttrs, oVarData['attributes'])
                        oVarAttrs = updateDictStructure(oVarAttrs, oVarDef['attributes'])
                        oVarAttrs = updateDictStructure(oVarAttrs, oVarCM)

                        # Get variable data
                        oVarResults = oVarData['results']
                        # Get variable format
                        if 'Format' in oVarData['attributes']:
                            sVarFormat = oVarData['attributes']['Format']
                        else:
                            sVarFormat = 'f4'

                        # Check and get library write method
                        if hasattr(oFileDriver.oFileLibrary, sVarMethod):
                            # Get write method
                            oVarMethod = getattr(oFileDriver.oFileLibrary, sVarMethod)

                            # Store variable (2d and 3d dimensions)
                            if oVarType[0] == 'var2d':
                                oVarMethod(oFileData, sVarName, oVarResults, oVarAttrs, sVarFormat,
                                           sVarDimY=sVarDimY, sVarDimX=sVarDimX)
                            elif oVarType[0] == 'var3d':
                                oVarMethod(oFileData, sVarName, oVarResults, oVarAttrs, sVarFormat,
                                           sVarDimT=sVarDimT, sVarDimY=sVarDimY, sVarDimX=sVarDimX)

                            # Info end saving variable
                            oLogStream.info(' -----> Save variable ' + sVarName + ' ... OK ')

                        else:
                            # Exit without saving variable
                            Exc.getExc(' ---> Save variable: ' +
                                       sVarKey + ' ... FAILED! Selected method is not available on io library', 2, 1)
                        # -------------------------------------------------------------------------------------
                    else:
                        # -------------------------------------------------------------------------------------
                        # Info skip saving variable
                        oLogStream.info(' -----> Save variable ' + sVarName +
                                        ' ... SKIPPED! Variable is already saved in selected file ')
                        # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Info start closing and zipping file
                    oLogStream.info(' ----> Close and zip file ' + sVarFileName + ' ... ')
                    # Close file
                    oFileDriver.oFileLibrary.closeFile(oFileData)
                    # Zip file
                    zipFileData(sFileUnzip, sZipExt_Default)
                    # Info end closing and zipping file
                    oLogStream.info(' ----> Close and zip file ' + sVarFileName + ' ... OK')

                    # Info end saving variable
                    oLogStream.info(' ---> Save workspace: ' + sVarKey + ' ... OK')
                    # -------------------------------------------------------------------------------------

                else:
                    # -------------------------------------------------------------------------------------
                    # Exit without saving variable
                    Exc.getExc(' ---> Save workspace: ' + sVarKey + ' ... FAILED! Variable file is not declared', 2, 1)
                    # -------------------------------------------------------------------------------------
            else:
                # -------------------------------------------------------------------------------------
                # Exit without saving variable
                Exc.getExc(' ---> Save workspace: ' + sVarKey + ' ... FAILED! Variable data are null! ', 2, 1)
                # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------

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
        self.oVarDef = kwargs['settings']['variables']['input']
        self.oVarFile = {'wrf_data': kwargs['wrf_data_file']}

        self.__defineVar()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define data variable
    def __defineVar(self):

        # -------------------------------------------------------------------------------------
        # Define variable(s) workspace by conventions and defined input field(s)
        for sVarKey, oVarValue in self.oVarDef.items():

            self.oVarData[sVarKey] = {}
            sVarID = oVarValue['id']['var_type'][0]

            if 'attributes' in oVarValue:
                oVarAttrs = oVarValue['attributes']
                for sAttrKey, oAttrValue in oVarAttrs.items():
                    if isinstance(oAttrValue, str):
                        if sAttrKey in oVarConventions_Default[sVarID].keys():
                            self.oVarData[sVarKey][sAttrKey] = {}
                            self.oVarData[sVarKey][sAttrKey] = deepcopy(oVarConventions_Default[sVarID][sAttrKey])
                    elif isinstance(oAttrValue, list):
                        if sAttrKey in oVarConventions_Default[sVarID].keys():
                            self.oVarData[sVarKey][sAttrKey] = {}
                            self.oVarData[sVarKey][sAttrKey] = deepcopy(oVarConventions_Default[sVarID][sAttrKey])

        # Update variable workspace
        for sVarKey, oVarValue in self.oVarDef.items():

            sVarID = oVarValue['id']['var_type'][0]

            for sAttrKey, oAttrValue in oVarConventions_Default[sVarID].items():
                self.oVarData[sVarKey][sAttrKey] = {}
                self.oVarData[sVarKey][sAttrKey] = oAttrValue

            if 'attributes' in oVarValue:
                oVarAttrs = oVarValue['attributes']
                for sAttrKey, oAttrValue in oVarAttrs.items():
                    self.oVarData[sVarKey][sAttrKey] = {}
                    self.oVarData[sVarKey][sAttrKey] = oAttrValue
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to get data
    def getDataProduct(self):

        # -------------------------------------------------------------------------------------
        # Iterate over file variable(s)
        oVarWS = {}
        oVarTime = self.oVarTime.time_range
        for sVarKey, oVarDef in self.oVarDef.items():

            # DEBUG START
            # sVarKey = 'rain_data'
            # oVarDef = self.oVarDef[sVarKey]
            # DEBUG END

            # -------------------------------------------------------------------------------------
            # Get input variable information
            oVarType = oVarDef['id']['var_type']
            oVarName = oVarDef['id']['var_name']
            sVarFile = oVarDef['id']['var_file']
            sVarMethodGet = oVarDef['id']['var_method_get']
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Check file tag in file definition(s)
            oVarGet = {}
            if sVarFile in self.oVarFile:

                # -------------------------------------------------------------------------------------
                # Iterate over time(s)
                for iVarTime, sVarTime in enumerate(oVarTime):

                    # -------------------------------------------------------------------------------------
                    # Define time tags
                    oTimeTags = {'$yyyy': sVarTime[0:4],
                                 '$mm': sVarTime[4:6], '$dd': sVarTime[6:8], '$HH': sVarTime[8:10],
                                 '$MM': sVarTime[10:12]}
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Get filename from file definition(s) using file tag in outcome variable(s)
                    sVarFileName = defineString(deepcopy(self.oVarFile[sVarFile]), oTimeTags)
                    # Info start about selected file
                    oLogStream.info(' ---> Get file: ' + sVarFileName + ' (Time: ' + sVarTime + ') ... ')
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Check file saved on disk
                    if exists(sVarFileName):

                        # -------------------------------------------------------------------------------------
                        # Get data
                        [oFileHandle, oFileDriver, bFileOpen] = handleFileData(sVarFileName)
                        oVarAttrs = self.oVarData[sVarKey]
                        # -------------------------------------------------------------------------------------

                        # -------------------------------------------------------------------------------------
                        # Check file opening
                        if bFileOpen is True:

                            # -------------------------------------------------------------------------------------
                            # Get file attribute(s)
                            oFileParameter = oFileDriver.oFileLibrary.getFileAttrs(oFileHandle)

                            # Iterate over data variable(s)
                            for sVarName in oVarName:

                                # -------------------------------------------------------------------------------------
                                # Info start about getting variable
                                oLogStream.info(' ---> Algorithm variable: ' +
                                                sVarKey + ' - Product variable: ' + sVarName + ' ...')

                                # Check variable data in workspace
                                if sVarName not in oVarWS:

                                    # -------------------------------------------------------------------------------------
                                    # Check variable data in file handle
                                    if oFileDriver.oFileLibrary.checkVarName(oFileHandle, sVarName):

                                        # -------------------------------------------------------------------------------------
                                        # Init variable workspace
                                        if sVarName not in oVarGet:
                                            oVarGet[sVarName] = {}
                                            oVarGet[sVarName]['values'] = None
                                            oVarGet[sVarName]['longitude'] = None
                                            oVarGet[sVarName]['latitude'] = None
                                            oVarGet[sVarName]['parameters'] = None
                                            oVarGet[sVarName]['attributes'] = None
                                            oVarGet[sVarName]['times'] = None
                                        # -------------------------------------------------------------------------------------

                                        # -------------------------------------------------------------------------------------
                                        # Get variable data
                                        a3dVarData_RAW = oFileDriver.oFileLibrary.get3DVar(oFileHandle, sVarName)
                                        # Get variable parameter(s)
                                        oVarParameter = oFileDriver.oFileLibrary.getVarAttrs(oFileHandle, sVarName)
                                        # Get variable time(s)
                                        oVarTimes = oFileDriver.oFileLibrary.getTime(oFileHandle, oVarKey_Valid['time'])
                                        # Get variable longitude
                                        a1dVarGeoX = oFileDriver.oFileLibrary.get1DVar(oFileHandle,
                                                                                       oVarKey_Valid['longitude'])
                                        # Get variable latitude
                                        a1dVarGeoY = oFileDriver.oFileLibrary.get1DVar(oFileHandle,
                                                                                       oVarKey_Valid['latitude'])

                                        # Remove missing and fill value(s)
                                        if 'missing_value' in oVarParameter:
                                            dVarMissValue = oVarParameter['missing_value']
                                            a3dVarData_RAW[where(a3dVarData_RAW == dVarMissValue)] = nan
                                        if '_FillValue' in oVarParameter:
                                            dVarFillValue = oVarParameter['_FillValue']
                                            a3dVarData_RAW[where(a3dVarData_RAW == dVarFillValue)] = nan
                                        # -------------------------------------------------------------------------------------

                                        # -------------------------------------------------------------------------------------
                                        # Save variable data
                                        if oVarGet[sVarName]['values'] is None:
                                            a3dVarData_INIT = empty([a3dVarData_RAW.shape[0], a3dVarData_RAW.shape[1],
                                                                     oVarTime.__len__()])
                                            a3dVarData_INIT[:, :, :] = nan
                                            oVarGet[sVarName]['values'] = deepcopy(a3dVarData_INIT)

                                        a3dVarData_DEF = oVarGet[sVarName]['values']
                                        a2dVarData_SQZ = squeezeDataArray(a3dVarData_RAW, 2)
                                        a3dVarData_DEF[:, :, iVarTime] = a2dVarData_SQZ
                                        oVarGet[sVarName]['values'] = a3dVarData_DEF
                                        # -------------------------------------------------------------------------------------

                                        # -------------------------------------------------------------------------------------
                                        # Save variable time step(s)
                                        if oVarGet[sVarName]['times'] is None:
                                            oVarGet[sVarName]['times'] = []
                                        oVarGet[sVarName]['times'].append(oVarTimes[0])
                                        # -------------------------------------------------------------------------------------

                                        # -------------------------------------------------------------------------------------
                                        # Save variable longitudes and latitudes
                                        if (oVarGet[sVarName]['longitude'] is None) \
                                                and (oVarGet[sVarName]['latitude'] is None):
                                            [a2dVarGeoX, a2dVarGeoY] = createMeshGrid(a1dVarGeoX, a1dVarGeoY)
                                            oVarGet[sVarName]['longitude'] = a2dVarGeoX
                                            oVarGet[sVarName]['latitude'] = a2dVarGeoY
                                        # -------------------------------------------------------------------------------------

                                        # -------------------------------------------------------------------------------------
                                        # Update variable parameter(s)
                                        if oVarGet[sVarName]['parameters'] is None:
                                            oVarGet[sVarName]['parameters'] = mergeDict(oFileParameter, oVarParameter)

                                        # Update variable attribute(s)
                                        if oVarGet[sVarName]['attributes'] is None:
                                            oVarGet[sVarName]['attributes'] = oVarAttrs
                                        # -------------------------------------------------------------------------------------

                                        # -------------------------------------------------------------------------------------
                                        # Info end about getting data variable
                                        oLogStream.info(' ---> Algorithm variable: ' +
                                                        sVarKey + ' - Product variable: ' + sVarName + ' ... OK')
                                        # -------------------------------------------------------------------------------------
                                    else:
                                        # -------------------------------------------------------------------------------------
                                        # Info end about getting data variable
                                        oVarGet[sVarName] = None
                                        Exc.getExc(' ---> Algorithm variable: ' +
                                                   sVarKey + ' - Product variable: ' + sVarName +
                                                   ' ... FAILED! Variable is not available in selected file!', 2, 1)
                                        # -------------------------------------------------------------------------------------

                                else:
                                    # -------------------------------------------------------------------------------------
                                    # Info end about getting data variable
                                    oLogStream.info(' ---> Algorithm variable: ' +
                                                    sVarKey + ' - Product variable: ' + sVarName +
                                                    ' ... SKIPPED! Variable already set in workspace!')
                                    # -------------------------------------------------------------------------------------

                                    # -------------------------------------------------------------------------------------
                                    # Debug
                                    # plt.figure()
                                    # plt.imshow(a3dVarData_RAW[:, :, 0]); plt.colorbar()
                                    # plt.figure()
                                    # plt.imshow(a2dVarData_SQZ); plt.colorbar()
                                    # plt.figure()
                                    # plt.imshow(a3dVarData_DEF[:, :, iVarTime]); plt.colorbar()
                                    # plt.show()
                                    # -------------------------------------------------------------------------------------

                            # -------------------------------------------------------------------------------------
                            # Close file handle
                            oFileDriver.oFileLibrary.closeFile(oFileHandle)
                            oLogStream.info(' ---> Get file: ' + sVarFileName + ' (Time: ' + sVarTime + ') ... OK')
                            # -------------------------------------------------------------------------------------
                        else:
                            # -------------------------------------------------------------------------------------
                            # Exit file not in workspace
                            Exc.getExc(' ---> Get file: ' + sVarFileName + ' (Time: ' + sVarTime +
                                       ') ... FAILED! File not correctly open!', 2, 1)
                            # -------------------------------------------------------------------------------------
                    else:
                        # -------------------------------------------------------------------------------------
                        # Exit file not in workspace
                        Exc.getExc(' ---> Get file: ' + sVarFileName + ' (Time: ' + sVarTime +
                                   ') ... FAILED! File is not in declared workspace!', 2, 1)
                        # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Save variable workspace
                oVarWS.update(oVarGet)
                # -------------------------------------------------------------------------------------
            else:
                # -------------------------------------------------------------------------------------
                # Exit file not in workspace
                Exc.getExc(' ---> Reference file is wrongly defined! Check settings file!', 2, 1)
                # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Return workspace
        return oVarWS
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
