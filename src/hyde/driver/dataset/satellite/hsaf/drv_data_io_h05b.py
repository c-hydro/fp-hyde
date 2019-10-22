"""
Library Features:

Name:          drv_data_io_h05b
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190401'
Version:       '1.0.2'
"""
#################################################################################
# Library
import logging
import progressbar

from sys import version_info

from datetime import timedelta
from datetime import datetime
from os import remove
from os.path import exists, isfile
from copy import deepcopy
from numpy import reshape, full, empty, nan, zeros, isnan, asarray, delete, where, unique, concatenate
import numpy.ma as ma

from src.common.analysis.lib_analysis_interpolation_point import interpPointData

from src.common.utils.lib_utils_op_string import defineString, convertUnicode2ASCII
from src.common.utils.lib_utils_op_list import mergeList
from src.common.utils.lib_utils_apps_data import updateDictStructure
from src.common.utils.lib_utils_apps_file import handleFileData, selectFileDriver, zipFileData
from src.common.utils.lib_utils_apps_time import getTimeFrom, getTimeTo, getTimeSteps, checkTimeRef, roundTimeStep, \
    findTimeDiff, findTimeClosest

from src.common.default.lib_default_args import sZipExt as sZipExt_Default
from src.common.default.lib_default_args import sTimeFormat as sTimeFormat_Default
from src.common.default.lib_default_args import sTimeCalendar as sTimeCalendar_Default
from src.common.default.lib_default_args import sTimeUnits as sTimeUnits_Default
from src.common.default.lib_default_conventions import oVarConventions as oVarConventions_Default
from src.common.default.lib_default_conventions import oFileConventions as oFileConventions_Default

from src.common.default.lib_default_args import sLoggerName

from src.hyde.driver.configuration.generic.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
import matplotlib.pylab as plt
#################################################################################


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
        self.sVarTimeStep = kwargs['timestep']
        self.sVarTimeRun = kwargs['timerun']
        self.oVarTime = kwargs['settings']['data']['dynamic']['time']
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to round time to closest time to closest defined time interval
    def __roundTimeStep(self, sTimeStep):

        oVarTime = self.oVarTime

        if 'time_reference_type' in oVarTime:

            sTimeUnits = oVarTime['time_reference_type']['units']
            iTimeRound = oVarTime['time_reference_type']['rounding']
            oTimeSteps = oVarTime['time_reference_type']['steps']

            bTimeHH = checkTimeRef(sTimeStep, oTimeHours=oTimeSteps)
            if bTimeHH is False:

                sTimeRound = roundTimeStep(sTimeStep,
                                           sDeltaUnits=sTimeUnits, iDeltaValue=iTimeRound)

                sTimeRound = findTimeClosest(sTimeRound, oTime_HH=oTimeSteps)

                return sTimeRound
            else:
                return sTimeStep
        else:
            return sTimeStep

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute reference time (to control files mount and avoid memory fails)
    def __selectRefTime(self, sVarTimeStep, sVarTimeRun):

        oVarTimeStep = datetime.strptime(sVarTimeStep, sTimeFormat_Default)
        oVarTimeRun = datetime.strptime(sVarTimeRun, sTimeFormat_Default)

        oVarTimeDelta = timedelta(seconds=self.oVarTime['time_observed_step'] * self.oVarTime['time_observed_delta'])
        oVarTimeCheck = oVarTimeStep + oVarTimeDelta

        if oVarTimeCheck > oVarTimeRun:
            sVarTimeRef = oVarTimeRun.strftime(sTimeFormat_Default)
        elif oVarTimeCheck < oVarTimeRun:
            sVarTimeRef = oVarTimeStep.strftime(sTimeFormat_Default)
        else:
            sVarTimeRef = oVarTimeRun.strftime(sTimeFormat_Default)

        iVarTimeDiff = findTimeDiff(sVarTimeRef, sVarTimeStep)

        return sVarTimeRef, iVarTimeDiff
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute data time
    def computeDataTime(self):

        sVarTimeStep = self.sVarTimeStep
        sVarTimeRun = self.sVarTimeRun
        oVarTime = self.oVarTime

        sVarTimeRun = self.__roundTimeStep(sVarTimeRun)

        sVarTimeRef, iVarTimeDiff = self.__selectRefTime(sVarTimeStep, sVarTimeRun)

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

        iVarTimeRefStep = int(iVarTimeDiff / iVarTimeObsDelta)
        iVarTimeObsStep = iVarTimeObsStep + iVarTimeRefStep

        sVarTimeFrom = getTimeFrom(sVarTimeRef, iVarTimeObsDelta, iVarTimeObsStep)[0]
        sVarTimeTo = getTimeTo(sVarTimeRef, iVarTimeForDelta, iVarTimeForStep)[0]

        a1oVarTimeObs = getTimeSteps(sVarTimeFrom, sVarTimeRef, iVarTimeObsDelta)
        a1oVarTimeFor = getTimeSteps(sVarTimeRef, sVarTimeTo, iVarTimeForDelta)

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

        try:
            self.a1oTime = kwargs['time']
        except BaseException:
            self.a1oTime = None
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

            if version_info < (3, 0):
                oFile = convertUnicode2ASCII(oFile)
            if isinstance(oFile, str):
                oFile = [oFile]

            if self.a1oTime is None:
                for sFile in oFile:
                    if exists(sFile):
                        if bFlag:
                            remove(sFile)
            else:

                if isinstance(self.a1oTime, str):
                    self.a1oTime = [self.a1oTime]

                for sTime in self.a1oTime:
                    oTimeTags = {'$yyyy': sTime[0:4],
                                 '$mm': sTime[4:6], '$dd': sTime[6:8], '$HH': sTime[8:10],
                                 '$MM': sTime[10:12]}
                    for sFile in oFile:
                        sFile = defineString(deepcopy(deepcopy(sFile)), oTimeTags)
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
        self.oVarIn = kwargs['settings']['variables']['input']
        self.oVarOut = kwargs['settings']['variables']['outcome']
        self.oVarData = kwargs['data']
        self.sVarFolderTMP = kwargs['temp_data_file']
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute data
    def computeDataProduct(self, oDataGeo=None):

        # -------------------------------------------------------------------------------------
        # Iterate over file variable(s)
        oVarWS = self.oVarData
        oVarIn = self.oVarIn
        oVarOut = self.oVarOut
        sVarFolderTMP = self.sVarFolderTMP
        oVarSel = DataObj()
        for (sVarKey_IN, oVarDef_IN), (sVarKey_OUT, oVarDef_OUT) in zip(oVarIn.items(), oVarOut.items()):

            # -------------------------------------------------------------------------------------
            # Get input variable information
            oVarType_IN = oVarDef_IN['id']['var_type']
            oVarName_IN = oVarDef_IN['id']['var_name']
            oVarFile_IN = oVarDef_IN['id']['var_file']
            oVarMethod_IN = oVarDef_IN['id']['var_method_compute']
            oVarAttrs_IN = oVarDef_IN['attributes']

            oVarType_OUT = oVarDef_OUT['id']['var_type']
            oVarName_OUT = oVarDef_OUT['id']['var_name']
            oVarFile_OUT = oVarDef_OUT['id']['var_file']
            oVarMethod_OUT = oVarDef_OUT['id']['var_method_save']
            oVarAttrs_OUT = oVarDef_OUT['attributes']

            assert sVarKey_IN == sVarKey_OUT
            sVarKey = list(set([sVarKey_IN, sVarKey_OUT]))[0]

            # Info start about computing variable
            oLogStream.info(' ---> Compute algorithm variable: ' + sVarKey + ' ... ')
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Check variable workspace
            if oVarWS:

                # -------------------------------------------------------------------------------------
                # Check data field(s) availability to compute results
                if sVarKey in oVarWS:

                    # -------------------------------------------------------------------------------------
                    # Iterate over declared variable(s)
                    oVarSel[sVarKey] = {}
                    for iVarID, (sVarType_IN, sVarName_IN, sVarFile_IN, sVarMethod_IN,
                                 sVarType_OUT, sVarName_OUT, sVarFile_OUT, sVarMethod_OUT) in enumerate(zip(
                            oVarType_IN, oVarName_IN, oVarFile_IN, oVarMethod_IN,
                            oVarType_OUT, oVarName_OUT, oVarFile_OUT, oVarMethod_OUT)):

                        # -------------------------------------------------------------------------------------
                        # Info variable starting
                        oLogStream.info(' ----> Select product variable ' +
                                        sVarName_IN + ' to ' + sVarName_OUT + ' ... ')

                        # Check variable field availability to compute results
                        if sVarName_IN in oVarWS[sVarKey]:

                            # -------------------------------------------------------------------------------------
                            # Get data
                            oVarData = oVarWS[sVarKey][sVarName_IN]
                            # -------------------------------------------------------------------------------------

                            # -------------------------------------------------------------------------------------
                            # Check fields definition in variable workspace
                            if ('values' in oVarData) and ('attributes' in oVarData) and (
                                    'times' in oVarData):

                                # -------------------------------------------------------------------------------------
                                # Get data and attributes
                                a2dVarValue = deepcopy(oVarData['values']).astype(float)
                                a2dVarGeoX = deepcopy(oVarData['longitude']).astype(float)
                                a2dVarGeoY = deepcopy(oVarData['latitude']).astype(float)
                                oVarTime = deepcopy(oVarData['times'])
                                oVarAttrs_IN_SEL = deepcopy(oVarData['attributes'])

                                # Get attributes using outcome definition(s)
                                oVarAttrs_OUT_SEL = selectVarAttributes(oVarAttrs_OUT, iVarID)

                                # Get missing value
                                if 'Missing_value' in oVarAttrs_OUT_SEL:
                                    dVarMissValue = oVarAttrs_OUT_SEL['Missing_value']
                                else:
                                    dVarMissValue = -9999.0
                                # Get scale factor
                                if 'ScaleFactor' in oVarAttrs_OUT_SEL:
                                    dScaleFactor = oVarAttrs_OUT_SEL['ScaleFactor']
                                else:
                                    dScaleFactor = 1
                                # Get fill value
                                if '_FillValue' in oVarAttrs_OUT_SEL:
                                    dVarFillValue = oVarAttrs_OUT_SEL['_FillValue']
                                else:
                                    dVarFillValue = -9999.0
                                # Get units
                                if 'units' in oVarAttrs_OUT_SEL:
                                    sVarUnits = oVarAttrs_OUT_SEL['units']
                                else:
                                    sVarUnits = None
                                # Get valid range
                                if 'Valid_range' in oVarAttrs_OUT_SEL:
                                    oVarValidRange = asarray(oVarAttrs_OUT_SEL['Valid_range'])
                                else:
                                    oVarValidRange = None
                                # Get interpolation radius x
                                if 'interp_radius_x' in oVarAttrs_OUT_SEL:
                                    dVarRadiusX = float(oVarAttrs_OUT_SEL['interp_radius_x'])
                                else:
                                    Exc.getExc(' ---> Interpolation radius x not defined! Default value is 0.066', 2, 1)
                                    dVarRadiusX = 0.066
                                # Get interpolation radius y
                                if 'interp_radius_y' in oVarAttrs_OUT_SEL:
                                    dVarRadiusY = asarray(oVarAttrs_OUT_SEL['interp_radius_y'])
                                else:
                                    Exc.getExc(' ---> Interpolation radius y not defined! Default value is 0.066', 2, 1)
                                    dVarRadiusY = 0.066
                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Check data attributes to control units conversion
                                if 'units' in oVarAttrs_IN_SEL:
                                    assert oVarAttrs_IN_SEL['units'] == 'kg.m-2' or oVarAttrs_IN_SEL['units'] == '%'
                                    assert oVarAttrs_IN_SEL['ScaleFactor'] == 1
                                else:
                                    Exc.getExc(' ---> Variable units are not defined! Mismatching in outcome data!', 2, 1)
                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Initialize variable to store results
                                a3dVarValue_FILTER = zeros(
                                    [oDataGeo.a2dGeoX.shape[0], oDataGeo.a2dGeoY.shape[1], oVarTime.__len__()])
                                a3dVarValue_FILTER[:, :, :] = nan

                                # Info start interpolating variable
                                oLogStream.info(' ----> Interpolate product variable ' +
                                                sVarName_IN + ' to ' + sVarName_OUT + ' ... ')

                                # Iterate over time step(s)
                                oPBar = progressbar.ProgressBar(redirect_stdout=True)
                                for iTimeStep, sTimeStep in enumerate(oPBar(oVarTime)):

                                    # -------------------------------------------------------------------------------------
                                    # Get data
                                    a1dVarValue = a2dVarValue[:, iTimeStep]
                                    a1dVarGeoX = a2dVarGeoX[:, iTimeStep]
                                    a1dVarGeoY = a2dVarGeoY[:, iTimeStep]

                                    # Select defined value(s)
                                    a1iVarIdx = where(isnan(a1dVarValue))[0]
                                    a1dVarValue_SEL = delete(a1dVarValue, a1iVarIdx)
                                    a1dVarGeoY_SEL = delete(a1dVarGeoY, a1iVarIdx)
                                    a1dVarGeoX_SEL = delete(a1dVarGeoX, a1iVarIdx)
                                    # -------------------------------------------------------------------------------------

                                    # -------------------------------------------------------------------------------------
                                    # Set nan for missing and outbounds values
                                    a1dVarValue_SEL[a1dVarValue_SEL == dVarMissValue] = nan
                                    if oVarValidRange[0] is not None:
                                        a1dVarValue_SEL[a1dVarValue_SEL < oVarValidRange[0]] = nan
                                    if oVarValidRange[1] is not None:
                                        a1dVarValue_SEL[a1dVarValue_SEL > oVarValidRange[1]] = nan
                                    # -------------------------------------------------------------------------------------

                                    # -------------------------------------------------------------------------------------
                                    # Interpolate variable over grid reference using nearest method (gdal library)
                                    a2dVarValue_INTERP = interpPointData(
                                        a1dVarValue_SEL, a1dVarGeoX_SEL, a1dVarGeoY_SEL,
                                        oDataGeo.a2dGeoX, oDataGeo.a2dGeoY,
                                        iCodeEPSG=4326, dInterpNoData=-9999.0,
                                        dInterpRadiusX=dVarRadiusX, dInterpRadiusY=dVarRadiusY,
                                        sInterpMethod='nearest', sInterpOption=None,
                                        sFolderTemp=sVarFolderTMP)

                                    # Apply scale factor (from kg m^-2 to mm (kg/m^2 == mm)
                                    a2dVarValue_INTERP = a2dVarValue_INTERP * dScaleFactor

                                    # Set fill value for undefined data (nan)
                                    a1dVarValue_INTERP = deepcopy(a2dVarValue_INTERP.ravel())
                                    a1dVarValue_INTERP[oDataGeo.a1iGeoIndexNaN] = dVarFillValue
                                    a1dVarValue_INTERP[isnan(a1dVarValue_INTERP)] = dVarFillValue

                                    # Check data valid range
                                    if oVarValidRange[0] is not None:
                                        a1iVarNoData_INTERP = where(a1dVarValue_INTERP < oVarValidRange[0])[0]
                                        a1dVarValue_INTERP[a1iVarNoData_INTERP] = dVarMissValue
                                    if oVarValidRange[1] is not None:
                                        a1iVarNoData_INTERP = where(a1dVarValue_INTERP > oVarValidRange[1])[0]
                                        a1dVarValue_INTERP[a1iVarNoData_INTERP] = dVarMissValue

                                    # Reshape data with selected domain
                                    a2dVarValue_DEF = reshape(a1dVarValue_INTERP,
                                                              [oDataGeo.a2dGeoX.shape[0], oDataGeo.a2dGeoY.shape[1]])
                                    # -------------------------------------------------------------------------------------

                                    # -------------------------------------------------------------------------------------
                                    # Debug
                                    # import numpy as np
                                    # from mpl_toolkits.basemap import Basemap
                                    # plt.figure(figsize=(8, 8))
                                    # m = Basemap(llcrnrlat=np.min(oDataGeo.a2dGeoY), urcrnrlat=np.max(oDataGeo.a2dGeoY),
                                    #            llcrnrlon=np.min(oDataGeo.a2dGeoX), urcrnrlon=np.max(oDataGeo.a2dGeoX),
                                    #            resolution='l')
                                    # m.drawcoastlines(color='gray')
                                    # m.drawcountries(color='gray')
                                    # plt.pcolormesh(oDataGeo.a2dGeoX, oDataGeo.a2dGeoY, a2dVarValue_DEF)
                                    # plt.colorbar()
                                    # plt.clim(0, 50)
                                    # plt.show()
                                    # -------------------------------------------------------------------------------------

                                    # -------------------------------------------------------------------------------------
                                    # Store results
                                    a3dVarValue_FILTER[:, :, iTimeStep] = a2dVarValue_DEF
                                    # -------------------------------------------------------------------------------------

                                # Info end interpolating variable
                                oLogStream.info(' ----> Interpolate product variable ' +
                                                sVarName_IN + ' to ' + sVarName_OUT + ' ... OK')
                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Add attributes to workspace
                                if not hasattr(oVarSel, 'iRows'):
                                    oVarSel.iRows = a3dVarValue_FILTER.shape[0]
                                if not hasattr(oVarSel, 'iCols'):
                                    oVarSel.iCols = a3dVarValue_FILTER.shape[1]
                                if not hasattr(oVarSel, 'iTime'):
                                    oVarSel.iTime = a3dVarValue_FILTER.shape[2]
                                if not hasattr(oVarSel, 'oDataTime'):
                                    oVarSel.oDataTime = oVarTime

                                if 'longitude' not in oVarSel:
                                    oVarSel['longitude'] = a1dVarGeoX
                                if 'latitude' not in oVarSel:
                                    oVarSel['latitude'] = a1dVarGeoY

                                # Save data
                                oVarSel[sVarKey][sVarName_OUT] = {}
                                oVarSel[sVarKey][sVarName_OUT]['results'] = a3dVarValue_FILTER
                                oVarSel[sVarKey][sVarName_OUT]['attributes'] = oVarAttrs_OUT_SEL
                                oVarSel[sVarKey][sVarName_OUT]['times'] = oVarTime

                                # Info variable ending
                                oLogStream.info(' ----> Select product variable ' +
                                                sVarName_IN + ' to ' + sVarName_OUT + ' ... OK')
                                # -------------------------------------------------------------------------------------
                        else:

                            # -------------------------------------------------------------------------------------
                            # Exit variable key not in workspace
                            oLogStream.info(' ----> Select product variable ' +
                                            sVarName_IN + ' to ' + sVarName_OUT + ' ... FAILED')
                            Exc.getExc(' =====> WARNING: variable field is not defined!', 2, 1)
                            oVarSel[sVarKey][sVarName_OUT] = None
                            # -------------------------------------------------------------------------------------

                        # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Info end computing variable
                    oLogStream.info(' ---> Compute algorithm variable: ' + sVarKey + ' ... OK')
                    # -------------------------------------------------------------------------------------

                else:

                    # -------------------------------------------------------------------------------------
                    # Exit variable key not in workspace
                    oLogStream.info(' ---> Compute algorithm variable: ' + sVarKey + ' ... FAILED!')
                    Exc.getExc(' =====> WARNING: data field is not defined!', 2, 1)
                    oVarSel[sVarKey] = None
                    # -------------------------------------------------------------------------------------

            else:

                # -------------------------------------------------------------------------------------
                # Exit variable key not in workspace
                oLogStream.info(' ---> Compute algorithm variable: ' + sVarKey + ' ... FAILED!')
                Exc.getExc(' =====> WARNING: data workspace is null!', 2, 1)
                oVarSel = None
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
        self.oVarOut = kwargs['settings']['variables']['outcome']
        self.oVarData = kwargs['data']
        self.oVarFramework = {'rain_product': kwargs['rain_product_file']}
        self.oVarColorMap = kwargs['rain_colormap_file']
        self.oAlgConventions = kwargs['settings']['algorithm']

        self.bVarSubSet = True

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to subset data
    @staticmethod
    def subsetData(oData_Dynamic, iData_Index=None):

        # Check data workspace
        if oData_Dynamic is not None:

            # Define time index
            if iData_Index is None:
                iData_Index = 0
            else:
                iData_Index = iData_Index + 1
            iData_Dynamic_Index = oData_Dynamic.iTime - 1

            # Check time step availability in data
            if iData_Dynamic_Index >= iData_Index:

                # Get data
                oData_Dynamic_Step = deepcopy(oData_Dynamic)
                # Get time(s)
                sData_Time = oData_Dynamic.oDataTime[iData_Index]
                # Get key(s) and removing static variable(s) [longitude, latitude ... ]
                oData_Key = list(oData_Dynamic.keys())
                oData_Key.remove('longitude')
                oData_Key.remove('latitude')

                # Remove attribute(s)
                delattr(oData_Dynamic_Step, 'iTime')
                delattr(oData_Dynamic_Step, 'oDataTime')

                # Iterate over data key(s)
                for sData_Key in oData_Key:

                    # Info variable
                    oLogStream.info(' ----> SubsetVar: ' + sData_Key)

                    # Get data
                    oData_WS = oData_Dynamic[sData_Key]

                    # Check workspace data availability
                    if oData_WS:

                        # Iterate over variable(s)
                        for sData_Var, oData_Value in oData_WS.items():

                            # Check variable data availability
                            if oData_WS[sData_Var]:

                                # Get results and times
                                oData_Results = oData_WS[sData_Var]['results']
                                oData_Time = oData_WS[sData_Var]['times']

                                # Remove unnecessary fields
                                oData_Dynamic_Step[sData_Key][sData_Var].pop('values', None)
                                oData_Dynamic_Step[sData_Key][sData_Var].pop('results', None)
                                oData_Dynamic_Step[sData_Key][sData_Var].pop('times', None)

                                # Save data
                                oData_Dynamic_Step[sData_Key][sData_Var]['results'] = oData_Results[:, :, iData_Index]
                                oData_Dynamic_Step[sData_Key][sData_Var]['times'] = [oData_Time[iData_Index]]

                        if not hasattr(oData_Dynamic_Step, 'iTime'):
                            oData_Dynamic_Step.iTime = 1
                        if not hasattr(oData_Dynamic_Step, 'oDataTime'):
                            oData_Dynamic_Step.oDataTime = [sData_Time]

                # Information
                oLogStream.info(' ---> SubsetData Time: ' + sData_Time + ' Index: ' + str(iData_Index))

            else:

                sData_Time = None
                iData_Index = None
                oData_Dynamic_Step = None

        else:
            Exc.getExc(' ---> Data workspace is null!', 2, 1)

            sData_Time = None
            iData_Index = None
            oData_Dynamic_Step = None

        return sData_Time, iData_Index, oData_Dynamic_Step

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
    def saveDataProduct(self, oDataGeo=None, oDataDynamic=None):

        # -------------------------------------------------------------------------------------
        # Get information if single or recursive method
        if self.bVarSubSet:
            sVarTime = oDataDynamic[0]
            iVarIndex = oDataDynamic[1]
            oVarData = oDataDynamic[2]

            if oVarData is None:
                return None
        else:
            sVarTime = self.sVarTime
            iVarIndex = 0
            oVarData = oDataDynamic

        oVarOut = self.oVarOut
        oVarFramework = self.oVarFramework
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Define time tags
        oTimeTags = {'$yyyy': sVarTime[0:4],
                     '$mm': sVarTime[4:6], '$dd': sVarTime[6:8], '$HH': sVarTime[8:10],
                     '$MM': sVarTime[10:12]}

        # Define general and geo-system information
        oFileGeneralInfo = updateDictStructure(oFileConventions_Default, self.oAlgConventions, 'general')
        oFileGeoSystemInfo = updateDictStructure(oFileConventions_Default, self.oAlgConventions, 'geosystem')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Iterate over outcome variable(s)
        for sVarKey, oVarDef in oVarOut.items():

            # -------------------------------------------------------------------------------------
            # Info start saving variable
            oLogStream.info(' ---> Save algorithm variable ' + sVarKey + ' ... ')

            # Get outcome variable information
            oVarType = oVarDef['id']['var_type']
            oVarName = oVarDef['id']['var_name']
            oVarFile = oVarDef['id']['var_file']
            oVarMethod = oVarDef['id']['var_method_save']
            oVarColormap = oVarDef['id']['var_colormap']
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Check variable workspace
            if oVarData[sVarKey]:

                # -------------------------------------------------------------------------------------
                # Iterate over declared variable(s)
                for iVarID, (oVarFeat, sVarName, sVarFile, sVarMethod, sVarColormap) in enumerate(zip(
                        oVarType, oVarName, oVarFile, oVarMethod, oVarColormap)):

                    # -------------------------------------------------------------------------------------
                    # Variable type
                    sVarType = oVarFeat[0]

                    # Get outcome variable colormap
                    oVarCM = {}
                    if sVarColormap in self.oVarColorMap:
                        oVarCM['colormap'] = self.__getColorMap(self.oVarColorMap[sVarColormap])
                    else:
                        oVarCM['colormap'] = None

                    # Get default variable attributes
                    oVarAttrs = oVarConventions_Default[sVarType]
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Check variable data availability
                    if oVarData[sVarKey][sVarName]:

                        # -------------------------------------------------------------------------------------
                        # Check file tag in file definition(s)
                        if sVarFile in oVarFramework:

                            # -------------------------------------------------------------------------------------
                            # Get filename from file definition(s) using file tag in outcome variable(s)
                            sVarFileName = defineString(deepcopy(oVarFramework[sVarFile]), oTimeTags)
                            # -------------------------------------------------------------------------------------

                            # -------------------------------------------------------------------------------------
                            # Check file saved on disk
                            if not exists(sVarFileName):

                                # -------------------------------------------------------------------------------------
                                # Info create file
                                oLogStream.info(' ----> Create file ' + sVarFileName + ' ... ')

                                # Get file driver (according with filename extensions
                                [oFileDriver, sFileUnzip, _] = selectFileDriver(sVarFileName, sZipExt_Default)

                                # Open file outcome
                                oFileData = oFileDriver.oFileLibrary.openFile(sFileUnzip, 'w')

                                # Write file attributes
                                oFileDriver.oFileLibrary.writeFileAttrs(oFileData, oFileGeneralInfo)
                                # Write geo system information
                                oFileDriver.oFileLibrary.writeGeoSystem(oFileData, oFileGeoSystemInfo)
                                # Write X, Y, time, nsim, ntime and nens
                                oFileDriver.oFileLibrary.writeDims(oFileData, 'X', oVarData.iCols)
                                oFileDriver.oFileLibrary.writeDims(oFileData, 'Y', oVarData.iRows)
                                oFileDriver.oFileLibrary.writeDims(oFileData, 'time', oVarData.iTime)
                                oFileDriver.oFileLibrary.writeDims(oFileData, 'nsim', 1)
                                oFileDriver.oFileLibrary.writeDims(oFileData, 'ntime', 2)
                                oFileDriver.oFileLibrary.writeDims(oFileData, 'nens', 1)

                                # Get file dimension(s)
                                oFileDims = oFileDriver.oFileLibrary.getDims(oFileData)

                                # Write time information
                                oFileDriver.oFileLibrary.writeTime(oFileData, 'time', oVarData.oDataTime, 'float64', 'time',
                                                                   sTimeFormat_Default, sTimeCalendar_Default,
                                                                   sTimeUnits_Default)

                                # Write longitude information
                                sVarNameX = 'longitude'
                                a2dVarDataX = oDataGeo.a2dGeoX
                                oVarAttrsX = oVarConventions_Default[sVarNameX]
                                sVarFormatX = oVarConventions_Default[sVarNameX]['Format']
                                oFileDriver.oFileLibrary.write2DVar(oFileData, sVarNameX,
                                                                    a2dVarDataX, oVarAttrsX, sVarFormatX,
                                                                    sVarDimY=oFileDims['Y']['name'],
                                                                    sVarDimX=oFileDims['X']['name'])
                                # Write latitude information
                                sVarNameY = 'latitude'
                                a2dVarDataY = oDataGeo.a2dGeoY
                                oVarAttrsY = oVarConventions_Default[sVarNameY]
                                sVarFormatY = oVarConventions_Default[sVarNameY]['Format']
                                oFileDriver.oFileLibrary.write2DVar(oFileData, sVarNameY,
                                                                    a2dVarDataY, oVarAttrsY, sVarFormatY,
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
                                [oFileDriver, sFileUnzip, _] = selectFileDriver(sVarFileName, sZipExt_Default)

                                # Open file outcome
                                oFileData = oFileDriver.oFileLibrary.openFile(sFileUnzip, 'a')
                                # Get file dimension(s)
                                oFileDims = oFileDriver.oFileLibrary.getDims(oFileData)

                                # Info get file
                                oLogStream.info(' ----> Get file ' + sVarFileName + ' previously created ... OK')
                                # -------------------------------------------------------------------------------------

                            # -------------------------------------------------------------------------------------
                            # Info start saving variable
                            oLogStream.info(' -----> Save product variable ' + sVarName + ' ... ')
                            # Check variable in file handle
                            if oFileDriver.oFileLibrary.checkVarName(oFileData, sVarName) is False:

                                # -------------------------------------------------------------------------------------
                                # Get file dimensions
                                sVarDimX = oFileDims['X']['name']
                                sVarDimY = oFileDims['Y']['name']
                                sVarDimT = oFileDims['time']['name']

                                # Get var structure
                                oVarStruct = oVarData[sVarKey][sVarName]

                                # Define var attribute(s)
                                oVarAttrs = updateDictStructure(oVarAttrs, oVarStruct['attributes'])
                                oVarAttrs = updateDictStructure(oVarAttrs,
                                                                selectVarAttributes(oVarDef['attributes'], iVarID))
                                oVarAttrs = updateDictStructure(oVarAttrs, oVarCM)

                                # Get variable data
                                oVarResults = oVarStruct['results']
                                # Get variable format
                                if 'Format' in oVarStruct['attributes']:
                                    sVarFormat = oVarStruct['attributes']['Format']
                                else:
                                    sVarFormat = 'f4'

                                # Check and get library write method
                                if hasattr(oFileDriver.oFileLibrary, sVarMethod):
                                    # Get write method
                                    oVarMethod = getattr(oFileDriver.oFileLibrary, sVarMethod)

                                    # Store variable (2d and 3d dimensions)
                                    if sVarType == 'var2d':
                                        oVarMethod(oFileData, sVarName, oVarResults, oVarAttrs, sVarFormat,
                                                   sVarDimY=sVarDimY, sVarDimX=sVarDimX)
                                    elif sVarType == 'var3d':
                                        oVarMethod(oFileData, sVarName, oVarResults, oVarAttrs, sVarFormat,
                                                   sVarDimT=sVarDimT, sVarDimY=sVarDimY, sVarDimX=sVarDimX)

                                    # Info end saving variable
                                    oLogStream.info(' -----> Save product variable ' + sVarName + ' ... OK ')

                                else:
                                    # Exit without saving variable
                                    oLogStream.info(' -----> Save product variable ' + sVarName + ' ... FAILED ')
                                    Exc.getExc(' =====> WARNING: selected method is not available in io library', 2, 1)
                                # -------------------------------------------------------------------------------------
                            else:
                                # -------------------------------------------------------------------------------------
                                # Info skip saving variable
                                oLogStream.info(' -----> Save product variable ' + sVarName + ' ... SKIPPED ')
                                Exc.getExc(' =====> WARNING: variable is already saved in selected file', 2, 1)
                                # -------------------------------------------------------------------------------------

                            # -------------------------------------------------------------------------------------
                            # Info start closing and zipping file
                            oLogStream.info(' ----> Close and zip file ' + sVarFileName + ' ... ')
                            # Close file
                            oFileDriver.oFileLibrary.closeFile(oFileData)
                            # Zip file
                            zipFileData(sFileUnzip, sZipExt_Default)
                            # Info end closing and zipping file
                            oLogStream.info(' ----> Close and zip file ' + sVarFileName + ' ... OK ')

                            # Info end saving variable
                            oLogStream.info(' ---> Save algorithm variable ' + sVarKey + ' ... OK ')
                            # -------------------------------------------------------------------------------------

                        else:
                            # -------------------------------------------------------------------------------------
                            # Exit without saving variable
                            oLogStream.info(' ---> Save algorithm variable ' + sVarKey + ' ... FAILED')
                            Exc.getExc(' =====> WARNING: variable is not declared in file', 2, 1)
                            # -------------------------------------------------------------------------------------

                    else:

                        # -------------------------------------------------------------------------------------
                        # Exit without saving variable
                        oLogStream.info(' ---> Save algorithm variable ' + sVarKey + ' ... FAILED')
                        Exc.getExc(' =====> WARNING: variable is null', 2, 1)
                        # -------------------------------------------------------------------------------------

                # End iterations of variables
                # -------------------------------------------------------------------------------------

            else:

                # -------------------------------------------------------------------------------------
                # Exit without saving variable
                oLogStream.info(' ---> Save algorithm variable ' + sVarKey + ' ... FAILED')
                Exc.getExc(' =====> WARNING: variable data is undefined', 2, 1)
                # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Active recursive method
        if self.bVarSubSet:
            self.saveDataProduct(oDataGeo, self.subsetData(oData_Dynamic=self.oVarData, iData_Index=iVarIndex))
        else:
            return None
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
        self.oVarFramework = {'rain_data_hh_03': kwargs['rain_file_hh_03'],
                              'rain_data_hh_06': kwargs['rain_file_hh_06'],
                              'rain_data_hh_12': kwargs['rain_file_hh_12'],
                              'rain_data_hh_24': kwargs['rain_file_hh_24'],
                              }

        self.__defineVar()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define data variable
    def __defineVar(self):

        # -------------------------------------------------------------------------------------
        # Define variable(s) workspace by conventions and defined input field(s)
        for sVarKey, oVarValue in self.oVarDef.items():

            self.oVarData[sVarKey] = {}

            oVarID = oVarValue['id']['var_type'][0]
            if isinstance(oVarID, list):
                sVarID = oVarID[0]
            else:
                sVarID = oVarID

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

            oVarID = oVarValue['id']['var_type'][0]
            if isinstance(oVarID, list):
                sVarID = oVarID[0]
            else:
                sVarID = oVarID

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
    def getDataProduct(self, a1dGeoBox):

        # -------------------------------------------------------------------------------------
        # Iterate over file variable(s)
        oVarWS = {}
        for sVarKey, oVarDef in self.oVarDef.items():

            # -------------------------------------------------------------------------------------
            # Get input variable information
            oVarType = oVarDef['id']['var_type']
            oVarName = oVarDef['id']['var_name']
            oVarFile = oVarDef['id']['var_file']
            oVarMethod = oVarDef['id']['var_method_get']
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Check file tag in file definition(s)
            oVarGet = {}
            if sVarKey in self.oVarFramework:

                # -------------------------------------------------------------------------------------
                # Iterate over time(s)
                oVarWS[sVarKey] = {}
                for iVarTime, sVarTime in enumerate(self.oVarTime):

                    # -------------------------------------------------------------------------------------
                    # Define time tags
                    oTimeTags = {'$yyyy': sVarTime[0:4],
                                 '$mm': sVarTime[4:6], '$dd': sVarTime[6:8], '$HH': sVarTime[8:10],
                                 '$MM': sVarTime[10:12]}
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Iterate over declared variable(s)
                    for iVarID, (sVarType, sVarName, sVarFile, sVarMethod) in enumerate(zip(
                            oVarType, oVarName, oVarFile, oVarMethod)):

                        # -------------------------------------------------------------------------------------
                        # Get filename from file definition(s) using file tag in outcome variable(s)
                        sVarFileName = defineString(deepcopy(self.oVarFramework[sVarFile]), oTimeTags)
                        # Info start about selected file
                        oLogStream.info(' ---> Get file: ' + sVarFileName + ' (Time: ' + sVarTime + ') ... ')
                        # -------------------------------------------------------------------------------------

                        # -------------------------------------------------------------------------------------
                        # Check file saved on disk
                        if exists(sVarFileName):

                            # -------------------------------------------------------------------------------------
                            # Get data
                            [oFileHandle, oFileDriver, bFileOpen] = handleFileData(sVarFileName)
                            oVarAttribute = selectVarAttributes(self.oVarData[sVarKey], iVarID)
                            # -------------------------------------------------------------------------------------

                            # -------------------------------------------------------------------------------------
                            # Check file opening
                            if bFileOpen is True:

                                # -------------------------------------------------------------------------------------
                                # Info start about getting variable
                                oLogStream.info(' ----> Algorithm variable: ' +
                                                sVarKey + ' - Product variable: ' +
                                                sVarName + ' ...')

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
                                # Get variable data and attributes
                                if 'Missing_value' in oVarAttribute:
                                    dVarMissingValue = oVarAttribute['Missing_value']
                                else:
                                    dVarMissingValue = -9999

                                assert sVarName in oFileHandle.variables
                                assert dVarMissingValue == 999.0

                                a1oVarData = oFileHandle[sVarName][:][0, :, :].ravel()
                                a1oVarGeoX = oFileHandle['longitude'][:].ravel()
                                a1oVarGeoY = oFileHandle['latitude'][:].ravel()

                                if ma.is_masked(a1oVarData):
                                    a1dVarData = a1oVarData.data
                                else:
                                    a1dVarData = a1oVarData

                                if ma.is_masked(a1oVarGeoX):
                                    a1dVarGeoX = a1oVarGeoX.data
                                else:
                                    a1dVarGeoX = a1oVarGeoX

                                if ma.is_masked(a1oVarGeoY):
                                    a1dVarGeoY = a1oVarGeoY.data
                                else:
                                    a1dVarGeoY = a1oVarGeoY

                                a1iVarData_NoData = where(a1dVarData >= dVarMissingValue)[0]
                                a1iVarGeoX_NoData = where(a1dVarGeoX == dVarMissingValue)[0]
                                a1iVarGeoY_NoData = where(a1dVarGeoY == dVarMissingValue)[0]

                                a1iVarNoData = unique(concatenate(
                                    (a1iVarData_NoData, a1iVarGeoX_NoData, a1iVarGeoY_NoData), 0))

                                a1dVarData[a1iVarNoData] = nan
                                a1dVarGeoX[a1iVarNoData] = nan
                                a1dVarGeoY[a1iVarNoData] = nan

                                oFileParameter = oFileDriver.oFileLibrary.getFileAttrs(oFileHandle)
                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Save variable data
                                if oVarGet[sVarName]['values'] is None:
                                    a2dVarData_INIT = empty([a1dVarData.shape[0], self.oVarTime.__len__()])
                                    a2dVarData_INIT[:, :] = nan
                                    oVarGet[sVarName]['values'] = deepcopy(a2dVarData_INIT)

                                a2dVarData_DEF = oVarGet[sVarName]['values']
                                a2dVarData_DEF[:, iVarTime] = a1dVarData
                                oVarGet[sVarName]['values'] = a2dVarData_DEF

                                # Save variable longitude
                                if oVarGet[sVarName]['longitude'] is None:
                                    a2dVarGeoX_INIT = empty([a1dVarData.shape[0], self.oVarTime.__len__()])
                                    a2dVarGeoX_INIT[:, :] = nan
                                    oVarGet[sVarName]['longitude'] = deepcopy(a2dVarGeoX_INIT)

                                a2dVarGeoX_DEF = oVarGet[sVarName]['longitude']
                                a2dVarGeoX_DEF[:, iVarTime] = a1dVarGeoX
                                oVarGet[sVarName]['longitude'] = a2dVarGeoX_DEF

                                # Save variable latitude
                                if oVarGet[sVarName]['latitude'] is None:
                                    a2dVarGeoY_INIT = empty([a1dVarData.shape[0], self.oVarTime.__len__()])
                                    a2dVarGeoY_INIT[:, :] = nan
                                    oVarGet[sVarName]['latitude'] = deepcopy(a2dVarGeoY_INIT)

                                a2dVarGeoY_DEF = oVarGet[sVarName]['latitude']
                                a2dVarGeoY_DEF[:, iVarTime] = a1dVarGeoY
                                oVarGet[sVarName]['latitude'] = a2dVarGeoY_DEF
                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Save variable time step(s)
                                if oVarGet[sVarName]['times'] is None:
                                    oVarGet[sVarName]['times'] = []
                                if sVarTime not in oVarGet[sVarName]['times']:
                                    oVarGet[sVarName]['times'].append(sVarTime)
                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Update variable parameter(s)
                                if oVarGet[sVarName]['parameters'] is None:
                                    oVarGet[sVarName]['parameters'] = oFileParameter

                                # Update variable attribute(s)
                                if oVarGet[sVarName]['attributes'] is None:
                                    oVarGet[sVarName]['attributes'] = oVarAttribute
                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Info end about getting data variable
                                oLogStream.info(' ----> Algorithm variable: ' +
                                                sVarKey + ' - Product variable: ' +
                                                sVarName + ' ... OK')
                                # Info end about file
                                oLogStream.info(' ---> Get file: ' + sVarFileName + ' (Time: ' +
                                                sVarTime + ') ... OK')
                                # -------------------------------------------------------------------------------------

                            else:

                                # -------------------------------------------------------------------------------------
                                # Exit variable key not in workspace
                                oLogStream.info(' ---> Get file: ' + sVarFileName + ' (Time: ' +
                                                sVarTime + ') ... FAILED!')
                                Exc.getExc(' =====> WARNING: file not correctly open!', 2, 1)
                                # -------------------------------------------------------------------------------------
                        else:

                            # -------------------------------------------------------------------------------------
                            # Exit variable key not in workspace
                            oLogStream.info(' ---> Get file: ' + sVarFileName + ' (Time: ' +
                                            sVarTime + ') ... FAILED!')
                            Exc.getExc(' =====> WARNING: file not found!', 2, 1)
                            # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Save variable workspace
                oVarWS[sVarKey].update(oVarGet)
                # -------------------------------------------------------------------------------------
            else:
                # -------------------------------------------------------------------------------------
                # Exit file not in workspace
                Exc.getExc(' =====> WARNING: reference file wrongly defined! Check your settings file!', 2, 1)
                # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Return workspace
        return oVarWS
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to select variable attribute(s)
def selectVarAttributes(oVarData, iVarID):
    oVarAttribute = {}
    for sAttKey, oAttData in oVarData.items():

        if not isinstance(oAttData, list):
            oAttData = [oAttData]

        if oAttData.__len__() < iVarID:
            oVarAttribute[sAttKey] = oAttData[0]
        elif oAttData.__len__() > iVarID:
            oVarAttribute[sAttKey] = oAttData[iVarID]

    return oVarAttribute
# -------------------------------------------------------------------------------------
