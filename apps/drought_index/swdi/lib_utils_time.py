import logging
from datetime import date


# -------------------------------------------------------------------------------------
# Method to set time run
def set_time(time_run_args=None, time_run_file=None, time_format='%Y-%m-%d %H:$M'):

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
    return time_run

# -------------------------------------------------------------------------------------
