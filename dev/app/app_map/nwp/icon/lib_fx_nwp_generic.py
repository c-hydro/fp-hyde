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
# method to compute rain field(s)
def compute_rain(var_dframe, var_time_reference,
                 var_attrs=None,
                 var_name_time='time', var_name_geo_x='longitude', var_name_geo_y='latitude',
                 var_type='accumulated', **kwargs):

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

# -------------------------------------------------------------------------------------
# Method to compute wind speed field(s)
def computeWindSpeed(oVarData_U, oVarData_V, oVarUnits=None, oVarType=None, iVarIdxStart=None, iVarIdxEnd=None):

    # Init results
    oVarData_WindSpeed = None

    # Set variable units and types
    if oVarUnits is None:
        oVarUnits = ['m s-1', 'm s-1']

    if oVarUnits.__len__() == 1:
        oVarUnits = [oVarUnits[0], oVarUnits[0]]

    if oVarUnits[0] == 'm s**-1':
        oVarUnits[0] = 'm s-1'
    if oVarUnits[1] == 'm s**-1':
        oVarUnits[1] = 'm s-1'

    if oVarType is None:
        oVarType = ['istantaneous', 'istantaneous']

    if oVarUnits.__len__() == 1:
        oVarUnits = [oVarUnits[0], oVarUnits[0]]

    if oVarType.__len__() == 1:
        oVarType = [oVarType[0], oVarType[0]]

    # Get variables dimensions
    iVarDim_U = oVarData_U.ndim
    iVarDim_V = oVarData_V.ndim

    # Check variables types
    if oVarType[0] != 'istantaneous' or oVarType[1] != 'istantaneous':
        Exc.getExc(' ---> Error: WindU and WindV allowed only in istantaneous format! Check your data!', 1, 1)
    # Check variables units
    if oVarUnits[0] != 'm s-1' or oVarUnits[1] != 'm s-1':
        Exc.getExc(' ---> Error: WindU or WindV units are not allowed! Check your data!', 1, 1)
    # Check variables dimensions
    if iVarDim_U != iVarDim_V:
        Exc.getExc(' ---> Error: WindU or WindV dimensions are different! Check your data!', 1, 1)

    # Compute results using 2d or 3d format
    if iVarDim_U == 3 and iVarDim_V == 3:

        # Set variable indexes
        if iVarIdxStart is None:
            iIdxStart_U = 0
            iIdxStart_V = 0
        else:
            iIdxStart_U = iVarIdxStart
            iIdxStart_V = iVarIdxStart

        if iVarIdxEnd is None:
            iIdxEnd_U = oVarData_U.shape[2]
            iIdxEnd_V = oVarData_V.shape[2]
        else:
            iIdxEnd_U = iVarIdxEnd + 1
            iIdxEnd_V = iVarIdxEnd + 1

        # Iterate over field(s)
        a3dVarData_U = oVarData_U[:, :, iIdxStart_U:iIdxEnd_U]
        a3dVarData_V = oVarData_V[:, :, iIdxStart_V:iIdxEnd_V]

        # Initialize dims
        iVarDims_U = a3dVarData_U.shape
        iVarDims_V = a3dVarData_V.shape
        try:
            assert iVarDims_U == iVarDims_V
            iVarDims = iVarDims_U
        except BaseException:
            Exc.getExc(' ---> Warning: WindU and WindV have different dimensions!!', 2, 1)
            iVarDims = min(iVarDims_U, iVarDims_V)

        # Compute wind speed
        oVarData_WindSpeed = empty((iVarDims[0], iVarDims[1], iVarDims[2]))
        oVarData_WindSpeed[:, :, :] = nan
        for iVarStep in range(0, iVarDims[2]):

            a2dVarData_U = a3dVarData_U[:, :, iVarStep]
            a2dVarData_V = a3dVarData_V[:, :, iVarStep]

            a2dVarData_WindSpeed = sqrt(a2dVarData_U ** 2 + a2dVarData_V ** 2)
            oVarData_WindSpeed[:, :, iVarStep] = a2dVarData_WindSpeed

    elif iVarDim_U == 2 and iVarDim_V == 2:

        # Compute wind speed
        oVarData_WindSpeed = sqrt(oVarData_U ** 2 + oVarData_V ** 2)

    # Results
    return oVarData_WindSpeed
# -------------------------------------------------------------------------------------
