"""
Class Features:

Name:          drv_data_io_type
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180521'
Version:       '2.0.7'
"""

#################################################################################
# Library
import logging

from os.path import join
from os.path import split
from os.path import exists

from src.common.default.lib_default_args import sLoggerName
from src.common.utils.lib_utils_op_system import defineFileExt

from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#################################################################################


#################################################################################
# Check file binary
def checkBinaryFile(filename):
    """Return true if the given filename is binary.
    @raise EnvironmentError: if the file does not exist or cannot be accessed.
    @attention: found @ http://bytes.com/topic/python/answers/21222-determine-file-type-binary-text on 6/08/2010
    @author: Trent Mick <TrentM@ActiveState.com>
    @author: Jorge Orpinel <jorge@orpinel.com>"""

    if exists(filename):
        fin = open(filename, 'rb')
        try:
            CHUNKSIZE = 1024
            while 1:
                chunk = fin.read(CHUNKSIZE)
                if b'\0' in chunk: # found null byte
                    return True
                if len(chunk) < CHUNKSIZE:
                    break # done
        finally:
            fin.close()

    return False
#################################################################################


#################################################################################
# Class to manage IO files
class Drv_Data_IO:
    
    # --------------------------------------------------------------------------------
    # Class init
    def __init__(self, sFileName, sFileMode=None, sFileType=None):

        # Check binary file format
        bFileBinary = checkBinaryFile(sFileName)

        # Define file path, name and extension
        sFilePath = split(sFileName)[0]
        sFileName = split(sFileName)[1]

        if sFileType is None:
            sFileExt = defineFileExt(sFileName)
        else:
            sFileExt = sFileType

        # Define FileType and FileWorkspace
        if sFileName.endswith('txt') or sFileName.endswith('asc') or (sFileExt == 'txt') or (sFileType == 'ascii'):
            
            sFileType = 'ascii'
            self.oFileWorkspace = FileAscii(sFilePath, sFileName, sFileType, sFileMode)

        elif sFileName.endswith('nc') or (sFileExt == 'nc') or (sFileType == 'netcdf4'):
            
            sFileType = 'netCDF'
            self.oFileWorkspace = FileNetCDF(sFilePath, sFileName, sFileType, sFileMode)

        elif sFileName.endswith('bin') or (sFileExt is '' and bFileBinary is True) or (sFileExt == 'bin'):
            
            sFileType = 'binary'
            self.oFileWorkspace = FileBinary(sFilePath, sFileName, sFileType, sFileMode)

        elif sFileName.endswith('grb') or sFileName.endswith('grib') \
                or sFileName.endswith('grib2') or (sFileType == 'grib'):

            sFileType = 'grib'
            self.oFileWorkspace = FileGrib(sFilePath, sFileName, sFileType, sFileMode)

        elif sFileName.endswith('H5') or sFileName.endswith('hdf5') or (sFileExt == 'hdf5'):

            sFileType = 'hdf5'
            self.oFileWorkspace = FileHDF5(sFilePath, sFileName, sFileType, sFileMode)

        elif sFileName.endswith('hdf4') or sFileName.endswith('hdf') or (sFileExt == 'hdf'):

            sFileType = 'hdf4'
            self.oFileWorkspace = FileHDF4(sFilePath, sFileName, sFileType, sFileMode)

        elif sFileName.endswith('csv') or (sFileExt == 'csv') or (sFileType == 'csv'):

            sFileType = 'csv'
            self.oFileWorkspace = FileCSV(sFilePath, sFileName, sFileType, sFileMode)

        else:
            sFileType = 'unknown'
            self.oFileWorkspace = FileUnknown(sFilePath, sFileName, sFileType, sFileMode)

    # --------------------------------------------------------------------------------
    
#################################################################################

#################################################################################


# --------------------------------------------------------------------------------
# Class to manage unknown files
class FileUnknown:

    # --------------------------------------------------------------------------------
    # Class init
    def __init__(self, sFilePath, sFileName, sFileType, sFileMode):
        self.sFilePath = sFilePath
        self.sFileName = sFileName
        self.sFileType = sFileType
        self.sFileMode = sFileMode

        # Print file unknown information
        self.printInfo()

    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Method to print information about unknown file
    def printInfo(self):
        Exc.getExc(' =====> WARNING: file ' + join(self.sFilePath, self.sFileName) +
                   ' has unknown extension! Please check library or file format!', 2, 1)
        Exc.getExc(' =====> ERROR: file format unknown!', 1, 1)
    # --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Class to manage Binary files
class FileBinary:

    # --------------------------------------------------------------------------------
    # Class variable(s)
    oFileLibrary = None
    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Class init
    def __init__(self, sFilePath, sFileName, sFileType, sFileMode):
        
        self.sFilePath = sFilePath
        self.sFileName = sFileName
        self.sFileType = sFileType
        self.sFileMode = sFileMode

        # Set library IO
        self.setFileLibIO()
    
    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Method to set library I/O function(s)
    def setFileLibIO(self):

        import src.common.io.lib_data_io_binary as file_library
        self.oFileLibrary = file_library

    # --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Class to manage grib files
class FileGrib:

    # --------------------------------------------------------------------------------
    # Class variable(s)
    oFileLibrary = None
    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Class init
    def __init__(self, sFilePath, sFileName, sFileType, sFileMode):
        self.sFilePath = sFilePath
        self.sFileName = sFileName
        self.sFileType = sFileType
        self.sFileMode = sFileMode

        # Set library IO
        self.setFileLibIO()

    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Method to set library I/O function(s)
    def setFileLibIO(self):
        import src.common.io.lib_data_io_grib as file_library
        self.oFileLibrary = file_library

    # --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Class to manage ASCII files
class FileAscii:

    # --------------------------------------------------------------------------------
    # Class variable(s)
    oFileLibrary = None
    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Class init
    def __init__(self, sFilePath, sFileName, sFileType, sFileMode):
        
        self.sFilePath = sFilePath
        self.sFileName = sFileName
        self.sFileType = sFileType
        self.sFileMode = sFileMode

        # Set library IO
        self.setFileLibIO()

    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Method to set library I/O function(s)
    def setFileLibIO(self):

        import src.common.io.lib_data_io_ascii as file_library
        self.oFileLibrary = file_library
        
    # --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Class to manage NetCDF grid files
class FileNetCDF:

    # --------------------------------------------------------------------------------
    # Class variables
    oFileLibrary = None
    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Class init
    def __init__(self, sFilePath, sFileName, sFileType, sFileMode):
        
        # Common variable(s)
        self.sFilePath = sFilePath
        self.sFileName = sFileName
        self.sFileType = sFileType
        self.sFileMode = sFileMode

        # Set library IO
        self.setFileLibIO()

    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Method to set library I/O function(s)
    def setFileLibIO(self):
        
        import src.common.io.lib_data_io_netcdf as file_library
        self.oFileLibrary = file_library
        
    # --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Class to manage HDF5 grid files
class FileHDF5:

    # --------------------------------------------------------------------------------
    # Class variables
    oFileLibrary = None
    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Class init
    def __init__(self, sFilePath, sFileName, sFileType, sFileMode):
        # Common variable(s)
        self.sFilePath = sFilePath
        self.sFileName = sFileName
        self.sFileType = sFileType
        self.sFileMode = sFileMode

        # Set library IO
        self.setFileLibIO()

    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Method to set library I/O function(s)
    def setFileLibIO(self):
        import src.common.io.lib_data_io_hdf5 as file_library
        self.oFileLibrary = file_library

    # --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Class to manage HDF4 grid files
class FileHDF4:

    # --------------------------------------------------------------------------------
    # Class variables
    oFileLibrary = None
    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Class init
    def __init__(self, sFilePath, sFileName, sFileType, sFileMode):
        # Common variable(s)
        self.sFilePath = sFilePath
        self.sFileName = sFileName
        self.sFileType = sFileType
        self.sFileMode = sFileMode

        # Set library IO
        self.setFileLibIO()

    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Method to set library I/O function(s)
    def setFileLibIO(self):
        import src.common.io.lib_data_io_hdf4 as file_library
        self.oFileLibrary = file_library

    # --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Class to manage csv formatted files
class FileCSV:

    # --------------------------------------------------------------------------------
    # Class variables
    oFileLibrary = None
    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Class init
    def __init__(self, sFilePath, sFileName, sFileType, sFileMode):
        # Common variable(s)
        self.sFilePath = sFilePath
        self.sFileName = sFileName
        self.sFileType = sFileType
        self.sFileMode = sFileMode

        # Set library IO
        self.setFileLibIO()

    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Method to set library I/O function(s)
    def setFileLibIO(self):
        import src.common.io.lib_data_io_csv as file_library
        self.oFileLibrary = file_library

    # --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------

#################################################################################
