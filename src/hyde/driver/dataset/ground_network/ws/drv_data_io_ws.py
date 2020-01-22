"""
Library Features:

Name:          drv_data_io_ws
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20191007'
Version:       '1.0.1'
"""
#################################################################################
# Library
import logging

from sys import version_info

from datetime import timedelta
from datetime import datetime
from os import remove
from os.path import exists, isfile
from copy import deepcopy
from numpy import reshape, full, nan, zeros, isnan, asarray, unique

from src.common.analysis.lib_analysis_interpolation_ancillary import filterData_Domain

from src.hyde.driver.dataset.ground_network.ws.cpl_data_variables_ws import DataVariables

from src.common.utils.lib_utils_op_string import defineString, convertUnicode2ASCII
from src.common.utils.lib_utils_op_dict import mergeDict
from src.common.utils.lib_utils_op_list import mergeList
from src.common.utils.lib_utils_apps_data import updateDictStructure
from src.common.utils.lib_utils_apps_file import handleFileData, selectFileDriver, zipFileData
from src.common.utils.lib_utils_apps_time import getTimeFrom, getTimeTo, getTimeSteps, checkTimeRef, roundTimeStep, \
    findTimeDiff, findTimeClosest, convertTimeFormat

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
# import matplotlib.pylab as plt
#################################################################################

# -------------------------------------------------------------------------------------
# Dictionary to define geographical attributes between dynamic data and geo data
oGeoValid = {'ncols': 'iCols', 'nrows': 'iRows',
             'xllcorner': 'dGeoXMin', 'yllcorner': 'dGeoYMin',
             'cellsize': 'dGeoXStep', 'nodata_value': 'dNoData', 'bounding_box': 'a1dGeoBox'}
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
        self.sVarTimeStep = kwargs['timestep']
        self.sVarTimeRun = kwargs['timerun']
        self.oVarTimeData = kwargs['settings']['data']['dynamic']['time']
        self.oVarTimeAlgorithm = kwargs['settings']['time']
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to round time to closest time to closest defined time interval
    def __roundTimeStep(self, sTimeStep):

        oVarTime = self.oVarTimeData

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

        oVarTimeDelta = timedelta(seconds=
                                  self.oVarTimeData['time_observed_step'] * self.oVarTimeData['time_observed_delta'])
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
        oVarTimeData = self.oVarTimeData
        oVarTimeAlgorithm = self.oVarTimeAlgorithm

        sVarTimeRun = self.__roundTimeStep(sVarTimeRun)

        sVarTimeRef, iVarTimeDiff = self.__selectRefTime(sVarTimeStep, sVarTimeRun)

        if 'time_observed_step' in oVarTimeData and 'time_observed_delta' in oVarTimeData:
            iVarTimeObsStep = oVarTimeData['time_observed_step']
            iVarTimeObsDelta = oVarTimeData['time_observed_delta']
        else:
            iVarTimeObsStep = 0
            iVarTimeObsDelta = 0

        if 'time_forecast_step' in oVarTimeData and 'time_forecast_delta' in oVarTimeData:
            iVarTimeForStep = oVarTimeData['time_forecast_step']
            iVarTimeForDelta = oVarTimeData['time_forecast_delta']
        else:
            iVarTimeForStep = 0
            iVarTimeForDelta = 0

        if 'time_step' in oVarTimeAlgorithm:
            iVarTimeAlgStep = oVarTimeAlgorithm['time_step']
            if iVarTimeAlgStep > 0:
                iVarTimeObsStep = int(86400 / iVarTimeObsDelta)

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
        self.oVarDef_IN = kwargs['settings']['variables']['source']
        self.oVarDef_OUT = kwargs['settings']['variables']['outcome']
        self.oVarData = kwargs['data']
        self.oVarFile = {'grid_ref': kwargs['grid_ref_file']}
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute data
    def computeDataProduct(self, oDataGeo=None, oDataAncillary=None):

        # -------------------------------------------------------------------------------------
        # Iterate over file variable(s)
        oVarWS_IN = self.oVarData
        oVarWS_OUT = DataObj()
        for sVarKey_IN, oVarDef_IN in self.oVarDef_IN.items():

            # -------------------------------------------------------------------------------------
            # Debug
            # sVarKey_IN = 'air_temperature_data'
            # oVarDef_IN = self.oVarDef_IN[sVarKey_IN]
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Get input variable information
            oVarType_IN = oVarDef_IN['id']['var_type']
            oVarName_IN = oVarDef_IN['id']['var_name']
            sVarFile_IN = oVarDef_IN['id']['var_file']
            bVarMode_IN = oVarDef_IN['id']['var_mode']
            oVarHandle_IN = oVarDef_IN['id']['var_handle']
            oVarMethod_IN = oVarDef_IN['id']['var_method_compute']
            # Get input variable attribute(s)
            oVarAttrs_DEF = oVarDef_IN['attributes']

            # Info start about computing variable
            sVarHandle_IN = ','.join(oVarHandle_IN)
            oLogStream.info(' ---> Compute -- Variable: ' + sVarKey_IN + ' - Handle: ' + sVarHandle_IN + ' ... ')
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Check for variable activation in data processing
            if bVarMode_IN:

                # -------------------------------------------------------------------------------------
                # Check data field(s) availability to compute results
                if sVarKey_IN in oVarWS_IN:

                    # -------------------------------------------------------------------------------------
                    # Get data
                    oVarData_IN = oVarWS_IN[sVarKey_IN]
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Check fields definition in variable workspace
                    if ('values' in oVarData_IN) and ('attributes' in oVarData_IN) and (
                            'times' in oVarData_IN):

                        # -------------------------------------------------------------------------------------
                        # Get data and attributes
                        oVarValue_IN = deepcopy(oVarData_IN['values'])
                        oVarGeoX_IN = deepcopy(oVarData_IN['longitude'])
                        oVarGeoY_IN = deepcopy(oVarData_IN['latitude'])
                        oVarGeoZ_IN = deepcopy(oVarData_IN['altitude'])
                        oVarAttrs_IN = deepcopy(oVarData_IN['attributes'])
                        oVarParams_IN = deepcopy(oVarData_IN['parameters'])
                        oVarTime_INOUT = deepcopy(oVarData_IN['times'])

                        # Get missing value
                        if 'Missing_value' in oVarAttrs_IN:
                            dVarMissValue_IN = oVarAttrs_IN['Missing_value']
                        else:
                            dVarMissValue_IN = -9999.0
                        # Get scale factor
                        if 'ScaleFactor' in oVarAttrs_IN:
                            dScaleFactor_IN = oVarAttrs_IN['ScaleFactor']
                        else:
                            dScaleFactor_IN = 1
                        # Get fill value
                        if '_FillValue' in oVarAttrs_IN:
                            dVarFillValue_IN = oVarAttrs_IN['_FillValue']
                        else:
                            dVarFillValue_IN = -9999.0
                        # Get units
                        if 'units' in oVarAttrs_IN:
                            sVarUnits_IN = oVarAttrs_IN['units']
                        else:
                            sVarUnits_IN = None
                        # Get valid range
                        if 'Valid_range' in oVarAttrs_IN:
                            oVarValidRange_IN = asarray(oVarAttrs_IN['Valid_range'])
                        else:
                            oVarValidRange_IN = None
                        # -------------------------------------------------------------------------------------

                        # -------------------------------------------------------------------------------------
                        # Initialize variable to store results
                        a3dVarValue_OUT_INIT = zeros(
                            [oDataGeo.a2dGeoX.shape[0], oDataGeo.a2dGeoY.shape[1], oVarTime_INOUT.__len__()])
                        a3dVarValue_OUT_INIT[:, :, :] = nan

                        # Iterate over time step(s)
                        for iTimeStep, (sTimeStep_INOUT,
                                        a1dVarValue_IN, a1dVarGeoX_IN, a1dVarGeoY_IN, a1dVarGeoZ_IN) \
                                in (enumerate(zip(oVarTime_INOUT,
                                                  oVarValue_IN, oVarGeoX_IN, oVarGeoY_IN, oVarGeoZ_IN))):

                            # -------------------------------------------------------------------------------------
                            # Info start about time step
                            oLogStream.info(' ----> TimeStep: ' + sTimeStep_INOUT + ' ... ')

                            # Get method to compute variable
                            oDrv_Data_Cmp = DataVariables(
                                time=sTimeStep_INOUT,
                                var=oVarHandle_IN,
                                data=a1dVarValue_IN, x=a1dVarGeoX_IN, y=a1dVarGeoY_IN, z=a1dVarGeoZ_IN,
                                geo=oDataGeo,
                                ancillary=oDataAncillary,
                                method=oVarMethod_IN['name'],
                                params=oVarMethod_IN['params'])
                            # Compute variable using interpolating method
                            oVarData_OUT = oDrv_Data_Cmp.computeVarData(
                                valid_range=oVarValidRange_IN,
                                missing_value=dVarMissValue_IN, fill_value=dVarFillValue_IN, units=sVarUnits_IN)
                            # -------------------------------------------------------------------------------------

                            # -------------------------------------------------------------------------------------
                            # Check data availability after computing process
                            if oVarData_OUT is not None:

                                # -------------------------------------------------------------------------------------
                                # Iterate over interpolated variable(s) [can be different with variable keys]
                                for sVarHandle_OUT, a2dVarData_OUT in oVarData_OUT.items():

                                    # Get attributed from outcome workspace
                                    if sVarHandle_OUT in self.oVarDef_OUT:
                                        oVarAttrs_OUT = self.oVarDef_OUT[sVarHandle_OUT]['attributes']
                                    else:
                                        oVarAttrs_OUT = None

                                    # Get missing value
                                    if 'Missing_value' in oVarAttrs_OUT:
                                        dVarMissValue_OUT = oVarAttrs_OUT['Missing_value']
                                    else:
                                        dVarMissValue_OUT = -9999.0
                                    # Get scale factor
                                    if 'ScaleFactor' in oVarAttrs_OUT:
                                        dScaleFactor_OUT = oVarAttrs_OUT['ScaleFactor']
                                    else:
                                        dScaleFactor_OUT = 1
                                    # Get fill value
                                    if '_FillValue' in oVarAttrs_OUT:
                                        dVarFillValue_OUT = oVarAttrs_OUT['_FillValue']
                                    else:
                                        dVarFillValue_OUT = -9999.0
                                    # Get units
                                    if 'units' in oVarAttrs_OUT:
                                        sVarUnits_OUT = oVarAttrs_OUT['units']
                                    else:
                                        sVarUnits_OUT = None
                                    # Get valid range
                                    if 'Valid_range' in oVarAttrs_OUT:
                                        oVarValidRange_OUT = asarray(oVarAttrs_OUT['Valid_range'])
                                    else:
                                        oVarValidRange_OUT = None

                                    # Init variable workspace
                                    if sVarHandle_OUT not in oVarWS_OUT:
                                        oVarWS_OUT[sVarHandle_OUT] = {}
                                        oVarWS_OUT[sVarHandle_OUT]['results'] = deepcopy(a3dVarValue_OUT_INIT)
                                        oVarWS_OUT[sVarHandle_OUT]['attributes'] = oVarAttrs_OUT
                                        oVarWS_OUT[sVarHandle_OUT]['times'] = []

                                    # Define data over domain
                                    a2dVarValue_OUT_DOMAIN = filterData_Domain(a2dVarData_OUT, oDataGeo.a1iGeoIndexNaN, nan)

                                    a1dVarValue_OUT_DOMAIN = deepcopy(a2dVarValue_OUT_DOMAIN.ravel())
                                    a1dVarValue_OUT_DOMAIN[oDataGeo.a1iGeoIndexNaN] = dVarFillValue_OUT
                                    a1dVarValue_OUT_DOMAIN[isnan(a1dVarValue_OUT_DOMAIN)] = dVarFillValue_OUT

                                    # Set nan for missing and outbounds values
                                    if oVarValidRange_OUT[0] is not None:
                                        a1dVarValue_OUT_DOMAIN[
                                            a1dVarValue_OUT_DOMAIN < oVarValidRange_OUT[0]] = dVarMissValue_OUT
                                    if oVarValidRange_OUT[1] is not None:
                                        a1dVarValue_OUT_DOMAIN[
                                            a1dVarValue_OUT_DOMAIN > oVarValidRange_OUT[1]] = dVarMissValue_OUT
                                    # a1dVarValue_OUT_DOMAIN[a1dVarValue_OUT_DOMAIN == dVarMissValue_OUT] = nan

                                    # Reshape data with selected domain
                                    a2dVarValue_OUT_FILTER = reshape(a1dVarValue_OUT_DOMAIN,
                                                                     [oDataGeo.a2dGeoX.shape[0], oDataGeo.a2dGeoY.shape[1]])

                                    # Save data in variable workspace
                                    a3dVarValue_OUT = oVarWS_OUT[sVarHandle_OUT]['results']
                                    a3dVarValue_OUT[:, :, iTimeStep] = a2dVarValue_OUT_FILTER
                                    oVarWS_OUT[sVarHandle_OUT]['results'] = a3dVarValue_OUT
                                    # Save times in variable workspace
                                    oVarWS_OUT[sVarHandle_OUT]['times'].append(sTimeStep_INOUT)
                                    # -------------------------------------------------------------------------------------

                            else:
                                # -------------------------------------------------------------------------------------
                                # Exit variable key not in workspace
                                Exc.getExc(' =====> WARNING: outcome data are null for time step ' +
                                           sTimeStep_INOUT + '!', 2, 1)
                                oLogStream.info(' ---> Compute -- Variable: ' + sVarKey_IN +
                                                ' - Handle: ' + sVarHandle_IN + ' ... SKIPPED')
                                # -------------------------------------------------------------------------------------

                            # -------------------------------------------------------------------------------------
                            # Info end about time step
                            oLogStream.info(' ----> TimeStep: ' + sTimeStep_INOUT + ' ... OK')
                            # -------------------------------------------------------------------------------------

                        # -------------------------------------------------------------------------------------
                        # Add attributes to workspace
                        if not hasattr(oVarWS_OUT, 'iRows'):
                            oVarWS_OUT.iRows = oDataGeo.a2dGeoX.shape[0]
                        if not hasattr(oVarWS_OUT, 'iCols'):
                            oVarWS_OUT.iCols = oDataGeo.a2dGeoY.shape[1]
                        if not hasattr(oVarWS_OUT, 'iTime'):
                            oVarWS_OUT.iTime = oVarTime_INOUT.__len__()
                        if not hasattr(oVarWS_OUT, 'oDataTime'):
                            oVarWS_OUT.oDataTime = oVarTime_INOUT
                        # Add longitude and latitude to workspace
                        if 'longitude' not in oVarWS_OUT:
                            oVarWS_OUT['longitude'] = oDataGeo.a2dGeoX
                        if 'latitude' not in oVarWS_OUT:
                            oVarWS_OUT['latitude'] = oDataGeo.a2dGeoX
                        # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Info end computing variable
                    oLogStream.info(' ---> Compute -- Variable: ' + sVarKey_IN +
                                    ' - Handle: ' + sVarHandle_IN + ' ... OK')
                    # -------------------------------------------------------------------------------------

                else:

                    # -------------------------------------------------------------------------------------
                    # Exit variable key not in workspace
                    Exc.getExc(' =====> WARNING: data field is not defined!', 2, 1)
                    oLogStream.info(' ---> Compute -- Variable: ' + sVarKey_IN +
                                    ' - Handle: ' + sVarHandle_IN + ' ... FAILED')
                    for sVarHandle_OUT in oVarHandle_IN:
                        oVarWS_OUT[sVarHandle_OUT] = None
                    # -------------------------------------------------------------------------------------

            else:

                # -------------------------------------------------------------------------------------
                # Info start about computing variable
                oLogStream.info(' ---> Compute -- Variable: ' + sVarKey_IN +
                                ' - Handle: ' + sVarHandle_IN + ' ... SKIPPED. Variable not activated.')
                for sVarHandle_OUT in oVarHandle_IN:
                    oVarWS_OUT[sVarHandle_OUT] = None
                # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Return workspace
        return oVarWS_OUT
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
        self.oVarFile = {'ws_product': kwargs['ws_product_file']}
        self.oVarColorMap = kwargs['ws_colormap_file']
        self.oAlgConventions = kwargs['settings']['algorithm']

        self.bVarSubSet = True

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to subset data
    @staticmethod
    def subsetData(oData_Dynamic, iData_Index=None):

        # -------------------------------------------------------------------------------------
        # Define time index
        if iData_Index is None:
            iData_Index = 0
        else:
            iData_Index = iData_Index + 1

        # Check time data availability in data workspace
        if hasattr(oData_Dynamic, 'iTime'):
            iData_Dynamic_Index = oData_Dynamic.iTime - 1
        else:
            iData_Dynamic_Index = None
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Check time step availability in data
        if iData_Dynamic_Index is not None:
            if iData_Dynamic_Index >= iData_Index:

                # -------------------------------------------------------------------------------------
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

                # Info time start
                oLogStream.info(
                    ' ----> SubsetTime: ' + sData_Time + ' SubsetIndex: ' + str(iData_Index) + ' ... ')
                # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Iterate over data key(s)
                for sData_Key in oData_Key:

                    # -------------------------------------------------------------------------------------
                    # Info starting
                    oLogStream.info(' -----> SubsetVar: ' + sData_Key + ' ... ')

                    # Check data availability on data dictionary
                    if oData_Dynamic[sData_Key] is not None:

                        # -------------------------------------------------------------------------------------
                        # Get data
                        oData_Results = oData_Dynamic[sData_Key]['results']
                        oData_Time = oData_Dynamic[sData_Key]['times']

                        # Check data index is included in time period (for variable data null times are not saved)
                        if iData_Index < oData_Time.__len__():

                            # Remove unnecessary fields
                            oData_Dynamic_Step[sData_Key].pop('values', None)
                            oData_Dynamic_Step[sData_Key].pop('results', None)
                            oData_Dynamic_Step[sData_Key].pop('times', None)

                            # Save data
                            oData_Dynamic_Step[sData_Key]['results'] = oData_Results[:, :, iData_Index]
                            oData_Dynamic_Step[sData_Key]['times'] = [oData_Time[iData_Index]]

                            if not hasattr(oData_Dynamic_Step, 'iTime'):
                                oData_Dynamic_Step.iTime = 1
                            if not hasattr(oData_Dynamic_Step, 'oDataTime'):
                                oData_Dynamic_Step.oDataTime = [sData_Time]

                            # Information ending
                            oLogStream.info(' -----> SubsetVar: ' + sData_Key + ' ... OK')
                            # -------------------------------------------------------------------------------------
                        else:
                            # -------------------------------------------------------------------------------------
                            # Information ending
                            oLogStream.info(' -----> SubsetVar: ' + sData_Key + ' ... SKIPPED. Variable data are null!')
                            oData_Dynamic_Step[sData_Key] = None
                            # -------------------------------------------------------------------------------------
                    else:
                        # -------------------------------------------------------------------------------------
                        # Information ending (for null dataset)
                        oLogStream.info(' -----> SubsetVar: ' + sData_Key + ' ... SKIPPED. All data are null!')
                        oData_Dynamic_Step[sData_Key] = None
                        # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Info time start
                oLogStream.info(
                    ' ----> SubsetTime: ' + sData_Time + ' SubsetIndex: ' + str(iData_Index) + ' ... OK')
                # -------------------------------------------------------------------------------------

            else:
                # -------------------------------------------------------------------------------------
                # Data null (for data step index > data step dynamic)
                Exc.getExc(' =====> WARNING: subset data failed. Subset index is greater than data dynamic index', 2, 1)
                sData_Time = None
                iData_Index = None
                oData_Dynamic_Step = None
                # -------------------------------------------------------------------------------------

        else:
            # -------------------------------------------------------------------------------------
            # Data null (for data step index > data step dynamic)
            Exc.getExc(' =====> WARNING: subset data failed. All data are null or not available ', 2, 1)
            sData_Time = None
            iData_Index = None
            oData_Dynamic_Step = None
            # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Return variable(s) and workspace(s)
        return sData_Time, iData_Index, oData_Dynamic_Step
        # -------------------------------------------------------------------------------------

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
    # Method to get geographical reference
    @staticmethod
    def __getGeoReference(oGeoRef=None, oGeoData=None):
        # Iterate over geographical reference attributes and geographical data
        if (oGeoRef is not None) and (oGeoData is not None):
            for sVarRef, sVarGeo in oGeoValid.items():
                if (sVarRef in oGeoRef) and (hasattr(oGeoData, sVarGeo)):
                    oGeoValue = getattr(oGeoData, sVarGeo)
                    oGeoRef[sVarRef] = oGeoValue
                else:
                    oGeoRef[sVarRef] = None

        return oGeoRef

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
                Exc.getExc(' =====> WARNING: save dynamic data . All data are null! Check your settings!', 2, 1)
                return None
        else:
            sVarTime = self.sVarTime
            iVarIndex = 0
            oVarData = oDataDynamic
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Define geographical reference
        self.oAlgConventions['georeference'] = self.__getGeoReference(self.oAlgConventions['georeference'], oDataGeo)

        # Define time tags
        oTimeTags = {'$yyyy': sVarTime[0:4],
                     '$mm': sVarTime[4:6], '$dd': sVarTime[6:8], '$HH': sVarTime[8:10],
                     '$MM': sVarTime[10:12]}

        # Define general and geo-system information
        oFileGeneralInfo = updateDictStructure(oFileConventions_Default, self.oAlgConventions, 'general')
        oFileGeoSystemInfo = updateDictStructure(oFileConventions_Default, self.oAlgConventions, 'geosystem')
        oFileGeoReferenceInfo = updateDictStructure(oFileConventions_Default, self.oAlgConventions, 'georeference')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Iterate over outcome variable(s)
        for sVarKey, oVarDef in self.oVarDef.items():

            # -------------------------------------------------------------------------------------
            # Info start saving variable
            oLogStream.info(' ---> Save workspace: ' + sVarKey + ' ... ')

            # Get outcome variable information
            oVarType = oVarDef['id']['var_type']
            oVarName = oVarDef['id']['var_name']
            sVarFile = oVarDef['id']['var_file']
            bVarMode = oVarDef['id']['var_mode']
            sVarMethod = oVarDef['id']['var_method_save']
            sVarColormap = oVarDef['id']['var_colormap']

            # Get outcome variable colormap
            oVarCM = {}
            if sVarKey in oVarData:
                if sVarColormap in self.oVarColorMap:
                    oVarCM['colormap'] = self.__getColorMap(self.oVarColorMap[sVarColormap])
                else:
                    oVarCM['colormap'] = None
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Check for variable activation in data saving
            if bVarMode:

                # -------------------------------------------------------------------------------------
                # Check variable workspace
                if oVarData[sVarKey]:

                    # -------------------------------------------------------------------------------------
                    # Check file tag in file definition(s)
                    if sVarFile in self.oVarFile:

                        # -------------------------------------------------------------------------------------
                        # Get filename from file definition(s) using file tag in outcome variable(s)
                        sVarFileName = defineString(deepcopy(self.oVarFile[sVarFile]), oTimeTags)
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
                            oFileDriver.oFileLibrary.writeFileAttrs(oFileData,
                                                                    mergeDict(oFileGeneralInfo, oFileGeoReferenceInfo))
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
                        oLogStream.info(' -----> Save variable ' + oVarName[0] + ' ... ')
                        # Check variable in file handle
                        if oFileDriver.oFileLibrary.checkVarName(oFileData, oVarName[0]) is False:

                            # -------------------------------------------------------------------------------------
                            # Get file dimensions
                            sVarDimX = oFileDims['X']['name']
                            sVarDimY = oFileDims['Y']['name']
                            sVarDimT = oFileDims['time']['name']

                            # Get var structure
                            oVarStruct = oVarData[sVarKey]
                            # Define var attribute(s)
                            oVarAttrs = deepcopy(oVarConventions_Default[oVarType[0]])
                            oVarAttrs = updateDictStructure(oVarAttrs, oVarStruct['attributes'])
                            oVarAttrs = updateDictStructure(oVarAttrs, oVarDef['attributes'])
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
                                if oVarType[0] == 'var2d':
                                    oVarMethod(oFileData, oVarName[0], oVarResults, oVarAttrs, sVarFormat,
                                               sVarDimY=sVarDimY, sVarDimX=sVarDimX)
                                elif oVarType[0] == 'var3d':
                                    oVarMethod(oFileData, oVarName[0], oVarResults, oVarAttrs, sVarFormat,
                                               sVarDimT=sVarDimT, sVarDimY=sVarDimY, sVarDimX=sVarDimX)

                                # Info end saving variable
                                oLogStream.info(' -----> Save variable ' + oVarName[0] + ' ... OK ')

                            else:
                                # Exit without saving variable
                                Exc.getExc(' =====> WARNING: selected method is not available on io library', 2, 1)
                                oLogStream.info(' -----> Save variable ' + oVarName[0] + ' ... FAILED!')
                            # -------------------------------------------------------------------------------------
                        else:
                            # -------------------------------------------------------------------------------------
                            # Info skip saving variable
                            oLogStream.info(' -----> Save variable ' + oVarName[0] +
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
                        Exc.getExc(' =====> WARNING: variable file is not declared', 2, 1)
                        oLogStream.info(' ---> Save workspace: ' + sVarKey + ' ... FAILED.')
                        # -------------------------------------------------------------------------------------
                else:
                    # -------------------------------------------------------------------------------------
                    # Exit without saving variable
                    Exc.getExc(' =====> WARNING: variable data are null! ', 2, 1)
                    oLogStream.info(' ---> Save workspace: ' + sVarKey + ' ... FAILED')
                    # -------------------------------------------------------------------------------------
            else:
                # -------------------------------------------------------------------------------------
                # Info start about computing variable
                oLogStream.info(' ---> Save workspace: ' + sVarKey + ' ... SKIPPED. Variable not activated.')
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
        self.oVarDef = kwargs['settings']['variables']['source']
        self.oVarFile = {'rain_data': kwargs['rain_file'],
                         'air_temperature_data': kwargs['air_temperature_file'],
                         'incoming_radiation_data': kwargs['incoming_radiation_file'],
                         'wind_data': kwargs['wind_file'],
                         'relative_humidity_data': kwargs['relative_humidity_file'],
                         'air_pressure_data': kwargs['air_pressure_file'],
                         'snow_height_data': kwargs['snow_height_file'],
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
    def getDataProduct(self, a1dGeoBox):

        # -------------------------------------------------------------------------------------
        # Iterate over file variable(s)
        oVarWS = {}
        for sVarKey, oVarDef in self.oVarDef.items():

            # DEBUG
            # sVarKey = 'air_temperature_data'
            # oVarDef = self.oVarDef[sVarKey]

            # -------------------------------------------------------------------------------------
            # Get input variable information
            oVarType = oVarDef['id']['var_type']
            oVarName = oVarDef['id']['var_name']
            sVarFile = oVarDef['id']['var_file']
            bVarMode = oVarDef['id']['var_mode']
            oVarMethod = oVarDef['id']['var_method_get']
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Check file tag in file definition(s)
            oVarGet = {}
            if sVarFile in self.oVarFile:

                # -------------------------------------------------------------------------------------
                # Info start about getting variable
                oLogStream.info(' ----> Algorithm variable: ' + sVarKey + ' - Product variable: ' +
                                oVarName[0] + ' ...')
                # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Check for variable activation in data processing
                if bVarMode:

                    # -------------------------------------------------------------------------------------
                    # Iterate over time(s)
                    for iVarTime, sVarTime in enumerate(self.oVarTime):

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
                        oLogStream.info(' -----> Get file: ' + sVarFileName + ' (Time: ' + sVarTime + ') ... ')
                        # -------------------------------------------------------------------------------------

                        # -------------------------------------------------------------------------------------
                        # Check file saved on disk
                        if exists(sVarFileName):

                            # -------------------------------------------------------------------------------------
                            # Get data
                            [oFileHandle, oFileDriver, bFileOpen] = handleFileData(sVarFileName, bFileTemp=False)
                            oVarAttribute = self.oVarData[sVarKey]
                            # -------------------------------------------------------------------------------------

                            # -------------------------------------------------------------------------------------
                            # Check file opening
                            if bFileOpen is True:

                                # -------------------------------------------------------------------------------------
                                # Init variable workspace
                                if sVarKey not in oVarGet:
                                    oVarGet[sVarKey] = {}
                                    oVarGet[sVarKey]['values'] = None
                                    oVarGet[sVarKey]['longitude'] = None
                                    oVarGet[sVarKey]['latitude'] = None
                                    oVarGet[sVarKey]['altitude'] = None
                                    oVarGet[sVarKey]['parameters'] = None
                                    oVarGet[sVarKey]['attributes'] = None
                                    oVarGet[sVarKey]['times'] = None
                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Get data from csv file (and store it in dataframe)
                                oVarDataFrame = oFileDriver.oFileLibrary.readFile2DataFrame(
                                    sVarFileName, oFileHandle.sFileDelimiter)
                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Get variable name, data and attributes
                                oVarDataCols = list(oVarDataFrame.columns.values)

                                a1dVarGeoX = oVarDataFrame['longitude'].values
                                a1dVarGeoY = oVarDataFrame['latitude'].values
                                a1dVarGeoZ = oVarDataFrame['altitude'].values
                                a1dVarData = oVarDataFrame['data'].values

                                a1sVarTimeStart = oVarDataFrame['time_start'].values
                                a1sVarTimeEnd = oVarDataFrame['time_end'].values
                                a1sVarUnits = oVarDataFrame['units'].values
                                a1sSensorName = oVarDataFrame['name'].values
                                a1sSensorCode = oVarDataFrame['code'].values

                                # Variable units
                                oVarUnits = unique(a1sVarUnits)
                                assert oVarUnits.__len__() == 1
                                assert oVarUnits[0] == oVarAttribute['units']
                                # Variable time start and time end
                                sVarTimeStart = unique(a1sVarTimeStart)[0]
                                sVarTimeStart = convertTimeFormat(sVarTimeStart, sTimeFormat_OUT=sTimeFormat_Default)
                                sVarTimeEnd = unique(a1sVarTimeEnd)[0]
                                sVarTimeEnd = convertTimeFormat(sVarTimeEnd, sTimeFormat_OUT=sTimeFormat_Default)
                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Save variable data
                                if oVarGet[sVarKey]['values'] is None:
                                    oVarGet[sVarKey]['values'] = []
                                oVarGet[sVarKey]['values'].append(a1dVarData)

                                # Save variable time step(s)
                                if oVarGet[sVarKey]['times'] is None:
                                    oVarGet[sVarKey]['times'] = []
                                oVarGet[sVarKey]['times'].append(sVarTimeEnd)

                                # Save variable longitudes, latitudes and altitudes
                                if oVarGet[sVarKey]['longitude'] is None:
                                    oVarGet[sVarKey]['longitude'] = []
                                oVarGet[sVarKey]['longitude'].append(a1dVarGeoX)
                                if oVarGet[sVarKey]['latitude'] is None:
                                    oVarGet[sVarKey]['latitude'] = []
                                oVarGet[sVarKey]['latitude'].append(a1dVarGeoY)
                                if oVarGet[sVarKey]['altitude'] is None:
                                    oVarGet[sVarKey]['altitude'] = []
                                oVarGet[sVarKey]['altitude'].append(a1dVarGeoZ)

                                # Save variable parameters and attributes
                                if oVarGet[sVarKey]['parameters'] is None:
                                    oVarGet[sVarKey]['parameters'] = None
                                if oVarGet[sVarKey]['attributes'] is None:
                                    oVarGet[sVarKey]['attributes'] = oVarAttribute
                                # -------------------------------------------------------------------------------------

                                # -------------------------------------------------------------------------------------
                                # Info end about file
                                oLogStream.info(' -----> Get file: ' + sVarFileName + ' (Time: ' +
                                                sVarTime + ') ... OK')
                                # -------------------------------------------------------------------------------------
                            else:
                                # -------------------------------------------------------------------------------------
                                # Exit variable key not in workspace
                                Exc.getExc(' =====> WARNING: file not correctly open!', 2, 1)
                                oLogStream.info(' -----> Get file: ' + sVarFileName + ' (Time: ' +
                                                sVarTime + ') ... FAILED')
                                # -------------------------------------------------------------------------------------
                        else:
                            # -------------------------------------------------------------------------------------
                            # Exit variable key not in workspace
                            Exc.getExc(' =====> WARNING: file not found!', 2, 1)
                            oLogStream.info(' -----> Get file: ' + sVarFileName + ' (Time: ' +
                                            sVarTime + ') ... FAILED')
                            # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Save variable workspace
                    oVarWS.update(oVarGet)

                    # Info end about getting data variable
                    oLogStream.info(' ----> Algorithm variable: ' + sVarKey + ' - Product variable: ' +
                                    oVarName[0] + ' ... OK')
                    # -------------------------------------------------------------------------------------
                else:
                    # -------------------------------------------------------------------------------------
                    # Info start about getting variable
                    oLogStream.info(' ----> Algorithm variable: ' + sVarKey + ' - Product variable: ' +
                                    oVarName[0] + ' ... SKIPPED. Variable not activated.')
                    # -------------------------------------------------------------------------------------
            else:
                # -------------------------------------------------------------------------------------
                # Exit file not in workspace
                Exc.getExc(' =====> WARNING: reference file is wrongly defined! Check settings file!', 2, 1)
                # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Return workspace
        return oVarWS
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
