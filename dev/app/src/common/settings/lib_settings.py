"""
Library Features:

Name:          lib_settings
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180521'
Version:       '1.0.0'
"""

#######################################################################################
# Library
from os import sep
from os.path import join, normpath
from collections import OrderedDict
from copy import deepcopy

from src.common.utils.lib_utils_op_dict import getDictValues

from src.common.default.lib_default_args import sPathDelimiter
from src.common.utils.lib_utils_op_system import createFolder
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to set file path(s)
def setPathFile(oFileValue, oFileKeyDef=None):

    oFileKeyOrder = OrderedDict(sorted(oFileKeyDef.items()))

    oFilePath = {}
    for sFileType, oFileType in oFileValue.items():

        oFilePart = []
        for sKey, sValue in oFileKeyOrder.items():

            oFileExt = getDictValues(oFileType, sValue)

            if oFileExt is not None:
                if not oFilePart:
                    oFilePart = oFileExt
                else:
                    oFilePart = join(oFilePart, oFileExt)

        if not oFilePart:
            oFilePart = None

        oFilePath[sFileType] = oFilePart

    return oFilePath
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get root path(s)
def selectDataSettings(oDataSettings, sPathKey='folder'):
    oDataGet = []
    oDataGet = getDictValues(oDataSettings, sPathKey, value=oDataGet)
    oDataSel = deepcopy(oDataGet)
    return oDataSel
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set root path(s)
def setPathRoot(path_list, path_delimiter='$', path_noise=None):

    for path_raw in path_list:

        if path_delimiter is not None:
            path_select = path_raw.split(path_delimiter)[0]
        else:
            path_select = path_raw

        path_norm = normpath(path_select)
        path_parts_raw = path_norm.split(sep)
        path_parts_chk = ' '.join(path_parts_raw).split()

        path_elements = [sep]
        for path_part in path_parts_chk:
            if path_noise is not None:
                if (path_noise[0] in path_part) or (path_noise[1] in path_part):
                    break
                else:
                    path_elements.append(path_part)
            else:
                path_elements.append(path_part)

        path_root = join(*path_elements)

        createFolder(path_root)

# -------------------------------------------------------------------------------------
