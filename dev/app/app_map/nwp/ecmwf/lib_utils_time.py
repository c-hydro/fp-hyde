"""
Library Features:

Name:          lib_utils_time
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20230830'
Version:       '1.0.0'
"""

# ----------------------------------------------------------------------------------------------------------------------
# libraries
import logging
import pandas as pd

from copy import deepcopy
from datetime import date

from lib_info_args import logger_name

# set logger
alg_logger = logging.getLogger(logger_name)
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to set time run
def set_time_run(time_run,
                 time_day_reference=None, time_hour_reference=0,
                 time_minute_reference=0, time_second_reference=0,
                 time_rounding='H'):

    if time_rounding.isupper():
        time_rounding = time_rounding.lower()

    time_run = time_run.floor(time_rounding)
    if time_day_reference is not None:
        time_run = time_run.replace(
            day=int(time_day_reference),
            hour=int(time_hour_reference), minute=int(time_minute_reference), second=int(time_second_reference))
    if time_hour_reference is not None:
        time_run = time_run.replace(
            hour=int(time_hour_reference), minute=int(time_minute_reference), second=int(time_second_reference))

    return time_run
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Method to set time info
def set_time_info(time_run_args=None, time_run_file=None,
                  time_format='%Y-%m-%d %H:$M', time_frequency='H', time_rounding='H'):

    alg_logger.info(' ----> Set time info ... ')

    if time_run_args is not None:
        time_run = time_run_args
        alg_logger.info(' ------> Time ' + time_run + ' set by argument')
    elif (time_run_args is None) and (time_run_file is not None):
        time_run = time_run_file
        alg_logger.info(' ------> Time ' + time_run + ' set by user')
    elif (time_run_args is None) and (time_run_file is None):
        time_now = date.today()
        time_run = time_now.strftime(time_format)
        alg_logger.info(' ------> Time ' + time_run + ' set by system')
    else:
        alg_logger.info(' ----> Set time info ... FAILED')
        alg_logger.error(' ===> Argument "time_run" is not correctly set')
        raise IOError('Time type or format is wrong')

    time_run = pd.Timestamp(time_run)
    if time_rounding.isupper():
        time_rounding = time_rounding.lower()
    time_reference = time_run.floor(time_rounding)

    alg_logger.info(' ----> Set time info ... DONE')

    return time_run, time_reference

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to split time frequency
def split_time_frequency(time_frequency):

    if time_frequency[0].isalpha():
        time_frequency = '1' + time_frequency

    time_frequency_value = int(time_frequency[0])
    time_frequency_unit = time_frequency[1]

    return time_frequency_value, time_frequency_unit
# ----------------------------------------------------------------------------------------------------------------------
