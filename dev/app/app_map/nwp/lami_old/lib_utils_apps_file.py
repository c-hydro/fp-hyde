"""
Library Features:

Name:          lib_utils_apps_file
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20200210'
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

from lib_utils_apps_zip import getExtZip, addExtZip, removeExtZip, deleteFileUnzip

from lib_default_args import logger_name
from lib_default_args import zip_ext as zip_ext_default

from lib_utils_op_system import createFolder, deleteFolder, copyFile, deleteFileName, createTemp

from drv_data_io_type import Drv_Data_IO
from drv_data_io_zip import Drv_Data_Zip

from drv_configuration_debug import Exc

# Logging
log_stream = logging.getLogger(logger_name)

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
def zipFileData(sFileName, sFileZipExt=zip_ext_default):

    oZipDrv = Drv_Data_Zip(sFileName, 'z', None, sFileZipExt).oFileWorkspace
    [oFileZip_IN, oFileZip_OUT] = oZipDrv.oFileLibrary.openZip(
        oZipDrv.sFileName_IN,
        oZipDrv.sFileName_OUT,
        oZipDrv.sZipMode)
    # Zip file
    oZipDrv.oFileLibrary.zipFile(oFileZip_IN, oFileZip_OUT)
    oZipDrv.oFileLibrary.closeZip(oFileZip_IN, oFileZip_OUT)

    log_stream.info(' ------> Zip file: ' + oZipDrv.sFileName_OUT)

    # Remove unzipped file
    deleteFileUnzip(sFileName, True)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to handle file Data (in netCDF, binary and ASCII formats)
def handleFileData(file_name, file_type=None, path_tmp=None, file_tmp=True):

    # -------------------------------------------------------------------------------------
    # Check file availability on disk
    if exists(file_name):

        # -------------------------------------------------------------------------------------
        # Create temporary folder to copy file from source (to manage multiprocess request)
        folder_tmp = createTemp(path_tmp)
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Get source file path and name
        [folder_name_src, file_name_src] = split(file_name)
        file_src = join(folder_name_src, file_name_src)

        # Get destination file path and name
        folder_name_dst = folder_tmp
        file_name_dst = file_name_src

        file_dst = join(folder_name_dst, file_name_dst)
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Create destination folder (if needed)
        if file_tmp:
            createFolder(folder_name_dst)
            # Copy file in temporary folder (to manage multiprocess file request)
            copyFile(file_src, file_dst)
        else:
            # Temporary file and folder not used
            folder_name_dst = folder_name_src
            file_dst = file_src
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Get zip extension (if exists)
        [zip_type_dst, zip_active_dst] = getExtZip(file_dst)
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Check file is compressed or not
        if zip_active_dst is True:

            # -------------------------------------------------------------------------------------
            # Check script for zipped file
            try:

                # -------------------------------------------------------------------------------------
                # Unzip file
                oZipDriver = Drv_Data_Zip(file_dst, 'u', None, zip_type_dst).oFileWorkspace
                [file_zip_handle, file_unzip_handle] = oZipDriver.oFileLibrary.openZip(
                    oZipDriver.sFileName_IN, oZipDriver.sFileName_OUT, oZipDriver.sZipMode)

                oZipDriver.oFileLibrary.unzipFile(file_zip_handle, file_unzip_handle)
                oZipDriver.oFileLibrary.closeZip(file_zip_handle, file_unzip_handle)

                # Open unzipped file
                file_drv = Drv_Data_IO(oZipDriver.sFileName_OUT,  sFileType=file_type).oFileWorkspace
                file_handle = file_drv.oFileLibrary.openFile(oZipDriver.sFileName_OUT, 'r')
                file_open = True

                # Delete unzipped file
                deleteFileName(oZipDriver.sFileName_OUT)

                # Temporary file and folder are used
                if file_tmp:
                    # Delete zipped temporary file
                    deleteFileName(file_dst)
                    # Delete temporary folder
                    deleteFolder(folder_name_dst)
                # -------------------------------------------------------------------------------------

            except BaseException as BExp:

                # -------------------------------------------------------------------------------------
                # Exit for errors in unzip or open file
                log_stream.warning('Handle file ' + file_name + ' FAILED! Errors in unzipping or opening file!')
                log_stream.warning('Exception found ' + str(BExp))
                file_drv = None
                file_handle = None
                file_open = False
                # -------------------------------------------------------------------------------------

        else:

            # -------------------------------------------------------------------------------------
            # Check script for normal file
            try:

                # -------------------------------------------------------------------------------------
                # Open file
                file_drv = Drv_Data_IO(file_dst, sFileType=file_type).oFileWorkspace
                file_handle = file_drv.oFileLibrary.openFile(file_dst, 'r')
                file_open = True

                # Temporary file and folder are used
                if file_tmp:
                    # Delete zipped temporary file
                    deleteFileName(file_dst)
                    # Delete temporary folder
                    deleteFolder(folder_name_dst)
                # -------------------------------------------------------------------------------------

            except BaseException as BExp:

                # -------------------------------------------------------------------------------------
                # Exit for errors in read file
                log_stream.warning('Handle file ' + file_name + ' FAILED! Errors in opening file!')
                log_stream.warning('Exception found ' + str(BExp))

                file_drv = None
                file_handle = None
                file_open = False
                # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------

    else:

        # -------------------------------------------------------------------------------------
        # Exit for errors in finding file
        log_stream.warning('Handle file ' + file_name + ' FAILED! File not found!!')
        file_drv = None
        file_handle = None
        file_open = False
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Return variable(s)
    return file_handle, file_drv, file_open
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
