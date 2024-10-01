"""
Class Features:

Name:          drv_data_io_zip
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20200227'
Version:       '2.0.8'

ZIP values:
sZipType: 'NoZip', 'GZip', 'BZ2'
"""

##################################################################################
# Library
import logging
import os
from os.path import join

import src.common.utils.lib_utils_apps_zip as lib_zip_apps

from src.common.default.lib_default_args import logger_name

# Log
log_stream = logging.getLogger(logger_name)

# Debug
# import matplotlib.pylab as plt
##################################################################################


##################################################################################
# Class to manage ZIP files
class Drv_Data_Zip:

    # --------------------------------------------------------------------------------
    # Class variables
    oFileWorkspace = None

    sFileName_IN = ''
    sFilePath_IN = ''
    sFileName_OUT = ''
    sFilePath_OUT = ''
    sZipMode = ''
    sZipType = None
    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Class init
    def __init__(self, sFileName_IN, sZipMode='', sFileName_OUT=None, sZipType=None):

        # Global variable(s)
        self.sFileName_IN = sFileName_IN
        self.sFileName_OUT = sFileName_OUT
        self.sZipMode = sZipMode
        self.sZipType = self.__cleanZipExt(sZipType)

        # Define filename IN
        self.__setFileNameIN()
        # Define filename OUT
        self.__setFileNameOUT()

        # Select zip library and methods
        if self.sFileName_IN.endswith('gz') or self.sZipType == 'gz':
            sZipType = 'GZip'
            self.oFileWorkspace = GZip(join(self.sFilePath_IN, self.sFileName_IN),
                                       join(self.sFilePath_OUT, self.sFileName_OUT),
                                       self.sZipMode, self.sZipType)
        elif self.sFileName_IN.endswith('7z') or self.sZipType == '7z':
            sZipType = '7Zip'
            pass
        elif self.sFileName_IN.endswith('bz2') or self.sZipType == 'bz2':
            sZipType = 'BZ2Zip'
            self.oFileWorkspace = BZ2(join(self.sFilePath_IN, self.sFileName_IN),
                                       join(self.sFilePath_OUT, self.sFileName_OUT),
                                       self.sZipMode, self.sZipType)

        elif self.sZipType == 'NoZip' or not self.sZipType:
            sZipType = 'NoZip'
            self.oFileWorkspace = NoZip(join(self.sFilePath_IN, self.sFileName_IN),
                                      join(self.sFilePath_OUT, self.sFileName_OUT),
                                      self.sZipMode, self.sZipType)

        else:
            
            if sZipMode == 'z':
                log_stream.error(' ===> Zip or unzip functions are not selected! Please check zip tag!')
                raise IOError(' Functions for zip or unzip libraries are not correctly selected')
            elif sZipMode == 'u':
                log_stream.warning(' ===> zip or unzip functions are not selected! Please check zip tag!')

    # ------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------
    # Method to remove unrequested character in zip extension
    @staticmethod
    def __cleanZipExt(zip_ext):

        zip_ext = zip_ext.replace('.', '')
        return zip_ext

    # ------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------
    # Method to define filename in
    def __setFileNameIN(self):

        # Define filename IN
        if self.sFileName_IN:
            self.sFilePath_IN = os.path.split(self.sFileName_IN)[0]
            self.sFileName_IN = os.path.split(self.sFileName_IN)[1]
        else:
            log_stream.error(' ===> Input filename is not defined! Please check driver argument(s)!!')
            raise IOError(' Input filename is not defined!')
    # ------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------
    # Method to define filename out
    def __setFileNameOUT(self):

        # Get zip type
        sZipType = self.sZipType

        # Define filename OUT (if not defined)
        sFilePath_OUT = ''
        sFileName_OUT = ''
        if not sZipType == 'NoZip':
            if not self.sFileName_OUT:
                if self.sZipMode is 'z':
                    sFilePath_OUT = self.sFilePath_IN
                    [sFileName_OUT, sZipType] = lib_zip_apps.addExtZip(self.sFileName_IN, sZipType)
                elif self.sZipMode is 'u':
                    self.sZipType = lib_zip_apps.getExtZip(self.sFileName_IN)[0]
                    sFilePath_OUT = self.sFilePath_IN
                    [sFileName_OUT, sZipType] = lib_zip_apps.removeExtZip(self.sFileName_IN, self.sZipType)
                elif self.sZipMode is '' or self.sZipMode is None:
                    pass
            else:
                sFilePath_OUT = os.path.split(sFileName_OUT)[0]
                sFileName_OUT = os.path.split(sFileName_OUT)[1]
        else:
            sFilePath_OUT = os.path.split(self.sFileName_IN)[0]
            sFileName_OUT = os.path.split(self.sFileName_IN)[1]

        self.sFilePath_OUT = sFilePath_OUT
        self.sFileName_OUT = sFileName_OUT
        self.sZipType = sZipType

    # ------------------------------------------------------------------------------

##################################################################################

##################################################################################


# --------------------------------------------------------------------------------
# Class to use no compression
class NoZip:

    # --------------------------------------------------------------------------------
    # Class variable(s)
    oFileLibrary = None
    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Class init
    def __init__(self, sFileName_IN, sFileName_OUT, sZipMode, sZipType):

        self.sFileName_IN = sFileName_IN
        self.sFileName_OUT = sFileName_OUT
        self.sZipMode = sZipMode
        self.sZipType = sZipType

        # Set library IO
        self.setFileLibZip()

    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Method to set library I/O function(s)
    def setFileLibZip(self):

        self.oFileLibrary = None

    # --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Class to use BZ2 compression
class BZ2:

    # --------------------------------------------------------------------------------
    # Class variable(s)
    oFileLibrary = None
    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Class init
    def __init__(self, sFileName_IN, sFileName_OUT, sZipMode, sZipType):

        self.sFileName_IN = sFileName_IN
        self.sFileName_OUT = sFileName_OUT
        self.sZipMode = sZipMode
        self.sZipType = sZipType

        # Set library IO
        self.setFileLibZip()

    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Method to set library I/O function(s)
    def setFileLibZip(self):

        import src.common.zip.lib_data_zip_bz2 as oFileLibrary
        self.oFileLibrary = oFileLibrary

    # --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Class to use GZip compression 
class GZip:

    # --------------------------------------------------------------------------------
    # Class variable(s)
    oFileLibrary = None
    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Class init
    def __init__(self, sFileName_IN, sFileName_OUT, sZipMode, sZipType):

        self.sFileName_IN = sFileName_IN
        self.sFileName_OUT = sFileName_OUT
        self.sZipMode = sZipMode
        self.sZipType = sZipType

        # Set library IO
        self.setFileLibZip()

    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Method to set library I/O function(s)
    def setFileLibZip(self):

        import src.common.zip.lib_data_zip_gzip as oFileLibrary
        self.oFileLibrary = oFileLibrary
        
    # --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
