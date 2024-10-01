"""
Library Features:

Name:          lib_logging
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190131'
Version:       '2.0.8'
"""

#######################################################################################
# Library
import logging
import logging.config
# import progressbar
import glob

from os.path import exists, split, join
from os import remove, rename

from src.common.default.lib_default_args import sLoggerName as sLoggerName_Default
from src.common.default.lib_default_args import sLoggerFile as sLoggerFile_Default
from src.common.default.lib_default_args import sLoggerHandle as sLoggerHandle_Default
from src.common.default.lib_default_args import sLoggerFormatter as sLoggerFormatter_Default

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to set logging file
def setLoggingFile(sLoggerFile=sLoggerFile_Default, sLoggerName=sLoggerName_Default,
                   sLoggerHandle=sLoggerHandle_Default, sLoggerFormatter=sLoggerFormatter_Default,
                   bLoggerHistory=False, iLoggerHistory=12):

    # Set to flush progressbar output in logging stream handle
    # progressbar.streams.wrap_stderr()

    # Save old logger file (to check run in the past)
    if bLoggerHistory:
        saveLoggingFile(sLoggerFile, iLoggerMax=iLoggerHistory)

    # Remove old logging file
    if exists(sLoggerFile):
        remove(sLoggerFile)

    # Open logger
    oLoggerStream = logging.getLogger(sLoggerName)
    oLoggerStream.setLevel(logging.DEBUG)

    # Set logger handle
    if sLoggerHandle == 'file':
        oLogHandle_1 = logging.FileHandler(sLoggerFile, 'w')
        oLogHandle_2 = logging.StreamHandler()

        # Set logger level
        oLogHandle_1.setLevel(logging.DEBUG)
        oLogHandle_2.setLevel(logging.DEBUG)

        # Set logger formatter
        oLogFormatter = logging.Formatter(sLoggerFormatter)
        oLogHandle_1.setFormatter(oLogFormatter)
        oLogHandle_2.setFormatter(oLogFormatter)

        # Add handle to logger
        oLoggerStream.addHandler(oLogHandle_1)
        oLoggerStream.addHandler(oLogHandle_2)

    elif sLoggerHandle == 'stream':
        oLogHandle = logging.StreamHandler()

        # Set logger level
        oLogHandle.setLevel(logging.DEBUG)

        # Set logger formatter
        oLogFormatter = logging.Formatter(sLoggerFormatter)
        oLogHandle.setFormatter(oLogFormatter)

        # Add handle to logger
        oLoggerStream.addHandler(oLogHandle)

    else:

        oLogHandle = logging.NullHandler()
        # Add handle to logger
        oLoggerStream.addHandler(oLogHandle)

    # Return logger stream
    return oLoggerStream

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to save logging file (to save execution history)
def saveLoggingFile(sLoggerFile, sLoggerExt='.old.{}', iLoggerMax=12):
    # Get logger folder
    sLoggerFolder = split(sLoggerFile)[0]
    # Iterate to store old logging file
    if exists(sLoggerFile):
        sLoggerFile_LOOP = sLoggerFile
        iLoggerID = 0
        while exists(sLoggerFile_LOOP):
            iLoggerID = iLoggerID + 1
            sLoggerFile_LOOP = sLoggerFile + sLoggerExt.format(iLoggerID)

            if iLoggerID > iLoggerMax:
                oLoggerOld = glob.glob(join(sLoggerFolder, '*'))
                for sLoggerOld in oLoggerOld:
                    if sLoggerOld.startswith(sLoggerFile):
                        remove(sLoggerOld)
                sLoggerFile_LOOP = sLoggerFile
                break

        if sLoggerFile_LOOP:
            if sLoggerFile != sLoggerFile_LOOP:
                rename(sLoggerFile, sLoggerFile_LOOP)
# -------------------------------------------------------------------------------------
