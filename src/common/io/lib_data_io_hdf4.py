"""
Library Features:

Name:          lib_data_io_hdf4
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20160805'
Version:       '1.5.0'
"""
#################################################################################
# Logging
import logging
from osgeo import gdal

from fp.default.lib_default_args import sLoggerName
from fp.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#################################################################################

# --------------------------------------------------------------------------------
# Method to open hdf4 file
def openFile(sFileName):

    # Check method
    try:
        # Open file
        oFile = gdal.Open(sFileName)
        return oFile

    except IOError as oError:
        Exc.getExc(' -----> ERROR: in open file (lib_data_io_hdf4)' + ' [' + str(oError) + ']', 1, 1)

# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to close hdf4 file
def closeFile(oFile):
    Exc.getExc(' -----> Warning: no close method defined (lib_data_io_hdf4)', 2, 1)
    pass

# --------------------------------------------------------------------------------
