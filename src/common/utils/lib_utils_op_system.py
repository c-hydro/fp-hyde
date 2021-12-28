"""
Library Features:

Name:          lib_utils_op_system
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180521'
Version:       '2.0.7'
"""

#######################################################################################
# Library
import logging
import datetime
import tempfile
import os

from os import remove
from os.path import exists
from shutil import copy2, rmtree
from random import randint

# Logging
log_stream = logging.getLogger(__name__)

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to remove empty folders recursively
def removeEmptyFolders(path, removeRoot=True):
    if not os.path.isdir(path):
        return

    # remove empty subfolders
    files = os.listdir(path)
    if len(files):
        for f in files:
            fullpath = os.path.join(path, f)
            if os.path.isdir(fullpath):
                removeEmptyFolders(fullpath)

    # if folder empty, delete it
    files = os.listdir(path)
    if len(files) == 0 and removeRoot:
        os.rmdir(path)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to copy file from source to destination
def copyFile(sFileSource, sFileDestination):
    if exists(sFileSource):
        if not sFileSource == sFileDestination:
            if exists(sFileDestination):
                remove(sFileDestination)
            copy2(sFileSource, sFileDestination)
        else:
            pass
    else:
        pass
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to create temporary folder
def createTemp(sPathTemp=None, iMethodTemp=1):

    # -------------------------------------------------------------------------------------
    # Check for undefined temporary folder string
    if sPathTemp is None:
        iMethodTemp = 2
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Define temporary folder method
    if iMethodTemp == 1:

        # -------------------------------------------------------------------------------------
        # Create temporary folder to copy file from source (to manage multiprocess request)
        sRN1 = str(randint(0, 1000))
        sRN2 = str(randint(1001, 5000))
        oTimeTemp = datetime.datetime.now()
        sTimeTemp = oTimeTemp.strftime('%Y%m%d-%H%M%S_%f')
        sFolderTemp = sTimeTemp.lower() + '_' + sRN1.lower() + '_' + sRN2.lower()
        # -------------------------------------------------------------------------------------
    elif iMethodTemp == 2:
        # -------------------------------------------------------------------------------------
        # Create temporary folder in a system temp folder
        sFolderTemp = tempfile.mkdtemp()
        # -------------------------------------------------------------------------------------
    else:
        # -------------------------------------------------------------------------------------
        # Exit with warning (method unknown)
        log_stream.warning(' =====> WARNING: invalid choice for temporary folder method!')
        sFolderTemp = None
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Return temporary folder
    return sFolderTemp
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to create folder by filename
def createFolderByFile(sFilePath):

    from os import makedirs
    from os.path import dirname, exists

    sFileFolder = dirname(sFilePath)
    if not exists(sFileFolder):
        makedirs(sFileFolder)
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to create folder (and check if folder exists)
def createFolder(sPathName=None, sPathDelimiter=None):

    from os import makedirs
    from os.path import exists

    if sPathName:
        if sPathDelimiter:
            sPathNameSel = sPathName.split(sPathDelimiter)[0]
        else:
            sPathNameSel = sPathName

        if not exists(sPathNameSel):
            makedirs(sPathNameSel)
        else:
            pass
    else:
        pass
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to delete folder (and check if folder exists)
def deleteFolder(sPathName):
    # Check folder status
    if exists(sPathName):
        # Remove folder (file only-read too)
        rmtree(sPathName, ignore_errors=True)
    else:
        pass
# -------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to define dynamic folder name
def defineFolder(sFolderName=None, oFolderTags=None):

    if sFolderName:
        if not oFolderTags:
            pass
        elif oFolderTags:
            for sKey, sValue in oFolderTags.items():
                sFolderName = sFolderName.replace(sKey, sValue)
    else:
        pass

    return sFolderName

# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to define check file availability name
def checkFileName(sFileName):

    from os.path import isfile

    if isfile(sFileName):
        bFileAvailability = True
    else:
        bFileAvailability = False

    return bFileAvailability
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to define dynamic filename
def defineFileName(sFileName='', oFileNameDict=None):
    if sFileName != '':
        if not oFileNameDict:
            pass
        elif oFileNameDict:
            for sKey, sValue in oFileNameDict.items():
                sFileName = sFileName.replace(sKey, sValue)
    else:
        pass

    return sFileName

# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
#  Method to define file extension
def defineFileExt(sFileName=None):

    from os.path import splitext
    if sFileName:
        try:
            [sFileRoot, sFileExt] = splitext(sFileName)
        except:
            sFileRoot = splitext(sFileName)
            sFileExt = None

        sFileExt = sFileExt.replace('.', '')
    else:
        sFileExt = None

    return sFileExt
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to delete file
def deleteFileName(sFileName=None):

    from os import remove
    from os.path import exists

    if sFileName:
        # Delete file if exists
        if exists(sFileName):
            remove(sFileName)
        else:
            pass
    else:
        pass
# --------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to get regular expression from file
def getFileNameRegExp(a1oFileName, oFilePattern=r'\d{4}\d{2}\d{2}\d{2}\d{2}', oFileFilter=r'[^a-zA-Z0-9-]'):

    import re

    # Cycle(s) on filename(s)
    a1sRegExp = []
    for sFileName in a1oFileName:

        # Match date in filename(s)
        oMatch_Pattern = re.search(oFilePattern, sFileName)

        # Get date of filename(s)
        oMatch_Filter = re.compile(oFileFilter)
        sRegExp = oMatch_Pattern.group()
        sRegExp = oMatch_Filter.sub("", sRegExp)
        a1sRegExp.append(sRegExp)

    return a1sRegExp
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to create filename patterns
def createFileNamePattern(sFileName, oFileTags={}):
    for sFileKey, sFileTag in oFileTags.iteritems():
        sFileName_Upd = sFileName.replace(sFileKey, sFileTag)
    return sFileName_Upd

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to select files in a given folder
def selectFileName(sPathName='', sFilePattern=None):
    from os.path import join, isfile

    if not sFilePattern:
        from os import listdir
        a1sFileName = [sFileName for sFileName in listdir(sPathName) if isfile(join(sPathName, sFileName))]
    else:
        import glob
        a1sFileName = glob.glob(join(sPathName, sFilePattern))
    return a1sFileName

# -------------------------------------------------------------------------------------
