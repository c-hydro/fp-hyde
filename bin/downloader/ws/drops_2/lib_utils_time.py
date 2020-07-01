# -------------------------------------------------------------------------------------
# Libraries
import logging

import pandas as pd

from datetime import date
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set time run
def set_time(time_run_args=None, time_run_file=None, time_format='%Y-%m-%d %H:$M',
             time_period=1, time_frequency='H', time_rounding='H', time_reverse=True):

    logging.info(' ---> Set time run ... ')
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

    time_tmp = pd.Timestamp(time_run)
    time_run = time_tmp.floor(time_rounding)

    if time_period > 0:
        time_range = pd.date_range(end=time_run, periods=time_period, freq=time_frequency)
    else:
        logging.warning(' ===> TimePeriod must be greater then 0. TimePeriod is set automatically to 1')
        time_range = pd.DatetimeIndex([time_now], freq=time_frequency)

    if time_reverse:
        time_range = time_range[::-1]

    return time_run, time_range
# -------------------------------------------------------------------------------------
