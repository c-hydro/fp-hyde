"""
Library Features:

Name:          lib_utils_apps_zip
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190913'
Version:       '2.1.0'
"""

#################################################################################
# Library
import logging
import os

from os.path import isfile

# Logging
log_stream = logging.getLogger(__name__)
#################################################################################

# --------------------------------------------------------------------------------
# Zip format dictionary
oZipDict = dict(Type_1='gz', Type_2='bz2', Type_3='7z', Type_4='tar',
                Type_5='tar.gz', Type_6='tar.7z', Type_7='zip')
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to delete FileName unzip
def deleteFileUnzip(sFileName_UNZIP, bFileName_DEL=False):
    if bFileName_DEL is True:
        if isfile(sFileName_UNZIP):
            os.remove(sFileName_UNZIP)
        else:
            pass
    else:
        pass
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to delete FileName zip
def deleteFileZip(sFileName_ZIP, bFileName_DEL=False):
    if bFileName_DEL is True:
        if isfile(sFileName_ZIP):
            os.remove(sFileName_ZIP)
        else:
            pass
    else:
        pass
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to check if a file has zip extension
def checkFileZip(sFileName_IN, sZipExt='NoZip'):

    # Define zip extension value (to overwrite None assignment)
    if sZipExt is None:
        sZipExt = 'NoZip'

    # Check if string starts with point
    if sZipExt.startswith('.'):
        sZipExt = sZipExt[1:]
    else:
        pass

    # Check if zip extension is activated
    if not (sZipExt == 'NoZip' or sZipExt == ''):
        # Check zip extension format
        [sZipExt, bZipExt] = checkExtZip(sZipExt)

        if bZipExt:
            if sZipExt in sFileName_IN:
                sFileName_OUT = sFileName_IN
            else:
                sFileName_OUT = sFileName_IN + '.' + sZipExt
        else:
            log_stream.warning(
                " =====> WARNING: sZipExt selected is not known extension! Add in zip dictionary if necessary!")
            sFileName_OUT = sFileName_IN
    else:
        sFileName_OUT = sFileName_IN
    return sFileName_OUT

# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to get zip extension using filename
def getExtZip(sFileName):

    sZipType = None
    bZipType = False
    for sZipDict in oZipDict.values():
        iCharLen = len(sZipDict)
        iFileLen = len(sFileName)

        if sFileName.endswith(sZipDict, (iFileLen - iCharLen), iFileLen):
            sZipType = sZipDict
            bZipType = True
            break

    return sZipType, bZipType
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to check if zip extension is a known string
def checkExtZip(sZipExt):

    # Check if string starts with point
    if sZipExt.startswith('.'):
        sZipExt = sZipExt[1:]
    else:
        pass

    # Check if zip extension is a known string
    if sZipExt in oZipDict.values():
        bZipExt = True
    else:
        bZipExt = False

    return sZipExt, bZipExt

# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to add zip extension to filename
def addExtZip(sFileName_UNZIP, sZipExt=''):

    if sZipExt is None:
        sZipExt = ''

    if sZipExt != '':
        # Remove dot as starting character
        if sZipExt.startswith('.'):
            sZipExt = sZipExt[1:-1]

        # Check zip extension format
        [sZipExt, bZipExt] = checkExtZip(sZipExt)

        # Create zip filename
        if bZipExt is True:
            sFileName_ZIP = ''.join([sFileName_UNZIP, '.', sZipExt])
        elif bZipExt is False:
            log_stream.warning(
                " =====> WARNING: selected zip extension is unknown! Add in zip dictionary if necessary!")
            sFileName_ZIP = ''.join([sFileName_UNZIP, '.', sZipExt])
        else:
            log_stream.error(
                " =====> ERROR: error in selecting zip extension! Check in zip dictionary!")
            raise NotImplemented

    else:
        sFileName_ZIP = sFileName_UNZIP

    return sFileName_ZIP, sZipExt

# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to remove only compressed extension 
def removeExtZip(sFileName_ZIP, sZipExt=''):

    # Check null zip extension
    if sZipExt is None:
        sZipExt = ''

    # Check zip extension format
    if sZipExt is not '':
        # Check zip extension format in selected mode
        [sZipExt, bZipExt] = checkExtZip(sZipExt)
    else:
        # Check zip extension format in default mode
        sFileName_UNZIP, sZipExt = os.path.splitext(sFileName_ZIP)
        # Check zip extension format
        [sZipExt, bZipExt] = checkExtZip(sZipExt)

    # Create zip filename
    if bZipExt is True:
        sFileName_UNZIP = sFileName_ZIP.split(sZipExt)[0]
        if sFileName_UNZIP.endswith('.'):
            sFileName_UNZIP = sFileName_UNZIP[0:-1]
        else:
            pass

    elif bZipExt is False:
        log_stream.warning(
            " =====> WARNING: sZipExt selected is not known extension! Add in zip dictionary if necessary!")
        [sFileName_UNZIP, sZipExt] = os.path.splitext(sFileName_ZIP)
    else:
        log_stream.error(" =====> ERROR: error in selection sZipExt extension! Check in zip dictionary!")
        raise NotImplemented

    return sFileName_UNZIP, sZipExt
# --------------------------------------------------------------------------------
