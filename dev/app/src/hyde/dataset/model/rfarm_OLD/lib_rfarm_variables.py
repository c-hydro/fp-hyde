"""
Library Features:

Name:          lib_rfarm_variables
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '2021130'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging
import numpy as np

from src.hyde.algorithm.io.nwp.ecmwf.lib_ecmwf_io_generic import reshape_var3d, create_darray_3d
from src.hyde.algorithm.settings.nwp.ecmwf.lib_ecmwf_args import logger_name


# Logging
log_stream = logging.getLogger(logger_name)

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to compute ecmwf0100
def compute_rain_ecmwf_0100(var_data_in, var_units='m', var_type='accumulated'):

    if (var_units == 'kg m**-2') or (var_units == 'Kg m**-2'):
        var_units = 'mm'

    if var_units == 'm':
        var_scale_factor = 0.001
    elif var_units == 'mm':
        var_scale_factor = 1
    else:
        log_stream.error(' ===> Rain components units are not allowed! Check your data!')
        raise IOError('Selected units are not allowed!')

    # Check attributes
    if not (var_units == 'mm') and not (var_units == 'm'):
        log_stream.error(' ===> Rain components units are not allowed! Check your data!')
        raise IOError('Data units is not allowed!')
    if not (var_type == 'accum') and not (var_type == 'accumulated'):
        log_stream.error(' ===> Rain components allowed only in instantaneous format! Check your data!')
        raise IOError('Data type is not allowed!')

    var_shape_in = var_data_in.shape
    var_data_out = np.zeros([var_shape_in[0], var_shape_in[1], var_shape_in[2]])
    var_data_out[:, :, :] = np.nan
    for var_step in range(0, var_shape_in[2]):
        var_data_step = var_data_in[:, :, var_step]
        var_data_step = var_data_step / var_scale_factor
        var_data_out[:, :, var_step] = var_data_step

    return var_data_out

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute lami_old-2i rain
def compute_rain_lami_2i(var_data_in, var_units='mm', var_type='accumulated'):

    if (var_units == 'kg m**-2') or (var_units == 'Kg m**-2'):
        var_units = 'mm'

    if var_units == 'm':
        var_scale_factor = 1000
    elif var_units == 'mm':
        var_scale_factor = 1
    else:
        log_stream.error(' ===> Rain components units are not allowed! Check your data!')
        raise IOError('Selected units are not allowed!')

    # Check attributes
    if not (var_units == 'mm') and not (var_units == 'm'):
        log_stream.error(' ===> Rain components units are not allowed! Check your data!')
        raise IOError('Data units is not allowed!')
    if not (var_type == 'accum') and not (var_type == 'accumulated'):
        log_stream.error(' ===> Rain components allowed only in accumulated format! Check your data!')
        raise IOError('Data type is not allowed!')

    var_shape_in = var_data_in.shape
    var_data_out = np.zeros([var_shape_in[0], var_shape_in[1], var_shape_in[2]])
    var_data_out[:, :, :] = np.nan
    for var_step in range(0, var_shape_in[2]):
        var_data_step = var_data_in[:, :, var_step]
        var_data_step = var_data_step / var_scale_factor
        var_data_out[:, :, var_step] = var_data_step

    return var_data_out
# -------------------------------------------------------------------------------------
