"""
Library Features:

Name:          lib_ecmwf_0100_time
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20200210'
Version:       '1.5.0'
"""

#######################################################################################
# Library
import logging
import pandas as pd

from src.hyde.algorithm.settings.nwp.ecmwf.lib_ecmwf_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
#######################################################################################


# -------------------------------------------------------------------------------------
# Class data object
class DataObj(dict):
    pass
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute time steps
def getVarTime(time_period):

    time_size = time_period.size
    time_start = pd.Timestamp(time_period.values[0])
    time_end = pd.Timestamp(time_period.values[-1])
    time_period = pd.date_range(start=time_start, end=time_end, periods=time_size)

    time_scale = (time_end - time_start) / (time_size - 1)
    time_delta = time_scale.seconds
    time_resolution = time_scale.resolution

    time_obj = DataObj
    time_obj.time_size = time_size
    time_obj.time_start = time_start
    time_obj.time_end = time_end
    time_obj.time_period = time_period
    time_obj.time_scale = time_scale
    time_obj.time_delta = time_delta
    time_obj.time_resolution = time_resolution

    return time_obj

# -------------------------------------------------------------------------------------
