"""
Library Features:

Name:          lib_utils_time
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20220320'
Version:       '1.0.0'
"""

# ----------------------------------------------------------------------------------------------------------------------
# Libraries
import logging
import re
import pandas as pd

from copy import deepcopy
from datetime import date

from lib_info_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Method to set time run
def set_time(time_ref_args=None, time_ref_file=None, time_format='%Y-%m-%d %H:$M',
             time_ref_file_start=None, time_ref_file_end=None,
             time_period=1, time_frequency='H', time_rounding='H', time_reverse=True,
             data_frequency='H', data_rounding='H'):

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
            logging.info(' ------> Time ' + time_ref + ' set by user')
        elif (time_ref_args is None) and (time_ref_file is None):
            time_now = date.today()
            time_ref = time_now.strftime(time_format)
            log_stream.info(' ------> Time ' + time_ref + ' set by system')
        else:
            log_stream.info(' ----> Set time period ... FAILED')
            log_stream.error(' ===> Argument "time_run" is not correctly set')
            raise IOError('Time type or format is wrong')

        time_tmp = pd.Timestamp(time_ref)
        if time_rounding == 'M':
            time_ref = time_tmp.replace(day=1, hour=0, minute=0)
        else:
            time_ref = time_tmp.floor(time_rounding)

        if isinstance(time_period, int):

            if time_period > 0:
                time_range = pd.date_range(end=time_ref, periods=time_period, freq=time_frequency)
            else:
                log_stream.warning(' ===> TimePeriod must be greater then 0. TimePeriod is set automatically to 1')
                time_range = pd.DatetimeIndex([time_ref], freq=time_frequency)

        elif isinstance(time_period, str):

            if time_period == 'CURRENT_MONTH':

                time_current_first = time_ref.replace(day=1, hour=0)
                time_current_end = deepcopy(time_ref)
                if time_frequency == 'M':
                    time_range = deepcopy(time_ref)
                else:
                    time_range = pd.date_range(start=time_current_first, end=time_current_end, freq=time_frequency)

            elif time_period == 'PREVIOUS_MONTH':

                time_current_first = time_ref.replace(day=1)
                if time_frequency == 'D':
                    time_delta = pd.Timedelta(days=1)
                elif time_frequency == 'H':
                    time_delta = pd.Timedelta(hours=1)
                else:
                    log_stream.error(' ===> TimeFrequency "' + time_frequency + '" type is not supported')
                    raise NotImplementedError('Case not implemented yet')
                time_previous_tmp = time_current_first - time_delta

                time_previous_end = time_previous_tmp + pd.offsets.MonthEnd(n=0)
                time_previous_start = time_previous_end.replace(day=1, hour=0)

                time_range = pd.date_range(start=time_previous_start, end=time_previous_end, freq=time_frequency)
                time_ref = time_range[-1]

            else:
                log_stream.error(' ===> TimePeriod "' + time_period + '" expression is not supported')
                raise NotImplementedError('Case not implemented yet')
        else:
            log_stream.error(' ===> TimePeriod "' + str(time_period) + '" type is not supported')
            raise NotImplementedError('Case not implemented yet')

        logging.info(' -----> Time info defined by "time_run" argument ... DONE')

    elif (time_ref_file_start is not None) and (time_ref_file_end is not None):

        log_stream.info(' -----> Time info defined by "time_start" and "time_end" arguments ... ')

        time_ref_file_start = pd.Timestamp(time_ref_file_start)
        time_ref_file_start = time_ref_file_start.floor(time_rounding)
        time_ref_file_end = pd.Timestamp(time_ref_file_end)
        time_ref_file_end = time_ref_file_end.floor(time_rounding)

        if time_ref_file_start > time_ref_file_end:
            log_stream.error(' ===> Variable "time_start" is greater than "time_end". Check your settings file.')
            raise RuntimeError('Time_Range is not correctly defined.')

        time_now = date.today()
        time_ref = time_now.strftime(time_format)
        time_ref = pd.Timestamp(time_ref)
        time_ref = time_ref.floor(time_rounding)
        time_range = pd.date_range(start=time_ref_file_start, end=time_ref_file_end, freq=time_frequency)

        log_stream.info(' -----> Time info defined by "time_start" and "time_end" arguments ... DONE')

    elif (time_ref_file_start is not None) and (time_ref_file_end is None):

        log_stream.info(' -----> Time info defined by "time_run" argument ... ')

        if time_ref_args is not None:
            time_ref = time_ref_args
            log_stream.info(' ------> Time ' + time_ref + ' set by argument')
        elif (time_ref_args is None) and (time_ref_file is not None):
            time_ref = time_ref_file
            logging.info(' ------> Time ' + time_ref + ' set by user')
        elif (time_ref_args is None) and (time_ref_file is None):
            time_now = date.today()
            time_ref = time_now.strftime(time_format)
            log_stream.info(' ------> Time ' + time_ref + ' set by system')
        else:
            log_stream.info(' ----> Set time period ... FAILED')
            log_stream.error(' ===> Argument "time_run" is not correctly set')
            raise IOError('Time type or format is wrong')

        time_ref = pd.Timestamp(time_ref)

        if data_frequency == 'D':
            if time_rounding == 'M':
                time_ref = time_ref.replace(day=1, hour=0, minute=0)
            else:
                time_ref = time_ref.floor(time_rounding)
            time_ref = time_ref.strftime('%Y-%m-%d')
        elif data_frequency == 'H':
            if time_rounding == 'M':
                time_user = deepcopy(time_ref)
                time_ref = time_ref.replace(day=1, hour=0, minute=0)
            else:
                time_ref = time_ref.floor(time_rounding)
            time_ref = time_ref.strftime('%Y-%m-%d %H')
        else:
            log_stream.error(' ===> DataFrequency "' + str(data_frequency) + '" type is not supported')
            raise NotImplementedError('Case not implemented yet')

        if time_frequency == 'M':
            time_tmp = pd.Timestamp(time_ref).strftime('%Y-%m')
            time_ref_file_start = pd.Timestamp(time_ref_file_start).strftime('%Y-%m')
        elif time_frequency == 'H':
            time_tmp = pd.Timestamp(time_ref).strftime('%Y-%m-%d %H')
            time_ref_file_start = pd.Timestamp(time_ref_file_start).strftime('%Y-%m-%d %H')
        else:
            time_tmp = pd.Timestamp(time_ref).strftime('%Y-%m-%d')

        time_end = pd.Timestamp(time_tmp)
        time_start = pd.Timestamp(time_ref_file_start)

        if time_period == 'FROM_TIME_START':
            time_range = pd.date_range(start=time_start, end=time_end, freq=time_frequency)

            if time_end not in time_range:
                time_range = time_range.append(pd.DatetimeIndex([time_end]))
                time_range = pd.DatetimeIndex(time_range)

        else:
            log_stream.error(' ===> TimePeriod "' + str(time_period) + '" type is not supported')
            raise NotImplementedError('Case not implemented yet')

        if time_frequency == 'M':
            time_range = time_range.format(formatter=lambda x: x.strftime('%Y-%m'))
            time_range = pd.DatetimeIndex(time_range)
            time_ref = time_user.floor('H')

    else:
        log_stream.info(' ----> Set time period ... FAILED')
        log_stream.error(' ===> Arguments "time_start" and/or "time_end" is/are not correctly set')
        raise IOError('Time type or format is wrong')

    if time_reverse:
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
