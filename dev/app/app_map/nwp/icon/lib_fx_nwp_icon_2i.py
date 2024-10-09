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
def compute_rain(var_dframe, var_time_reference,
                 var_attrs=None,
                 var_name_time='time', var_name_geo_x='longitude', var_name_geo_y='latitude',
                 var_type='accumulated', var_period=None,
                 var_decimals=3, **kwargs):

    # get variable units
    var_units = check_attributes('units', var_attrs)
    # get variable scale factor
    var_scale_factor = check_attributes('scale_factor', var_attrs)

    if var_units.lower() != 'kg m**-2' and var_units.lower() != 'mm':
        alg_logger.error(' ===> Rain units must be "kg m**-2" or "mm"')
        raise NotImplementedError('Case not implemented yet')
    if var_type != 'accumulated':
        alg_logger.error(' ===> Rain type must be "accumulated"')
        raise NotImplementedError('Case not implemented yet')

    if var_period is None:
        var_period = 1
    if var_period != 1:

        time_n = var_dframe.shape[0]

        var_data_in = var_dframe.values
        var_data_out = np.zeros_like(var_data_in)
        for time_i in range(0, time_n):

            tmp_data = var_data_in[time_i, :, :]
            tmp_data[tmp_data < 0] = 0
            tmp_data = np.around(tmp_data, decimals=var_decimals)
            var_data_out[time_i, :, :] = tmp_data

        var_dframe.values = var_data_out

    # apply scale factor
    var_dframe.values = var_dframe.values * var_scale_factor
    # apply units definition
    var_attrs['units'] = 'mm'

    return var_dframe, var_attrs
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to compute air temperature field(s)
def compute_air_temperature(var_dframe, var_time_reference,
                            var_attrs=None,
                            var_name_time='time', var_name_geo_x='longitude', var_name_geo_y='latitude',
                            var_type='instantaneous', **kwargs):

    # get variable units
    var_units = check_attributes('units', var_attrs)
    # get variable scale factor
    var_scale_factor = check_attributes('scale_factor', var_attrs)

    if var_units.upper() != 'K' and var_units.upper() != 'C':
        alg_logger.error(' ===> Air Temperature units must be "K" or "C"')
        raise NotImplementedError('Case not implemented yet')
    if var_type != 'instantaneous':
        alg_logger.error(' ===> Air Temperature type must be "instantaneous"')
        raise NotImplementedError('Case not implemented yet')
    else:
        if var_name_time in var_dframe.dims:

            time_range = pd.DatetimeIndex(var_dframe[var_name_time].values)
            time_idx = list(var_dframe.dims).index(var_name_time)

            if time_range[0] == var_time_reference:
                if time_idx == 0:
                    var_dframe = var_dframe[1:, :, :]
                elif time_idx == 1:
                    var_dframe = var_dframe[:, 1:, :]
                elif time_idx == 2:
                    var_dframe = var_dframe[:, :, 1:]

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
def compute_wind_component(var_dframe, var_time_reference,
                           var_attrs=None,
                           var_name_time='time', var_name_geo_x='longitude', var_name_geo_y='latitude',
                           var_type='instantaneous', **kwargs):

    # get variable units
    var_units = check_attributes('units', var_attrs)
    # get variable scale factor
    var_scale_factor = check_attributes('scale_factor', var_attrs)

    if var_units.lower() != 'm s**-1' and var_units.lower() != 'm s-1':
        alg_logger.error(' ===> Wind component units must be "m s**-1" or "m s-1"')
        raise NotImplementedError('Case not implemented yet')
    if var_type != 'instantaneous':
        alg_logger.error(' ===> Wind component type must be "instantaneous"')
        raise NotImplementedError('Case not implemented yet')
    else:
        if var_name_time in var_dframe.dims:

            time_range = pd.DatetimeIndex(var_dframe[var_name_time].values)
            time_idx = list(var_dframe.dims).index(var_name_time)

            if time_range[0] == var_time_reference:
                if time_idx == 0:
                    var_dframe = var_dframe[1:, :, :]
                elif time_idx == 1:
                    var_dframe = var_dframe[:, 1:, :]
                elif time_idx == 2:
                    var_dframe = var_dframe[:, :, 1:]

    # apply scale factor
    var_dframe.values = var_dframe.values * var_scale_factor

    # apply units definition
    var_attrs['units'] = 'm s-1'

    return var_dframe, var_attrs
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to compute relative humidity field(s)
def compute_relative_humidity(var_dframe, var_time_reference,
                              var_attrs=None,
                              var_name_time='time', var_name_geo_x='longitude', var_name_geo_y='latitude',
                              var_type='instantaneous', **kwargs):

    # get variable units
    var_units = check_attributes('units', var_attrs)
    # get variable scale factor
    var_scale_factor = check_attributes('scale_factor', var_attrs)

    if var_units.upper() != '%':
        alg_logger.error(' ===> Relative Humidity units must be "%"')
        raise NotImplementedError('Case not implemented yet')
    if var_type != 'instantaneous':
        alg_logger.error(' ===> Relative Humidity type must be "instantaneous"')
        raise NotImplementedError('Case not implemented yet')
    else:
        if var_name_time in var_dframe.dims:

            time_range = pd.DatetimeIndex(var_dframe[var_name_time].values)
            time_idx = list(var_dframe.dims).index(var_name_time)

            if time_range[0] == var_time_reference:
                if time_idx == 0:
                    var_dframe = var_dframe[1:, :, :]
                elif time_idx == 1:
                    var_dframe = var_dframe[:, 1:, :]
                elif time_idx == 2:
                    var_dframe = var_dframe[:, :, 1:]

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
def compute_incoming_radiation(var_dframe, var_time_reference,
                               var_attrs=None,
                               var_name_time='time', var_name_geo_x='longitude', var_name_geo_y='latitude',
                               var_type='average', **kwargs):

    # get variable units
    var_units = check_attributes('units', var_attrs)
    # get variable scale factor
    var_scale_factor = check_attributes('scale_factor', var_attrs)

    if var_units != 'W m**-2' and var_units != 'W m-2':
        alg_logger.error(' ===> Incoming Radiation units must be "W m**-2" or "W m-2"')
        raise NotImplementedError('Case not implemented yet')
    if var_type != 'average':
        alg_logger.error(' ===> Incoming Radiation type must be "average"')
        raise NotImplementedError('Case not implemented yet')
    else:

        time_idx = list(var_dframe.dims).index(var_name_time)
        geo_x_idx = list(var_dframe.dims).index(var_name_geo_x)
        geo_y_idx = list(var_dframe.dims).index(var_name_geo_y)

        values_src = var_dframe.values
        values_sum = np.zeros(shape=(values_src.shape[geo_y_idx], values_src.shape[geo_x_idx]))
        for n in range(0, values_src.shape[time_idx]):

            values_avg = values_src[n, :, :]

            values_ist = n * values_avg - values_sum
            values_sum = values_sum + values_ist

            values_ist[values_ist < 0.0] = 0.0

            var_dframe.values[n, :, :] = values_ist

    # apply scale factor
    var_dframe.values = var_dframe.values * var_scale_factor

    # apply units definition
    var_attrs['units'] = 'W m-2'

    return var_dframe, var_attrs
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to compute surface albedo field(s)
def compute_surface_albedo(var_dframe, var_time_reference,
                           var_attrs=None,
                           var_name_time='time', var_name_geo_x='longitude', var_name_geo_y='latitude',
                           var_type='instantaneous', **kwargs):

    # get variable units
    var_units = check_attributes('units', var_attrs)
    # get variable scale factor
    var_scale_factor = check_attributes('scale_factor', var_attrs)

    if var_units.upper() != '%':
        alg_logger.error(' ===> Surface Albedo units must be "%"')
        raise NotImplementedError('Case not implemented yet')
    if var_type != 'instantaneous':
        alg_logger.error(' ===> Surface Albedo type must be "instantaneous"')
        raise NotImplementedError('Case not implemented yet')
    else:
        if var_name_time in var_dframe.dims:

            time_range = pd.DatetimeIndex(var_dframe[var_name_time].values)
            time_idx = list(var_dframe.dims).index(var_name_time)

            if time_range[0] == var_time_reference:
                if time_idx == 0:
                    var_dframe = var_dframe[1:, :, :]
                elif time_idx == 1:
                    var_dframe = var_dframe[:, 1:, :]
                elif time_idx == 2:
                    var_dframe = var_dframe[:, :, 1:]

    # apply scale factor
    var_dframe.values = var_dframe.values * var_scale_factor
    # apply limits
    var_dframe.values = var_dframe.values / 100

    # apply units definition
    var_attrs['units'] = '-'

    return var_dframe, var_attrs
# ----------------------------------------------------------------------------------------------------------------------
