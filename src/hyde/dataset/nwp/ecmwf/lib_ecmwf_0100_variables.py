"""
Library Features:

Name:          lib_ecmwf_0100_variables
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '2020210'
Version:       '1.5.0'
"""

#######################################################################################
# Library
import logging
import numpy as np

from src.hyde.algorithm.io.nwp.ecmwf.lib_ecmwf_io_generic import reshape_var3d, create_darray_3d
from src.hyde.algorithm.settings.nwp.ecmwf.lib_ecmwf_args import logger_name
from src.hyde.model.astronomic_radiation.lib_astrorad_utils import computeCloudFactor

from src.hyde.driver.model.astronomic_radiation.drv_model_astrorad_exec import AstroRadModel

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
        var_scale_factor = 0.001
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

    var_values_out = np.zeros([var_shape_in[0], var_shape_in[1], var_shape_in[2]])
    var_values_out[:, :, :] = np.nan
    for var_step in range(0, var_shape_in[2]):
        var_values_step = var_values_in[:, :, var_step]
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
# Method to convert rain to cloud factor
def convertRain2CloudFactor(var_dset, var_name,
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
    var_name_1 = list(var_name)[0]
    var_name_2 = list(var_name)[1]
    var_units_1 = var_units[0]
    var_units_2 = var_units[1]
    var_step_type_1 = var_step_type[0]
    var_step_type_2 = var_step_type[1]
    var_time = var_time[0]
    var_geo_x = var_geo_x[0]
    var_geo_y = var_geo_y[0]

    # Get values
    var_da_in_1 = var_dset[var_name_1]
    var_values_in_1 = var_da_in_1.values
    var_dims_in_1 = var_da_in_1.dims

    var_time = var_dset[var_time]
    var_geo_x = var_dset[var_geo_x]
    var_geo_y = var_dset[var_geo_y]

    var_da_in_1 = create_darray_3d(var_values_in_1, var_time, var_geo_x, var_geo_y,
                                   dim_key_time='valid_time', dim_key_x='longitude', dim_key_y='latitude',
                                   dim_name_x='longitude', dim_name_y='latitude', dim_name_time='step',
                                   dims_order=['step', 'latitude', 'longitude'])
    var_dset_in_1 = var_da_in_1.to_dataset(name=var_name_1)
    var_dset_out = computeRain(var_dset_in_1, [var_name_1], var_units=[var_units_1], var_step_type=[var_step_type_1])

    var_values_tmp = var_dset_out[var_name_1].values
    var_values_cf = computeCloudFactor(var_values_tmp)
    var_da_cf = create_darray_3d(var_values_cf, var_time, var_geo_x, var_geo_y,
                                 dim_key_time='time', dim_key_x='longitude', dim_key_y='latitude',
                                 dim_name_x='longitude', dim_name_y='latitude', dim_name_time='time',
                                 dims_order=['latitude', 'longitude', 'time'])
    var_dset_out[var_name_2] = var_da_cf

    return var_dset_out

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute astronomic radiation
def computeAstronomicRadiation(var_dset, geo_dset, var_name,
                               var_time=None, var_geo_x=None, var_geo_y=None,
                               var_tag_cf="CloudFactor",
                               var_tag_ar="IncomingRadiation", var_tag_k="ShortWaveRadiation",
                               var_units='W/m^2', var_step_type='instant'):
    # Set args
    if var_geo_y is None:
        var_geo_y = ['latitude']
    if var_geo_x is None:
        var_geo_x = ['longitude']
    if var_time is None:
        var_time = ['time']

    # Parse args
    var_name_rain = list(var_name)[0]
    var_name_cf = list(var_name)[1]
    var_time = var_time[0]
    var_geo_x = var_geo_x[0]
    var_geo_y = var_geo_y[0]

    # Get data and geographical information
    var_data_cf = var_dset[var_name_cf].values
    var_time = var_dset[var_time]
    var_geo_values = geo_dset.values
    var_geo_y = geo_dset[var_geo_y].values
    var_geo_x = geo_dset[var_geo_x].values
    # Compute grids for x and y directions
    var_geo_grid_x, var_geo_grid_y = np.meshgrid(var_geo_x, var_geo_y)

    # Incoming radiation computed by AstronomicRadiation model
    driver_model_exec = AstroRadModel(var_data_cf, var_time, var_geo_values, var_geo_grid_x, var_geo_grid_y)
    model_params = driver_model_exec.configure_model_parameters()
    model_dset = driver_model_exec.configure_model_datasets()
    model_time = driver_model_exec.configure_model_time()

    var_model_ar, var_model_k = driver_model_exec.execute_run(model_dset, model_time, model_params)

    var_da_ar = create_darray_3d(var_model_ar, var_time, var_geo_x, var_geo_y,
                                 dim_key_time='time', dim_key_x='longitude', dim_key_y='latitude',
                                 dim_name_x='longitude', dim_name_y='latitude', dim_name_time='time',
                                 dims_order=['latitude', 'longitude', 'time'])
    var_da_k = create_darray_3d(var_model_k, var_time, var_geo_x, var_geo_y,
                                dim_key_time='time', dim_key_x='longitude', dim_key_y='latitude',
                                dim_name_x='longitude', dim_name_y='latitude', dim_name_time='time',
                                dims_order=['latitude', 'longitude', 'time'])

    var_dset_out = var_da_ar.to_dataset(name=var_tag_ar)
    var_dset_out[var_tag_k] = var_da_k

    return var_dset_out

# -------------------------------------------------------------------------------------
