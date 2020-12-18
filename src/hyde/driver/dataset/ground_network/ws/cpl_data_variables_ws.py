"""
Library Features:

Name:          cpl_data_variables_ws
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180918'
Version:       '1.0.0'
"""
#################################################################################
# Library
import logging
import inspect

import src.hyde.dataset.ground_network.ws.lib_ws_variables as oVarMethods
from src.common.analysis.lib_analysis_interpolation_ancillary import filterData_ValidRange

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
#################################################################################


# -------------------------------------------------------------------------------------
# Class data object
class DataObj(dict):
    pass
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class to compute data variable
class DataVariables:

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, **kwargs):

        self.sVarTime = kwargs['time']
        self.oVarName = kwargs['var']
        self.a1dVarData = kwargs['data']
        self.a1dVarGeoX = kwargs['x']
        self.a1dVarGeoY = kwargs['y']
        self.a1dVarGeoZ = kwargs['z']

        self.oGeoData = kwargs['geo']
        self.oAncillaryData = kwargs['ancillary']

        self.oVarFx, self.sVarMethod = self.__selectVarMethod(kwargs['method'])
        self.oVarParams = self.__linkVarAttrs(kwargs['params'])

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to select computing function
    @staticmethod
    def __selectVarMethod(sVarMethod):
        if hasattr(oVarMethods, sVarMethod):
            oVarFx = getattr(oVarMethods, sVarMethod)
        else:
            oVarFx = None
        return oVarFx, sVarMethod
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute variable attributes
    @staticmethod
    def __linkVarAttrs(oVarParams_RAW):

        oVarParams_LINK = {}
        if 'interp_nodata' in oVarParams_RAW.keys():
            oVarParams_LINK['dInterpNoData'] = oVarParams_RAW['interp_nodata']
        if 'interp_method' in oVarParams_RAW.keys():
            oVarParams_LINK['sInterpMethod'] = oVarParams_RAW['interp_method']
        if 'interp_radius_x' in oVarParams_RAW.keys():
            oVarParams_LINK['dInterpRadiusX'] = oVarParams_RAW['interp_radius_x']
        if 'interp_radius_y' in oVarParams_RAW.keys():
            oVarParams_LINK['dInterpRadiusY'] = oVarParams_RAW['interp_radius_y']
        if 'regression_radius_influence' in oVarParams_RAW.keys():
            oVarParams_LINK['dInterRadiusInfluence'] = oVarParams_RAW['regression_radius_influence']

        return oVarParams_LINK
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute variable data
    def computeVarData(self, **kwargs):

        # -------------------------------------------------------------------------------------
        # Info about algorithm starting
        sVarMethod = self.sVarMethod
        sVarList = ','.join(self.oVarName)
        oLogStream.info(' -----> Set method: ' + sVarMethod + ' - Outcome variable(s): ' + sVarList + ' ... ')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Parser method argument(s)
        if 'valid_range' in kwargs:
            oVarValidRange = kwargs['valid_range']
        else:
            oVarValidRange = None
        if 'missing_value' in kwargs:
            dVarMissValue = kwargs['missing_value']
        else:
            dVarMissValue = -9999.0
        if 'fill_value' in kwargs:
            dVarFillValue = kwargs['fill_value']
        else:
            dVarFillValue = -9999.0
        if 'units' in kwargs:
            sVarUnits = kwargs['units']
        else:
            sVarUnits = None
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Check function availability
        if self.oVarFx:

            # -------------------------------------------------------------------------------------
            # Compute variable parameter(s)
            oVarParams = self.oVarParams
            # Get ancillary data (predictors for snow multivariate regression)
            oAncillaryData = self.oAncillaryData

            # Get variable data (filtered using a valid range)
            a1dVarValue_FILTER, a1dVarGeoX_FILTER, a1dVarGeoY_FILTER, a1dVarGeoZ_FILTER = filterData_ValidRange(
                self.a1dVarData,
                self.a1dVarGeoX, self.a1dVarGeoY, self.a1dVarGeoZ,
                oVarValidRange)

            # Get geographical data
            a2dDomainGeoZ = self.oGeoData.a2dGeoData
            a2dDomainGeoX = self.oGeoData.a2dGeoX
            a2dDomainGeoY = self.oGeoData.a2dGeoY
            dDomainCellSizeX = self.oGeoData.dGeoXStep
            dDomainCellSizeY = self.oGeoData.dGeoXStep
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Check data availability on domain
            if (a1dVarValue_FILTER is not None) and (a1dVarGeoX_FILTER is not None) and (a1dVarGeoX_FILTER is not None):

                # -------------------------------------------------------------------------------------
                # Inspect function to get signature
                oFxSignature = inspect.signature(self.oVarFx)

                # Prepare data to apply variable computing method
                oDataFx = {'a1dVarData': a1dVarValue_FILTER,
                           'a1dVarGeoX': a1dVarGeoX_FILTER, 'a1dVarGeoY': a1dVarGeoY_FILTER,
                           'a1dVarGeoZ': a1dVarGeoZ_FILTER,
                           'sVarUnits': sVarUnits, 'dVarMissValue': dVarMissValue, 'dVarFillValue': dVarFillValue,
                           'a2dDomainGeoX': a2dDomainGeoX, 'a2dDomainGeoY': a2dDomainGeoY, 'a2dDomainGeoZ': a2dDomainGeoZ,
                           'dDomainGeoCellSizeX': dDomainCellSizeX, 'dDomainGeoCellSizeY': dDomainCellSizeY,
                           'oAncillaryData': oAncillaryData,
                           }

                # Update signature using data from algorithm (parameters link to interpolation method)
                for iAlgParamID, oAlgParamName in enumerate(oFxSignature.parameters.values()):
                    sAlgParamName = oAlgParamName.name
                    if sAlgParamName in oVarParams.keys():
                        oDataFx[sAlgParamName] = oVarParams[sAlgParamName]
                    else:
                        if sAlgParamName not in oDataFx:
                            oDataFx[sAlgParamName] = oAlgParamName.default

                # Remove keys not included in function signature
                oDataRemove = dict(oDataFx)
                for sDataKey in oDataRemove.keys():
                    if sDataKey not in oFxSignature.parameters.keys():
                        oDataFx.pop(sDataKey, None)

                # Call function with mutable argument(s)
                oVarResults = self.oVarFx(**oDataFx)
                # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Save results in a dictionary (with variable name as a key)
                oVarDict = {}
                if self.oVarName.__len__() > 1:
                    for sVarName, oVarData in zip(self.oVarName, oVarResults):
                        oVarDict[sVarName] = oVarData
                elif self.oVarName.__len__() == 1:
                    sVarName = self.oVarName[0]
                    oVarDict[sVarName] = oVarResults

                # Info about algorithm ending
                oLogStream.info(' -----> Set method: ' + sVarMethod + ' - Outcome variable(s): ' + sVarList + ' ... OK')
                # -------------------------------------------------------------------------------------
            else:
                # -------------------------------------------------------------------------------------
                # Exit due to all data are null over domain
                Exc.getExc(' =====> WARNING: variable source data are null. Check your data!.', 2, 1)
                oLogStream.info(
                    ' -----> Set method: ' + sVarMethod + ' - Outcome variable(s): ' + sVarList + ' ... FAILED')
                oLogStream.info(' -----> Outcome variable(s) data are null for time step: ' + self.sVarTime)
                oVarDict = None
                # -------------------------------------------------------------------------------------
        else:
            # -------------------------------------------------------------------------------------
            # Exit with none data
            Exc.getExc(' =====> WARNING: selected method not found and outcome variable(s) are null. '
                       'Check your settings.', 2, 1)
            oLogStream.info(' -----> Set method: ' + sVarMethod + ' - Outcome variable(s): ' + sVarList + ' ... FAILED')
            oLogStream.info(' -----> Outcome variable(s) data are null for time step: ' + self.sVarTime)
            oVarDict = None
            # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Return variable(s) dictionary
        return oVarDict
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
