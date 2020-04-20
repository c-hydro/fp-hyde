"""
Library Features:

Name:           lib_astrorad_utils
Author(s):      Fabio Delogu (fabio.delogu@cimafoundation.org);
                Simone Gabellani (simone.gabellani@cimafoundation.org)
Date:           '20200215'
Version:        '2.5.0'
"""

#######################################################################################
# Logging
import logging
import datetime
import numpy as np

from src.hyde.algorithm.settings.model.astronomic_radiation.lib_astrorad_args import logger_name, time_format

# Logging
log_stream = logging.getLogger(logger_name)

# Debug
import matplotlib.pylab as plt
#######################################################################################

# -------------------------------------------------------------------------------------
# Default lookup table for cloud factor against rain values
lookup_table_cf_default = {
    'CF_L1': {'Rain': [0, 1],       'CloudFactor': [0.95]},
    'CF_L2': {'Rain': [1, 3],   	'CloudFactor': [0.75]},
    'CF_L3': {'Rain': [3, 5],   	'CloudFactor': [0.65]},
    'CF_L4': {'Rain': [5, 10],   	'CloudFactor': [0.50]},
    'CF_L5': {'Rain': [10, None],   'CloudFactor': [0.15]}
}
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute cloud attenuation factor using rain data
def computeCloudFactor(data_rain, lookup_table_cf=None):
    # Define lookup table
    if lookup_table_cf is None:
        lookup_table_cf = lookup_table_cf_default

    # Initialize Cloud Factor 3D workspace
    data_cf = np.zeros([data_rain.shape[0], data_rain.shape[1], data_rain.shape[2]])
    data_cf[:, :, :] = np.nan
    for data_id in range(0, data_rain.shape[2]):
        data_rain_step = data_rain[:, :, data_id]
        data_cf_step = applyLU(data_rain_step, lookup_table_cf, 'Rain', 'CloudFactor')
        data_cf[:, :, data_id] = data_cf_step

    return data_cf
# -------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to compute look-up table
def applyLU(var_data_in, lookup_table=None, var_in='Rain', var_out='CloudFactor'):

    var_data_in = np.float32(var_data_in)
    var_idx_in = np.argwhere(np.isnan(var_data_in))

    var_data_out = np.zeros([var_data_in.shape[0], var_data_in.shape[1]])
    for lu_table_key, lu_table_value in lookup_table.items():
        lu_var_in = lu_table_value[var_in]
        lu_var_out = lu_table_value[var_out]

        # Condition using lookup dimension(s)
        if lu_var_in.__len__() == 2 and lu_var_out.__len__() == 1:

            # Get LU value in
            lu_var_in_min = lu_var_in[0]
            lu_var_in_max = lu_var_in[1]
            # Get LU value out
            lu_var_out = lu_var_out[0]

            if (lu_var_in_min is not None) and (lu_var_in_max is not None):
                var_data_out[(var_data_in >= lu_var_in_min) & (var_data_in < lu_var_in_max)] = lu_var_out
            elif (lu_var_in_min is not None) and (lu_var_in_max is None):
                var_data_out[(var_data_in >= lu_var_in_min)] = lu_var_out
            elif (lu_var_in_min is None) and (lu_var_in_max is not None):
                var_data_out[(var_data_in <= lu_var_in_max)] = lu_var_out
            else:
                log_stream.error(' ===> LookUp condition not available')
                raise NotImplemented('LookUp condition not available')
        else:
            log_stream.error(' ===> LookUp variable range not available')
            raise NotImplemented('LookUp variable range not available')

        var_data_out[var_idx_in[:, 0], var_idx_in[:, 1]] = np.nan

    return var_data_out
    # --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
