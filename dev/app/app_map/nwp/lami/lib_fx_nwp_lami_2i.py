"""
Library Features:

Name:          lib_fx_nwp_lami_2i
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20241003'
Version:       '1.5.0'
"""


# ----------------------------------------------------------------------------------------------------------------------
# libraries
import logging

import numpy as np
import pandas as pd

from lib_info_args import logger_name, proj_epsg, time_format_datasets

# logging
logging.getLogger('rasterio').setLevel(logging.WARNING)

# set logger
alg_logger = logging.getLogger(logger_name)
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# check attributes availability
def check_attributes(attr_name, attr_dict):
    if attr_name in list(attr_dict.keys()):
        attr_value = attr_dict[attr_name]
    else:
        alg_logger.error(' ===> Attribute "' + attr_name + '" are not defined')
        raise NotImplementedError('Case not implemented yet')
    return attr_value
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to compute rain field(s)
def compute_rain(var_dframe, var_attrs=None,
                 var_name_time='time', var_period=None, var_frequency='1H',
                 var_type='accumulated', **kwargs):

    # get variable units
    var_units = check_attributes('units', var_attrs)
    # get variable scale factor
    var_scale_factor = check_attributes('scale_factor', var_attrs)

    # check variable units
    if var_units.lower() != 'kg m**-2' and var_units.lower() != 'mm':
        alg_logger.error(' ===> Rain units must be "kg m**-2" or "mm"')
        raise NotImplementedError('Case not implemented yet')
    # check variable type
    if var_type != 'accumulated':
        alg_logger.error(' ===> Rain type must be "accumulated"')
        raise NotImplementedError('Case not implemented yet')
    # check time fields
    if var_name_time not in var_dframe.dims:
        alg_logger.error(' ===> Time dimension must be "time" or does not exist')
        raise NotImplementedError('Case not implemented yet')

    # get time information
    time_range = pd.DatetimeIndex(var_dframe[var_name_time].values)
    time_idx = list(var_dframe.dims).index(var_name_time)

    # check time index
    if time_idx != 0:
        alg_logger.error(' ===> Time index must be 0')
        raise NotImplementedError('Case not implemented yet')
    # check frequency
    if var_frequency != '1H':
        alg_logger.error(' ===> Rain frequency must be "1H"')
        raise NotImplementedError('Case not implemented yet')

    # select variable period
    if var_period is not None:
        idx_start, idx_end = var_period[0], var_period[1]
        var_dframe = var_dframe[idx_start:idx_end, :, :]

    # apply scale factor
    var_dframe.values = var_dframe.values * var_scale_factor
    # apply units definition
    var_attrs['units'] = 'mm'

    return var_dframe, var_attrs
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to compute air temperature field(s)
def compute_air_temperature(var_dframe, var_attrs=None,
                            var_name_time='time', var_period=None, var_frequency='1H',
                            var_type='instantaneous', **kwargs):

    # get variable units
    var_units = check_attributes('units', var_attrs)
    # get variable scale factor
    var_scale_factor = check_attributes('scale_factor', var_attrs)

    # check variable units
    if var_units.upper() != 'K' and var_units.upper() != 'C':
        alg_logger.error(' ===> Air Temperature units must be "K" or "C"')
        raise NotImplementedError('Case not implemented yet')
    # check variable type
    if var_type != 'instantaneous':
        alg_logger.error(' ===> Air Temperature type must be "instantaneous"')
        raise NotImplementedError('Case not implemented yet')
    # check time fields
    if var_name_time not in var_dframe.dims:
        alg_logger.error(' ===> Time dimension must be "time" or does not exist')
        raise NotImplementedError('Case not implemented yet')

    # get time information
    time_range = pd.DatetimeIndex(var_dframe[var_name_time].values)
    time_idx = list(var_dframe.dims).index(var_name_time)

    # check time index
    if time_idx != 0:
        alg_logger.error(' ===> Time index must be 0')
        raise NotImplementedError('Case not implemented yet')
    # check frequency
    if var_frequency != '1H':
        alg_logger.error(' ===> Air Temperature frequency must be "1H"')
        raise NotImplementedError('Case not implemented yet')

    # select variable period
    if var_period is not None:
        idx_start, idx_end = var_period[0], var_period[1]
        var_dframe = var_dframe[idx_start:idx_end, :, :]

    # apply scale factor
    var_dframe = var_dframe * var_scale_factor
    # apply conversion from K to C
    if var_units == 'K':
        var_dframe.values = var_dframe.values - 273.15
    # apply units definition
    var_attrs['units'] = 'C'

    return var_dframe, var_attrs
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to compute wind component field(s)
def compute_wind_component(var_dframe, var_attrs=None,
                           var_name_time='time', var_period=None, var_frequency='1H',
                           var_type='instantaneous', **kwargs):

    # get variable units
    var_units = check_attributes('units', var_attrs)
    # get variable scale factor
    var_scale_factor = check_attributes('scale_factor', var_attrs)

    # check variable units
    if var_units.lower() != 'm s**-1' and var_units.lower() != 'm s-1':
        alg_logger.error(' ===> Wind component units must be "m s**-1" or "m s-1"')
        raise NotImplementedError('Case not implemented yet')
    # check variable type
    if var_type != 'instantaneous':
        alg_logger.error(' ===> Wind component type must be "instantaneous"')
        raise NotImplementedError('Case not implemented yet')
    # check time fields
    if var_name_time not in var_dframe.dims:
        alg_logger.error(' ===> Time dimension must be "time" or does not exist')
        raise NotImplementedError('Case not implemented yet')

    # get time information
    time_range = pd.DatetimeIndex(var_dframe[var_name_time].values)
    time_idx = list(var_dframe.dims).index(var_name_time)

    # check time index
    if time_idx != 0:
        alg_logger.error(' ===> Time index must be 0')
        raise NotImplementedError('Case not implemented yet')
    # check frequency
    if var_frequency != '1H':
        alg_logger.error(' ===> Wind component frequency must be "1H"')
        raise NotImplementedError('Case not implemented yet')

    # select variable period
    if var_period is not None:
        idx_start, idx_end = var_period[0], var_period[1]
        var_dframe = var_dframe[idx_start:idx_end, :, :]

    # apply scale factor
    var_dframe.values = var_dframe.values * var_scale_factor

    # apply units definition
    var_attrs['units'] = 'm s-1'

    return var_dframe, var_attrs
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to compute relative humidity field(s)
def compute_relative_humidity(var_dframe, var_attrs=None,
                              var_name_time='time', var_period=None, var_frequency='1H',
                              var_type='instantaneous', **kwargs):

    # get variable units
    var_units = check_attributes('units', var_attrs)
    # get variable scale factor
    var_scale_factor = check_attributes('scale_factor', var_attrs)

    # check variable units
    if var_units.upper() != '%':
        alg_logger.error(' ===> Relative Humidity units must be "%"')
        raise NotImplementedError('Case not implemented yet')
    # check variable type
    if var_type != 'instantaneous':
        alg_logger.error(' ===> Relative Humidity type must be "instantaneous"')
        raise NotImplementedError('Case not implemented yet')
    # check time fields
    if var_name_time not in var_dframe.dims:
        alg_logger.error(' ===> Time dimension must be "time" or does not exist')
        raise NotImplementedError('Case not implemented yet')

    # get time information
    time_range = pd.DatetimeIndex(var_dframe[var_name_time].values)
    time_idx = list(var_dframe.dims).index(var_name_time)

    # check time index
    if time_idx != 0:
        alg_logger.error(' ===> Time index must be 0')
        raise NotImplementedError('Case not implemented yet')
    # check frequency
    if var_frequency != '1H':
        alg_logger.error(' ===> Relative Humidity frequency must be "1H"')
        raise NotImplementedError('Case not implemented yet')

    # select variable period
    if var_period is not None:
        idx_start, idx_end = var_period[0], var_period[1]
        var_dframe = var_dframe[idx_start:idx_end, :, :]

    # apply scale factor
    var_dframe.values = var_dframe.values * var_scale_factor
    # apply limits
    var_dframe.values[var_dframe.values > 100] = 100
    var_dframe.values[var_dframe.values < 0] = 0
    # apply units definition
    var_attrs['units'] = '%'

    return var_dframe, var_attrs
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to compute incoming radiation field(s)
def compute_incoming_radiation(var_dframe, var_attrs=None,
                               var_name_time='time', var_name_geo_x='longitude', var_name_geo_y='latitude',
                               var_period=None, var_frequency='1H',
                               var_type='average', **kwargs):

    # get variable units
    var_units = check_attributes('units', var_attrs)
    # get variable scale factor
    var_scale_factor = check_attributes('scale_factor', var_attrs)

    # check variable units
    if var_units != 'W m**-2' and var_units != 'W m-2':
        alg_logger.error(' ===> Incoming Radiation units must be "W m**-2" or "W m-2"')
        raise NotImplementedError('Case not implemented yet')
    # check variable type
    if var_type != 'average':
        alg_logger.error(' ===> Incoming Radiation type must be "average"')
        raise NotImplementedError('Case not implemented yet')
    # check time fields
    if var_name_time not in var_dframe.dims:
        alg_logger.error(' ===> Time dimension must be "time" or does not exist')
        raise NotImplementedError('Case not implemented yet')

    # get time information
    time_range = pd.DatetimeIndex(var_dframe[var_name_time].values)
    time_idx = list(var_dframe.dims).index(var_name_time)

    # check time index
    if time_idx != 0:
        alg_logger.error(' ===> Time index must be 0')
        raise NotImplementedError('Case not implemented yet')
    # check frequency
    if var_frequency != '1H':
        alg_logger.error(' ===> Incoming Radiation frequency must be "1H"')
        raise NotImplementedError('Case not implemented yet')

    # get geo x information
    geo_x_idx = list(var_dframe.dims).index(var_name_geo_x)
    # check geo x index
    if geo_x_idx != 2:
        alg_logger.error(' ===> Geo x index must be 2')
        raise NotImplementedError('Case not implemented yet')

    # get geo y information
    geo_y_idx = list(var_dframe.dims).index(var_name_geo_y)
    # check geo x index
    if geo_y_idx != 1:
        alg_logger.error(' ===> Geo y index must be 1')
        raise NotImplementedError('Case not implemented yet')

    # select variable period
    if var_period is not None:
        idx_start, idx_end = var_period[0], var_period[1]
        var_dframe = var_dframe[idx_start:idx_end, :, :]

    # compute variable field(s)
    n = var_dframe.shape[0]
    values_src = var_dframe.values
    values_sum = np.zeros(shape=(values_src.shape[geo_y_idx], values_src.shape[geo_x_idx]))
    for i in range(0, n):

        values_avg = values_src[i, :, :]

        values_ist = i * values_avg - values_sum
        values_sum = values_sum + values_ist

        values_ist[values_ist < 0.0] = 0.0

        var_dframe.values[i, :, :] = values_ist

    # apply scale factor
    var_dframe.values = var_dframe.values * var_scale_factor

    # apply units definition
    var_attrs['units'] = 'W m-2'
    return var_dframe, var_attrs
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to compute surface albedo field(s)
def compute_surface_albedo(var_dframe, var_attrs=None,
                           var_name_time='time', var_period=None, var_frequency='1H',
                           var_type='instantaneous', **kwargs):

    # get variable units
    var_units = check_attributes('units', var_attrs)
    # get variable scale factor
    var_scale_factor = check_attributes('scale_factor', var_attrs)

    # check variable units
    if var_units.upper() != '%':
        alg_logger.error(' ===> Surface Albedo units must be "%"')
        raise NotImplementedError('Case not implemented yet')
    # check variable type
    if var_type != 'instantaneous':
        alg_logger.error(' ===> Surface Albedo type must be "instantaneous"')
        raise NotImplementedError('Case not implemented yet')
    # check time fields
    if var_name_time not in var_dframe.dims:
        alg_logger.error(' ===> Time dimension must be "time" or does not exist')
        raise NotImplementedError('Case not implemented yet')

    # get time information
    time_range = pd.DatetimeIndex(var_dframe[var_name_time].values)
    time_idx = list(var_dframe.dims).index(var_name_time)

    # check time index
    if time_idx != 0:
        alg_logger.error(' ===> Time index must be 0')
        raise NotImplementedError('Case not implemented yet')
    # check frequency
    if var_frequency != '1H':
        alg_logger.error(' ===> Relative Humidity frequency must be "1H"')
        raise NotImplementedError('Case not implemented yet')

    # select variable period
    if var_period is not None:
        idx_start, idx_end = var_period[0], var_period[1]
        var_dframe = var_dframe[idx_start:idx_end, :, :]

    # apply scale factor
    var_dframe.values = var_dframe.values * var_scale_factor
    # apply limits
    var_dframe.values = var_dframe.values / 100

    # apply units definition
    var_attrs['units'] = '-'

    return var_dframe, var_attrs
# ----------------------------------------------------------------------------------------------------------------------
