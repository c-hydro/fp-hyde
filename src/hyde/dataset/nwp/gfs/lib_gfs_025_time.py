"""
Library Features:

Name:          lib_gfs_025_time
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20200302'
Version:       '1.5.0'
"""

#######################################################################################
# Library
import logging
import pandas as pd

from src.hyde.algorithm.settings.nwp.gfs.lib_gfs_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
#######################################################################################

# -------------------------------------------------------------------------------------
# EXAMPLE_TIME PARAMETER(S)
# RAIN            P1 = 0,1,2 ...,71 P2 = 1,2,3, ... 72          UTR = 1, TRI = 4
# TEMPERATURE     P1 = 0,1,2 ,,,,73 P2 = 0,0,0,0                UTR = 1, TRI = 0
# SWH             P1 = 0,0,0 P2 = 3,6,9                         UTR = 1, TRI = 3
# WIND            P1 = 0,1,2 P2 = 0,0,0                         UTR = 1, TRI = 0 (2 VARS)
# REL HUMIDITY    P1 = 0,1,2 P2 = 0,0,0                         UTR = 1, TRI = 0

# Time forecast unit definition (TRU)
oUTR = {0:      {'minute':     60},
        1:      {'hour':       3600},
        2:      {'day':        86400},
        3:      {'month':      None},
        4:      {'year':       None},
        5:      {'decade':     None},
        6:      {'normal':     None},
        7:      {'century':    None},
        254:    {'second':     1},
        }
# Time range indicator definition (TRI)
oTRI = {0:   'istantaneous',
        3:   'average',
        4:   'accumulation',
        }
# -------------------------------------------------------------------------------------


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

