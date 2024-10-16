"""
Library Features:

Name:          lib_data_io_geo
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20230307'
Version:       '1.0.0'
"""
# ----------------------------------------------------------------------------------------------------------------------
# Library
import logging
import os
import rasterio

import numpy as np
import xarray as xr

from copy import deepcopy

from lib_info_args import logger_name

# set logger
alg_logger = logging.getLogger(logger_name)

# logging
logging.getLogger('rasterio').setLevel(logging.WARNING)
logging.getLogger('repurpose').setLevel(logging.WARNING)

# debug
# import matplotlib.pylab as plt
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to create grid data
def create_grid_data(geo_x_min, geo_x_max, geo_y_min, geo_y_max, geo_x_res, geo_y_res):

    geo_x_arr = np.arange(geo_x_min, geo_x_max + np.abs(geo_x_res / 2), np.abs(geo_x_res), float)
    geo_y_arr = np.flip(np.arange(geo_y_min, geo_y_max + np.abs(geo_y_res / 2), np.abs(geo_y_res), float), axis=0)
    geo_x_grid, geo_y_grid = np.meshgrid(geo_x_arr, geo_y_arr)

    geo_x_min_round, geo_x_max_round = round(np.min(geo_x_grid), 7), round(np.max(geo_x_grid), 7)
    geo_y_min_round, geo_y_max_round = round(np.min(geo_y_grid), 7), round(np.max(geo_y_grid), 7)

    return geo_x_grid, geo_y_grid, geo_x_min_round, geo_x_max_round, geo_y_min_round, geo_y_max_round
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to read grid data
def read_grid_data(file_name, geo_x_name='long', geo_y_name='latg'):

    # open file
    if os.path.exists(file_name):
        # get data in netcdf format
        if file_name.endswith('nc') or file_name.endswith('nc4'):
            file_dset = xr.open_dataset(file_name)

            if geo_x_name in list(file_dset.variables):
                file_geo_x = file_dset.variables[geo_x_name].values
            else:
                alg_logger.error(' ===> Variable "' + geo_x_name + '" is not available in the file')
                raise IOError('Variable is mandatory to correctly run the algorithm')
            if geo_y_name in list(file_dset.variables):
                file_geo_y = file_dset.variables[geo_y_name].values
            else:
                alg_logger.error(' ===> Variable "' + geo_y_name + '" is not available in the file')
                raise IOError('Variable is mandatory to correctly run the algorithm')

            file_values = file_dset.values

        # get data in raster format
        elif (file_name.endswith('tif') or file_name.endswith('tiff') or
              file_name.endswith('asc') or file_name.endswith('txt')):

            file_handle = rasterio.open(file_name, 'r')
            bounds, res, transform = file_handle.bounds, file_handle.res, file_handle.transform
            data = file_handle.read()

            values = np.float32(data[0, :, :])

            center_right = bounds.right - (res[0] / 2)
            center_left = bounds.left + (res[0] / 2)
            center_top = bounds.top - (res[1] / 2)
            center_bottom = bounds.bottom + (res[1] / 2)

            if center_bottom > center_top:
                logging.warning(
                    ' ===> Coords "center_bottom": ' + str(center_bottom) + ' is greater than "center_top": '
                    + str(center_top) + '. Try to inverse the bottom and top coords. ')
                center_tmp = center_top
                center_top = center_bottom
                center_bottom = center_tmp

            lon = np.arange(center_left, center_right + np.abs(res[0] / 2), np.abs(res[0]), float)
            lat = np.flip(np.arange(center_bottom, center_top + np.abs(res[1] / 2), np.abs(res[1]), float), axis=0)
            lons, lats = np.meshgrid(lon, lat)

            lat_upper = lats[0, 0]
            lat_lower = lats[-1, 0]
            if lat_lower > lat_upper:
                lats = np.flipud(lats)
                values = np.flipud(values)

            file_geo_x, file_geo_y = deepcopy(lons), deepcopy(lats)
            file_values = deepcopy(values)

    else:
        alg_logger.error(' ===> File static source grid "' + file_name + '" is not available')
        raise FileNotFoundError('File is mandatory to correctly run the algorithm')

    return file_values, file_geo_x, file_geo_y
# ----------------------------------------------------------------------------------------------------------------------
