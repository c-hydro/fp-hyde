"""
Library Features:

Name:          cpl_data_variables_wrf
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180717'
Version:       '1.0.0'
"""
#################################################################################
# Library
import logging
import inspect

from six import string_types
from numpy import append, unique

import src.hyde.dataset.nwp.wrf.lib_wrf_variables as oVarMethods

from src.common.utils.lib_utils_op_list import convertList2Str, mergeList
from src.common.utils.lib_utils_op_dict import mergeDict
from src.common.default.lib_default_args import sLoggerName
from src.hyde.driver.configuration.generic.drv_configuration_debug import Exc

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
        self.oVarComp = self.__selectVarComponent(kwargs['component'])
        self.oVarFx = self.__selectVarMethod(kwargs['method'])
        self.oVarData, self.oVarAttr, self.oVarParams, self.oVarTimes = self.__selectVarData(kwargs['data'])

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to select data
    def __selectVarData(self, oVarRaw):
        oVarData = {}
        oVarAttr = {}
        oVarParams = {}
        oVarTimes = {}
        for iVarKey, sVarName in self.oVarComp.items():
            oVarData[iVarKey] = oVarRaw[sVarName]['values']
            oVarAttr[iVarKey] = oVarRaw[sVarName]['attributes']
            oVarParams[iVarKey] = oVarRaw[sVarName]['parameters']
            oVarTimes[iVarKey] = oVarRaw[sVarName]['times']
        return oVarData, oVarAttr, oVarParams, oVarTimes
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to select component(s)
    @staticmethod
    def __selectVarComponent(oVarComp):
        oDictComp = {}
        for iVarComp, sVarComp in enumerate(oVarComp):
            oDictComp[iVarComp] = sVarComp
        return oDictComp
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to select computing function
    @staticmethod
    def __selectVarMethod(sVarMethod):
        if hasattr(oVarMethods, sVarMethod):
            oVarFx = getattr(oVarMethods, sVarMethod)
        else:
            oVarFx = None
        return oVarFx
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute variable attributes
    def __computeVarAttrs(self):

        oVarAttrSplit = mergeDict(self.oVarAttr, self.oVarParams)

        oVarAttrMerge = DataObj()
        for iVarKey, oVarAttr in oVarAttrSplit.items():
            for sAttrKey, oAttrValue in oVarAttr.items():

                if sAttrKey not in oVarAttrMerge:

                    oAttrValue_Upd = oAttrValue
                    oVarAttrMerge[sAttrKey] = oAttrValue_Upd

                elif sAttrKey in oVarAttrMerge:

                    if oVarAttrMerge[sAttrKey]:
                        if isinstance(oVarAttrMerge[sAttrKey], dict):

                            oAttrValue_Upd = mergeDict(oVarAttrMerge[sAttrKey], oAttrValue)

                        elif isinstance(oVarAttrMerge[sAttrKey], list):

                            #oAttrValue_1 = convertList2Str(oVarAttrMerge[sAttrKey])
                            oAttrValue_1 = oVarAttrMerge[sAttrKey]
                            oAttrValue_2 = oAttrValue
                            oAttrValue_Upd = mergeList(oAttrValue_1, oAttrValue_2)

                        elif isinstance(oVarAttrMerge[sAttrKey], (int, float, complex)):

                            a1dAttrValue = oVarAttrMerge[sAttrKey]
                            oAttrValue_Upd = unique(append(a1dAttrValue, oAttrValue))
                            if oAttrValue_Upd.__len__() == 1:
                                oAttrValue_Upd = oAttrValue_Upd[0]

                        elif isinstance(oVarAttrMerge[sAttrKey], string_types):

                            oAttrValue_Upd = mergeList(oVarAttrMerge[sAttrKey], oAttrValue)
                            if oAttrValue_Upd.__len__() == 1:
                                oAttrValue_Upd = oAttrValue_Upd[0]

                        else:
                            oAttrValue_Upd = None
                    else:
                        oAttrValue_Upd = None

                    oVarAttrMerge[sAttrKey] = oAttrValue_Upd

        return oVarAttrMerge
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute variable time(s)
    def __computeVarTimes(self, iVarIndex_Start, iVarIndex_End, sVarType='istantaneous'):

        oVarTimesMerge = []
        for iTimeKey, oTimeValue in self.oVarTimes.items():

            if not oVarTimesMerge:
                oVarTimesMerge = oTimeValue
            else:
                oVarTimesMerge = mergeList(oVarTimesMerge, oTimeValue)

        oVarTimesMerge = oVarTimesMerge[iVarIndex_Start: iVarIndex_End]

        if sVarType == 'istantaneous':
            oVarTimesMerge = oVarTimesMerge
        elif sVarType == 'accumulated':
            oVarTimesMerge = oVarTimesMerge[1:]
        else:
            raise NotImplementedError('Type variable is not correctly defined')

        return oVarTimesMerge
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute variable data
    def computeVarData(self, **kwargs):

        # Parser method argument(s)
        if 'type' in kwargs:
            sVarType = kwargs['type']
        else:
            sVarType = None
        if 'index_start' in kwargs:
            iVarIndex_Start = kwargs['index_start']
        else:
            iVarIndex_Start = None
        if 'index_end' in kwargs:
            iVarIndex_End = kwargs['index_end']
        else:
            iVarIndex_End = None

        # Check function availability
        if self.oVarFx:

            # Compute variable attributes
            oVarAttrs = self.__computeVarAttrs()
            # Compute variable times
            oVarTimes = self.__computeVarTimes(iVarIndex_Start, iVarIndex_End, sVarType=sVarType)

            # Inspect function to get signature
            oFxSignature = inspect.signature(self.oVarFx)

            # Update signature using value from workspace
            oParamDict = {}
            for iParamID, oParamName in enumerate(oFxSignature.parameters.values()):
                sParamName = oParamName.name
                if iParamID in self.oVarData:
                    oParamDict[sParamName] = self.oVarData[iParamID]
                else:
                    oParamDict[sParamName] = oParamName.default
            if isinstance(oVarAttrs['units'], list):
                oParamDict['oVarUnits'] = oVarAttrs['units']
            else:
                oParamDict['oVarUnits'] = [oVarAttrs['units']]
            oParamDict['oVarType'] = [sVarType]
            oParamDict['iVarIdxStart'] = iVarIndex_Start
            oParamDict['iVarIdxEnd'] = iVarIndex_End

            # Call function with mutable argument(s)
            oVarResults = self.oVarFx(**oParamDict)

        else:
            oVarResults = None
            oVarAttrs = None
            oVarTimes = None

        return oVarResults, oVarTimes, oVarAttrs
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
