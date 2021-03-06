"""
Library Features:

Name:          lib_gfs_025_variables
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '2020302'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging
import numpy as np
import pandas as pd

from src.hyde.algorithm.io.nwp.gfs.lib_gfs_io_generic import reshape_var3d, create_darray_3d
from src.hyde.algorithm.settings.nwp.gfs.lib_gfs_args import logger_name

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
def computeWindSpeed(var_dset, var_name,
                     var_time=None, var_geo_x=None, var_geo_y=None,
                     var_units=None, var_step_type=None):

    # Set args
    if var_step_type is None:
        var_step_type = ['instant']
    if var_units is None:
        var_units = ['m s**-1']
    if var_geo_y is None:
        var_geo_y = ['latitude']
    if var_geo_x is None:
        var_geo_x = ['longitude']
    if var_time is None:
        var_time = ['valid_time']

    # Parse args
    var_name_1 = list(var_name)[0]
    var_name_2 = list(var_name)[1]
    var_name_3 = list(var_name)[2]
    var_units = var_units[0]
    var_step_type = var_step_type[0]
    var_time = var_time[0]
    var_geo_x = var_geo_x[0]
    var_geo_y = var_geo_y[0]

    # Get values
    var_da_in_1 = var_dset[var_name_1]
    var_values_in_1 = var_da_in_1.values
    var_dims_in_1 = var_da_in_1.dims

    var_da_in_2 = var_dset[var_name_2]
    var_values_in_2 = var_da_in_2.values
    var_dims_in_2 = var_da_in_2.dims

    var_time = var_dset[var_name_1][var_time]
    var_geo_x = var_dset[var_name_1][var_geo_x]
    var_geo_y = var_dset[var_name_1][var_geo_y]

    if (var_dims_in_1[0] == 'step') or (var_dims_in_1[0] == 'time'):
        var_values_in_1 = reshape_var3d(var_values_in_1)
    var_shape_in_1 = var_values_in_1.shape

    if (var_dims_in_2[0] == 'step') or (var_dims_in_2[0] == 'time'):
        var_values_in_2 = reshape_var3d(var_values_in_2)
    var_shape_in_2 = var_values_in_2.shape

    # Check attributes
    if not (var_units == 'm s-1') and not (var_units == 'm s**-1'):
        log_stream.error(' ===> Wind components units are not allowed! Check your data!')
        raise IOError('Data units is not allowed!')
    if not (var_step_type == 'instant') and not (var_step_type == 'instantaneous'):
        log_stream.error(' ===> Wind components allowed only in istant format! Check your data!')
        raise IOError('Data type is not allowed!')
    if not var_shape_in_1 == var_shape_in_2:
        log_stream.error(' ===> Wind dimensions are not the same! Check your data!')
        raise IOError('Data dimensions are not allowed!')
    else:
        var_shape_in = list({var_shape_in_1, var_shape_in_2})[0]

    var_values_out = np.zeros([var_shape_in[0], var_shape_in[1], var_shape_in[2]])
    var_values_out[:, :, :] = np.nan
    for var_step in range(0, var_shape_in[2]):
        var_values_step_1 = var_values_in_1[:, :, var_step]
        var_values_step_2 = var_values_in_2[:, :, var_step]
        var_values_out[:, :, var_step] = np.sqrt(var_values_step_1 ** 2 + var_values_step_2 ** 2) * 0.7

    var_da_in_1 = create_darray_3d(var_values_in_1, var_time, var_geo_x, var_geo_y,
                                   dim_key_time='time', dim_key_x='longitude', dim_key_y='latitude',
                                   dim_name_x='longitude', dim_name_y='latitude', dim_name_time='time',
                                   dims_order=['latitude', 'longitude', 'time'])
    var_da_in_2 = create_darray_3d(var_values_in_2, var_time, var_geo_x, var_geo_y,
                                   dim_key_time='time', dim_key_x='longitude', dim_key_y='latitude',
                                   dim_name_x='longitude', dim_name_y='latitude', dim_name_time='time',
                                   dims_order=['latitude', 'longitude', 'time'])
    var_da_out = create_darray_3d(var_values_out, var_time, var_geo_x, var_geo_y,
                                  dim_key_time='time', dim_key_x='longitude', dim_key_y='latitude',
                                  dim_name_x='longitude', dim_name_y='latitude', dim_name_time='time',
                                  dims_order=['latitude', 'longitude', 'time'])

    var_dset_out = var_da_in_1.to_dataset(name=var_name_1)
    var_dset_out[var_name_2] = var_da_in_2
    var_dset_out[var_name_3] = var_da_out

    return var_dset_out
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

    if (var_dims_in[0] == 'step') or (var_dims_in[0] == 'time'):
        var_values_in = reshape_var3d(var_values_in)
    var_shape_in = var_values_in.shape

    # Check attributes
    if not (var_units == 'mm') and not (var_units == 'm'):
        log_stream.error(' ===> Rain components units are not allowed! Check your data!')
        raise IOError('Data units is not allowed!')
    if not (var_step_type == 'accum') and not (var_step_type == 'accumulated'):
        log_stream.error(' ===> Rain components allowed only in istant format! Check your data!')
        raise IOError('Data type is not allowed!')

    var_values_step_start = None
    var_values_out = np.zeros([var_shape_in[0], var_shape_in[1], var_shape_in[2]])
    var_values_out[:, :, :] = np.nan
    for var_step in range(0, var_shape_in[2]):

        var_values_step_tmp = var_values_in[:, :, var_step]

        if var_values_step_start is None:
            var_values_step_end = var_values_step_tmp
            var_values_step = var_values_step_end
            var_values_step_start = var_values_step_end
        else:
            var_values_step_end = var_values_step_tmp
            var_values_step = var_values_step_end - var_values_step_start
            var_values_step_start = var_values_step_end

        var_values_step[var_values_step < 0.0] = 0.0
        var_values_out[:, :, var_step] = var_values_step / var_scale_factor

    var_da_out = create_darray_3d(var_values_out, var_time, var_geo_x, var_geo_y,
                                  dim_key_time='time', dim_key_x='longitude', dim_key_y='latitude',
                                  dim_name_x='longitude', dim_name_y='latitude', dim_name_time='time',
                                  dims_order=['latitude', 'longitude', 'time'])

    var_dset_out = var_da_out.to_dataset(name=var_name)

    return var_dset_out
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute AirTemperature
def computeAirTemperature(var_dset, var_name,
                          var_time=None, var_geo_x=None, var_geo_y=None,
                          var_units=None, var_step_type=None):

    # Set args
    if var_step_type is None:
        var_step_type = ['instant']
    if var_units is None:
        var_units = ['K']
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

    if (var_dims_in[0] == 'step') or (var_dims_in[0] == 'time'):
        var_values_in = reshape_var3d(var_values_in)
    var_shape_in = var_values_in.shape

    # Check attributes
    if not (var_units == 'K'):
        log_stream.error(' ===> Air Temperature components units are not allowed! Check your data!')
        raise IOError('Data units is not allowed!')
    if not (var_step_type == 'instant') and not (var_step_type == 'instantaneous'):
        log_stream.error(' ===> Air Temperature components allowed only in istant format! Check your data!')
        raise IOError('Data type is not allowed!')

    var_values_out = np.zeros([var_shape_in[0], var_shape_in[1], var_shape_in[2]])
    var_values_out[:, :, :] = np.nan
    for var_step in range(0, var_shape_in[2]):
        var_values_step = var_values_in[:, :, var_step]
        var_values_out[:, :, var_step] = var_values_step - 273.15

    var_da_out = create_darray_3d(var_values_out, var_time, var_geo_x, var_geo_y,
                                  dim_key_time='time', dim_key_x='longitude', dim_key_y='latitude',
                                  dim_name_x='longitude', dim_name_y='latitude', dim_name_time='time',
                                  dims_order=['latitude', 'longitude', 'time'])

    var_dset_out = var_da_out.to_dataset(name=var_name)

    return var_dset_out
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute RelativeHumidity
def computeRelativeHumidity(var_dset, var_name,
                            var_time=None, var_geo_x=None, var_geo_y=None,
                            var_units=None, var_step_type=None):

    # Set args
    if var_step_type is None:
        var_step_type = ['instant']
    if var_units is None:
        var_units = ['%']
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

    if (var_dims_in[0] == 'step') or (var_dims_in[0] == 'time'):
        var_values_in = reshape_var3d(var_values_in)
    var_shape_in = var_values_in.shape

    # Check attributes
    if not (var_units == '%'):
        log_stream.error(' ===> Relative Humidity components units are not allowed! Check your data!')
        raise IOError('Data units is not allowed!')
    if not (var_step_type == 'instant') and not (var_step_type == 'instantaneous'):
        log_stream.error(' ===> Relative Humidity components allowed only in istant format! Check your data!')
        raise IOError('Data type is not allowed!')

    var_values_out = np.zeros([var_shape_in[0], var_shape_in[1], var_shape_in[2]])
    var_values_out[:, :, :] = np.nan
    for var_step in range(0, var_shape_in[2]):
        var_values_step = var_values_in[:, :, var_step]

        var_idx_up_step = np.where(var_values_step > 100)
        var_idx_down_step = np.where(var_values_step < 0)

        var_values_step[var_idx_up_step[0], var_idx_up_step[1]] = 100
        var_values_step[var_idx_down_step[0], var_idx_down_step[1]] = 0

        var_values_out[:, :, var_step] = var_values_step

    var_da_out = create_darray_3d(var_values_out, var_time, var_geo_x, var_geo_y,
                                  dim_key_time='time', dim_key_x='longitude', dim_key_y='latitude',
                                  dim_name_x='longitude', dim_name_y='latitude', dim_name_time='time',
                                  dims_order=['latitude', 'longitude', 'time'])

    var_dset_out = var_da_out.to_dataset(name=var_name)

    return var_dset_out
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute IncomingRadiation
def computeIncomingRadiation(var_dset, var_name,
                             var_time=None, var_geo_x=None, var_geo_y=None,
                             var_units=None, var_step_type=None,
                             var_interval_exp='H', var_avg_idx=6):

    # Set args
    if var_step_type is None:
        var_step_type = ['instant']
    if var_units is None:
        var_units = ['W m**-2']
    if var_geo_y is None:
        var_geo_y = ['latitude']
    if var_geo_x is None:
        var_geo_x = ['longitude']
    if var_time is None:
        var_time = ['valid_time']

    # Parse args
    var_name_1 = list(var_name)[0]
    var_name_2 = list(var_name)[1]
    var_name_3 = list(var_name)[2]
    var_units = var_units[0]
    var_step_type = var_step_type[0]
    var_time = var_time[0]
    var_geo_x = var_geo_x[0]
    var_geo_y = var_geo_y[0]

    # Get values
    var_da_in_1 = var_dset[var_name_1]
    var_values_in_1 = var_da_in_1.values
    var_dims_in_1 = var_da_in_1.dims

    var_da_in_2 = var_dset[var_name_2]
    var_values_in_2 = var_da_in_2.values
    var_dims_in_2 = var_da_in_2.dims

    var_time = var_dset[var_name_1][var_time]
    var_geo_x = var_dset[var_name_1][var_geo_x]
    var_geo_y = var_dset[var_name_1][var_geo_y]

    if (var_dims_in_1[0] == 'step') or (var_dims_in_1[0] == 'time'):
        var_values_in_1 = reshape_var3d(var_values_in_1)
    var_shape_in_1 = var_values_in_1.shape

    if (var_dims_in_2[0] == 'step') or (var_dims_in_2[0] == 'time'):
        var_values_in_2 = reshape_var3d(var_values_in_2)
    var_shape_in_2 = var_values_in_2.shape

    # Check attributes
    if not (var_units == 'W m-2') and not (var_units == 'W m**-2'):
        log_stream.error(' ===> IncomingRadiation components units are not allowed! Check your data!')
        raise IOError('Data units is not allowed!')
    if not (var_step_type == 'avg') and not (var_step_type == 'average'):
        log_stream.error(' ===> IncomingRadiation components allowed only in average format! Check your data!')
        raise IOError('Data type is not allowed!')
    if not var_shape_in_1 == var_shape_in_2:
        log_stream.error(' ===> IncomingRadiation dimensions are not the same! Check your data!')
        raise IOError('Data dimensions are not allowed!')
    else:
        var_shape_in = list({var_shape_in_1, var_shape_in_2})[0]

    var_interval_cmp = pd.Timedelta((var_time[1] - var_time[0]).values)
    if var_interval_cmp.resolution == var_interval_exp:

        idx_start = np.arange(0, var_shape_in[2], var_avg_idx).tolist()
        idx_end = np.arange(6, var_shape_in[2] + var_avg_idx, var_avg_idx).tolist()

    else:
        log_stream.error(' ===> IncomingRadiation step resolution is not allowed! Check your data!')
        raise NotImplemented('Step resolution is not allowed!')

    ts_values_out_1 = np.zeros([var_shape_in[2]])
    ts_values_out_1[:] = np.nan
    var_values_out_1 = np.zeros([var_shape_in[0], var_shape_in[1], var_shape_in[2]])
    var_values_out_1[:, :, :] = np.nan
    ts_values_out_2 = np.zeros([var_shape_in[2]])
    ts_values_out_2[:] = np.nan
    var_values_out_2 = np.zeros([var_shape_in[0], var_shape_in[1], var_shape_in[2]])
    var_values_out_2[:, :, :] = np.nan
    for idx_start_tmp, idx_end_tmp in zip(idx_start, idx_end):

        var_values_tmp_1 = var_values_in_1[:, :, idx_start_tmp:idx_end_tmp]
        var_values_tmp_2 = var_values_in_2[:, :, idx_start_tmp:idx_end_tmp]

        var_values_cmp_1 = None
        var_values_cmp_2 = None

        ts_values_partial_1 = np.zeros([var_avg_idx])
        ts_values_partial_1[:] = np.nan
        var_values_partial_1 = np.zeros([var_shape_in[0], var_shape_in[1], var_avg_idx])
        var_values_partial_1[:, :, :] = np.nan
        ts_values_partial_2 = np.zeros([var_avg_idx])
        ts_values_partial_2[:] = np.nan
        var_values_partial_2 = np.zeros([var_shape_in[0], var_shape_in[1], var_avg_idx])
        var_values_partial_2[:, :, :] = np.nan
        for i_tmp, i_avg_idx in enumerate(range(0, var_avg_idx)):

            i_tmp_end = i_tmp
            i_tmp_start = i_tmp + 1

            var_values_select_1 = var_values_tmp_1[:, :, i_avg_idx]
            var_values_select_2 = var_values_tmp_2[:, :, i_avg_idx]

            if var_values_cmp_1 is None:
                var_values_cmp_1 = var_values_select_1
                var_values_spool_1 = var_values_select_1
            else:
                var_values_cmp_1 = i_tmp_start * var_values_select_1 - i_tmp_end * var_values_spool_1
                var_values_spool_1 = var_values_select_1

            if var_values_cmp_2 is None:
                var_values_cmp_2 = var_values_select_2
                var_values_spool_2 = var_values_select_2
            else:
                var_values_cmp_2 = i_tmp_start * var_values_select_2 - i_tmp_end * var_values_spool_2
                var_values_spool_2 = var_values_select_2

            var_values_partial_1[:, :, i_tmp] = var_values_cmp_1
            ts_values_partial_1[i_tmp] = np.nanmean(var_values_cmp_1)
            var_values_partial_2[:, :, i_tmp] = var_values_cmp_2
            ts_values_partial_2[i_tmp] = np.nanmean(var_values_cmp_2)

        ts_values_out_1[idx_start_tmp:idx_end_tmp] = ts_values_partial_1
        var_values_out_1[:, :, idx_start_tmp:idx_end_tmp] = var_values_partial_1
        ts_values_out_2[idx_start_tmp:idx_end_tmp] = ts_values_partial_2
        var_values_out_2[:, :, idx_start_tmp:idx_end_tmp] = var_values_partial_2

    ts_values_out = np.zeros([var_shape_in[2]])
    ts_values_out[:] = np.nan
    var_values_out = np.zeros([var_shape_in[0], var_shape_in[1], var_shape_in[2]])
    var_values_out[:, :, :] = np.nan
    for var_step in range(0, var_shape_in[2]):
        var_values_step_1 = var_values_out_1[:, :, var_step]
        # var_values_step_2 = var_values_out_2[:, :, var_step]
        var_values_out[:, :, var_step] = var_values_step_1  # + var_values_step_2

        ts_values_out[var_step] = np.nanmean(var_values_out[:, :, var_step])

    var_da_out_1 = create_darray_3d(var_values_out_1, var_time, var_geo_x, var_geo_y,
                                    dim_key_time='time', dim_key_x='longitude', dim_key_y='latitude',
                                    dim_name_x='longitude', dim_name_y='latitude', dim_name_time='time',
                                    dims_order=['latitude', 'longitude', 'time'])
    var_da_out_2 = create_darray_3d(var_values_out_2, var_time, var_geo_x, var_geo_y,
                                    dim_key_time='time', dim_key_x='longitude', dim_key_y='latitude',
                                    dim_name_x='longitude', dim_name_y='latitude', dim_name_time='time',
                                    dims_order=['latitude', 'longitude', 'time'])
    var_da_out = create_darray_3d(var_values_out, var_time, var_geo_x, var_geo_y,
                                  dim_key_time='time', dim_key_x='longitude', dim_key_y='latitude',
                                  dim_name_x='longitude', dim_name_y='latitude', dim_name_time='time',
                                  dims_order=['latitude', 'longitude', 'time'])

    var_dset_out = var_da_out_1.to_dataset(name=var_name_1)
    var_dset_out[var_name_2] = var_da_out_2
    var_dset_out[var_name_3] = var_da_out

    return var_dset_out

# -------------------------------------------------------------------------------------
