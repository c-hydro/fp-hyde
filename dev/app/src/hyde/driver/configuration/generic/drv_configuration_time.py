"""
Class Features

Name:          drv_configuration_time
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180521'
Version:       '2.0.7'
"""

#######################################################################################
# Library
import logging
import time

from src.common.default.lib_default_args import sTimeFormat, sTimeType
from src.common.utils.lib_utils_apps_time import getTimeNow, getTimeFrom, getTimeTo, \
    getTimeSteps, getTimeRun, computeTimeRestart

from src.hyde.driver.configuration.generic.drv_configuration_debug import Exc

# Log
oLogStream = logging.getLogger(__name__)

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
    sTimeNow = None
    sTimeRun = None
    sTimeFrom = None
    sTimeTo = None

    iTimeDelta = None
    iTimeStep = None

    sTimeRefHH = None

    a1oTimeStep = {}
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method class initialization
    def __init__(self, sTimeArg=time.strftime(sTimeFormat, time.gmtime()), sTimeNow=None,
                 iTimeStep=1, iTimeDelta=3600, oTimeRefHH=None):

        # -------------------------------------------------------------------------------------
        # Store information in global workspace
        self.sTimeArg = sTimeArg
        self.sTimeNow = sTimeNow
        self.iTimeStep = iTimeStep
        self.iTimeDelta = iTimeDelta
        self.oTimeRefHH = oTimeRefHH
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to set times
    def getDataTime(self, bTimeReverse=False, bTimeRestart=True):

        # -------------------------------------------------------------------------------------
        # Info start
        oLogStream.info(' ---> Configure time ... ')

        # Get time now
        self.__getTimeNow()
        # Get running time
        self.__getTimeRun()

        # Get initial time step (taking care restart time condition)
        self.__getTimeFrom(self.iTimeStep, bTimeRestart)
        # Get ending time step (taking care corrivation time condition)
        self.__getTimeTo()

        # Compute period time steps
        self.__computeTimePeriodSteps(bTimeReverse)

        # Info end
        oLogStream.info(' ---> Configure time ... OK')

        return DataObject(self.__dict__)
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to get TimeNow
    def __getTimeNow(self):

        if self.sTimeNow is None:
            self.sTimeNow = getTimeNow(self.sTimeNow, sTimeType)[0]
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to set time now
    def __getTimeRun(self):
        self.sTimeRun = getTimeRun(self.sTimeNow, self.sTimeArg, sTimeType)
        self.sTimeNow = self.sTimeRun
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define time restart
    def __getTimeFrom(self, iTimeStep=0, bTimeRestart=True):

        # -------------------------------------------------------------------------------------
        # Restart time condition
        if bTimeRestart:
            # Evaluation of time restart and time from
            sTimeFrom = computeTimeRestart(self.sTimeRun, self.oTimeRefHH, self.iTimeDelta, iTimeStep)
        else:
            # Evaluation of time restart and time from
            sTimeFrom = getTimeFrom(sTimeTo=self.sTimeRun, iTimeDelta=self.iTimeDelta, iTimeStep=iTimeStep)[0]

        # Pass to global variable(s)
        self.sTimeFrom = sTimeFrom
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to get time to
    def __getTimeTo(self, iTimeStep=0):

        # -------------------------------------------------------------------------------------
        # Evaluation of time to
        sTimeTo = getTimeTo(sTimeFrom=self.sTimeRun, iTimeDelta=self.iTimeDelta, iTimeStep=iTimeStep)[0]

        # Pass to global variable(s)
        self.sTimeTo = sTimeTo
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute period time steps
    def __computeTimePeriodSteps(self, bTimeReverse=False):

        # -------------------------------------------------------------------------------------
        # Evaluation of time steps period
        a1oTimeStep = getTimeSteps(sTimeFrom=self.sTimeFrom, sTimeTo=self.sTimeTo, iTimeDelta=self.iTimeDelta)

        if bTimeReverse is True:
            a1oTimeStep = list(reversed(a1oTimeStep))

        self.a1oTimeStep = a1oTimeStep
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute check time steps
    def __computeTimeCheckSteps(self):

        # -------------------------------------------------------------------------------------
        # Evaluation of time steps Data check
        if self.iTimeStepCheck > 0:
            a1oTimeCheck = getTimeSteps(sTimeTo=self.sTimeRun, iTimeDelta=self.iTimeDelta,
                                        iTimeStep=self.iTimeStepCheck - 1)
        elif self.iTimeStepCheck == 0:
            a1oTimeCheck = [self.sTimeRun]
        elif self.iTimeStepCheck < 0:
            # Exit status with warning
            Exc.getExc(' =====> WARNING: Data check steps are set less than 0! Update to 0', 2, 1)
            a1oTimeCheck = [self.sTimeRun]
            self.iTimeStepCheck = 0
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Pass to global variable(s)
        self.a1oTimeCheck = a1oTimeCheck
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
