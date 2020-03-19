"""
Class Features

Name:          drv_configuration_time_wrf
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20200228'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging
import time
import pandas as pd

from src.hyde.algorithm.settings.nwp.wrf.lib_wrf_args import logger_name, time_format

# Log
log_stream = logging.getLogger(logger_name)

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
class DataObject(dict):
    pass
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class Time
class DataTime:

    # -------------------------------------------------------------------------------------
    # Global Variable(s)
    time_now = None
    time_settings = None
    time_run = None
    time_from = None
    time_to = None

    time_frequency = None
    time_period = None

    time_rounding = None

    time_steps = {}
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method class initialization
    def __init__(self, time_arg=time.strftime(time_format, time.gmtime()),
                 time_settings=None,
                 time_now=None,
                 time_period_past=0, time_period_future=0, time_frequency='H',
                 time_rounding='H'):

        # -------------------------------------------------------------------------------------
        # Store information in global workspace
        self.time_arg = time_arg
        self.time_settings = time_settings
        self.time_now = time_now
        self.time_period_past = int(time_period_past)
        self.time_period_future = int(time_period_future)
        self.time_frequency = time_frequency
        self.time_rounding = time_rounding
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to set times
    def getDataTime(self, time_reverse=False):

        # -------------------------------------------------------------------------------------
        # Info start
        log_stream.info(' ---> Configure time ... ')

        # Get time now
        self.time_now = self.__getTimeNow()
        # Get time argument
        self.time_arg = self.__getTimeArg()
        # Set time run
        self.time_run = self.__setTimeRun(self.time_now, self.time_arg)
        # Round time to reference
        self.time_run = self.__computeTimeRound(self.time_rounding)

        # Get initial time step (taking care restart time condition)
        self.time_from = self.__getTimeFrom(self.time_run,
                                            time_period=self.time_period_past,
                                            time_frequency=self.time_frequency)
        # Get ending time step
        self.time_to = self.__getTimeTo(self.time_run,
                                        time_period=self.time_period_future,
                                        time_frequency=self.time_frequency)

        # Compute period time steps
        self.time_steps = self.__computeTimePeriod(self.time_from, self.time_to,
                                                   time_frequency=self.time_frequency,
                                                   time_reverse=time_reverse)

        # Info end
        log_stream.info(' ---> Configure time ... OK')

        return DataObject(self.__dict__)
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to round time to reference
    def __computeTimeRound(self, time_rounding):

        log_stream.info(' ----> Round time run  ... ')
        time_round = self.time_run.round(time_rounding)

        if time_round > self.time_run:
            time_round = pd.date_range(end=time_round, periods=2, freq=time_rounding)[0]

        log_stream.info(' -----> Algorithm time run:  [' + time_round.strftime(time_format) + ']')
        log_stream.info(' ----> Round time run  ... DONE')

        return time_round
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to get time now
    def __getTimeNow(self):

        log_stream.info(' ----> Configure time now  ... ')
        try:
            if self.time_now is None:
                log_stream.info(' -----> Time now is not set. Time will be taken using time library.')
                self.time_now = time.strftime(time_format, time.gmtime())
            else:
                log_stream.info(' -----> Time argument is set using script configuration file')

            if pd.to_datetime(self.time_now, format=time_format, errors='coerce'):
                log_stream.warning(' ===> Mismatch in input time now format. '
                                   'Expected format is: ' + time_format + '. Try to recover using automatic parser.')
                time_now = pd.to_datetime(self.time_now)
            else:
                time_now = pd.to_datetime(self.time_now, format=time_format)
            time_now = time_now.floor('min')
            time_now = time_now.replace(minute=0)

            self.time_now = time_now.strftime(time_format)

            log_stream.info(' ----> Configure time now ... DONE [' + self.time_now + ']')

        except BaseException:
            log_stream.error(' -----> Time now definition failed! Check your data and settings!')
            raise BaseException('Error in time now definition!')

        return time_now
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to get time set in argument(s)
    def __getTimeArg(self):

        log_stream.info(' ----> Configure time argument  ... ')
        try:
            if self.time_arg is None:

                if self.time_settings is not None:
                    self.time_arg = self.time_settings
                    log_stream.info(' -----> Time argument is not set. Time will be taken using time in settings file.')
                else:
                    log_stream.info(' -----> Time argument is not set. Time will be taken using time library.')
                    self.time_arg = time.strftime(time_format, time.gmtime())
            else:
                log_stream.info(' -----> Time argument is set using script arg(s)')

            if pd.to_datetime(self.time_now, format=time_format, errors='coerce'):
                log_stream.warning(' ===> Mismatch in input time argument format. '
                                   'Expected format is: ' + time_format + '. Try to recover using automatic parser.')
                time_arg = pd.to_datetime(self.time_arg)
            else:
                time_arg = pd.to_datetime(self.time_arg, format=time_format)

            time_arg = time_arg.floor('min')
            time_arg = time_arg.replace(minute=0)

            self.time_arg = time_arg.strftime(time_format)

            log_stream.info(' ----> Configure time argument ... DONE [' + self.time_arg + ']')

        except BaseException:
            log_stream.error(' -----> Time now definition failed! Check your data and settings!')
            raise BaseException('Error in time now definition!')

        return time_arg

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to set time run
    @staticmethod
    def __setTimeRun(time_now, time_arg):

        log_stream.info(' ----> Set time run  ... ')
        if time_arg is not None:
            log_stream.info(' -----> Time argument is used as time run [' + time_arg.strftime(time_format) + ']')
            log_stream.info(' ----> Set time run  ... DONE')
            return time_arg
        else:
            log_stream.info(' -----> Time now is used as time run [' + time_now.strftime(time_format) + ']')
            log_stream.info(' ----> Set time run  ... DONE')
            return time_now

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define time restart
    def __parserTimeFrm(self):

        pass

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define time restart
    @staticmethod
    def __getTimeFrom(time_run, time_period=0, time_frequency='H'):

        if time_period == 0:
            time_from = time_run
        else:
            time_period = time_period + 1
            time_from = pd.date_range(end=time_run, periods=time_period, freq=time_frequency)[0]
        return time_from

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to get time to
    @staticmethod
    def __getTimeTo(time_run, time_period=0, time_frequency='H'):

        if time_period == 0:
            time_to = time_run
        else:
            time_period = time_period + 1
            time_to = pd.date_range(start=time_run, periods=time_period, freq=time_frequency)[-1]
        return time_to

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute period time steps
    @staticmethod
    def __computeTimePeriod(time_from, time_to, time_frequency='H', time_reverse=False):

        time_range = pd.date_range(time_from, time_to, freq=time_frequency)
        time_range = time_range.floor(time_frequency)

        if time_reverse:
            time_range = time_range.sort_values(return_indexer=False, ascending=False)

        return time_range

# -------------------------------------------------------------------------------------
