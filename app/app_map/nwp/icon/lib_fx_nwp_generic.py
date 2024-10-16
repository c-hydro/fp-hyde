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
# method to compute wind speed field(s)
def compute_wind_speed(var_dset, var_time_reference, var_attrs=None,
                       var_name_wind_speed='wind_speed', var_name_u='wind_u', var_name_v='wind_v',
                       var_name_time='time', var_name_geo_x='longitude', var_name_geo_y='latitude',
                       var_type='instantaneous', **kwargs):

    # get variable data and attributes
    var_dset_u, var_attrs_u = var_dset[var_name_u], var_attrs[var_name_u]
    var_dset_v, var_attrs_v = var_dset[var_name_v], var_attrs[var_name_v]

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
    else:

        n = var_dset.dims[var_name_time]
        cols = var_dset.dims[var_name_geo_x]
        rows = var_dset.dims[var_name_geo_y]

        values_time = pd.DatetimeIndex(var_dset[var_name_time].values)
        values_src_u, values_src_v = var_dset_u.values, var_dset_v.values

        var_da = var_dset[var_name_u].copy()

        # iterate over time steps
        values_data_ws = np.zeros(shape=(n, rows, cols))
        for n, t in enumerate(values_time):

            # extract wind components
            values_step_u, values_step_v = values_src_u[n, :, :], values_src_v[n, :, :]
            # compute wind speed
            values_step_ws = np.sqrt(values_step_u ** 2 + values_step_v ** 2)

            # apply limits
            values_step_ws[values_step_ws < 0.0] = 0.0
            # apply scale factor
            values_step_ws = values_step_ws * var_scale_factor

            # store in a common obj
            values_data_ws[n, :, :] = values_step_ws

        # assign wind speed values to dataset
        var_da.values = values_data_ws
        var_da.name = var_name_wind_speed

    # apply units definition
    var_attrs['units'] = 'm s-1'

    return var_da, var_attrs

# ----------------------------------------------------------------------------------------------------------------------
