"""
Library Features:

Name:          lib_utils_time
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20231121'
Version:       '1.1.0'
"""

# ----------------------------------------------------------------------------------------------------------------------
# libraries
import logging
import re
import pandas as pd
from datetime import date

from lib_info_args import logger_name

# logging
log_stream = logging.getLogger(logger_name)
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to replace time part
def replace_time_part(time_obj_src, time_rounding='H', time_value=0):

    time_list = []
    for time_step in time_obj_src:
        if time_rounding == 'H':
            time_tmp = time_step.replace(hour=time_value)
        else:
            log_stream.error(' ===> Time rounding "' + time_rounding + '" is not expected')
            raise NotImplementedError('Case not implemented yet')
        time_list.append(time_tmp)

    time_obj_dst = pd.DatetimeIndex(time_list)

    return time_obj_dst
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Method to set time run
def set_time(time_ref_args=None, time_ref_file=None, time_format='%Y-%m-%d %H:$M',
             time_ref_file_start=None, time_ref_file_end=None,
             time_period=1, time_frequency='H', time_rounding='H', time_reverse=True):

    log_stream.info(' ----> Set time period ... ')

    if time_rounding is None:
        log_stream.warning(' ===> Variable "time_rounding" is defined by NoneType. It will be set to "H"')
        time_rounding = 'H'
    if time_frequency is None:
        log_stream.warning(' ===> Variable "time_frequency" is defined by NoneType. It will be set to "H"')
        time_frequency = 'H'

    if (time_ref_file_start is None and time_ref_file_end is None) and (time_period is None and time_frequency is None):

        if time_ref_file is None:
            time_now = date.today()
            time_ref = pd.Timestamp(time_now.strftime(time_format)).floor('H')
        else:
            time_ref = pd.Timestamp(time_ref_file).floor('H')
        time_range = pd.DatetimeIndex([time_ref], freq='H')

        log_stream.warning(' ===> All the time information are set to NoneType; '
                           '"time_run" and "time_range" will be initialized with default values')
        log_stream.info(' ----> Set time period ... DEACTIVATED')
        return [time_ref, time_range]

    if (time_ref_file_start is None) and (time_ref_file_end is None):

        log_stream.info(' -----> Time info defined by "time_run" argument ... ')

        if time_ref_args is not None:
            time_ref = time_ref_args
            log_stream.info(' ------> Time ' + time_ref + ' set by argument')
        elif (time_ref_args is None) and (time_ref_file is not None):
            time_ref = time_ref_file
            log_stream.info(' ------> Time ' + time_ref + ' set by user')
        elif (time_ref_args is None) and (time_ref_file is None):
            time_now = date.today()
            time_ref = time_now.strftime(time_format)
            log_stream.info(' ------> Time ' + time_ref + ' set by system')
        else:
            log_stream.info(' ----> Set time period ... FAILED')
            log_stream.error(' ===> Argument "time_run" is not correctly set')
            raise IOError('Time type or format is wrong')

        time_tmp = pd.Timestamp(time_ref)
        time_ref = time_tmp.floor(time_rounding)

        if time_period is not None:
            if time_period > 0:
                time_range = pd.date_range(end=time_ref, periods=time_period, freq=time_frequency)
            else:
                log_stream.warning(' ===> TimePeriod must be greater then 0. TimePeriod is set automatically to 1')
                time_range = pd.DatetimeIndex([time_ref], freq=time_frequency)
        else:
            log_stream.error(' ===> TimePeriod must be defined and not equal to NoneType')
            raise RuntimeError('Set TimePeriod value in the settings file')

        log_stream.info(' -----> Time info defined by "time_run" argument ... DONE')

    elif (time_ref_file_start is not None) and (time_ref_file_end is not None):

        log_stream.info(' -----> Time info defined by "time_start" and "time_end" arguments ... ')

        time_ref_file_start = pd.Timestamp(time_ref_file_start)
        if time_rounding == 'Y':
            time_year = time_ref_file_start.year
            time_ref_file_start = pd.Timestamp(str(time_year) + '-01-01 00:00:00')
        else:
            time_ref_file_start = time_ref_file_start.floor(time_rounding)

        time_ref_file_end = pd.Timestamp(time_ref_file_end)
        if time_rounding == 'Y':
            time_year = time_ref_file_end.year
            time_ref_file_end = pd.Timestamp(str(time_year) + '-12-31 23:00:00')
        else:
            time_ref_file_end = time_ref_file_end.floor(time_rounding)

        if time_ref_file_start > time_ref_file_end:
            log_stream.error(' ===> Variable "time_start" is greater than "time_end". Check your settings file.')
            raise RuntimeError('Time_Range is not correctly defined.')

        time_now = date.today()
        time_ref = time_now.strftime(time_format)
        time_ref = pd.Timestamp(time_ref)
        if time_rounding == 'Y':
            time_year = time_ref.year
            time_ref = pd.Timestamp(str(time_year) + '-01-01 00:00:00')
        else:
            time_ref = time_ref.floor(time_rounding)
        time_range = pd.date_range(start=time_ref_file_start, end=time_ref_file_end, freq=time_frequency)

        log_stream.info(' -----> Time info defined by "time_start" and "time_end" arguments ... DONE')

    else:
        log_stream.info(' ----> Set time period ... FAILED')
        log_stream.error(' ===> Arguments "time_start" and/or "time_end" is/are not correctly set')
        raise IOError('Time type or format is wrong')

    if time_reverse:
        if time_range is not None:
            time_range = time_range[::-1]

    log_stream.info(' ----> Set time period ... DONE')

    return [time_ref, time_range]

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to define time frequency
def define_time_frequency(time_index, time_freq_default='D'):

    if isinstance(time_index, pd.DatetimeIndex):
        if time_index.shape[0] >= 3:
            time_freq_raw = pd.infer_freq(time_index)

            if time_freq_raw is None:
                log_stream.warning(' ===> Time freq is not defined by inferred frequency. Define using the '
                                   'time delta methods')
                time_delta = time_index[1] - time_index[0]
                time_freq_raw = time_delta.resolution_string

            time_freq_str = re.findall("[a-zA-Z]+", time_freq_raw)[0]

        elif time_index.shape[0] == 2:
            time_delta = time_index[1] - time_index[0]
            time_freq_str = time_delta.resolution_string
        elif time_index.shape[0] == 1:
            time_freq_str = time_freq_default
        else:
            log_stream.error(' ===> Time index is not correctly defined. Check your settings file.')
            raise RuntimeError('Time index is not correctly defined')
    else:
        log_stream.warning(' ===> Time index is not defined by pd.DatetimeIndex. '
                           'The time frequency is set to "' + time_freq_default + '"')
        time_freq_str = time_freq_default

    return time_freq_str
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Method to define time period
def define_time_range(time_dict, time_reverse=False):

    time_period = time_dict['time_period']
    time_reference = time_dict['time_reference']
    time_frequency = time_dict['time_frequency']
    time_rounding = time_dict['time_rounding']
    time_start = time_dict['time_start']
    time_end = time_dict['time_end']

    if time_start and time_end:

        time_start, time_end = pd.Timestamp(time_start), pd.Timestamp(time_end)
        time_start, time_end = time_start.round(time_rounding), time_end.round(time_rounding)

        time_range = pd.date_range(start=time_start, end=time_end, freq=time_frequency)

    elif time_period and time_reference:

        time_end = pd.Timestamp(time_reference)
        time_end = time_end.round(time_rounding)
        time_range = pd.date_range(end=time_end, periods=time_period, freq=time_frequency)

        time_start = time_range[0]

    else:
        log_stream.error(' ===> "time_start" and "time_end" or "time_period" and "time_reference" must be defined')
        raise RuntimeError('Time information are not enough to define the "time_range')

    if time_reverse:
        time_range = time_range[::-1]

    return time_range, time_start, time_end
# ----------------------------------------------------------------------------------------------------------------------
