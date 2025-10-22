"""
Library Features:

Name:          lib_utils_obj
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20231010'
Version:       '1.0.0'
"""


# ----------------------------------------------------------------------------------------------------------------------
# libraries
import logging
import unicodedata
import re
import numpy as np
import pandas as pd
import xarray as xr
from copy import deepcopy

from lib_info_args import logger_name
from lib_info_args import (geo_coord_name_x, geo_coord_name_y, time_coord_name,
                           geo_dim_name_x, geo_dim_name_y, time_dim_name)

# logging
log_stream = logging.getLogger(logger_name)
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to invert dictionary
def invert_dict(dict_src):
    dict_dst = {v: k for k, v in dict_src.items()}
    return dict_dst
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to convert dictionary to dataframe
def convert_dict_to_dframe(obj_dict):
    tmp_data, tmp_time, name_time = {}, None, None
    for obj_key, obj_dframe in obj_dict.items():
        tmp_data[obj_key] = obj_dframe.values[:, 0]
        if tmp_time is None:
            tmp_time = obj_dframe.index
            name_time = obj_dframe.index.name

    obj_dframe = pd.DataFrame(data=tmp_data, index=tmp_time, columns=list(obj_dict.keys()))
    obj_dframe.index.name = name_time

    return obj_dframe
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to sanitize string
def sanitize_string(string_name):

    string_name = string_name.lower()
    string_name = re.sub(r"['.,-]", "", string_name)
    string_name = string_name.replace(' ', '')
    string_name = unicodedata.normalize('NFD', string_name).encode('ascii', 'ignore')
    string_name = string_name.decode("utf-8")

    return string_name
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to pad list collections
def pad_list(list_ref, list_in, default_value=None):
    list_ref_size = list_ref.__len__()
    list_in_size = list_in.__len__()

    list_out = deepcopy(list_in)
    if list_in_size < list_ref_size:
        list_out.extend([default_value] * (list_ref_size - len(list_in)))
        # alg_logger.warning(' ===> List is less than the reference size')
    elif list_in_size > list_ref_size:
        list_out = list_in[:list_ref_size]
        # alg_logger.warning(' ===> List is greater than the reference size')
    else:
        pass

    return list_out
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to create a dictionary from list(s)
def create_dict_from_list(list_keys, list_values):

    if not isinstance(list_values, list):
        list_values = [list_values]

    list_values = pad_list(list_keys, list_values, default_value=list_values[0])
    obj_dict = {k: v for k, v in zip(list_keys, list_values)}

    return obj_dict
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to create a data array
def create_darray_2d(data, geo_x, geo_y, geo_1d=True, time=None,
                     coord_name_x=geo_coord_name_x, coord_name_y=geo_coord_name_y, coord_name_time=time_coord_name,
                     dim_name_x=geo_dim_name_x, dim_name_y=geo_dim_name_y, dim_name_time=time_dim_name,
                     dims_order=None):

    if dims_order is None:
        dims_order = [dim_name_y, dim_name_x]
    if time is not None:
        dims_order = [dim_name_y, dim_name_x, dim_name_time]

    if geo_1d:
        if geo_x.shape.__len__() == 2:
            geo_x = geo_x[0, :]
        if geo_y.shape.__len__() == 2:
            geo_y = geo_y[:, 0]

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
                                   coords={coord_name_x: (dim_name_x, geo_x),
                                           coord_name_y: (dim_name_y, geo_y),
                                           coord_name_time: (dim_name_time, time)})
        else:
            log_stream.error(' ===> Time obj is in wrong format')
            raise IOError('Variable time format not valid')

    else:
        log_stream.error(' ===> Longitude and Latitude must be 1d')
        raise IOError('Variable shape is not valid')

    return data_da
# ----------------------------------------------------------------------------------------------------------------------
