"""
Class Features

Name:          drv_configuration_time_mcm
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20201206'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging
import time

import pandas as pd

from copy import deepcopy
from datetime import date

from src.hyde.algorithm.settings.radar.lib_mcm_args import time_format, time_type

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Class Time
class DriverTime:

    # -------------------------------------------------------------------------------------
    # Method class initialization
    def __init__(self, time_run_args=None, time_info=None):

        # -------------------------------------------------------------------------------------
        # Store information in global workspace
        self.time_run_args = time_run_args
        self.time_run_file = time_info['time_run']
        self.time_period = time_info['time_period']
        self.time_frequency = time_info['time_frequency']
        self.time_rounding = time_info['time_rounding']
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to set time run
    def set_algorithm_time(self, time_reverse=True):

        logging.info(' ---> Set time run ... ')

        time_run_args = self.time_run_args
        time_run_file = self.time_run_file

        time_frequency = self.time_frequency
        time_period = self.time_period
        time_rounding = self.time_rounding

        if time_run_args is not None:
            time_run = time_run_args
            logging.info(' ----> Time ' + time_run + ' set by argument')
        elif (time_run_args is None) and (time_run_file is not None):
            time_run = time_run_file
            logging.info(' ----> Time ' + time_run + ' set by user')
        elif (time_run_args is None) and (time_run_file is None):
            time_now = date.today()
            time_run = time_now.strftime(time_format)
            logging.info(' ----> Time ' + time_run + ' set by system')
        else:
            logging.info(' ---> Set time run ... FAILED')
            logging.error(' ===> Time is not correctly set')
            raise IOError('Time type or format is wrong')

        logging.info(' ---> Set time run ... DONE')

        time_exec = deepcopy(time_run)

        time_tmp = pd.Timestamp(time_run)
        time_run = time_tmp.floor(time_rounding)
        time_exec = pd.Timestamp(time_exec)

        if time_period > 0:
            time_range = pd.date_range(end=time_run, periods=time_period, freq=time_frequency)
        else:
            logging.warning(' ===> TimePeriod must be greater then 0. TimePeriod is set automatically to 1')
            time_range = pd.DatetimeIndex([time_run], freq=time_frequency)

        if time_reverse:
            time_range = time_range[::-1]

        return time_run, time_exec, time_range

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
