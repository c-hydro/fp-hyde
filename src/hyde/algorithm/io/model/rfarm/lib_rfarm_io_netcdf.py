# -------------------------------------------------------------------------------------
# Libraries
import copy
import logging
import os

import numpy as np
import pandas as pd
import xarray as xr

from src.hyde.dataset.nwp.wrf.lib_wrf_variables import computeRain
from src.hyde.algorithm.io.nwp.gfs.lib_gfs_io_generic import reshape_var3d
from src.hyde.algorithm.settings.model.rfarm.lib_rfarm_args import logger_name

log_stream = logging.getLogger(logger_name)

# Debug
# import matplotlib.pylab as plt
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read data for wrf
def read_data_wrf(file_list,
                  var_name='RAINNC', var_geox='lon', var_geoy='lat', var_time='Time',
                  time_step_start=None, time_step_end=None):

    # Create list of filename
    if isinstance(file_list, str):
        file_list = [file_list]

    file_list_break = None
    file_list_n = file_list.__len__()

    if time_step_start is None:
        time_step_start = 0
    if time_step_end is None:
        time_step_end = file_list_n

    file_available = []
    for file_id, file_step in enumerate(file_list):
        if os.path.exists(file_step):
            file_available.append(file_step)
            file_list_break = False
        else:
            log_stream.warning(' ====> File not found [' + file_step + '] - Following files are not included!')
            file_list_break = True
            break

    file_available_n = file_available.__len__()
    if file_available_n != file_list_n:
        log_stream.warning(' ====> Available file(s) are ' + str(file_available_n) +
                           ' -- Expected file(s) are ' + str(file_list_n))
        log_stream.warning(' ====> Time steps are limited to ' + str(file_available_n))

        file_step_start = time_step_start
        file_step_end = file_available_n
    else:
        file_step_start = time_step_start
        file_step_end = time_step_end

    # Get data using a list of filename
    file_handle = xr.open_mfdataset(file_available)
    # Get data values
    var_data_tyx = file_handle[var_name][file_step_start:file_step_end, :, :]

    # Get time steps
    var_time_array = file_handle[var_time].values
    var_time_idx = pd.DatetimeIndex(var_time_array)[file_step_start:file_step_end]

    # Get geographical information
    var_geox_1d = file_handle[var_geox].values
    var_geoy_1d = file_handle[var_geoy].values
    [var_geox_2d, var_geoy_2d] = np.meshgrid(var_geox_1d, var_geoy_1d, sparse=False, indexing='xy')
    var_geoy_2d = np.flipud(var_geoy_2d)

    # Set correct south-north and west-east direction(s)
    var_data_xyt = np.zeros([var_data_tyx.shape[1], var_data_tyx.shape[2], file_list_n])
    var_data_xyt[:, :, :] = np.nan
    for i in range(0, var_data_tyx.shape[0]):
        var_data_xyt[:, :, i] = np.flipud(var_data_tyx[i, :, :])

    var_time_freq = var_time_idx.inferred_freq
    var_time_first = var_time_idx[0]
    var_time_last = var_time_idx[-1]
    if file_list_break:
        var_time_idx = pd.date_range(start=var_time_first, freq=var_time_freq, periods=file_list_n)

    time_issue = False
    if var_time_freq is None:
        var_time_exp = pd.date_range(start=var_time_first, end=var_time_last, periods=var_data_tyx.shape[0])
        for time_idx, time_exp in zip(var_time_idx, var_time_exp):
            time_idx = pd.DatetimeIndex([time_idx])
            time_exp = pd.DatetimeIndex([time_exp])
            if not time_idx.equals(time_exp):
                log_stream.warning(
                    ' ====> Time definition is not correct - Get: ' + str(time_idx[0]) + ' Exp: ' + str(time_exp[0]))
                time_issue = True
                break
        if time_issue:
            var_time_idx = var_time_exp
            log_stream.warning(
                ' ====> Time idx derived by file attribute have to be changed according with time exp')

    # DEBUG START
    # import matplotlib.pylab as plt
    # plt.figure()
    # plt.imshow(var_geox_2d)
    # plt.colorbar();
    # plt.figure()
    # plt.imshow(var_geoy_2d)
    # plt.colorbar()
    # plt.figure()
    # plt.imshow(var_data_tyx[2, :, :])
    # plt.clim(0, 20)
    # plt.figure()
    # plt.imshow(var_data_xyt[:, :, 2])
    # plt.clim(0, 20)
    # plt.show()
    # DEBUG END

    return var_data_xyt, var_time_idx, var_geox_2d, var_geoy_2d
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to convert data for wrf
def convert_data_wrf(var_data_raw, var_units, var_type_feat='accumulated'):
    var_data_cmp = computeRain(var_data_raw, oVarUnits=[var_units],  oVarType=[var_type_feat])

    var_data_n = var_data_cmp.shape[2]

    var_data_def = np.zeros([var_data_cmp.shape[0], var_data_cmp.shape[1], var_data_cmp.shape[2]])
    for i in range(0, var_data_n):
        var_data_step = var_data_cmp[:, :, i]

        if np.any(var_data_step < 0):
            log_stream.warning(' ====> Some values are less then 0.0 at step ' + str(i + 1) + ' -- Set to 0.0')
            var_data_step[var_data_step <= 0.0] = 0.0

        if np.all(np.isnan(var_data_step)):
            log_stream.warning(' ====> All values are NaNs at step ' + str(i + 1) + ' -- Set to 0.0')
            var_data_step[:, :] = 0.0
        elif np.any(np.isnan(var_data_step)):
            log_stream.warning(' ====> Some values are NaNs at step ' + str(i + 1) + ' -- Set to 0.0')
            var_data_step[np.isnan(var_data_step)] = 0.0

        var_data_def[:, :, i] = var_data_step

    return var_data_def
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to convert time for wrf
def convert_time_wrf(var_time_cmp, var_time_exp=None, var_type_feat='accumulated'):

    if var_type_feat == 'accumulated':
        var_time_cmp = var_time_cmp[1:]
    elif var_type_feat == 'istantaneous':
        var_time_cmp = var_time_cmp[0:]
    else:
        log_stream.error(' ====> Data type are not defined correctly')
        raise TypeError

    if var_time_exp.equals(var_time_cmp):
        var_time_series = var_time_exp
    else:
        var_freq_inferred = var_time_cmp.inferred_freq

        if var_freq_inferred is not None:
            var_time_series = pd.date_range(start=var_time_cmp[0],
                                            periods=list(var_time_cmp.values).__len__(),
                                            freq=var_freq_inferred)
        else:
            log_stream.error(' ====> Data frequency is not defined correctly')
            raise TypeError(' Data frequency is equal to ' + str(var_freq_inferred))

    return var_time_series
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read gfs025 forecast

def read_data_gfs_025(file_name, tag_time='time', tag_geo_x='lon', tag_geo_y='lat',
                var_units='kg m**-2', var_step_type=None):

    # Parse args
    #var_name = list(var_name)[0]
    #var_units = var_units[0]
    #var_step_type = var_step_type[0]

    # Starting info
    log_stream.info(' --> Open file ' + file_name + ' ... ')

    # Open datasets
    dst_tmp = xr.open_dataset(file_name)

    if dst_tmp.dims.__len__() > 3:
        if 'height' in list(dst_tmp.dims):
            dst = dst_tmp.squeeze('height')
            dst = dst.drop('height')
        else:
            log_stream.warning(
                ' ==> Datasets has more then 3 dimensions. Add the name of extra-variable to remove it from datasets')
    else:
        dst = dst_tmp

    # Get variables ALL and DATA
    var_list_all = list(dst.variables)
    var_list_data = list(dst.data_vars)

    # Get time, geo x and geo y
    log_stream.info(' --->  Get time, geo_x and geo_y data ... ')
    if tag_time in var_list_all:
        da_time = dst[tag_time]
    else:
        log_stream.error(' ==> Time dimension name is not in the variables list of grib file')
        raise IOError(' ==> Check the time dimension!')
    if tag_geo_x in var_list_all:
        da_geo_x = dst[tag_geo_x]
    else:
        log_stream.error(' ==> GeoX dimension name is not in the variables list of grib file')
        raise IOError(' ==> Check the GeoX dimension!')
    if tag_geo_y in var_list_all:
        da_geo_y = dst[tag_geo_y]
    else:
        log_stream.error(' ==> GeoY dimension name is not in the variables list of grib file')
        raise IOError(' ==> Check the GeoY dimension!')
    log_stream.info(' --->  Get time, geo_x and geo_y data ... DONE')

    # Get data
    da_var = []
    for var_list_step in var_list_data:
        log_stream.info(' --->  Get ' + var_list_step + ' data ... ')
        da_step = dst[var_list_step]
        da_var.append(da_step)
        log_stream.info(' --->  Get ' + var_list_step + ' data ... DONE')

    # Ending info
    log_stream.info(' --> Open file ' + file_name + ' ... DONE')

    # Start Debug
    #mat = da_values[0].values
    #plt.figure()
    #plt.imshow(mat[0,:,:])
    #plt.colorbar()
    #plt.show()
    # End Debug

    if var_step_type is None:
        var_step_type = ['accum']
    if var_units is None:
        var_units = ['m']

    # Get values
    var_da_in = da_var[0]
    var_values_in = var_da_in.values
    var_dims_in = var_da_in.dims

    var_time = da_time
    var_geo_x = da_geo_x
    var_geo_y = da_geo_y

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
    if (var_step_type == 'accum') or (var_step_type == 'accumulated'):

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

            [var_geox_2d, var_geoy_2d] = np.meshgrid(var_geo_x, var_geo_y, sparse=False, indexing='xy')

    elif (var_step_type == 'inst') or (var_step_type == 'instantaneous'):
        var_values_out = copy.deepcopy(var_values_in)
        var_values_in[var_values_in < 0.0] = 0.0
        [var_geox_2d, var_geoy_2d] = np.meshgrid(var_geo_x, var_geo_y, sparse=False, indexing='xy')

    # DEBUG START
    #import matplotlib.pylab as plt
    #plt.figure()
    #plt.imshow(var_geox_2d)
    #plt.colorbar();
    #plt.figure()
    #plt.imshow(var_geoy_2d)
    ##plt.colorbar()
    #plt.figure()
    #plt.imshow(var_values_out[:, :, 0])
    #plt.clim(0, 20)
    #plt.show(block=True)
    # DEBUG END

    return var_values_out, var_time, var_geox_2d, var_geoy_2d
# -------------------------------------------------------------------------------------