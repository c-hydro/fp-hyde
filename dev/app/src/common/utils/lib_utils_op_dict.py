"""
Library Features:

Name:          lib_utils_op_dict
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180521'
Version:       '2.0.7'
"""

#######################################################################################
# Library
import logging
import numpy as np
import functools

from operator import getitem

from src.common.utils.lib_utils_op_list import convertList2Dict
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(__name__)

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to prepare dictionary single or multiple keys (in list format)
def prepareDictKey(ob_keys, sep_keys=''):
    try:
        if isinstance(ob_keys, str):
            if sep_keys:
                dict_keys = ob_keys.split(sep_keys)
            else:
                dict_keys = [ob_keys]
            return dict_keys
        elif isinstance(ob_keys, list):
            dict_keys = ob_keys
            return dict_keys
        else:
            Exc.getExc(' =====> ERROR: keys format unknown!', 1, 1)
    except BaseException:
        return None
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get values into dictionary using single or multiple keys (in list format)
def lookupDictKey(dic, key, *keys):
    try:
        if keys:
            return lookupDictKey(dic.get(key, {}), *keys)
        return dic.get(key)
    except BaseException:
        Exc.getExc(' =====> WARNING: impossible to get dictionary value using selected keys!', 2, 1)
        return None
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Delete key(s) from dictionary
def removeDictKey(d, keys):

    if isinstance(keys, list):
        r = dict(d)
        for key in keys:
            if key in d:
                del r[key]
            else:
                pass
        return r
    else:
        Exc.getExc(' =====> WARNING: keys values must be included in a list!', 2, 1)
        return d
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get recursively dictionary value
def getDictDeep(d, key, value=None):

    for k, v in iter(d.items()):
        if isinstance(v, dict):
            value = getDictDeep(v, key, value)
        else:
            if k == key:
                value = v
    return value
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set value in nested dictionary
def setDictValue(dataDict, mapList, val):
    """Set item in nested dictionary"""
    functools.reduce(getitem, mapList[:-1], dataDict)[mapList[-1]] = val
    return dataDict
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to update recursively dictionary value
def updateDictValue(d, tag, value):
    for k, v in iter(d.items()):
        if isinstance(v, dict):
            v = updateDictValue(v, tag, value)
        else:
            try:
                if tag in v:
                    upd = v.replace(tag, str(value))
                    d[k] = upd

            except BaseException:
                pass
    return d
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Get dictionary index using a selected key
def getDictIndex(dictionary=None, keyname=None):
    if dictionary and keyname:
        dict_keys = dictionary.keys()
        key_index = dict_keys.index(keyname)
    else:
        key_index= None
    return key_index
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Get selected index tuple from dictionary
def getDictTuple(dictionary=None, index=-1):    # considering development using scalar and array
    dict_sel = {}
    if dictionary and index >= 0:
        dict_tuple = dictionary.items()[index]
        dict_sel[dict_tuple[0]] = dict_tuple[1]
    else:
        dict_sel = None
    return dict_sel
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get value from dictionary (using a list)
def getDictValue(dataDict, mapList, pflag=1):
    try:
        return functools.reduce(lambda d, k: d[k], mapList, dataDict)
    except BaseException:
        if pflag == 1:
            Exc.getExc(' =====> WARNING: impossible to get dictionary value using selected keys!', 2, 1)
        else:
            pass
        return None
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to update recursively dictionary value
def getDictValues(d, key, value=[]):

    for k, v in iter(d.items()):

        if isinstance(v, dict):
            if k == key:

                for kk, vv in iter(v.items()):
                    temp = [kk, vv]
                    value.append(temp)

            else:
                vf = getDictValues(v, key, value)

                if isinstance(vf, list):
                    if vf:
                        vf_end = vf[0]
                    else:
                        vf_end = None

                elif isinstance(vf, np.ndarray):
                    vf_end = vf.tolist()
                else:
                    vf_end = vf

                if vf_end not in value:
                    if vf_end:

                        if isinstance(value, list):
                            value.append(vf_end)
                        elif isinstance(value, str):
                            value = [value, vf_end]

                    else:
                        pass
                else:
                    pass

        else:
            if k == key:

                if isinstance(v, np.ndarray):
                    value = v
                else:
                    value = v
    return value
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to join 2 dictionaries
def joinDict(oDictA=None, oDictB=None):
    if oDictA and oDictB:
        from copy import deepcopy
        oDictAB = deepcopy(oDictA)
        oDictAB.update(oDictB)
    else:
        oDictAB = None
    return oDictAB
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to merge dictionaries
def mergeDict(d1, d2):

    dd = {}
    for d in (d1, d2):  # you can list as many input dicts as you want here
        for key, value in iter(d.items()):
            dd[key] = value

    return dd
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to check dictionary keys (True or False)
def checkDictKeys(a1oVarCheck={'VarDefault': False}, sVarTag='variable(s)'):

    # Check variable input type
    if isinstance(a1oVarCheck, list):
        a1oVarCheck = convertList2Dict(a1oVarCheck)
    else:
        pass

    # Count number of true and false
    iVarF = list(a1oVarCheck.values()).count(False)
    iVarT = list(a1oVarCheck.values()).count(True)
    # Length of Data
    iVarLen = a1oVarCheck.__len__()

    # Compute variable percentage
    if iVarF == 0:
        dDictPerc = 100.0
    elif iVarT == 0:
        dDictPerc = 0.0
    else:
        dDictPerc = float(iVarT)/float(iVarLen)

    # Check variable(s) availability
    if iVarT > 0:
        iDictCheck = True
    else:
        iDictCheck = False

    # Select exit message(s) for variable(s) not defined
    if a1oVarCheck.__len__() != iVarF and iVarF > 0:
        a1oVarKeyNF = []
        for oVarKey, bVarValue in iter(a1oVarCheck.items()):
            if bVarValue is False:

                if isinstance(oVarKey, str):
                    a1oVarKeyNF.append(oVarKey)
                else:
                    a1oVarKeyNF.append(str(oVarKey))
            else:
                pass
        # Exit message if some variable(s) are not available
        a1sVarKeyNF = ', '.join(a1oVarKeyNF)
        Exc.getExc(' =====> WARNING: ' + sVarTag + ' ' + a1sVarKeyNF + ' not defined in given dictionary!', 2, 1)
    elif a1oVarCheck.__len__() == iVarF and iVarF > 0:
        # Exit message if all variable(s) are not available
        Exc.getExc(' =====> WARNING: all ' + sVarTag + ' not defined in given dictionary!', 2, 1)
    else:
        pass

    return iDictCheck, dDictPerc
# -------------------------------------------------------------------------------------
