"""
Library Features:

Name:          lib_utils_op_list
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190117'
Version:       '2.0.8'
"""

#######################################################################################
# Library
import logging
import collections
import re

from collections import Iterable
from copy import deepcopy
from numpy import where, asarray
from itertools import groupby

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to sort list in natural way
def sortListNatural(l):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key=alphanum_key)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to flat list elements
def flatList(items):
    """Yield items from any nested iterable; see Reference."""
    for x in items:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            for sub_x in flatList(x):
                yield sub_x
        else:
            yield x
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to reduce list elements
def reduceList(oList_WS_ALL):
    
    oList_ORDERED = sorted(oList_WS_ALL)
    
    oList_WS_ORDERED= collections.OrderedDict()
    for sList_ORDERED in oList_ORDERED:
        oListPair= oList_WS_ALL[sList_ORDERED]
        oList_WS_ORDERED[sList_ORDERED] = oListPair
    
    
    oList_IDX = []
    for iList_ID, (sList_KEY, oList_VALUE) in enumerate(oList_WS_ORDERED.items()):

        oList_UNIQUE = []
        for sList_VALUE in oList_VALUE:
            if sList_VALUE not in oList_UNIQUE:
                oList_UNIQUE.append(sList_VALUE)
        if oList_UNIQUE:
            oList_BOTH = set(oList_VALUE).intersection(oList_UNIQUE)
            oList_IDX.extend([oList_VALUE.index(iI) for iI in oList_BOTH])

    oList_WS_RED = []
    if oList_IDX:
        a1iList_IDX = asarray(list(set(oList_IDX)), dtype=int)

        oList_WS_RED = collections.OrderedDict()
        for iList_ID, (sList_KEY, oList_VALUE) in enumerate(oList_WS_ORDERED.items()):
            oList_SEL = [oList_VALUE[iList_IDX] for iList_IDX in a1iList_IDX]

            oList_WS_RED[sList_KEY] = oList_SEL

    return oList_WS_RED
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to convert list 2 dicitonary
def convertList2Dict(var_list, var_fill=None, var_split={'split': False, 'chunk': 2, 'key': 0}):

    var_dict = {}
    for step, var in enumerate(var_list):

        if var_split['split'] is True:

            var_splitted = [var[i:i + var_split['chunk']] for i in range(0, len(var), var_split['chunk'])][0]

            var_keys = deepcopy(var_splitted)
            var_values = deepcopy(var_splitted)
            var_index = int(var_split['key'])
            var_key = var_keys[var_index]
            var_values.pop(var_index)

            var_dict[var_key] = var_values[0]

        else:
            if var_fill is not None:
                var_dict[var_fill] = var
            else:
                var_dict[step] = var

    return var_dict
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to find element indexing
def findIndexElement(main_list, elements=None):
    idx_tot = []
    if main_list and elements is not None:

        if isinstance(elements, str):
            elements = [elements]

        for element in elements:
            if element in main_list:
                idx = main_list.index(element)
                idx_tot.append(idx)
            else:
                idx_tot.append(None)
    return idx_tot
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get list element(s) using indexes
def getListElement(main_list=[], indexes=None):

    if main_list and indexes is not None:
        sel_list = [main_list[x] for x in indexes]
    else:
        sel_list = None
    return sel_list
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to enumerate list boolean element(s) [True/False]
def enumListBool(oList=[True]):
    if oList:
        oElem = asarray(oList)
        oElemT = where(oElem == True)[0]
        oElemF = where(oElem == False)[0]
    else:
        oElemT = None
        oElemF = None
    return oElemT, oElemF
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to check if list element(s) are all the same
def checkListAllSame(items=False):
    if items:
        items_check = all(x == items[0] for x in items)
    else:
        items_check = False
    return items_check
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to reduce list unique value(s)
def reduceListUnique(oList=[]):
    return list(set(oList))
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to convert list to string (given an delimiter)
def convertList2Str(oListData, sListDel=','):
    sListData = sListDel.join(str(oL) for oL in oListData)
    return sListData
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to filter list empty element ("")
def filterListEmpty(oListData):
    return list(filter(None, oListData))
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to merge two lists
def mergeList(oList1, oList2):

    if not isinstance(oList1, list):
        oList1 = [oList1]
    if not isinstance(oList2, list):
        oList2 = [oList2]

    oSet1 = set(oList1)
    oSet2 = set(oList2)

    oSetDiff = oSet2 - oSet1

    oListMerge = oList1 + list(oSetDiff)

    return oListMerge
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to enumerate list element frequency
def countListElemFreq(oList):
    return [len(list(oGroup)) for oKey, oGroup in groupby(oList)]
# -------------------------------------------------------------------------------------
