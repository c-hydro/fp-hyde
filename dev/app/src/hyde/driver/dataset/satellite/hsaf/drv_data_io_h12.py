"""
Library Features:

Name:          drv_data_io_h12
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '2019104'
Version:       '1.0.1'
"""
#################################################################################
# Library
import logging

from os import remove
from os.path import exists
from copy import deepcopy
from numpy import where, reshape

from src.common.analysis.lib_analysis_filtering import defineLookUpTable
from src.common.analysis.lib_analysis_interpolation_grid import interpGridData, interpGridIndex

from src.common.utils.lib_utils_apps_data import updateDictStructure
from src.common.utils.lib_utils_apps_file import handleFileData, selectFileDriver, zipFileData
from src.common.utils.lib_utils_file_workspace import savePickle, restorePickle

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
# Algorithm definition(s)
oVarKey_NotValid = ['codedValues', 'distinctLatitudes', 'distinctLongitudes', 'g2grid',
                             'hundred', 'latLonValues', 'latitudes', 'longitudes',
                             'numberOfSection', 'sectionNumber', 'values']
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class data object
class DataObj(dict):
    pass
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

        for bFlag, oFile in zip(self.a1bFlag, self.a1oFile):
            if isinstance(oFile, str):
                oFile = [oFile]
            for sFile in oFile:
                if exists(sFile):
                    if bFlag is True:
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
        self.oVarData = kwargs['data']
        self.oVarFile = {'grid_ref': kwargs['grid_ref_file']}
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute data
    def computeDataProduct(self, oDataGeo=None):

        # -------------------------------------------------------------------------------------
        # Iterate over file variable(s)
        oVarWS = self.oVarData
        for sVarKey, oVarData in oVarWS.items():

            # -------------------------------------------------------------------------------------
            # Info start computing variable
            oLogStream.info(' ---> Compute variable: ' + sVarKey + ' ... ')

            # Check data variable availability
            if oVarWS[sVarKey] is not None:

                # -----------------------------------------------------------------------------------
                # Initialize results workspace
                oVarWS[sVarKey]['results'] = {}
                if ('values' in oVarData) and ('attributes' in oVarData):

                    # -------------------------------------------------------------------------------------
                    # Get data and attributes
                    a2dVarValue = deepcopy(oVarData['values'])
                    oVarAttrs = deepcopy(oVarData['attributes'])
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Check flags definition to apply a look up table
                    if ('flag_masks' in oVarAttrs) and ('flag_values' in oVarAttrs) and ('flag_meanings' in oVarAttrs):

                        oVarTable = defineLookUpTable(oVarAttrs['flag_values'], oVarAttrs['flag_masks'],
                                                      oVarAttrs['flag_meanings'])

                        for sTableKey, oTableValue in oVarTable.items():

                            dTableIN_MIN = float(oTableValue['in']['min'])
                            dTableIN_MAX = float(oTableValue['in']['max'])
                            if oTableValue['out'] is not None:
                                dTableOUT = float(oTableValue['out'])
                            else:
                                dTableOUT = oTableValue['out']

                            if dTableOUT is not None:

                                a2iVarIndex = where((a2dVarValue >= dTableIN_MIN) & (a2dVarValue <= dTableIN_MAX))
                                a2dVarValue[a2iVarIndex[0], a2iVarIndex[1]] = dTableOUT

                    else:
                        pass
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Info start interpolating variable
                    oLogStream.info(' ----> Interpolate variable over domain ... ')
                    # Create grid reference(s)
                    if not exists(self.oVarFile['grid_ref']):
                        a1iVarIndex_INTERP = interpGridIndex(a2dVarValue,
                                                             oVarData['longitude'], oVarData['latitude'],
                                                             oDataGeo.a2dGeoX, oDataGeo.a2dGeoY)

                        savePickle(self.oVarFile['grid_ref'], a1iVarIndex_INTERP)
                    else:
                        a1iVarIndex_INTERP = restorePickle(self.oVarFile['grid_ref'])

                    # Interpolate variable over grid reference
                    a2dVarValue_INTERP = interpGridData(a2dVarValue,
                                                        oVarData['longitude'], oVarData['latitude'],
                                                        oDataGeo.a2dGeoX, oDataGeo.a2dGeoY,
                                                        a1iVarIndex_OUT=a1iVarIndex_INTERP)

                    # Filter variable over grid reference points
                    if 'Missing_value' in oVarAttrs:
                        dVarMissValue = oVarAttrs['Missing_value']
                    else:
                        dVarMissValue = -9999.0

                    a1dVarValue_INTERP = deepcopy(a2dVarValue_INTERP.ravel())
                    a1dVarValue_INTERP[oDataGeo.a1iGeoIndexNaN] = dVarMissValue
                    a2dVarValue_FILTER = reshape(a1dVarValue_INTERP,
                                                 [oDataGeo.a2dGeoX.shape[0], oDataGeo.a2dGeoY.shape[1]])
                    # Info end interpolating variable
                    oLogStream.info(' ----> Interpolate variable over domain ... OK')
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Debug
                    # plt.figure()
                    # plt.imshow(a2dVarValue); plt.colorbar(); plt.clim(0, 100)
                    # plt.figure()
                    # plt.imshow(a2dVarValue_INTERP); plt.colorbar(); plt.clim(-3, 100)
                    # plt.figure()
                    # plt.imshow(a2dVarValue_FILTER); plt.colorbar(); plt.clim(-3, 10)
                    # plt.show()
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Save data
                    oVarWS[sVarKey]['results'] = a2dVarValue_FILTER
                    # Info end computing variable
                    oLogStream.info(' ---> Compute variable: ' + sVarKey + ' ... OK')
                    # -------------------------------------------------------------------------------------

                else:

                    # -------------------------------------------------------------------------------------
                    # Exit variable key not in workspace
                    Exc.getExc(' ---> Compute variable: ' + sVarKey +
                               ' ... FAILED! Values and/or Attributes field(s) is/are not defined!', 2, 1)
                    oVarWS[sVarKey]['results'] = None
                    # -------------------------------------------------------------------------------------

            else:

                # -------------------------------------------------------------------------------------
                # Exit variable key not in workspace
                Exc.getExc(' ---> Compute variable: ' + sVarKey +
                           ' ... FAILED! Variable data is None!', 2, 1)
                oVarWS[sVarKey] = None
                # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Return workspace
        return oVarWS
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
        self.oVarFile = {'snow_cover_product': kwargs['snow_cover_product_file']}
        self.oAlgConventions = kwargs['settings']['algorithm']

        self.oVarCM = {'snow_cover_data': self.__getColorMap(kwargs['snow_cover_colormap_file'])}
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to get variable colormap
    @staticmethod
    def __getColorMap(sFileCM):

        # Get file driver (according with filename extensions
        if exists(sFileCM):
            oFileDriver = selectFileDriver(sFileCM, sFileMode='r')[0]
            oFileCM = oFileDriver.oFileLibrary.openFile(sFileCM, 'r')
            oFileLines = oFileDriver.oFileLibrary.getLines(oFileCM)
        else:
            oFileLines = None

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
            oLogStream.info(' ---> Save variable: ' + sVarKey + ' ... ')

            # Get outcome variable information
            oVarType = oVarDef['id']['var_type']
            sVarName = oVarDef['id']['var_name']
            sVarFile = oVarDef['id']['var_file']

            # Get outcome variable colormap
            oVarCM = {}
            if self.oVarCM:
                if sVarKey in self.oVarCM:
                    oVarCM['colormap'] = self.oVarCM[sVarKey]
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Check data availability
            if self.oVarData[sVarKey] is not None:

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
                        oFileDriver.oFileLibrary.writeDims(oFileData, 'X', oDataGeo.iCols)
                        oFileDriver.oFileLibrary.writeDims(oFileData, 'Y', oDataGeo.iRows)
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
                        sVarFormat = oVarData['attributes']['Format']

                        # Store variable (2d and 3d dimensions)
                        if oVarType[0] == 'var2d':
                            oFileDriver.oFileLibrary.write2DVar(oFileData, sVarName,
                                                                oVarResults, oVarAttrs, sVarFormat,
                                                                sVarDimY=sVarDimY, sVarDimX=sVarDimX)
                        elif oVarType[0] == 'var3d':
                            oFileDriver.oFileLibrary.write3DVar(oFileData, sVarName,
                                                                oVarResults, oVarAttrs, sVarFormat,
                                                                sVarDimT=sVarDimT, sVarDimY=sVarDimY, sVarDimX=sVarDimX)

                        # Info end saving variable
                        oLogStream.info(' -----> Save variable ' + sVarName + ' ... OK ')
                        # -------------------------------------------------------------------------------------

                    else:
                        # -------------------------------------------------------------------------------------
                        # Info skip saving variable
                        oLogStream.info(' -----> Save variable ' + sVarName +
                                        ' ... SKIPPED! Variable is already saved in selected file ')
                        # -------------------------------------------------------------------------------------

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
                    oLogStream.info(' ---> Save variable: ' + sVarKey + ' ... OK')
                    # -------------------------------------------------------------------------------------

                else:

                    # -------------------------------------------------------------------------------------
                    # Exit variable key not in workspace
                    Exc.getExc(' ---> Save file: ' + sVarFileName +
                               ' ... FAILED! File is not in declared workspace!', 2, 1)
                    # Exit without saving variable
                    Exc.getExc(' ---> Save variable: ' + sVarKey + ' ... FAILED', 2, 1)
                    # -------------------------------------------------------------------------------------

            else:

                # -------------------------------------------------------------------------------------
                # Exit without saving variable
                Exc.getExc(' ---> Save variable: ' + sVarKey + ' ... FAILED! Variable data is None!', 2, 1)
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
        self.sVarTime = kwargs['time']
        self.oVarDef = kwargs['settings']['variables']['input']
        self.oVarFile = {'snow_cover_data': kwargs['snow_cover_data_file'],
                         'snow_cover_quality': kwargs['snow_cover_quality_file']}

        self.__defineVar()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define data variable
    def __defineVar(self):

        # -------------------------------------------------------------------------------------
        # Define variable(s) workspace by conventions and defined input field(s)
        for sVarKey, oVarValue in self.oVarDef.items():

            self.oVarData[sVarKey] = {}
            sVarID = oVarValue['id']['var_type']

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

            sVarID = oVarValue['id']['var_type']

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
        for sVarKey, sVarFile in self.oVarFile.items():

            # -------------------------------------------------------------------------------------
            # Info start getting variable
            oLogStream.info(' ---> Get variable: ' + sVarKey + ' ... ')

            # Check var in data key(s)
            if sVarKey in self.oVarData.keys():

                # -------------------------------------------------------------------------------------
                # Get data
                [oFileHandle, oFileDriver, bFileOpen] = handleFileData(sVarFile)
                oVarAttrs = self.oVarData[sVarKey]
                # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Check file opening
                if bFileOpen is True:

                    # -------------------------------------------------------------------------------------
                    # Iterate over data field(s)
                    for oFileMsg in oFileHandle:

                        # -------------------------------------------------------------------------------------
                        # Get variable name, data and attributes
                        sVarName = oFileMsg.name
                        sVarName = sVarName.replace(' ', '_')

                        # Info start getting data
                        oLogStream.info(' ----> Get data: ' + sVarName + ' ... ')

                        [a2dVarData, a2dVarGeoY, a2dVarGeoX] = oFileDriver.oFileLibrary.getVar2D_BOX(
                            oFileMsg, oGeoBox=a1dGeoBox)

                        oVarParameters = oFileDriver.oFileLibrary.getFileAttr(oFileMsg, oVarKeyNA=oVarKey_NotValid)
                        # -------------------------------------------------------------------------------------

                        # -------------------------------------------------------------------------------------
                        # Save variable workspace
                        oVarWS[sVarKey] = {}
                        oVarWS[sVarKey]['values'] = {}
                        oVarWS[sVarKey]['values'] = a2dVarData
                        oVarWS[sVarKey]['longitude'] = {}
                        oVarWS[sVarKey]['longitude'] = a2dVarGeoX
                        oVarWS[sVarKey]['latitude'] = {}
                        oVarWS[sVarKey]['latitude'] = a2dVarGeoY
                        oVarWS[sVarKey]['parameters'] = {}
                        oVarWS[sVarKey]['parameters'] = oVarParameters
                        oVarWS[sVarKey]['attributes'] = {}
                        oVarWS[sVarKey]['attributes'] = oVarAttrs

                        # Info start getting data
                        oLogStream.info(' ----> Get data: ' + sVarName + ' ... OK')
                        # Info start getting variable
                        oLogStream.info(' ---> Get variable: ' + sVarKey + ' ... OK')
                        # -------------------------------------------------------------------------------------

                else:
                    # -------------------------------------------------------------------------------------
                    # Exit variable key not in workspace
                    Exc.getExc(' ---> Get variable: ' + sVarKey + ' ... FAILED! File not correctly open!', 2, 1)
                    oVarWS[sVarKey] = None
                    # -------------------------------------------------------------------------------------

            else:
                # -------------------------------------------------------------------------------------
                # Exit variable key not in workspace
                Exc.getExc(' ---> Get variable: ' + sVarKey +
                           ' ... FAILED! Variable is not in declared workspace!', 2, 1)
                oVarWS[sVarKey] = None
                # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Return workspace
        return oVarWS
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
