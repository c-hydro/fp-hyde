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
def compute_wind_speed(var_dframe_u, var_dframe_v, var_time_reference,
                       var_attrs=None,
                       var_name_time='time', var_name_geo_x='longitude', var_name_geo_y='latitude',
                       var_type='instantaneous', **kwargs):
    print()
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



# -------------------------------------------------------------------------------------
# Method to compute surface albedo field(s)
def computeSurfaceAlbedo(oVarData_ALB, oVarUnits=None, oVarType=None,
                             iVarIdxStart=None, iVarIdxEnd=None):

    # Init results
    oVarData_SurfaceAlbedo = None

    # Set variable units and types
    if oVarUnits is None:
        oVarUnits = ['%']
    if oVarType is None:
        oVarType = ['istantaneous']

    # Get variables dimensions
    iVarDim_ALB = oVarData_ALB.ndim

    # Check variables types
    if oVarType[0] != 'istantaneous':
        Exc.getExc(' ---> Error: SurfaceAlbedo allowed only in istantaneous format! Check your data!', 1, 1)
    # Check variables units
    if oVarUnits[0] != '%':
        Exc.getExc(' ---> Error: SurfaceAlbedo units is not allowed! Check your data!', 1, 1)

    # Compute results using 2d or 3d format
    if iVarDim_ALB == 3:

        # Set variable indexes
        if iVarIdxStart is None:
            iIdxStart = 0
        else:
            iIdxStart = iVarIdxStart

        if iVarIdxEnd is None:
            iIdxEnd = oVarData_ALB.shape[2]
        else:
            iIdxEnd = iVarIdxEnd + 1

        # Iterate over field(s)
        a3dVarData_ALB = oVarData_ALB[:, :, iIdxStart:iIdxEnd]

        # Initialize dims
        iVarDims = a3dVarData_ALB.shape

        # Compute incoming radiation
        oVarData_SurfaceAlbedo = empty((iVarDims[0], iVarDims[1], iVarDims[2]))
        oVarData_SurfaceAlbedo[:, :, :] = nan

        for iVarStep in range(0, iVarDims[2]):
            a2dVarData_ALB = a3dVarData_ALB[:, :, iVarStep]
            oVarData_SurfaceAlbedo[:, :, iVarStep] = a2dVarData_ALB / 100

    elif iVarDim_ALB == 2:

        # Compute surface albedo in [-]
        oVarData_SurfaceAlbedo = oVarData_ALB / 100

    # Results
    return oVarData_SurfaceAlbedo
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute incoming radiation field(s)
def computeIncomingRadiation(oVarData_SW, oVarUnits=None, oVarType=None,
                             iVarIdxStart=None, iVarIdxEnd=None):

    # Init results
    oVarData_IncomingRadiation = None

    # Set variable units and types
    if oVarUnits is None:
        oVarUnits = ['W m-2']
    if oVarType is None:
        oVarType = ['average']

    # Get variables dimensions
    iVarDim_SW = oVarData_SW.ndim

    # Check variables types
    if oVarType[0] != 'istantaneous' and oVarType[0] != 'average':
        Exc.getExc(' ---> Error: ShortWaveRadiation allowed only in istantaneous or average format! Check your data!',
                   1, 1)
    # Check variables units
    if oVarUnits[0] != 'W m-2' and oVarUnits[0] != 'W m**-2':
        Exc.getExc(' ---> Error: ShortWaveRadiation units is not allowed! Check your data!', 1, 1)

    # Compute results using 2d or 3d format
    if iVarDim_SW == 3:

        # Set variable indexes
        if iVarIdxStart is None:
            iIdxStart = 0
        else:
            iIdxStart = iVarIdxStart

        if iVarIdxEnd is None:
            iIdxEnd = oVarData_SW.shape[2]
        else:
            iIdxEnd = iVarIdxEnd + 1

        # Iterate over field(s)
        a3dVarData_SW = oVarData_SW[:, :, iIdxStart:iIdxEnd]

        # Initialize dims
        iVarDims = a3dVarData_SW.shape

        # Compute incoming radiation
        oVarData_IncomingRadiation = empty((iVarDims[0], iVarDims[1], iVarDims[2]))
        oVarData_IncomingRadiation[:, :, :] = nan

        if oVarType[0] == 'istantaneous':

            for iVarStep in range(0, iVarDims[2]):
                a2dVarData_SW = a3dVarData_SW[:, :, iVarStep]
                oVarData_IncomingRadiation[:, :, iVarStep] = a2dVarData_SW

        elif oVarType[0] == 'average':

            # Rule to compute average:
            # VarMean_xhour_n = n(VarMean_nxhour_n) - VarMean_xhour_n-1
            a2dVarData_SW_SUM = zeros([iVarDims[0], iVarDims[1]])
            for iVarStep in range(0, iVarDims[2]):

                a2dVarData_SW_AVG = a3dVarData_SW[:, :, iVarStep]

                a2dVarData_SW_IST = iVarStep * a2dVarData_SW_AVG - a2dVarData_SW_SUM
                a2dVarData_SW_SUM = a2dVarData_SW_SUM + a2dVarData_SW_IST

                a2dVarData_SW_IST[a2dVarData_SW_IST < 0.0] = 0.0

                oVarData_IncomingRadiation[:, :, iVarStep] = a2dVarData_SW_IST

    elif iVarDim_SW == 2:

        # Compute incoming radiation in W m^2
        oVarData_IncomingRadiation = oVarData_SW

    # Results
    return oVarData_IncomingRadiation
# -------------------------------------------------------------------------------------



