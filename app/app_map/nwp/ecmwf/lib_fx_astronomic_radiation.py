"""
Library Features:

Name:           lib_fx_astronomic_radiation
Author(s):      Fabio Delogu (fabio.delogu@cimafoundation.org)
                Simone Gabellani (simone.gabellani@cimafoundation.org)
Date:           '20241012'
Version:        '2.1.0'
"""

# ----------------------------------------------------------------------------------------------------------------------
# logging
import logging

import pandas as pd
import numpy as np

from lib_info_args import logger_name

# log stream
log_stream = logging.getLogger(logger_name)

# debug
import matplotlib.pylab as plt

# default lookup table for cloud factor against rain values
lookup_table_cf_default = {
    'CF_L1': {'Rain': [0, 1],       'CloudFactor': [0.95]},
    'CF_L2': {'Rain': [1, 3],   	'CloudFactor': [0.75]},
    'CF_L3': {'Rain': [3, 5],   	'CloudFactor': [0.65]},
    'CF_L4': {'Rain': [5, 10],   	'CloudFactor': [0.50]},
    'CF_L5': {'Rain': [10, None],   'CloudFactor': [0.15]}
}
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to compute astronomic radiation (by FAO algorithm)
def exec_astronomic_radiation(var_data_cf,
                              geo_z,
                              time_period, time_delta,
                              geo_lz, geo_lm, geo_phi, param_gsc, param_as, param_bs):

    # time information
    seconds_delta = time_delta.seconds
    time_delta_mid_t = time_delta.seconds / 3600 # in hour
    minutes_input_step = time_delta.seconds / 60 # in minute?

    # iterate on time steps
    var_model_k_avg = np.zeros([time_period.__len__()])
    var_model_ar_avg = np.zeros([time_period.__len__()])
    var_model_k = np.zeros([time_period.__len__(), geo_z.shape[0], geo_z.shape[1]])
    var_model_ar = np.zeros([time_period.__len__(), geo_z.shape[0], geo_z.shape[1]])
    for time_id, time_step in enumerate(time_period):

        # compute cloud factor
        var_data_cf_step = var_data_cf[time_id, :, :]

        # compute time information
        time_delta_mid = time_delta / 2
        time_mid = pd.Timestamp(time_step - time_delta_mid)
        hour_mid = time_mid.hour
        doy_mid = time_mid.dayofyear

        # inverse relative distance Earth-Sun
        ird = 1.0 + 0.033 * np.cos(2 * np.pi / 365 * doy_mid)
        b = 2 * np.pi * (doy_mid - 81) / 364.0

        # seasonal correction for solar time [h]
        solar_corr = 0.1645 * np.sin(2 * b) - 0.1255 * np.cos(b) - 0.025 * np.sin(b)

        # solar declination [rad]
        solar_decl = 0.4093 * np.sin(2 * np.pi / 365 * doy_mid - 1.405)

        # solar time angle at midpoint of hourly or shorter period [rad]
        solar_time_angle = np.pi / 12.0 * (hour_mid + 0.06667 * (geo_lz - geo_lm) + solar_corr - 12.0)

        # solar time angle at beginning of period [rad]
        solar_time_angle_start = solar_time_angle - np.pi * time_delta_mid_t / 24.0
        # solar time angle at end of period [rad]
        solar_time_angle_end = solar_time_angle + np.pi * time_delta_mid_t / 24.0

        # extraterrestrial Radiation [MJ/m^2/interval] (Duffie & Beckman, 1980)
        var_model_ar_step = (12 * minutes_input_step / np.pi * param_gsc * ird * (
            (solar_time_angle_end - solar_time_angle_start) * np.sin(geo_phi) * np.sin(solar_decl) +
            np.cos(geo_phi) * np.cos(solar_decl) * (np.sin(solar_time_angle_end) - np.sin(solar_time_angle_start))))

        # extraterrestrial Radiation [W/m^2] --> Incoming radiation
        var_model_ar_step = var_model_ar_step * 10 ** 6 / seconds_delta
        var_model_ar_step[var_model_ar_step <= 0.0] = 0.0
        var_model_ar_step[np.isnan(var_data_cf_step)] = np.nan

        # clear-sky shortwave radiation
        var_model_k_step = var_data_cf_step * (param_as + param_bs * geo_z) * var_model_ar_step

        # store K and AR results
        var_model_k_avg[time_id] = np.nanmean(var_model_k_step)
        var_model_ar_avg[time_id] = np.nanmean(var_model_ar_step)
        var_model_k[time_id, :, :] = var_model_k_step
        var_model_ar[time_id, :, :] = var_model_ar_step

    return var_model_ar, var_model_k
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to define parameters for astronomic radiation computation
def define_parameters(geo_x, geo_y):

    # degree to rad factor
    tor = np.pi / 180.0

    # gsc solar constant =MJ m-2 day-1
    gsc = 118.08
    # gsc solar constant =MJ m-2 min-1
    arad_param_gsc = gsc / (60.0 * 24.0)

    # longitude of the centre of the local time zone
    geo_lz = np.round(geo_x / 15) * 15

    # lm longitude of the measurement site [degrees west of Greenwich],
    geo_lm = 360.0 - geo_x
    # latitude [rad]
    geo_phi = geo_y * tor

    # K astronomic parameter(s)
    arad_param_as = 0.65
    arad_param_bs = 2.0 * 10e-5

    return geo_lz, geo_lm, geo_phi, arad_param_gsc, arad_param_as, arad_param_bs

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to compute cloud attenuation factor using rain data
def compute_cloud_factor(data_rain, lookup_table_cf=None):

    # define lookup table
    if lookup_table_cf is None:
        lookup_table_cf = lookup_table_cf_default

    # initialize cloud factor 3D workspace
    data_cf = np.zeros([data_rain.shape[0], data_rain.shape[1], data_rain.shape[2]])
    data_cf[:, :, :] = np.nan
    for data_id in range(0, data_rain.shape[2]):
        data_rain_step = data_rain[:, :, data_id]
        data_cf_step = apply_cloud_factor_lut(data_rain_step, lookup_table_cf, 'Rain', 'CloudFactor')
        data_cf[:, :, data_id] = data_cf_step

    return data_cf
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to compute look-up table
def apply_cloud_factor_lut(var_data_in, lookup_table=None, var_in='Rain', var_out='CloudFactor'):

    var_data_in = np.float32(var_data_in)
    var_idx_in = np.argwhere(np.isnan(var_data_in))

    var_data_out = np.zeros([var_data_in.shape[0], var_data_in.shape[1]])
    for lu_table_key, lu_table_value in lookup_table.items():
        lu_var_in = lu_table_value[var_in]
        lu_var_out = lu_table_value[var_out]

        # condition using lookup dimension(s)
        if lu_var_in.__len__() == 2 and lu_var_out.__len__() == 1:

            # get LU value in
            lu_var_in_min = lu_var_in[0]
            lu_var_in_max = lu_var_in[1]
            # get LU value out
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
# ----------------------------------------------------------------------------------------------------------------------
