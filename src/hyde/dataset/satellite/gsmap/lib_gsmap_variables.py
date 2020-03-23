"""
Library Features:

Name:          lib_gsmap_variables
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '2020302'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging
import numpy as np
import pandas as pd

from src.hyde.algorithm.io.satellite.gsmap.lib_gsmap_io_generic import reshape_var3d, create_darray_3d
from src.hyde.algorithm.settings.satellite.gsmap.lib_gsmap_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to define variable attribute(s)
def getVarAttributes(var_attrs_in):
    var_attrs_tmp = {}
    for var_attrs_step in var_attrs_in:
        for var_attr_key, var_attr_value in var_attrs_step.items():
            if var_attr_key not in list(var_attrs_tmp.keys()):
                var_attrs_tmp[var_attr_key] = var_attr_value
            else:
                var_attr_tmp = var_attrs_tmp[var_attr_key]
                var_attr_list = [var_attr_tmp, var_attr_value]
                var_attr_list = list(set(var_attr_list))
                var_attrs_tmp[var_attr_key] = var_attr_list

    var_attr_out = {}
    for var_attr_key, var_attr_value in var_attrs_tmp.items():
        if isinstance(var_attr_value, list) and var_attr_value.__len__() == 1:
            var_attr_out[var_attr_key] = var_attr_value[0]
        else:
            var_attr_out[var_attr_key] = var_attr_value

    return var_attr_out
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute WindSpeed
def computeRain(var_dset, var_name,
                var_time=None, var_geo_x=None, var_geo_y=None,
                var_units=None, var_step_type=None):

    # Set args
    if var_step_type is None:
        var_step_type = ['accum']
    if var_units is None:
        var_units = ['m']
    if var_geo_y is None:
        var_geo_y = ['latitude']
    if var_geo_x is None:
        var_geo_x = ['longitude']
    if var_time is None:
        var_time = ['valid_time']

    # Parse args
    var_name = list(var_name)[0]
    var_units = var_units[0]
    var_step_type = var_step_type[0]
    var_time = var_time[0]
    var_geo_x = var_geo_x[0]
    var_geo_y = var_geo_y[0]

    # Get values
    var_da_in = var_dset[var_name]
    var_values_in = var_da_in.values
    var_dims_in = var_da_in.dims

    var_time = var_dset[var_time]
    var_geo_x = var_dset[var_geo_x]
    var_geo_y = var_dset[var_geo_y]

    if (var_units == 'kg m**-2') or (var_units == 'Kg m**-2'):
        var_units = 'mm'

    if var_units == 'm':
        var_scale_factor = 1000
    elif var_units == 'mm':
        var_scale_factor = 1
    else:
        log_stream.error(' ===> Rain components units are not allowed! Check your data!')
        raise IOError('Selected units are not allowed!')

    var_time_str = var_dims_in[0].lower()
    if (var_time_str == 'step') or (var_time_str == 'time'):
        var_values_in = reshape_var3d(var_values_in)
    var_shape_in = var_values_in.shape

    # Check attributes
    if not (var_units == 'mm') and not (var_units == 'm'):
        log_stream.error(' ===> Rain components units are not allowed! Check your data!')
        raise IOError('Data units is not allowed!')
    if not (var_step_type == 'accum') and not (var_step_type == 'accumulated'):
        log_stream.error(' ===> Rain components allowed only in accumulated format! Check your data!')
        raise IOError('Data type is not allowed!')

    var_values_step_start = None
    var_values_out = np.zeros([var_shape_in[0], var_shape_in[1], var_shape_in[2]])
    var_values_out[:, :, :] = np.nan
    for var_step in range(0, var_shape_in[2]):

        var_values_step = var_values_in[:, :, var_step]

        var_values_step[var_values_step < 0.0] = 0.0
        var_values_out[:, :, var_step] = var_values_step / var_scale_factor

    var_da_out = create_darray_3d(var_values_out, var_time, var_geo_x, var_geo_y,
                                  dim_key_time='time', dim_key_x='longitude', dim_key_y='latitude',
                                  dim_name_x='longitude', dim_name_y='latitude', dim_name_time='time',
                                  dims_order=['latitude', 'longitude', 'time'])

    var_dset_out = var_da_out.to_dataset(name=var_name)

    return var_dset_out
# -------------------------------------------------------------------------------------
