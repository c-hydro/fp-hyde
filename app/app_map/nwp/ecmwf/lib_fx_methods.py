"""
Library Features:

Name:          lib_fx_utils
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20230727'
Version:       '1.0.0'
"""

# ----------------------------------------------------------------------------------------------------------------------
# libraries
import logging
import warnings
warnings.filterwarnings(
    "ignore",
    message=r"Possible more than \d+ neighbours within \d+ m",
    module=r"repurpose\.resample"
)

import numpy as np
import pandas as pd
import xarray as xr

from copy import deepcopy

import lib_fx_nwp_generic as lib_fx_nwp

from lib_utils_io import create_darray
from lib_utils_geo import resample_points_to_grid
from lib_info_args import logger_name

# set logger
alg_logger = logging.getLogger(logger_name)
logging.getLogger('repurpose').setLevel(logging.WARNING)

# debug
import matplotlib.pylab as plt
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to transform data to dataset
def transform_data_2_dset(obj_data_src, obj_time, obj_geo_x, obj_geo_y, obj_attrs=None,
                          var_name_time='time', var_name_geo_x='longitude', var_name_geo_y='latitude',
                          coord_name_time='time', coord_name_x='longitude', coord_name_y='latitude',
                          dim_name_time='time', dim_name_x='longitude', dim_name_y='latitude'):

    # iterate over variable(s)
    obj_collections_dst = xr.Dataset()
    for var_name, var_data in obj_data_src.items():

        # get attrs information
        var_attrs = {}
        if obj_attrs is not None:
            if var_name in list(obj_attrs.keys()):
                var_attrs = obj_attrs[var_name]

        # get time information
        var_time = pd.DatetimeIndex(obj_time)
        
        # create variable data array
        var_dframe = create_darray(
            var_data, obj_geo_x, obj_geo_y,
            geo_1d=False, time=var_time,
            coord_name_x=coord_name_x, coord_name_y=coord_name_y, coord_name_time=coord_name_time,
            dim_name_x=dim_name_x, dim_name_y=dim_name_y, dim_name_time=dim_name_time)
        # assign variable attributes
        var_dframe.attrs = var_attrs

        # store variable in a common dataset
        obj_collections_dst[var_name] = var_dframe

    return obj_collections_dst
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to transform dataset to data
def transform_dset_2_data(obj_data_src, obj_attrs_src,
                          var_name_time='time', var_name_geo_x='west_east', var_name_geo_y='south_north'):

    # check data format
    if not isinstance(obj_data_src, xr.Dataset):
        alg_logger.error(' ===> Data obj format is not supported')
        raise NotImplemented('Case not implemented yet')

    # adapt data
    obj_data_dst, obj_attrs_dst = {}, {}
    for variable_name in obj_data_src.variables:
        if variable_name not in [var_name_time, var_name_geo_x, var_name_geo_y]:
            variable_data = obj_data_src[variable_name]
            obj_data_dst[variable_name] = variable_data.values

            obj_attrs_dst[variable_name] = obj_attrs_src[variable_name]

    return obj_data_dst, obj_attrs_dst
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to extract data
def extract_data(obj_collections_src,
                var_name_time='time', var_name_geo_x='west_east', var_name_geo_y='south_north'):

    # get data and time information
    obj_data_dst = obj_collections_src['data']
    # check data format
    if not isinstance(obj_data_dst, xr.Dataset):
        alg_logger.error(' ===> Data obj format is not supported')
        raise NotImplemented('Case not implemented yet')

    # adapt attributes
    obj_attrs_dst = obj_collections_src['attrs']

    # adapt geographical values x
    if var_name_geo_x in list(obj_data_dst.variables):
        geo_x_values_dst = obj_data_dst[var_name_geo_x].values
    else:
        alg_logger.error(' ===> Geographical variable "' + var_name_geo_x + '" is not available in the datasets')
        raise RuntimeError('Geographical variable is needed by the method')
    # adapt geographical values y
    if var_name_geo_y in list(obj_data_dst.variables):
        geo_y_values_dst = obj_data_dst[var_name_geo_y].values
    else:
        alg_logger.error(' ===> Geographical variable "' + var_name_geo_y + '" is not available in the datasets')
        raise RuntimeError('Geographical variable is needed by the method')
    # adapt time
    if var_name_time in list(obj_data_dst.variables):
        time_values_dst = obj_data_dst[var_name_time].values
    else:
        alg_logger.error(' ===> Geographical variable "' + var_name_geo_y + '" is not available in the datasets')
        raise RuntimeError('Geographical variable is needed by the method')

    return obj_data_dst, obj_attrs_dst, time_values_dst, geo_x_values_dst, geo_y_values_dst
# ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------
# method to resample data
def resample_data(obj_data_src, geo_x_values_src, geo_y_values_src, geo_x_values_dst, geo_y_values_dst,
                  geo_resample_idx=True,
                  geo_mask_dst=None, **kwargs):

    # iterate over variable(s)
    obj_data_dst = {}
    for var_name, var_values_src in obj_data_src.items():
        if var_values_src is not None:

            if var_name in kwargs:
                var_settings = kwargs.get(var_name)
            else:
                var_settings = {}

            idx_1d_dst = None
            if geo_resample_idx:

                idx_1d_src = np.arange(0, geo_y_values_src.shape[0] * geo_x_values_src.shape[1])
                idx_2d_src = np.reshape(idx_1d_src, [geo_y_values_src.shape[0], geo_x_values_src.shape[1]])

                idx_2d_dst, _, _ = resample_points_to_grid(
                    idx_2d_src, geo_x_values_src, geo_y_values_src, geo_x_values_dst, geo_y_values_dst,
                    **var_settings)

                idx_1d_dst = idx_2d_dst.ravel()
                idx_1d_dst = np.asarray(idx_1d_dst, dtype=int)

            var_values_dst = np.zeros((var_values_src.shape[0], geo_y_values_dst.shape[0], geo_x_values_dst.shape[1]))
            for n in range(0, var_values_src.shape[0]):

                if idx_1d_dst is None:
                    var_values_tmp, _, _ = resample_points_to_grid(
                        var_values_src[n, :, :], geo_x_values_src, geo_y_values_src, geo_x_values_dst, geo_y_values_dst,
                        **var_settings)
                else:
                    var_arr_src = var_values_src[n, :, :].ravel()
                    var_arr_dst = var_arr_src[idx_1d_dst]
                    var_values_tmp = np.reshape(var_arr_dst, [geo_x_values_dst.shape[0], geo_y_values_dst.shape[1]])

                var_values_tmp = np.flipud(var_values_tmp)
                var_values_tmp[geo_mask_dst == 0] = np.nan

                var_values_dst[n, :, :] = var_values_tmp

            ''' debug
            import matplotlib
            matplotlib.use('TkAgg')
            plt.figure()
            plt.imshow(np.flipud(var_values_src[0, :, :]))
            plt.colorbar()
            plt.figure()
            plt.imshow(var_values_dst[0, :, :])
            plt.colorbar()
            plt.show()
            '''

            obj_data_dst[var_name] = var_values_dst
        else:
            alg_logger.warning(' ===> Data "' + var_name + '" is not available in the datasets')
            obj_data_dst[var_name] = None

    return obj_data_dst
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to apply settings to data
def apply_settings(var_data, var_settings):

    var_fill_data = None
    if 'fill_data' in list(var_settings.keys()):
        var_fill_data = var_settings['fill_data']
    if var_fill_data is None:
        var_fill_data = np.nan
    var_type_in = None
    if 'type_in' in list(var_settings.keys()):
        var_type_in = var_settings['type_in']
    if var_type_in is None:
        var_type_in = 'float'
    var_type_out = None
    if 'type_out' in list(var_settings.keys()):
        var_type_out = var_settings['type_out']
    if var_type_out is None:
        var_type_out = 'float'
    if var_type_in != var_type_out:
        var_data = var_data.astype(var_type_out)
    if var_type_in == var_type_out:
        var_data = var_data.astype(var_type_in)

    if 'no_data' in list(var_settings.keys()):
        var_no_data = var_settings['no_data']
        if var_no_data is not None:
            var_data[var_data == var_no_data] = var_fill_data

    if 'scale_factor' in list(var_settings.keys()):
        var_scale_factor = var_settings['scale_factor']
        if var_scale_factor is not None:
            var_data = var_data / var_scale_factor

    if 'min_value' in list(var_settings.keys()):
        var_min_value = var_settings['min_value']
        if var_min_value is not None:
            var_data[var_data < var_min_value] = var_fill_data

    if 'max_value' in list(var_settings.keys()):
        var_max_value = var_settings['max_value']
        if var_max_value is not None:
            var_data[var_data > var_max_value] = var_fill_data

    if ('mask_in' in list(var_settings.keys())) and ('mask_out' in list(var_settings.keys())):
        var_mask_in, var_mask_out = var_settings['mask_in'], var_settings['mask_out']
        var_data_tmp = deepcopy(var_data)
        if var_mask_in is not None and var_mask_out is not None:
            for value_in, value_out in zip(var_mask_in, var_mask_out):

                if isinstance(value_in, list) and isinstance(value_out, list):
                    pass  # nothing to do if the input and output values are lists
                else:
                    var_data[var_data_tmp == value_in] = value_out

    return var_data
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
def organize_attrs(obj_attrs, attr_index='date_created_utc'):

    # arrange time variable
    variable_attrs = {}
    for attr_key, attr_value in obj_attrs.items():
        variable_attrs[attr_key] = [attr_value]
    # set time index
    variable_index = variable_attrs[attr_index]

    # define time dframe
    attrs_dframe = pd.DataFrame(data=variable_attrs, index=[variable_index])

    return attrs_dframe
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to organize time
def organize_time(obj_time, time_index='time_creation'):

    # arrange time variable
    variable_time = {}
    for time_key, time_value in obj_time.items():
        variable_time[time_key] = [time_value]
    # set time index
    variable_index = variable_time[time_index]

    # define time dframe
    time_dframe = pd.DataFrame(data=variable_time, index=[variable_index])

    return time_dframe

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to compose data (from multiple variables to one variable for example)
def compose_data(obj_data_src, obj_attrs_src, obj_time_src, obj_method,
                 geo_terrain_ref=None, geo_x_ref=None, geo_y_ref=None):

    # iterate over variable(s)
    for var_name, var_method in obj_method.items():

        # get fx parameters
        fx_name, fx_variables = var_method['fx'], var_method['variables']

        # check fx method
        if fx_name is not None:

            # search fx method in the library
            if hasattr(lib_fx_nwp, fx_name):

                # get data and time information
                if isinstance(obj_data_src, dict):
                    obj_data_tmp = {k: obj_data_src[k] for k in fx_variables}
                    obj_attrs_tmp = {k: obj_attrs_src.get(k, None) for k in fx_variables}
                elif isinstance(obj_data_src, xr.Dataset):
                    obj_data_tmp = obj_data_src[fx_variables]
                    obj_attrs_tmp = {k: obj_attrs_src.get(k, None) for k in fx_variables}
                else:
                    alg_logger.error(' ===> Data obj format is not supported')
                    raise NotImplemented('Case not implemented yet')

                # define fx method
                fx_obj = getattr(lib_fx_nwp, fx_name)

                # define fx arguments
                fx_args = {'var_data': obj_data_tmp, 'var_time': obj_time_src,
                           'var_attrs': obj_attrs_tmp,
                           'var_geo_terrain': geo_terrain_ref, 'var_geo_x': geo_x_ref, 'var_geo_y': geo_y_ref}

                # apply fx method and arguments
                data_dframe_def, data_attrs_def = fx_obj(**fx_args)

                # store data in a collection
                obj_data_src[var_name] = data_dframe_def
                obj_attrs_src[var_name] = data_attrs_def

            else:
                alg_logger.error(' ===> Method fx "' + fx_name + '" is not available for variable "' + var_name + '"')
                raise NotImplementedError('Case not implemented yet')

    return obj_data_src, obj_attrs_src
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to organize data
def organize_data(obj_data, obj_geo, var_name_pivot='ssm_data',
                  var_name_geo_x='longitude', var_name_geo_y='latitude', **kwargs):

    # get geo information
    n_data = None
    variable_geo = {}
    for var_name, var_data in obj_geo.items():
        if n_data is None:
            n_data = var_data.flatten().shape[0]

        if var_name in kwargs:
            var_settings = kwargs.get(var_name)
        else:
            var_settings = {}

        var_data_tmp = deepcopy(var_data.flatten())
        var_data_def = apply_settings(var_data_tmp, var_settings)

        variable_geo[var_name] = var_data_def

    # define variable obj
    variable_data = {}
    for var_name, var_data in obj_data.items():

        if var_name in kwargs:
            var_settings = kwargs.get(var_name)
        else:
            var_settings = None

        if var_data is None:
            var_data = np.zeros((n_data, 1))
            var_data[:] = np.nan
            alg_logger.warning(' ===> Data "' + var_name + '" is not available in the datasets')
        else:

            ''' debug
            plt.figure()
            plt.imshow(var_data.astype(float))
            plt.colorbar()
            plt.show()
            '''
            if isinstance(var_data, list):
                pass
            else:
                var_data = var_data.flatten()

        if var_settings is not None:
            if var_settings:
                var_data_tmp = deepcopy(var_data)
                var_data_def = apply_settings(var_data_tmp, var_settings)
            else:
                var_data_def = deepcopy(var_data)
        else:
            var_data_def = None

        if var_data_def is not None:
            variable_data[var_name] = var_data_def

    # define variable collections
    variable_collections = {**variable_data, **variable_geo}

    # define variable data frame
    variable_dframe = pd.DataFrame(data=variable_collections)
    if var_name_pivot is not None:
        var_name_subset = [var_name_geo_x, var_name_geo_y, var_name_pivot]
    else:
        var_name_subset = [var_name_geo_x, var_name_geo_y]

    variable_dframe = variable_dframe.dropna(axis=0, how='any', subset=var_name_subset)
    variable_dframe.reset_index(drop=True, inplace=True)

    return variable_dframe

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to mask data
def mask_data(obj_data_src, **kwargs):

    # iterate over variable(s)
    obj_data_dst = {}
    for var_name, var_data_src in obj_data_src.items():
        if var_data_src is not None:
            if var_name in kwargs:
                var_settings = kwargs.get(var_name)
            else:
                var_settings = {}

            # get variable data
            var_data_dst = deepcopy(var_data_src)

            # get no data value
            var_no_data = np.nan
            if 'no_data' in var_settings:
                var_no_data = var_settings['no_data']
                if var_no_data is None:
                    var_no_data = np.nan
            # apply mask of min values
            if 'var_min' in var_settings:
                var_min = var_settings['var_min']
                if var_min is not None:
                    var_data_dst[var_data_dst < var_min] = var_no_data
            # apply mask of max values
            if 'var_max' in var_settings:
                var_max = var_settings['var_max']
                if var_max is not None:
                    var_data_dst[var_data_dst > var_max] = var_no_data
            # store data in a collection
            obj_data_dst[var_name] = var_data_dst

            ''' debug
            plt.figure()
            plt.imshow(var_data_dst)
            plt.colorbar()
            plt.show()
            '''

        else:
            alg_logger.warning(' ===> Data "' + var_name + '" is not available in the datasets')
            obj_data_dst[var_name] = None

    return obj_data_dst
# ----------------------------------------------------------------------------------------------------------------------
