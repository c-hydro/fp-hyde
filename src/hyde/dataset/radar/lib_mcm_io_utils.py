"""
Library Features:

Name:          lib_mcm_io_utils
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190708'
Version:       '1.0.0'
"""

#######################################################################################
# Libraries
import logging
import rasterio
import numpy as np

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to read data
def readData(filename):

    try:
        dset = rasterio.open(filename)
        bounds = dset.bounds
        res = dset.res
        transform = dset.transform
        data = dset.read()
        values = data[0, :, :]

        decimal_round = 7

        center_right = bounds.right - (res[0] / 2)
        center_left = bounds.left + (res[0] / 2)
        center_top = bounds.top - (res[1] / 2)
        center_bottom = bounds.bottom + (res[1] / 2)

        lon = np.arange(center_left, center_right + np.abs(res[0] / 2), np.abs(res[0]), float)
        lat = np.arange(center_bottom, center_top + np.abs(res[0] / 2), np.abs(res[1]), float)
        lons, lats = np.meshgrid(lon, lat)

        min_lon_round = round(np.min(lons), decimal_round)
        max_lon_round = round(np.max(lons), decimal_round)
        min_lat_round = round(np.min(lats), decimal_round)
        max_lat_round = round(np.max(lats), decimal_round)

        center_right_round = round(center_right, decimal_round)
        center_left_round = round(center_left, decimal_round)
        center_bottom_round = round(center_bottom, decimal_round)
        center_top_round = round(center_top, decimal_round)

        assert min_lon_round == center_left_round
        assert max_lon_round == center_right_round
        assert min_lat_round == center_bottom_round
        assert max_lat_round == center_top_round

        lats = np.flipud(lats)

        # plotMap_Pcolor(values, lons, lats, dDataMin=0, dDataMax=10, sMapRes='l')
        file_obj = {'data': values, 'longitude': lons, 'latitude': lats, 'transform': transform}
        file_status = True

    except Exception as exc:

        Exc.getExc(' =====> WARNING: read file failed!', 2, 1, oExcRaised=exc)
        file_obj = None
        file_status = False

    return file_obj, file_status
# -------------------------------------------------------------------------------------
