"""
Library Features:

Name:          lib_data_io_shapefile
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190109'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import geopandas as gpd
import pandas as pd
import logging

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to open ASCII file (in read or write mode)
def openFile(sFileName):
    try:
        oFileData = gpd.read_file(sFileName)
        return oFileData
    except IOError as oError:
        Exc.getExc(' =====> ERROR: in open file (lib_data_io_shapefile' + ' [' + str(oError) + ']', 1, 1)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get selected or all data from shapefile handle
def getData(oFileData, oFileFields_SEL=None):

    oFileGeoms = ((feature['geometry'], 1) for feature in oFileData.iterfeatures())
    oFileFields_ALL = oFileData.columns.values.tolist()

    if oFileFields_SEL is None:
        oFileFields_SEL = oFileFields_ALL

    oPoints = pd.DataFrame()
    for iFileID, sFileField in enumerate(oFileFields_SEL):

        if sFileField in oFileFields_ALL:
            oFileValue = oFileData[sFileField]
            oPoints.insert(loc=iFileID, column=sFileField, value=oFileValue)

    return oPoints
# -------------------------------------------------------------------------------------

