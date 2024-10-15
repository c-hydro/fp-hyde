"""
Library Features:

Name:          lib_fx_nwp_generic
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20241003'
Version:       '1.5.0'
"""


# ----------------------------------------------------------------------------------------------------------------------
# libraries
import logging

import numpy as np
import pandas as pd

from lib_fx_astronomic_radiation import exec_astronomic_radiation, define_parameters, compute_cloud_factor

from lib_utils_io import create_darray
from lib_info_args import logger_name

# logging
logging.getLogger('rasterio').setLevel(logging.WARNING)

# set logger
alg_logger = logging.getLogger(logger_name)

# define default attributes for incoming radiation
default_attrs_k = {
    "mask_in": None, "mask_out": None, "mask_meaning": None, "type_in": "int", "type_out": "int",
    "min_value": 0, "max_value": None, "no_data": None,
    "scale_factor": 1, "missing_value": -9999.0, "fill_value": -9999.0,
    "format": "f4", "units": "W m**-2",
    "long_name": "mean surface net short-wave radiation flux"
}
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
# method to compute astronomic radiation field(s)
def compute_astronomic_radiation(var_data, var_time,
                                 var_geo_terrain=None, var_geo_x=None, var_geo_y=None, var_attrs=None,
                                 var_name_rain='rain', var_name_k='incoming_radiation',
                                 var_name_time='time', var_name_geo_x='longitude', var_name_geo_y='latitude',
                                 var_period=None, var_frequency='1H',
                                 var_type_rain='accumulated', var_type_inc_rad='instantaneous', **kwargs):

    # get rain data and attributes
    if var_name_rain in list(var_data.keys()):
        var_values_rain = var_data[var_name_rain]
    else:
        alg_logger.error(' ===> Rain data are not available')
        raise NotImplementedError('Case not implemented yet')
    if var_name_rain in list(var_attrs.keys()):
        var_attrs_rain = var_attrs[var_name_rain]
    else:
        alg_logger.error(' ===> Rain attributes are not available')
        raise NotImplementedError('Case not implemented yet')
    # get incoming radiation data and attributes (if available)
    if var_name_k in list(var_data.keys()):
        var_values_k = var_data[var_name_k]
    else:
        var_values_k = None
    if var_name_k in list(var_attrs.keys()):
        var_attrs_k = var_attrs[var_name_k]
    else:
        var_attrs_k = default_attrs_k

    # get rain variable units
    var_units_rain = check_attributes('units', var_attrs_rain)

    # check rain variable units
    if var_units_rain.lower() != 'mm':
        alg_logger.error(' ===> Rain units must be "mm"')
        raise NotImplementedError('Case not implemented yet')
    # check rain variable type
    if var_type_rain != 'accumulated':
        alg_logger.error(' ===> Rain type must be "accumulated"')
        raise NotImplementedError('Case not implemented yet')

    # get incoming radiation variable units
    var_units_k = check_attributes('units', var_attrs_k)

    # check incoming radiation variable units
    if var_units_k != 'W m**-2':
        alg_logger.error(' ===> Incoming Radiation units must be "W m**-2"')
        raise NotImplementedError('Case not implemented yet')
    # check incoming radiation variable type
    if var_type_inc_rad != 'instantaneous':
        alg_logger.error(' ===> Incoming Radiation type must be "instantaneous"')
        raise NotImplementedError('Case not implemented yet')

    # get time information
    time_range = pd.DatetimeIndex(var_time)
    time_steps = len(time_range)
    time_delta = pd.Timedelta(var_frequency.lower())

    # check frequency
    if var_frequency != '1H':
        alg_logger.error(' ===> Variable frequency must be "1H"')
        raise NotImplementedError('Case not implemented yet')

    # compute cloud factor
    var_values_cf = compute_cloud_factor(var_values_rain)
    # compute parameters
    geo_lz, geo_lm, geo_phi, arad_param_gsc, arad_param_as, arad_param_bs = define_parameters(var_geo_x, var_geo_y)

    # compute astronomic and incoming radiation
    var_values_ar, var_values_k = exec_astronomic_radiation(
        var_values_cf, var_geo_terrain,
        time_range, time_delta,
        geo_lz, geo_lm, geo_phi, arad_param_gsc, arad_param_as, arad_param_bs)

    # var_da = create_darray(
    #    var_model_k, var_geo_x, var_geo_y, geo_1d=False, time=time_range, name=None,
    #    coord_name_x='west_east', coord_name_y='south_north', coord_name_time='time',
    #    dim_name_x='longitude', dim_name_y='latitude', dim_name_time='time',
    #    dims_order=['time', 'latitude', 'longitude'])

    return var_values_k, var_attrs_k

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to compute wind speed field(s)
def compute_wind_speed(var_data, var_time,
                       var_geo_x=None, var_geo_y=None, var_attrs=None,
                       var_name_wind_speed='wind_speed', var_name_u='wind_u', var_name_v='wind_v',
                       var_name_time='time', var_name_geo_x='longitude', var_name_geo_y='latitude',
                       var_type='instantaneous', **kwargs):

    # get variable data and attributes
    var_values_u, var_attrs_u = var_data[var_name_u], var_attrs[var_name_u]
    var_values_v, var_attrs_v = var_data[var_name_v], var_attrs[var_name_v]

    # join variable attributes
    var_attrs = {}
    for (attrs_name_u, attrs_value_u), (attrs_name_v, attrs_value_v) in zip(var_attrs_u.items(), var_attrs_v.items()):

        if attrs_name_u == attrs_name_v:
            attrs_name = attrs_name_u = attrs_name_v

            if attrs_value_u != attrs_value_v:
                attrs_value = ','.join([str(attrs_value_u), str(attrs_value_v)])
            else:
                attrs_value = attrs_value_u = attrs_value_v
            var_attrs[attrs_name] = attrs_value

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

    n, cols, rows = var_time.shape[0], var_geo_x.shape[0], var_geo_y.shape[1]
    values_time = pd.DatetimeIndex(var_time)

    # iterate over time steps
    var_values_ws = np.zeros(shape=(n, cols, rows))
    for n, t in enumerate(values_time):

        # extract wind components
        step_values_u, step_values_v = var_values_u[n, :, :], var_values_v[n, :, :]
        # compute wind speed
        step_values_ws = np.sqrt(step_values_u ** 2 + step_values_v ** 2)

        # apply limits
        step_values_ws[step_values_ws < 0.0] = 0.0
        # apply scale factor
        step_values_ws = step_values_ws * var_scale_factor

        # store in a common obj
        var_values_ws[n, :, :] = step_values_ws

    # apply units definition
    var_attrs['units'] = 'm s-1'

    return var_values_ws, var_attrs

# ----------------------------------------------------------------------------------------------------------------------
