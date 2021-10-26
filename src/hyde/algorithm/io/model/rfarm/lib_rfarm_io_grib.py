# -------------------------------------------------------------------------------------
# Libraries
import logging
import numpy as np
import pandas as pd
import xarray as xr

from src.hyde.algorithm.settings.model.rfarm.lib_rfarm_args import time_format, logger_name

logging.getLogger("cfgrib").setLevel(logging.WARNING)
log_stream = logging.getLogger(logger_name)

# Debug
import matplotlib.pylab as plt
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to scale time
def time_scaling(time_range_in, time_range_out):
    time_size_in = time_range_in.shape[0]
    time_size_out = time_range_out.shape[0]

    if time_size_out > time_size_in:
        time_scale = int(time_size_out / time_size_in)
    elif time_size_out == time_size_in:
        time_scale = 1
    else:
        log_stream.error(' ==> Time scale definition not implemented!')
        raise NotImplementedError('Time scale definition not implemented yet!')

    return time_scale

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read data for ecmwf 0100
def read_data_ecmwf_0100(file_name, data_filters=None, data_var='tp',
                         tag_var_time='valid_time', tag_var_geo_x='longitude', tag_var_geo_y='latitude',
                         tag_dim_time='step', tag_dim_geo_x='longitude', tag_dim_geo_y='latitude'):

    # Starting info
    log_stream.info(' --> Open file ' + file_name + ' ... ')

    # Define data filter for default configuration
    if data_filters is None:
        data_filters = {'filter_by_keys': {'dataType': 'fc'}}

    # Open datasets
    dst = xr.open_dataset(file_name, engine='cfgrib', backend_kwargs=data_filters)

    # Get variables ALL and DATA
    var_list_all = list(dst.variables)
    var_list_data = list(dst.data_vars)

    # Get time, geo x and geo y
    log_stream.info(' --->  Get time, geo_x and geo_y data ... ')
    if tag_var_time in var_list_all:
        da_time = dst[tag_var_time]
    else:
        log_stream.error(' ==> Time dimension name is not in the variables list of grib file')
        raise IOError(' ==> Check the time dimension!')
    if tag_var_geo_x in var_list_all:
        da_geo_x = dst[tag_var_geo_x]
    else:
        log_stream.error(' ==> GeoX dimension name is not in the variables list of grib file')
        raise IOError(' ==> Check the GeoX dimension!')
    if tag_var_geo_y in var_list_all:
        da_geo_y = dst[tag_var_geo_y]
    else:
        log_stream.error(' ==> GeoY dimension name is not in the variables list of grib file')
        raise IOError(' ==> Check the GeoY dimension!')
    log_stream.info(' --->  Get time, geo_x and geo_y data ... DONE')

    # Get data
    if data_var in var_list_data:
        da_var = dst[data_var]
    else:
        log_stream.error(' ==> Variable name ' + data_var + ' is not in the variables list of grib file')
        raise IOError(' ==> Check the variable datasets!')

    da_dims = list(da_var.dims)
    if tag_dim_time not in da_dims:
        log_stream.error(' ==> Dimension name ' + tag_dim_time + ' is not in the dimensions list of grib file')
        raise IOError(' ==> Check the dimension name!')
    if tag_dim_geo_x not in da_dims:
        log_stream.error(' ==> Dimension name ' + tag_dim_geo_x + ' is not in the dimensions list of grib file')
        raise IOError(' ==> Check the dimension name!')
    if tag_dim_geo_y not in da_dims:
        log_stream.error(' ==> Dimension name ' + tag_dim_geo_y + ' is not in the dimensions list of grib file')
        raise IOError(' ==> Check the dimension name!')

    # Ending info
    log_stream.info(' --> Open file ' + file_name + ' ... DONE')

    return da_var, da_time, da_geo_x, da_geo_y
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to adjust ecmwf 0100 datasets
def adjust_data_ecmwf_0100(da_var, da_time, da_geo_x, da_geo_y,
                           tag_var_time='valid_time', tag_var_geo_x='longitude', tag_var_geo_y='latitude',
                           tag_dim_time='step', tag_dim_geo_x='longitude', tag_dim_geo_y='latitude'
                           ):

    da_dims = list(da_var.dims)
    idx_dim_time = da_dims.index(tag_dim_time)

    if (list(da_geo_y.dims).__len__() == 1) and (list(da_geo_x.dims).__len__() == 1):
        tmp_point_x = da_geo_x.values
        tmp_point_y = da_geo_y.values
        tmp_geo_x, tmp_geo_y = np.meshgrid(tmp_point_x, tmp_point_y)
    elif (list(da_geo_y.dims).__len__() == 2) and (list(da_geo_x.dims).__len__() == 2):
        tmp_geo_x = da_geo_x.values
        tmp_geo_y = da_geo_y.values
    else:
        log_stream.error(' ==> Longitude and Latitude dimensions are not equal.')
        raise IOError(' ==> Check the dimensions of Longitude and Latitude')

    if idx_dim_time == 0:

        geo_y_upper = tmp_geo_y[0, 0]
        geo_y_lower = tmp_geo_y[-1, 0]
        if geo_y_lower > geo_y_upper:
            values_geo_y = np.flipud(tmp_geo_y)
            values_geo_x = tmp_geo_x
        else:
            values_geo_y = tmp_geo_y
            values_geo_x = tmp_geo_x

        values_raw = da_var.values
        values_var = np.zeros(shape=[values_raw.shape[1], values_raw.shape[2], values_raw.shape[0]])
        values_var[:, :, :] = np.nan
        for i in range(0, values_raw.shape[0]):
            if geo_y_lower > geo_y_upper:
                values_tmp = np.flipud(values_raw[i, :, :])
            else:
                values_tmp = values_raw[i, :, :]
            values_var[:, :, i] = values_tmp

    else:
        log_stream.error(' ==> Time dimension index is not in a allowed position.')
        raise IOError(' ==> Check the position of time dimension!')

    values_time = pd.DatetimeIndex(da_time.values)

    return values_var,  values_time, values_geo_x, values_geo_y
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to adjust lami 2i datasets
def adjust_data_lami_2i(da_var, da_time, da_geo_x, da_geo_y,
                        tag_var_time='valid_time', tag_var_geo_x='longitude', tag_var_geo_y='latitude',
                        tag_dim_time='step', tag_dim_geo_x='x', tag_dim_geo_y='y'
                        ):

    da_dims = list(da_var.dims)
    idx_dim_time = da_dims.index(tag_dim_time)

    if idx_dim_time == 0:
        geo_y_upper = da_geo_y.values[0, 0]
        geo_y_lower = da_geo_y.values[-1, 0]
        if geo_y_lower > geo_y_upper:
            values_geo_y = np.flipud(da_geo_y.values)
            values_geo_x = da_geo_x.values

            values_raw = da_var.values
            values_var = np.zeros(shape=[values_raw.shape[1], values_raw.shape[2], values_raw.shape[0]])
            values_var[:, :, :] = np.nan
            for i in range(0, values_raw.shape[0]):
                values_tmp = np.flipud(values_raw[i, :, :])
                values_var[:, :, i] = values_tmp
        else:
            values_geo_y = da_geo_y.values
            values_geo_x = da_geo_x.values
            values_var = da_var.values

    else:
        log_stream.error(' ==> Time dimension index is not in a allowed position.')
        raise IOError(' ==> Check the position of time dimension!')

    values_time = pd.DatetimeIndex(da_time.values)

    return values_var,  values_time, values_geo_x, values_geo_y
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read data for lami-2i
def read_data_lami_2i(file_name, data_filters=None, data_var='tp',
                          tag_var_time='valid_time', tag_var_geo_x='longitude', tag_var_geo_y='latitude',
                          tag_dim_time='step', tag_dim_geo_x='x', tag_dim_geo_y='y'):

    # Starting info
    log_stream.info(' --> Open file ' + file_name + ' ... ')

    # Define data filter for default configuration
    if data_filters is None:
        data_filters = {'filter_by_keys': {'typeOfLevel': 'surface'}}

    # Open datasets
    dst = xr.open_dataset(file_name, engine='cfgrib', backend_kwargs=data_filters)

    # Get variables ALL and DATA
    var_list_all = list(dst.variables)
    var_list_data = list(dst.data_vars)

    # Get time, geo x and geo y
    log_stream.info(' --->  Get time, geo_x and geo_y data ... ')
    if tag_var_time in var_list_all:
        da_time = dst[tag_var_time]
    else:
        log_stream.error(' ==> Time dimension name is not in the variables list of grib file')
        raise IOError(' ==> Check the time dimension!')
    if tag_var_geo_x in var_list_all:
        da_geo_x = dst[tag_var_geo_x]
    else:
        log_stream.error(' ==> GeoX dimension name is not in the variables list of grib file')
        raise IOError(' ==> Check the GeoX dimension!')
    if tag_var_geo_y in var_list_all:
        da_geo_y = dst[tag_var_geo_y]
    else:
        log_stream.error(' ==> GeoY dimension name is not in the variables list of grib file')
        raise IOError(' ==> Check the GeoY dimension!')
    log_stream.info(' --->  Get time, geo_x and geo_y data ... DONE')

    # Get data
    if data_var in var_list_data:
        da_var = dst[data_var]
    else:
        log_stream.error(' ==> Variable name ' + data_var + ' is not in the variables list of grib file')
        raise IOError(' ==> Check the variable datasets!')

    da_dims = list(da_var.dims)
    if tag_dim_time not in da_dims:
        log_stream.error(' ==> Dimension name ' + tag_dim_time + ' is not in the dimensions list of grib file')
        raise IOError(' ==> Check the dimension name!')
    if tag_dim_geo_x not in da_dims:
        log_stream.error(' ==> Dimension name ' + tag_dim_geo_x + ' is not in the dimensions list of grib file')
        raise IOError(' ==> Check the dimension name!')
    if tag_dim_geo_y not in da_dims:
        log_stream.error(' ==> Dimension name ' + tag_dim_geo_y + ' is not in the dimensions list of grib file')
        raise IOError(' ==> Check the dimension name!')

    # Ending info
    log_stream.info(' --> Open file ' + file_name + ' ... DONE')

    return da_var, da_time, da_geo_x, da_geo_y
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to convert time for lami-2i
def convert_time_ecmwf_0100_OLD(var_time_idx, var_time_exp=None):
    var_time_date = computeTime(var_time_idx, time_format)[0]
    var_time_cmp = pd.to_datetime(var_time_date)

    if var_time_exp.equals(var_time_cmp):
        var_time_series = var_time_exp
    else:
        var_freq_inferred = var_time_cmp.inferred_freq
        var_time_series = pd.date_range(start=var_time_cmp[0],
                                        periods=list(var_time_cmp.values).__len__(),
                                        freq=var_freq_inferred)

    return var_time_series
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to convert data for lami-2i
def convert_data_ecmwf_0100_OLD(var_data_raw, var_units, var_type_feat='accumulated'):
    var_data_def = computeRain_ECMWF_0100(var_data_raw, oVarUnits=[var_units],  oVarType=[var_type_feat])
    return var_data_def
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read data for lami-2i
def read_data_lami_2i_OLD(file_handle, file_drv, var_name='Total Precipitation'):

    # Get geographical information
    var_geox, var_geoy = file_drv.oFileLibrary.getVarGeo_LAMI_2i(file_handle)

    # Get time steps
    var_time = file_drv.oFileLibrary.getVarTime_LAMI_2i(file_handle, var_name)[var_name]

    # Get data values
    var_data = file_drv.oFileLibrary.getVar3D_LAMI_2i(file_handle, var_name)[var_name]

    # Set correct south-north and west-east direction(s)
    var_n = var_data.shape[2]
    for i in range(0, var_n):
        var_data[:, :, i] = np.flipud(var_data[:, :, i])
    var_geoy = np.flipud(var_geoy)

    return var_data, var_time, var_geox, var_geoy
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to convert time for lami-2i
def convert_time_lami_2i_OLD(var_time_idx, var_time_exp=None):
    var_time_date = computeTime(var_time_idx, time_format)[0]
    var_time_cmp = pd.to_datetime(var_time_date)

    if var_time_exp.equals(var_time_cmp):
        var_time_series = var_time_exp
    else:
        var_freq_inferred = var_time_cmp.inferred_freq
        var_time_series = pd.date_range(start=var_time_cmp[0],
                                        periods=list(var_time_cmp.values).__len__(),
                                        freq=var_freq_inferred)

    return var_time_series
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to convert data for lami-2i
def convert_data_lami_2i_OLD(var_data_raw, var_units, var_type_feat='accumulated'):
    var_data_def = computeRain(var_data_raw, oVarUnits=[var_units],  oVarType=[var_type_feat])
    return var_data_def
# -------------------------------------------------------------------------------------
