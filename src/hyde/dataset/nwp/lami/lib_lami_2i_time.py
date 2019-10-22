"""
Library Features:

Name:          lib_lami_2i_time
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20181207'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging

import sys
import inspect

from numpy import abs
from datetime import timedelta, datetime

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
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
# Method to compute time variables
def computeTime(oVarTime, sTimeFormat='%Y%m%d%H%M'):

    # -------------------------------------------------------------------------------------
    # Iterate over time-steps
    oTimeRef = None
    sTimePrev = None
    a1oTimeSteps = None
    a1oTimeIdx = None
    iTimeIdxStart = None
    iTimeIdxEnd = None
    for iTimeIdx, (iTimeData, oTimeData) in enumerate(oVarTime.items()):

        # -------------------------------------------------------------------------------------
        # Get time parameter(s)
        iP_1 = int(oTimeData['P1'])
        iP_2 = int(oTimeData['P2'])
        iUTR = int(oTimeData['TimeRangeUnit'])
        iTRI = int(oTimeData['TimeRangeIndicator'])
        oTimeAnalysis = oTimeData['TimeAnalysis']

        sTimeYear = oTimeData['Year']
        sTimeMonth = oTimeData['Month']
        sTimeDay = oTimeData['Day']
        sTimeHour = oTimeData['Hour']
        sTimeMinute = oTimeData['Minute']
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Get time delta using dictionary definition
        if iUTR in oUTR:
            iTimeUnit = int(list(oUTR[iUTR].values())[0])
        else:
            iTimeUnit = None

        # Get time delta using dictionary definition
        if iTRI in oTRI:
            sTimeRangeFunc = oTRI[iTRI]
        else:
            sTimeRangeFunc = None
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Define time P1 and P2 for each step
        sTimeAnalysis = oTimeAnalysis.strftime(sTimeFormat)
        oTimeAnalysis = datetime.strptime(sTimeAnalysis, sTimeFormat)

        sTimeStart = sTimeYear + sTimeMonth + sTimeDay + sTimeHour + sTimeMinute
        oTimeStart = datetime.strptime(sTimeStart, sTimeFormat)

        oTimeStep_P1 = oTimeStart + timedelta(seconds=iTimeUnit * iP_1)
        oTimeStep_P2 = oTimeStart + timedelta(seconds=iTimeUnit * iP_2)

        # Define time reference
        if oTimeRef is None:
            # First step
            oTimeRef = oTimeAnalysis
        else:
            oTimeRef = datetime.strptime(sTimePrev, sTimeFormat)
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Initialize time idxs and steps workspace
        if a1oTimeIdx is None:
            a1oTimeIdx = []
        if a1oTimeSteps is None:
            a1oTimeSteps = []

        # Get method to evaluate range indicator definition
        if hasattr(sys.modules[__name__], sTimeRangeFunc):
            oFxName = getattr(sys.modules[__name__], sTimeRangeFunc)
        else:
            oFxName = None

        # Check method availability
        if oFxName is not None:
            oFxArgs_GENERIC = {
                'oTimeStep_P1': oTimeStep_P1,
                'oTimeStep_P2': oTimeStep_P2,
                'oTimeRef': oTimeRef,
                'iTimeUnit': iTimeUnit,
            }

            # Inspect function to get signature
            oFxSignature = inspect.signature(oFxName)

            # Update signature using value from workspace
            oFxArgs_SELECT = {}
            for iArgsID, oArgsName in enumerate(oFxSignature.parameters.values()):
                sArgsName = oArgsName.name
                if sArgsName in oFxArgs_GENERIC.keys():
                    oFxArgs_SELECT[sArgsName] = oFxArgs_GENERIC[sArgsName]
                else:
                    oFxArgs_SELECT[sArgsName] = oFxSignature.parameters[sArgsName].default

            # Call function with mutable argument(s)
            oFxOut = oFxName(**oFxArgs_SELECT)
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Parser results
            if oFxOut:

                # Save time idxs and steps
                a1oTimeIdx.append(iTimeIdx)

                for sTimeStep in oFxOut:
                    if sTimeStep not in a1oTimeSteps:
                        a1oTimeSteps.append(sTimeStep)
                sTimePrev = sTimeStep
            else:
                sTimePrev = oTimeRef.strftime(sTimeFormat)
            # -------------------------------------------------------------------------------------

        else:
            pass
        # -------------------------------------------------------------------------------------

    else:
        pass
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Return variable(s)
    return a1oTimeSteps, a1oTimeIdx
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute istantaneous variable time features
def istantaneous(oTimeStep_P1, oTimeRef, iTimeUnit=3600, sTimeFormat='%Y%m%d%H%M'):

    # Get time information
    iTimeStep = int(abs(int((((oTimeRef - oTimeStep_P1).total_seconds()) / iTimeUnit))))

    # Compute time save period
    oTimeSave_P2 = oTimeStep_P1
    oTimeSave_P1 = oTimeSave_P2 - timedelta(seconds=(iTimeStep - 1)*iTimeUnit)

    # Compute time save steps
    a1oTimeSteps = []
    while oTimeSave_P1 <= oTimeSave_P2:

        # Get time save
        sTimeSave = oTimeSave_P1.strftime(sTimeFormat)
        a1oTimeSteps.append(sTimeSave)

        # Increase time step
        oTimeSave_P1 += timedelta(seconds=iTimeUnit)

    return a1oTimeSteps
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute average variable time features
def average(oTimeStep_P1, oTimeStep_P2, iTimeUnit=3600, sTimeFormat='%Y%m%d%H%M'):

    # Get time information
    iTimeStep = int(abs(int((((oTimeStep_P2 - oTimeStep_P1).total_seconds()) / iTimeUnit))))

    # Compute time save period
    oTimeSave_P1 = oTimeStep_P1 + timedelta(seconds=iTimeUnit)
    oTimeSave_P2 = oTimeStep_P2

    # Compute time save steps
    a1oTimeSteps = []
    while oTimeSave_P1 <= oTimeSave_P2:
        # Get time save
        sTimeSave = oTimeSave_P1.strftime(sTimeFormat)
        a1oTimeSteps.append(sTimeSave)

        # Increase time step
        oTimeSave_P1 += timedelta(seconds=iTimeUnit)

    return a1oTimeSteps

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute accumulation variable time features
def accumulation(oTimeStep_P1, oTimeStep_P2, iTimeUnit=3600, sTimeFormat='%Y%m%d%H%M'):

    # Get time information
    iTimeStep = int(abs(int((((oTimeStep_P2 - oTimeStep_P1).total_seconds()) / iTimeUnit))))

    # Compute time save period
    oTimeSave_P2 = oTimeStep_P2
    oTimeSave_P1 = oTimeSave_P2 - timedelta(seconds=(iTimeStep - 1)*iTimeUnit)

    # Compute time save steps
    a1oTimeSteps = []
    while oTimeSave_P1 <= oTimeSave_P2:
        # Get time save
        sTimeSave = oTimeSave_P1.strftime(sTimeFormat)
        a1oTimeSteps.append(sTimeSave)

        # Increase time step
        oTimeSave_P1 += timedelta(seconds=iTimeUnit)

    return a1oTimeSteps
# -------------------------------------------------------------------------------------
