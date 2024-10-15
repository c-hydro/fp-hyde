"""
Library Features:

Name:          lib_utils_io
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20230727'
Version:       '1.0.0'
"""

# ----------------------------------------------------------------------------------------------------------------------
# libraries
import logging

from copy import deepcopy
from glob import glob

import numpy as np
import pandas as pd
import xarray as xr

from lib_info_args import logger_name
from lib_utils_generic import fill_tags2string

# set logger
alg_logger = logging.getLogger(logger_name)
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to search file with asterisk
def search_file_with_asterisk(file_path_template):

    if '*' in file_path_template:
        file_name_list = glob(file_path_template)
    else:
        file_name_list = deepcopy(file_path_template)

    if not isinstance(file_name_list, list):
        file_name_list = [file_name_list]

    return file_name_list
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to fill string with tags time
def fill_string_with_time(tmpl_string, tmpl_time, tmpl_tags):

    tmpl_values = {}
    for tmpl_key in tmpl_tags.keys():
        tmpl_values[tmpl_key] = tmpl_time

    filled_string = fill_tags2string(tmpl_string, tmpl_tags, tmpl_values)

    return filled_string
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to fill string with tags info (in string format)
def fill_string_with_info(tmpl_string, tmpl_name, tmpl_tags):

    if not isinstance(tmpl_name, dict):
        raise IOError('Name obj is not in dictionary format')

    tmpl_values = {}
    for tmpl_key in tmpl_tags.keys():
        if tmpl_key in list(tmpl_name.keys()):
            tmpl_values[tmpl_key] = tmpl_name[tmpl_key]

    filled_string = fill_tags2string(tmpl_string, tmpl_tags, tmpl_values)

    return filled_string
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to create a data array
def create_darray(data, geo_x, geo_y, geo_1d=False, time=None, name=None,
                  coord_name_x='longitude', coord_name_y='latitude', coord_name_time='time',
                  dim_name_x='longitude', dim_name_y='latitude', dim_name_time='time',
                  dims_order=None):

    if dims_order is None:
        dims_order = [dim_name_y, dim_name_x]
    if time is not None:
        dims_order = [dim_name_time, dim_name_y, dim_name_x]

    if geo_1d:
        if geo_x.shape.__len__() == 2:
            geo_x = geo_x[0, :]
        if geo_y.shape.__len__() == 2:
            geo_y = geo_y[:, 0]
    else:

        if geo_x.shape.__len__() == 2:
            if coord_name_x == dim_name_x:
                coord_name_x = 'west_east'
            if coord_name_y == dim_name_y:
                coord_name_y = 'south_north'

            dim_name_x = dim_name_y = [dim_name_y, dim_name_x]

        elif geo_x.shape.__len__() == 1:
            if coord_name_x == dim_name_x:
                coord_name_x = 'west_east'
            if coord_name_y == dim_name_y:
                coord_name_y = 'south_north'

            dim_name_x = dim_name_y = [dim_name_y, dim_name_x]
            geo_x, geo_y = np.meshgrid(geo_x, geo_y)

        else:
            alg_logger.error(' ===> Longitude and Latitude must be 2d')
            raise IOError('Variable shape is not valid')

    if time is None:
        data_da = xr.DataArray(data,
                               dims=dims_order,
                               coords={coord_name_x: (dim_name_x, geo_x),
                                       coord_name_y: (dim_name_y, geo_y)})
    elif isinstance(time, pd.DatetimeIndex):

        if data.shape.__len__() == 2:
            data = np.expand_dims(data, axis=-1)

        data_da = xr.DataArray(data,
                               dims=dims_order,
                               coords={
                                   coord_name_time: (dim_name_time, time),
                                   coord_name_y: (dim_name_y, geo_y),
                                   coord_name_x: (dim_name_x, geo_x)
                               })
    else:
        alg_logger.error(' ===> Time obj is in wrong format')
        raise IOError('Variable time format not valid')

    if name is not None:
        data_da.name = name

    return data_da
# ----------------------------------------------------------------------------------------------------------------------
