"""
Library Features:

Name:          drv_data_ancillary_ws
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180919'
Version:       '1.0.0'
"""
#################################################################################
# Library
import logging
import rasterio

from os.path import exists

from src.hyde.dataset.ground_network.ws.lib_ws_ancillary_snow import computeSnowPredictor

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
#################################################################################

# -------------------------------------------------------------------------------------
# Dictionary of information about ancillary data
oDataAttributes = dict(
    slope_data={
        'command_line': 'gdaldem slope $FILE_REF $FILE_ANCILLARY -s 111120'
    },
    aspect_data={
        'command_line': 'gdaldem aspect $FILE_REF $FILE_ANCILLARY'
    },
    roughness_data={
        'command_line': 'gdaldem roughness $FILE_REF $FILE_ANCILLARY'
    },
    hillshade_data={
        'command_line': 'gdaldem hillshade $FILE_REF $FILE_ANCILLARY -s 111120'
    }
)
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Class data object
class DataObj(dict):
    pass
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Class to build data ancillary
class DataAncillaryBuilder:

    # -------------------------------------------------------------------------------------
    # Class declaration(s)
    oVarData = DataObj()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, **kwargs):
        self.oVarDef = kwargs['settings']['data']['static']['predictor']
        self.oVarFile = {'slope_data': kwargs['slope_file'],
                         'roughness_data': kwargs['roughness_file'],
                         'aspect_data': kwargs['aspect_file'],
                         'hillshade_data': kwargs['hillshade_file'],
                         }
        self.oVarAttrs = oDataAttributes
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to get data
    def getDataAncillary(self, sFileLand):

        # -------------------------------------------------------------------------------------
        # Info start
        oLogStream.info(' ---> Get ancillary data ... ')

        # Get ancillary file
        oVarFile = self.oVarFile
        oVarDef = self.oVarDef
        oVarAttrs = self.oVarAttrs
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Add land data to ancillary dictionary
        oDataAncillary = {}
        if exists(sFileLand):
            oVarLand = rasterio.open(sFileLand)
            a3dVarLand = oVarLand.read()
            a2dVarLand = a3dVarLand[0, :, :]

            oDataAncillary['land_ref'] = a2dVarLand
        else:
            # Store null data
            oDataAncillary['land_ref'] = None
            Exc.getExc(' =====> WARNING: land reference file not found! Check your data!', 2, 1)
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Add extra data to ancillary dictionary
        if exists(sFileLand):
            for sVarKey, sFileAncillary in oVarFile.items():

                # Check variable key in predictor keys and attributes keys
                if (sVarKey in oVarDef.keys()) and (sVarKey in oVarAttrs.keys()):

                    # Create ascii grid file to land derived data (slope, aspect, roughness, ... )
                    if not exists(sFileAncillary):
                        sVarCommandLine = oVarAttrs[sVarKey]['command_line']
                        a2dVarData = computeSnowPredictor(sFileLand, sFileAncillary, sVarCommandLine)
                    else:
                        oVarData = rasterio.open(sFileAncillary)
                        a3dVarData = oVarData.read()
                        a2dVarData = a3dVarData[0, :, :]

                    # Store data to ancillary dictionary
                    oDataAncillary[sVarKey] = a2dVarData
                else:
                    # Store data to ancillary dictionary skipped
                    Exc.getExc(' =====> WARNING: variable ' + sVarKey +
                               ' not correctly declared! Check your settings!', 2, 1)
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Info end
        oLogStream.info(' ---> Get ancillary data ... OK')
        # Return variable(s)
        return oDataAncillary
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
