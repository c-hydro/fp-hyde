"""
Library Features:

Name:          lib_astrorad_apps
Author(s):     Fabio Delogu     (fabio.delogu@cimafoundation.org)
               Simone Gabellani (simone.gabellani@cimafoundation.org)

Date:          '20200215'
Version:       '1.1.0'
"""

#################################################################################
# Logging
import logging
import numpy as np

from src.common.default.lib_default_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)

# Debug
import matplotlib.pylab as plt
#################################################################################


# --------------------------------------------------------------------------------
# Method to compute cloud factor
def computeParameters(geo_x, geo_y):
    # Degree to rad factor
    tor = np.pi / 180.0

    # Gsc solar constant =MJ m-2 day-1
    gsc = 118.08
    # Gsc solar constant =MJ m-2 min-1
    arad_param_gsc = gsc / (60.0 * 24.0)

    # longitude of the centre of the local time zone
    geo_lz = np.round(geo_x / 15) * 15

    # Lm longitude of the measurement site [degrees west of Greenwich],
    geo_lm = 360.0 - geo_x
    # Latitude [rad]
    geo_phi = geo_y * tor

    # K astronomic parameter(s)
    arad_param_as = 0.65
    arad_param_bs = 2.0 * 10e-5

    # Return
    return geo_lz, geo_lm, geo_phi, arad_param_gsc, arad_param_as, arad_param_bs

# --------------------------------------------------------------------------------
