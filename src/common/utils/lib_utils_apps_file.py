"""
Library Features:

Name:          lib_utils_apps_file
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180521'
Version:       '2.0.7'
"""

#######################################################################################
# Library
import logging

from sys import version_info

if version_info >= (3, 0):
    from importlib.machinery import SourceFileLoader
elif version_info < (3, 0):
    from imp import load_source

from os.path import exists, split, join

from src.common.utils.lib_utils_apps_zip import getExtZip, addExtZip, removeExtZip, deleteFileUnzip

from src.common.default.lib_default_args import sLoggerName
from src.common.default.lib_default_args import sZipExt as sZipExt_Default

from src.common.utils.lib_utils_op_system import createFolder, deleteFolder, copyFile, deleteFileName, createTemp

from src.common.driver.dataset.drv_data_io_type import Drv_Data_IO
from src.common.driver.dataset.drv_data_io_zip import Drv_Data_Zip

from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to import file in dictionary format
def importFileDict(sFileName, DataName='Data'):

    if exists(sFileName):
        try:

            if version_info >= (3, 0):
                oFileData = SourceFileLoader(DataName, sFileName).load_module()
            elif version_info < (3, 0):
                oFileData = load_source(DataName, '',  open(sFileName))

            oFileDict = {}
            for sFileVar in vars(oFileData):
                if not sFileVar.startswith('__'):
                    oFileValue = getattr(oFileData, sFileVar)
                    oFileDict[sFileVar] = oFileValue
                else:
                    pass

            bFileData = True
        except BaseException:
            Exc.getExc(' =====> WARNING: read file ' + sFileName + ' FAILED!', 2, 1)
            oFileDict = None
            bFileData = False
    else:
        Exc.getExc(' =====> WARNING: file ' + sFileName + ' NOT FOUND!', 2, 1)
        oFileDict = None
        bFileData = False

    return oFileDict, bFileData
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Select file driver according with file status (existent, zipped or unzipped)
def selectFileDriver(sFileName, sZipExt=None, sFileMode=None):

    # -------------------------------------------------------------------------------------
    # Check zip extension of filename
    bZipExt = getExtZip(sFileName)[1]

    if bZipExt is False:
        if sZipExt is not None:
            sFileZip = addExtZip(sFileName, sZipExt)[0]
            sFileUnzip = sFileName
        else:
            sFileZip = None
            sFileUnzip = sFileName
    else:
        sFileZip = sFileName
        sFileUnzip = removeExtZip(sFileName, sZipExt)[0]
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Check file availability on disk
    oFileDriver = None
    if (not exists(sFileUnzip)) and (not exists(sFileZip)):

        # -------------------------------------------------------------------------------------
        # Open non existent file
        try:
            # Open file in write mode
            if sFileMode is None:
                oFileDriver = Drv_Data_IO(sFileUnzip, 'w').oFileWorkspace
            else:
                oFileDriver = Drv_Data_IO(sFileUnzip, sFileMode).oFileWorkspace
            # Create destination folder (if does not exist)
            createFolder(oFileDriver.sFilePath)

        except BaseException:
            # Exception
            Exc.getExc(' =====> ERROR: driver selection to open file ' +
                       sFileName + ' FAILED! Errors in opening file in write mode!', 1, 1)
        # -------------------------------------------------------------------------------------

    elif (sFileZip is not None) and exists(sFileZip):

        # -------------------------------------------------------------------------------------
        # Unzip and open existent file
        try:
            # Get source file path and name
            sFile_Source = sFileZip

            # Get destination file path and name
            sPathName_Destination = createTemp(None)
            sFileName_Destination = sFileZip
            sFile_Destination = join(sPathName_Destination, sFileName_Destination)

            # Copy file in temporary folder (to manage multiprocess file request)
            copyFile(sFile_Source, sFile_Destination)

            # Open zip driver
            oZipDriver = Drv_Data_Zip(sFile_Destination, 'u', None, sZipExt).oFileWorkspace
            [oFile_ZIP, oFile_UNZIP] = oZipDriver.oFileLibrary.openZip(oZipDriver.sFileName_IN,
                                                                       oZipDriver.sFileName_OUT,
                                                                       oZipDriver.sZipMode)
            oZipDriver.oFileLibrary.unzipFile(oFile_ZIP, oFile_UNZIP)
            oZipDriver.oFileLibrary.closeZip(oFile_ZIP, oFile_UNZIP)

            # Open unzipped file in append mode
            if sFileMode is None:
                oFileDriver = Drv_Data_IO(oZipDriver.sFileName_OUT, 'a').oFileWorkspace
            else:
                oFileDriver = Drv_Data_IO(oZipDriver.sFileName_OUT, sFileMode).oFileWorkspace

        except BaseException:
            # Exception
            Exc.getExc(' =====> ERROR: driver selection to unzip or open file ' +
                       sFileZip + ' FAILED! Errors in unzipping or opening file in append mode!', 1, 1)
        # -------------------------------------------------------------------------------------

    elif (sFileUnzip is not None) and exists(sFileUnzip):

        # -------------------------------------------------------------------------------------
        # Open existent file
        try:
            # Open unzipped file in append mode
            if sFileMode is None:
                oFileDriver = Drv_Data_IO(sFileUnzip, 'a').oFileWorkspace
            else:
                oFileDriver = Drv_Data_IO(sFileUnzip, sFileMode).oFileWorkspace
        except BaseException:
            # Exception
            Exc.getExc(' =====> ERROR: driver selection open file ' +
                       sFileUnzip + ' FAILED! Errors in opening file in append mode!', 1, 1)
        # -------------------------------------------------------------------------------------

    else:
        # -------------------------------------------------------------------------------------
        # Exception
        Exc.getExc(' =====> ERROR: driver selection open file ' +
                   sFileUnzip + ' FAILED! Errors in selecting driver to open file!', 1, 1)
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Return file handling
    return oFileDriver, sFileUnzip, sFileZip
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to zip file data
def zipFileData(sFileName, sFileZipExt=sZipExt_Default):

    oZipDrv = Drv_Data_Zip(sFileName, 'z', None, sFileZipExt).oFileWorkspace
    [oFileZip_IN, oFileZip_OUT] = oZipDrv.oFileLibrary.openZip(
        oZipDrv.sFileName_IN,
        oZipDrv.sFileName_OUT,
        oZipDrv.sZipMode)
    # Zip file
    oZipDrv.oFileLibrary.zipFile(oFileZip_IN, oFileZip_OUT)
    oZipDrv.oFileLibrary.closeZip(oFileZip_IN, oFileZip_OUT)

    oLogStream.info(' ------> Zip file: ' + oZipDrv.sFileName_OUT)

    # Remove unzipped file
    deleteFileUnzip(sFileName, True)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to handle file Data (in netCDF, binary and ASCII formats)
def handleFileData(sFileName, sFileType=None, sPathTemp=None, bFileTemp=True):

    # -------------------------------------------------------------------------------------
    # Check file availability on disk
    if exists(sFileName):

        # -------------------------------------------------------------------------------------
        # Create temporary folder to copy file from source (to manage multiprocess request)
        sFolderTemp = createTemp(sPathTemp)
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Get source file path and name
        [sPathName_Source, sFileName_Source] = split(sFileName)
        sFile_Source = join(sPathName_Source, sFileName_Source)

        # Get destination file path and name
        sPathName_Destination = sFolderTemp
        sFileName_Destination = sFileName_Source

        sFile_Destination = join(sPathName_Destination, sFileName_Destination)
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Create destination folder (if needed)
        if bFileTemp:
            createFolder(sPathName_Destination)
            # Copy file in temporary folder (to manage multiprocess file request)
            copyFile(sFile_Source, sFile_Destination)
        else:
            # Temporary file and folder not used
            sPathName_Destination = sPathName_Source
            sFile_Destination = sFile_Source
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Get zip extension (if exists)
        [sZipType_Destination, bZipType_Destination] = getExtZip(sFile_Destination)
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Check file is compressed or not
        if bZipType_Destination is True:

            # -------------------------------------------------------------------------------------
            # Check script for zipped file
            try:

                # -------------------------------------------------------------------------------------
                # Unzip file
                oZipDriver = Drv_Data_Zip(sFile_Destination, 'u', None, sZipType_Destination).oFileWorkspace
                [oFile_ZIP, oFile_UNZIP] = oZipDriver.oFileLibrary.openZip(oZipDriver.sFileName_IN,
                                                                           oZipDriver.sFileName_OUT,
                                                                           oZipDriver.sZipMode)
                oZipDriver.oFileLibrary.unzipFile(oFile_ZIP, oFile_UNZIP)
                oZipDriver.oFileLibrary.closeZip(oFile_ZIP, oFile_UNZIP)

                # Open unzipped file
                oFileDriver = Drv_Data_IO(oZipDriver.sFileName_OUT,  sFileType=sFileType).oFileWorkspace
                oFileHandle = oFileDriver.oFileLibrary.openFile(oZipDriver.sFileName_OUT, 'r')
                bFileOpen = True

                # Delete unzipped file
                deleteFileName(oZipDriver.sFileName_OUT)

                # Temporary file and folder are used
                if bFileTemp:
                    # Delete zipped temporary file
                    deleteFileName(sFile_Destination)
                    # Delete temporary folder
                    deleteFolder(sPathName_Destination)
                # -------------------------------------------------------------------------------------

            except BaseException:

                # -------------------------------------------------------------------------------------
                # Exit for errors in unzip or open file
                Exc.getExc(' =====> WARNING: handle file ' + sFileName + ' FAILED! '
                           'Errors in unzipping or opening file!', 2, 1)
                oFileDriver = None
                oFileHandle = None
                bFileOpen = False
                # -------------------------------------------------------------------------------------

        else:

            # -------------------------------------------------------------------------------------
            # Check script for normal file
            try:

                # -------------------------------------------------------------------------------------
                # Open file
                oFileDriver = Drv_Data_IO(sFile_Destination, sFileType=sFileType).oFileWorkspace
                oFileHandle = oFileDriver.oFileLibrary.openFile(sFile_Destination, 'r')
                bFileOpen = True

                # Temporary file and folder are used
                if bFileTemp:
                    # Delete zipped temporary file
                    deleteFileName(sFile_Destination)
                    # Delete temporary folder
                    deleteFolder(sPathName_Destination)
                # -------------------------------------------------------------------------------------

            except BaseException:

                # -------------------------------------------------------------------------------------
                # Exit for errors in read file
                Exc.getExc(' =====> WARNING: handle file ' + sFileName + ' FAILED! '
                           'Errors in opening file!', 2, 1)
                oFileDriver = None
                oFileHandle = None
                bFileOpen = False
                # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------

    else:

        # -------------------------------------------------------------------------------------
        # Exit for errors in finding file
        Exc.getExc(' =====> WARNING: handle file ' + sFileName + ' FAILED! File not found!', 2, 1)
        oFileDriver = None
        oFileHandle = None
        bFileOpen = False
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Return variable(s)
    return oFileHandle, oFileDriver, bFileOpen
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
