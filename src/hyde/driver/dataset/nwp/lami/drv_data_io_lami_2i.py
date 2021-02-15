"""
Library Features:

Name:          drv_data_io_lami_2i
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20181203'
Version:       '1.0.0'
"""
#################################################################################
# Library
import logging
import progressbar
import datetime

from os import remove, chdir
from os.path import exists, isfile, split, realpath
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

from src.hyde.driver.dataset.nwp.lami.cpl_data_variables_lami_2i import DataVariables

from src.common.driver.configuration.drv_configuration_debug import Exc

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
            sVarTimeObs = sVarTime
        else:
            iVarTimeObsStep = 0
            iVarTimeObsDelta = 0
            sVarTimeObs = None

        if 'time_forecast_step' in oVarTime and 'time_forecast_delta' in oVarTime:
            iVarTimeForStep = oVarTime['time_forecast_step']
            iVarTimeForDelta = oVarTime['time_forecast_delta']

            oVarTimeFor = datetime.datetime.strptime(sVarTime, sTimeFormat_Default)
            oVarTimeFor = oVarTimeFor + datetime.timedelta(seconds=iVarTimeForDelta)
            sVarTimeFor = oVarTimeFor.strftime(sTimeFormat_Default)

        else:
            iVarTimeForStep = 0
            iVarTimeForDelta = 0
            sVarTimeFor = None

        sVarTimeFrom = getTimeFrom(sVarTime, iVarTimeObsDelta, iVarTimeObsStep)[0]
        sVarTimeTo = getTimeTo(sVarTime, iVarTimeForDelta, iVarTimeForStep)[0]

        if iVarTimeObsStep > 0:
            a1oVarTimeObs = getTimeSteps(sVarTimeFrom, sVarTimeObs, iVarTimeObsDelta)
        else:
            a1oVarTimeObs = []
        if iVarTimeForStep > 0:
            a1oVarTimeFor = getTimeSteps(sVarTimeFor, sVarTimeTo, iVarTimeForDelta)
        else:
            a1oVarTimeFor = []

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
# Class to analyze data product
class DataProductAnalyzer:

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, **kwargs):
        self.sVarTime = kwargs['time']
        self.oVarDef = kwargs['settings']['variables']['source']
        self.oVarData = kwargs['data']
        self.oVarFile = {'grid_ref': kwargs['grid_ref_file']}
        self.oVarFctSteps = kwargs['forecast_expected_step']
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute data
    def computeDataProduct(self, oDataGeo=None):

        # -------------------------------------------------------------------------------------
        # Iterate over file variable(s)
        oVarWS = self.oVarData
        oVarSel = DataObj()
        for sVarKey, oVarDef in self.oVarDef.items():

            # -------------------------------------------------------------------------------------
            # DEBUG
            # sVarKey = 'air_temperature_data' # OK
            # sVarKey = 'wind_data' # OK
            # sVarKey = 'rain_data'
            # sVarKey = 'incoming_radiation_data' # OK
            # sVarKey = 'relative_humidity_data'
            # sVarKey = 'albedo_data'
            # oVarDef = self.oVarDef[sVarKey]
            # -------------------------------------------------------------------------------------

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

                    a3dVarValue_CMP, oVarTimes_CMP, oVarAttrs_CMP = oDrv_Data_Cmp.computeVarData(
                        type=oVarType[1])
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
                                dVarMissValue = oVarAttrs['Missing_value']
                            else:
                                dVarMissValue = -9999.0
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
                            # Initialize variable to store results
                            a3dVarValue_FILTER = zeros([oDataGeo.a2dGeoX.shape[0], oDataGeo.a2dGeoY.shape[1],
                                                        self.oVarFctSteps.__len__()])
                            a3dVarValue_FILTER[:, :, :] = dVarMissValue

                            # Info start interpolating variable
                            oLogStream.info(' ----> Interpolate and filter variable over domain ... ')

                            # Iterate over time step(s)
                            oPBar = progressbar.ProgressBar()
                            for iTimeStep, sTimeStep in enumerate(oPBar(oVarTime)):

                                # -------------------------------------------------------------------------------------
                                # Define idx between expected time steps and data time steps
                                iTimeStep_Exp = self.oVarFctSteps.index(sTimeStep)
                                # -------------------------------------------------------------------------------------

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
                                # plt.imshow(a3dVarValue[:, :, iTimeStep]); plt.colorbar(); plt.clim(0, 200)
                                # plt.figure()
                                # plt.imshow(a2dVarValue_INTERP); plt.colorbar(); plt.clim(0, 200)
                                # plt.figure()
                                # plt.imshow(a2dVarValue_FILTER); plt.colorbar(); plt.clim(0, 200)
                                # plt.show()
                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Store results
                                a3dVarValue_FILTER[:, :, iTimeStep_Exp] = a2dVarValue_FILTER
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
        self.oVarFile = {'nwp_product': kwargs['nwp_product_file']}
        self.oVarColorMap = kwargs['nwp_colormap_file']
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
                        oFileDriver.oFileLibrary.writeDims(oFileData, 'west_east', self.oVarData.iCols)
                        oFileDriver.oFileLibrary.writeDims(oFileData, 'south_north', self.oVarData.iRows)
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
                                                            sVarDimY=oFileDims['south_north']['name'],
                                                            sVarDimX=oFileDims['west_east']['name'])
                        # Write latitude information
                        sVarNameY = 'latitude'
                        a2VarDataY = oDataGeo.a2dGeoY
                        oVarAttrsY = oVarConventions_Default[sVarNameY]
                        sVarFormatY = oVarConventions_Default[sVarNameY]['Format']
                        oFileDriver.oFileLibrary.write2DVar(oFileData, sVarNameY,
                                                            a2VarDataY, oVarAttrsY, sVarFormatY,
                                                            sVarDimY=oFileDims['south_north']['name'],
                                                            sVarDimX=oFileDims['west_east']['name'])

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
                        sVarDimX = oFileDims['west_east']['name']
                        sVarDimY = oFileDims['south_north']['name']
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
        self.oVarDef = kwargs['settings']['variables']['source']
        self.oVarFile = {'rain_data': kwargs['rain_file'],
                         'air_temperature_data': kwargs['air_temperature_file'],
                         'incoming_radiation_data': kwargs['incoming_radiation_file'],
                         'wind_data': kwargs['wind_file'],
                         'relative_humidity_data': kwargs['relative_humidity_file'],
                         'albedo_data': kwargs['albedo_file'],
                         }

        self.oVarFctSteps = kwargs['forecast_expected_step']

        self.tmp_folder, self.tmp_filename = split(kwargs['tmp_data'])
        if self.tmp_folder.__len__() == 0:
            self.tmp_folder = None
        if self.tmp_filename.__len__() == 0:
            self.tmp_filename = None

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
        for sVarKey, oVarDef in self.oVarDef.items():

            # -------------------------------------------------------------------------------------
            # DEBUG
            # sVarKey = 'air_temperature_data'
            # sVarKey = 'wind_data'
            # sVarKey = 'rain_data'
            # sVarKey = 'incoming_radiation_data'
            # sVarKey = 'relative_humidity_data'
            # oVarDef = self.oVarDef[sVarKey]
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Get input variable information
            oVarType = oVarDef['id']['var_type']
            oVarName = oVarDef['id']['var_name']
            oVarSource = oVarDef['id']['var_file']
            sVarMethodGet = oVarDef['id']['var_method_get']
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Iterate over dataset(s)
            for sVarFile in oVarSource:

                # -------------------------------------------------------------------------------------
                # Check file tag in file definition(s)
                if sVarFile in self.oVarFile:

                    # -------------------------------------------------------------------------------------
                    # Get time information
                    sVarTime = self.oVarTime

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
                        # Iterate over variable component(s)
                        oVarGet = {}
                        for iIdx, sVarComp in enumerate(oVarName):

                            # -------------------------------------------------------------------------------------
                            # Get data
                            [oFileHandle, oFileDriver, bFileOpen] = handleFileData(
                                sVarFileName, file_type='grib', path_tmp=self.tmp_folder, file_tmp=False)
                            oVarAttrs = self.oVarData[sVarKey]

                            # Check variable name in file handle
                            bFileVar = oFileDriver.oFileLibrary.checkVarName(oFileHandle, sVarComp,
                                                                             iVarMsg=oVarName.__len__())
                            # -------------------------------------------------------------------------------------

                            # -------------------------------------------------------------------------------------
                            # Check file opening
                            if (bFileOpen is True) and (bFileVar is True):

                                # -------------------------------------------------------------------------------------
                                # Info end about getting data variable
                                oLogStream.info(' ----> Algorithm variable: ' +
                                                sVarKey + ' - Product variable: ' + sVarComp + ' ... ')
                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Get geographical references
                                a2dVarGeoX, a2dVarGeoY = oFileDriver.oFileLibrary.getVarGeo_LAMI_2i(oFileHandle)

                                # Get file attributes
                                oVarParams = oFileDriver.oFileLibrary.getVarAttr_LAMI_2i(
                                    oFileHandle, sVarComp, ['distinctLatitudes', 'distinctLongitudes',
                                                            'values', 'latLonValues',
                                                            'latitudes', 'longitudes'])[sVarComp]
                                # Get time steps
                                oVarTime = oFileDriver.oFileLibrary.getVarTime_LAMI_2i(oFileHandle, sVarComp)[sVarComp]

                                # Get data values
                                a3dVarData = oFileDriver.oFileLibrary.getVar3D_LAMI_2i(oFileHandle, sVarComp)[sVarComp]

                                # Check data time steps
                                iVarT = a3dVarData.shape[2] - 1
                                try:
                                    assert self.oVarFctSteps.__len__() == iVarT
                                except BaseException:
                                    Exc.getExc(' -----> Excepted forecast time steps [' + str(self.oVarFctSteps.__len__())
                                               + '] are not equal to data time steps [' + str(iVarT) + ']',
                                               2, 1)
                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Init variable workspace
                                oVarGet[sVarComp] = {}
                                oVarGet[sVarComp]['values'] = {}
                                oVarGet[sVarComp]['parameters'] = {}
                                oVarGet[sVarComp]['attributes'] = {}
                                oVarGet[sVarComp]['longitude'] = None
                                oVarGet[sVarComp]['latitude'] = None
                                oVarGet[sVarComp]['times'] = None
                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Save variable values
                                oVarGet[sVarComp]['values'] = a3dVarData

                                # Save variable parameter(s)
                                oVarGet[sVarComp]['parameters'] = oVarParams

                                # Save variable attribute(s)
                                oVarGet[sVarComp]['attributes'] = oVarAttrs

                                # Save variable time step(s)
                                oVarGet[sVarComp]['times'] = oVarTime

                                # Save variable longitudes and latitudes
                                oVarGet[sVarComp]['longitude'] = a2dVarGeoX
                                oVarGet[sVarComp]['latitude'] = a2dVarGeoY
                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Save variable workspace
                                oVarWS.update(oVarGet)

                                # Info end about getting data variable
                                oLogStream.info(' ----> Algorithm variable: ' +
                                                sVarKey + ' - Product variable: ' + sVarComp + ' ... OK')

                                # Info end about selected file
                                oLogStream.info(' ---> Get file: ' + sVarFileName + ' (Time: ' + sVarTime + ') ... OK')
                                # -------------------------------------------------------------------------------------

                            else:

                                # -------------------------------------------------------------------------------------
                                # Check exit condition
                                if bFileVar is False:
                                    # Exit file not in workspace
                                    Exc.getExc(' ---> Get file: ' + sVarFileName + ' (Time: ' + sVarTime +
                                               ') ... FAILED! Variable ' + sVarComp + ' not available in file !', 2, 1)
                                else:
                                    # Exit file not in workspace
                                    Exc.getExc(' ---> Get file: ' + sVarFileName + ' (Time: ' + sVarTime +
                                               ') ... FAILED! File not correctly open!', 2, 1)
                                # -------------------------------------------------------------------------------------
                    else:
                        # -------------------------------------------------------------------------------------
                        # Exit file not in workspace
                        Exc.getExc(' ---> Get file: ' + sVarFileName + ' (Time: ' + sVarTime +
                                   ') ... FAILED! File not found!', 2, 1)
                        # -------------------------------------------------------------------------------------

                else:
                    # -------------------------------------------------------------------------------------
                    # Exit file not in workspace
                    Exc.getExc(' ---> Reference file is wrongly defined! Check settings file!', 2, 1)
                    # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Return workspace
        return oVarWS
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
