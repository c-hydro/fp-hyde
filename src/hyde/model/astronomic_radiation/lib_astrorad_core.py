"""
Library Features:

Name:           lib_astrorad_core
Author(s):      Fabio Delogu (fabio.delogu@cimafoundation.org)
                Simone Gabellani (simone.gabellani@cimafoundation.org)
Date:           '20200215'
Version:        '2.0.0'
"""

#######################################################################################
# Logging
import logging

import pandas as pd
import numpy as np

from src.common.default.lib_default_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)

# Debug
import matplotlib.pylab as plt
#######################################################################################


# --------------------------------------------------------------------------------
# Method to compute astronomic radiation by FAO algorithm
def execAstroRad_FAO(var_data_cf, geo_z,
                     time_period, time_delta,
                     geo_lz, geo_lm, geo_phi,
                     param_gsc, param_as, param_bs):

    # Time information
    seconds_delta = time_delta.seconds
    time_delta_mid_t = time_delta.seconds / 3600 # in hour
    minutes_input_step = time_delta.seconds / 60 # in minute?

    # Cycle(s) on time steps
    var_model_k_avg = np.zeros([time_period.__len__()])
    var_model_ar_avg = np.zeros([time_period.__len__()])
    var_model_k = np.zeros([geo_z.shape[0], geo_z.shape[1], time_period.__len__()])
    var_model_ar = np.zeros([geo_z.shape[0], geo_z.shape[1], time_period.__len__()])
    for time_id, time_step in enumerate(time_period):

        # Compute cloud factor
        var_data_cf_step = var_data_cf[:, :, time_id]

        # Compute time information
        time_delta_mid = time_delta / 2
        time_mid = pd.Timestamp(time_step - time_delta_mid)
        hour_mid = time_mid.hour
        doy_mid = time_mid.dayofyear

        # Inverse relative distance Earth-Sun
        ird = 1.0 + 0.033 * np.cos(2 * np.pi / 365 * doy_mid)
        b = 2 * np.pi * (doy_mid - 81) / 364.0

        # Seasonal correction for solar time [h]
        solar_corr = 0.1645 * np.sin(2 * b) - 0.1255 * np.cos(b) - 0.025 * np.sin(b)

        # Solar declination [rad]
        solar_decl = 0.4093 * np.sin(2 * np.pi / 365 * doy_mid - 1.405)

        # Solar time angle at midpoint of hourly or shorter period [rad]
        solar_time_angle = np.pi / 12.0 * (hour_mid + 0.06667 * (geo_lz - geo_lm) + solar_corr - 12.0)

        # Solar time angle at beginning of period [rad]
        solar_time_angle_start = solar_time_angle - np.pi * time_delta_mid_t / 24.0
        # Solar time angle at end of period [rad]
        solar_time_angle_end = solar_time_angle + np.pi * time_delta_mid_t / 24.0

        # Extraterrestrial Radiation [MJ/m^2/interval] (Duffie & Beckman, 1980)
        var_model_ar_step = (12 * minutes_input_step / np.pi * param_gsc * ird * (
            (solar_time_angle_end - solar_time_angle_start) * np.sin(geo_phi) * np.sin(solar_decl) +
            np.cos(geo_phi) * np.cos(solar_decl) * (np.sin(solar_time_angle_end) - np.sin(solar_time_angle_start))))

        # Extraterrestrial Radiation [W/m^2] --> Incoming radiation
        var_model_ar_step = var_model_ar_step * 10 ** 6 / seconds_delta
        var_model_ar_step[var_model_ar_step <= 0.0] = 0.0
        var_model_ar_step[np.isnan(var_data_cf_step)] = np.nan

        # Clear-sky shortwave radiation
        var_model_k_step = var_data_cf_step * (param_as + param_bs * geo_z) * var_model_ar_step

        # Store K and AR results
        var_model_k_avg[time_id] = np.nanmean(var_model_k_step)
        var_model_ar_avg[time_id] = np.nanmean(var_model_ar_step)
        var_model_k[:, :, time_id] = var_model_k_step
        var_model_ar[:, :, time_id] = var_model_ar_step

    # Return variable(s)
    return var_model_ar, var_model_k
# --------------------------------------------------------------------------------
