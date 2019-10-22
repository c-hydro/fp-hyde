"""
Library Features:

Name:          cpl_data_variables_lami_2i
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20181203'
Version:       '1.0.0'
"""
#################################################################################
# Library
import logging
import inspect

from six import string_types
from numpy import append, unique

import src.hyde.dataset.nwp.lami.lib_lami_2i_variables as oVarMethods

from src.common.utils.lib_utils_op_list import convertList2Str, mergeList
from src.common.utils.lib_utils_op_dict import mergeDict
from src.common.default.lib_default_args import sLoggerName

from src.hyde.dataset.nwp.lami.lib_lami_2i_time import computeTime

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

                    oVarAttrMerge[sAttrKey] = oAttrValue_Upd

        return oVarAttrMerge
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute variable time(s)
    def __computeVarTimes(self):

        iVarIdx_START = None
        iVarIdx_END = None
        oVarTimes_ALL = []
        oVarIdxs_ALL = []
        for iTimeKey, oTimeValue in self.oVarTimes.items():

            oVarTimes, oVarIdxs = computeTime(oTimeValue)

            if not oVarTimes_ALL:
                oVarTimes_ALL = oVarTimes

            if set(oVarTimes_ALL) != set(oVarTimes):
                oVarTimes_ALL = mergeList(oVarTimes_ALL, oVarTimes)
                oVarTimes_MISSED = list(set(oVarTimes_ALL) - set(oVarTimes))

                for sVarTime_MISSED in oVarTimes_MISSED:
                    oVarTimes_ALL.remove(sVarTime_MISSED)

            if not oVarIdxs_ALL:
                oVarIdxs_ALL = oVarIdxs

            if set(oVarIdxs_ALL) != set(oVarIdxs):
                oVarIdxs_ALL = mergeList(oVarIdxs_ALL, oVarIdxs)
                oVarIdxs_MISSED = list(set(oVarIdxs_ALL) - set(oVarIdxs))

                for sVarIdx_MISSED in oVarIdxs_MISSED:
                    oVarIdxs_ALL.remove(sVarIdx_MISSED)

        if oVarIdxs_ALL:
            iVarIdx_START = oVarIdxs_ALL[0]
            iVarIdx_END = oVarIdxs_ALL[-1]

        return oVarTimes_ALL, iVarIdx_START, iVarIdx_END
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute variable data
    def computeVarData(self, **kwargs):

        # Parser method argument(s)
        if 'type' in kwargs:
            sVarType = kwargs['type']
        else:
            sVarType = None

        # Check function availability
        if self.oVarFx:

            # Compute variable attributes
            oVarAttrs = self.__computeVarAttrs()
            # Compute variable times
            oVarTimes, iVarIndex_Start, iVarIndex_End = self.__computeVarTimes()

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
