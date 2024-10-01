"""
Library Features:

Name:          lib_utils_apps_time
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180521'
Version:       '2.0.7'
"""

#################################################################################
# Library
import logging
import time
import datetime

from sys import version_info
from time import mktime
from numpy import abs

from src.common.default.lib_default_args import sTimeFormat as sTimeFormat_Default

# Log
log_stream = logging.getLogger(__name__)

# Debug
# import matplotlib.pylab as plt
#################################################################################

# --------------------------------------------------------------------------------
# Dictionary of seconds for unit(s)
oSecondsUnits = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to get restart time
def computeTimeRestart(sTime, oTimeRestartHH='00', iTimeStep=3600, iTimePeriod=0):

    # Check time restart definition
    if isinstance(oTimeRestartHH, str):
        oTimeRestartHH = [oTimeRestartHH]
    if oTimeRestartHH is None:
        bTimeRoundHH = False
    else:
        bTimeRoundHH = True

    # Sort time restart list
    if bTimeRoundHH:
        if isinstance(oTimeRestartHH, str):
            oTimeRestartHH = [oTimeRestartHH]
        oTimeRestartHH.sort()

    # Compute time restart
    # sTimeFormat = defineTimeFormat(sTime)
    oTime = datetime.datetime.strptime(sTime, sTimeFormat_Default)
    oTime = oTime.replace(minute=0, second=0)

    oTimeRaw_From = oTime - datetime.timedelta(seconds=int(iTimePeriod * iTimeStep))
    oTimeRaw_To = oTime + datetime.timedelta(seconds=int(iTimePeriod * iTimeStep))

    oTimeRaw_From = oTimeRaw_From.replace(hour=0, minute=0)
    oTimeRaw_To = oTimeRaw_To.replace(hour=23, minute=0)

    a1oTimeRaw = []
    if bTimeRoundHH:
        for oTimeRaw_Step in computeDateRange(oTimeRaw_From, oTimeRaw_To):
            for sTimeRestartHH in oTimeRestartHH:
                oTimeRaw_Step = oTimeRaw_Step.replace(hour=int(sTimeRestartHH))
                a1oTimeRaw.append(oTimeRaw_Step.strftime(sTimeFormat_Default))
        a1oTimeRaw = convertTimeList2Obj(a1oTimeRaw)
    else:
        a1oTimeRaw = computeDateRange(oTimeRaw_From, oTimeRaw_To)

    a1oTimeFilter = []
    for oTimeFilter in a1oTimeRaw:
        if oTimeFilter <= oTime:
            a1oTimeFilter.append(oTimeFilter)

    if bTimeRoundHH:
        for sTimeRestartHH in oTimeRestartHH:
            iTimeRestartHour = int(sTimeRestartHH)
            iTimeArgHour = int(oTime.hour)
            if iTimeRestartHour == iTimeArgHour:
                a1oTimeFilter.append(oTime)

    oTimeRestart = None
    for iTimeID, oTimeFilter in enumerate(reversed(a1oTimeFilter)):

        if iTimeID == iTimePeriod:
            oTimeRestart = oTimeFilter
            break
        else:
            oTimeRestart = None

    if oTimeRestart:
        sTimeRestart = oTimeRestart.strftime(sTimeFormat_Default)
    else:
        sTimeRestart = None

    return sTimeRestart

# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to convert time list to date-time objects
def convertTimeList2Obj(a1oTimeList):
    return [datetime.datetime.strptime(sTime, sTimeFormat_Default) for sTime in a1oTimeList]
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to compute date(s) between two time(s)
def computeDateRange(oDate1, oDate2):
    for iN in range(int((oDate2 - oDate1).days) + 1):
        yield oDate1 + datetime.timedelta(iN)
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to check time reference
def checkTimeRef(sTime, oTimeMins=None, oTimeHours=None):
    oTime = datetime.datetime.strptime(sTime, sTimeFormat_Default)

    a1bTimeCheck = []
    if oTimeMins:
        oTimeCheck = [str(oTime.minute).zfill(2)]
        if oTimeCheck not in oTimeMins:
            a1bTimeCheck.append(False)
        else:
            a1bTimeCheck.append(True)

    if oTimeHours:
        oTimeCheck = [str(oTime.hour).zfill(2)]
        if oTimeCheck not in oTimeHours:
            a1bTimeCheck.append(False)
        else:
            a1bTimeCheck.append(True)

    if all(a1bTimeCheck) is True:
        bTimeCheck = True
    else:
        bTimeCheck = False

    return bTimeCheck
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to round time step to give delta of defined units (minutes, ...)
def roundTimeStep(sTime, sDeltaUnits='minutes', iDeltaValue=None):

    oTime = datetime.datetime.strptime(sTime, sTimeFormat_Default)
    if sDeltaUnits == 'minutes':
        oDeltaValue = datetime.timedelta(minutes=iDeltaValue)
    elif sDeltaUnits == 'hours':
        oDeltaValue = datetime.timedelta(minutes=iDeltaValue*60)
    else:
        oDeltaValue = None

    oTime_Round = None
    if iDeltaValue:
        if version_info >= (3, 0):
            oTime_Round = oTime + (datetime.datetime.min - oTime) % oDeltaValue
        elif version_info < (3, 0):

            if iDeltaValue < 0:
                sDeltaDirection = 'down'
            elif iDeltaValue > 0:
                sDeltaDirection = 'up'
            else:
                sDeltaDirection = None

            if sDeltaUnits == 'minutes':
                if sDeltaDirection:
                    oTime_Minute = (oTime.minute // abs(iDeltaValue) +
                                    (1 if sDeltaDirection == 'up' else 0)) * abs(iDeltaValue)
                    oTime_Round = oTime + datetime.timedelta(minutes=oTime_Minute - oTime.minute)
                else:
                    oTime_Round = oTime

            elif sDeltaUnits == 'hours':
                if sDeltaDirection:
                    oTime_Minute = (oTime.minute // abs(iDeltaValue * 60) +
                                    (1 if sDeltaDirection == 'up' else 0)) * abs(iDeltaValue * 60)
                    oTime_Round = oTime + datetime.timedelta(minutes=oTime_Minute - oTime.minute)
                else:
                    oTime_Round = oTime
    elif iDeltaValue == 0:
        if sDeltaUnits == 'minutes':
            oTime_Round = oTime.replace(minute=iDeltaValue)
        elif sDeltaUnits == 'hours':
            oTime_Round = oTime.replace(hour=iDeltaValue)
    else:
        oTime_Round = None

    if oTime_Round:
        sTime_Round = oTime_Round.strftime(sTimeFormat_Default)
    else:
        sTime_Round = None

    return sTime_Round

# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to find closest time (comparing with hours, minutes ...)
def findTimeClosest(sTime_Ref, oTime_HH=None):
    # Create datetime object
    oTime_Ref = datetime.datetime.strptime(sTime_Ref, sTimeFormat_Default)
    # Closest time using hours
    if oTime_HH is not None:
        a1oTime_Delta = []
        for sTime_HH_Step in oTime_HH:
            oTime_Step = oTime_Ref.replace(hour=int(sTime_HH_Step))
            oTime_Delta = oTime_Ref - oTime_Step
            if oTime_Delta > datetime.timedelta(seconds=1):
                a1oTime_Delta.append(oTime_Delta)

        oTime_Delta_Min = min(a1oTime_Delta)
        iTime_Delta_Index = a1oTime_Delta.index(oTime_Delta_Min)

        sTime_HH_Select = oTime_HH[iTime_Delta_Index]

        oTime_Select = oTime_Ref.replace(hour=int(sTime_HH_Select))
        sTime_Select = oTime_Select.strftime(sTimeFormat_Default)
        return sTime_Select
    else:
        log_stream.warning(' =====> Some arguments to find closest time are not defined! Check your data!')
        return sTime_Ref
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to check time format
def correctTimeLength(sTime):

    sTimeUpd = None
    if len(sTime) == 12:
        sTimeUpd = sTime
    elif len(sTime) == 16:
        sTimeUpd = sTime
    elif 8 <= len(sTime) < 12:
        iTimeLength = len(sTime)
        iTimeLessDigits = 12 - iTimeLength
        sTimeLessFormat = '0' * iTimeLessDigits
        sTimeUpd = sTime + sTimeLessFormat
    else:
        log_stream.error(' =====> sTime has not allowed length. sTime cannot defined!')
        raise TypeError

    sTimeUpdFormat = defineTimeFormat(sTimeUpd)

    # Check time format definition
    checkTimeFormat(sTimeUpd, sTimeUpdFormat)

    return sTimeUpd, sTimeUpdFormat
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to check time format for time string
def checkTimeFormat(sTime, sTimeFormat=sTimeFormat_Default):
    try:
        datetime.datetime.strptime(sTime, sTimeFormat)
    except BaseException as BExp:
        log_stream.error(' =====> sTime has not correct format. sTime cannot defined!')
        raise BExp
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to define time format
def defineTimeFormat(sTime):

    if sTime.__len__() == 12:
        sTimeFormat = '%Y%m%d%H%M'
    elif sTime.__len__() == 10:
        sTimeFormat = '%Y%m%d%H'
    elif sTime.__len__() == 8:
        sTimeFormat = '%Y%m%d'
    elif sTime.__len__() == 16:
        sTimeFormat = '%Y-%m-%d %H:%M'
    elif sTime.__len__() == 19:
        sTimeFormat = '%Y-%m-%d %H:%M:%S'
    else:
        log_stream.error(' =====> sTime has not allowed length. sTimeFormat cannot defined!')
        raise TypeError

    # Check time format
    try:
        datetime.datetime.strptime(sTime, sTimeFormat)
    except BaseException as BExp:
        log_stream.error(' =====> sTimeFormat is not correctly selected. sTimeFormat cannot defined!')
        raise BExp

    return sTimeFormat
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to convert time format
def convertTimeFormat(sTime_IN, sTimeFormat_IN=None, sTimeFormat_OUT=None):

    # Select automatically time format (is not defined by args)
    if sTimeFormat_IN is None:
        sTimeFormat_IN = defineTimeFormat(sTime_IN)

    # Create datetime obj to convert time format
    oTime_IN = datetime.datetime.strptime(sTime_IN, sTimeFormat_IN)

    # Convert time string using a different time format
    if sTimeFormat_OUT is not None:
        sTime_OUT = oTime_IN.strftime(sTimeFormat_OUT)
    else:
        sTime_OUT = sTime_IN

    return sTime_OUT

# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to convert local time to GMT time and viceversa (sTimeLocal  --> 'yyyymmddHHMM')
def convertTimeLOCxGMT(sTime_IN=None, iTimeDiff=0):
    if sTime_IN:
        sTimeFormat_IN = defineTimeFormat(sTime_IN)
        sTimeFormat_OUT = sTimeFormat_IN

        oTime_IN = datetime.datetime.strptime(sTime_IN, sTimeFormat_IN)
        oTime_IN = oTime_IN.replace(minute=0, second=0, microsecond=0)
        oTime_OUT = oTime_IN + datetime.timedelta(seconds=iTimeDiff * 3600)
        sTime_OUT = oTime_OUT.strftime(sTimeFormat_OUT)
    else:
        log_stream.error(" =====> sTime_IN not defined! sTime_OUT cannot calculated!")
        raise ValueError

    return sTime_OUT
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to get local time
def getTimeLocal(sTimeFormat=sTimeFormat_Default):
    return time.strftime(sTimeFormat, time.localtime())  # ---> LOCAL TIME
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to get GMT time
def getTimeGMT(sTimeFormat=sTimeFormat_Default):
    return time.strftime(sTimeFormat, time.gmtime())  # ---> GMT TIME
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to get running time
def getTimeRun(sTimeNow='', sTimeArg='', sTimeType='GMT'):

    if not sTimeNow == '':
        [sTimeNow, sTimeNowFormat] = getTimeNow(sTimeNow, sTimeType)
        oTimeNow = datetime.datetime.strptime(sTimeNow, sTimeNowFormat)
    else:
        oTimeNow = None
        sTimeNowFormat = None

    if not sTimeArg == '':
        [sTimeArg, sTimeArgFormat] = getTimeNow(sTimeArg, sTimeType)
        oTimeArg = datetime.datetime.strptime(sTimeArg, sTimeArgFormat)
    else:
        oTimeArg = None
        sTimeArgFormat = None

    if oTimeArg:
        sTimeRun = oTimeArg.strftime(sTimeFormat_Default)
    else:
        sTimeRun = oTimeNow.strftime(sTimeFormat_Default)

    return sTimeRun

# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to define sTimeNow
def getTimeNow(sTimeNow='', sTimeRefType='local'):

    if sTimeNow is None:
        sTimeNow = ''

    if not sTimeNow == '':
        [sTimeNow, sTimeFormat] = correctTimeLength(sTimeNow)
    elif sTimeNow == '':

        if sTimeRefType == 'local':
            sTimeNow = getTimeLocal()
        elif sTimeRefType == 'GMT':
            sTimeNow = getTimeGMT()
        else:
            log_stream.warning(' =====> sTimeTypeRef is not defined correctly! sTimeNow initialized as local time!')
            sTimeNow = getTimeLocal()

        [sTimeNow, sTimeFormat] = correctTimeLength(sTimeNow)

    else:
        log_stream.error(' =====> sTimeNow format is unknown. Please check your time string!')
        raise ValueError

    return sTimeNow, sTimeFormat
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to define sTimeStep
def getTimeStep(sTimeIN=None, iTimeDelta=3600, iTimeStep=0):
    if sTimeIN:
        sTimeFormat = defineTimeFormat(sTimeIN)
        oTimeIN = datetime.datetime.strptime(sTimeIN, sTimeFormat)
        oTimeOUT = oTimeIN + datetime.timedelta(seconds=iTimeStep * iTimeDelta)
        sTimeOUT = oTimeOUT.strftime(sTimeFormat)
    else:
        log_stream.error(" =====> sTimeIN not defined! sTimeOUT cannot calculated!")
        raise ValueError

    return sTimeOUT, sTimeFormat
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to define sTimeTo
def getTimeTo(sTimeFrom=None, iTimeDelta=3600, iTimeStep=0):
    if sTimeFrom:
        sTimeFormat = defineTimeFormat(sTimeFrom)
        oTimeFrom = datetime.datetime.strptime(sTimeFrom, sTimeFormat)
        oTimeTo = oTimeFrom + datetime.timedelta(seconds=iTimeStep * iTimeDelta)
        sTimeTo = oTimeTo.strftime(sTimeFormat)
    else:
        log_stream.error(" =====> sTimeFrom not defined! sTimeTo cannot calculated!")
        raise ValueError

    return sTimeTo, sTimeFormat
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to define sTimeFrom
def getTimeFrom(sTimeTo=None, iTimeDelta=3600, iTimeStep=0):
    if sTimeTo:
        sTimeFormat = defineTimeFormat(sTimeTo)
        oTimeTo = datetime.datetime.strptime(sTimeTo, sTimeFormat)
        oTimeFrom = oTimeTo - datetime.timedelta(seconds=iTimeStep * iTimeDelta)
        sTimeFrom = oTimeFrom.strftime(sTimeFormat)
    else:
        log_stream.error(" =====> ERROR: sTimeTo not defined! sTimeFrom cannot calculated!")
        raise ValueError

    return sTimeFrom, sTimeFormat
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to define a1oTimeSteps (using sTimeFrom, sTimeTo, iTimeDelta, iTimeStep)
def getTimeSteps(sTimeFrom=None, sTimeTo=None, iTimeDelta=3600, iTimeStep=0):
    # Case sTimeFrom and sTimeTo to define a1oTimeSteps
    if sTimeFrom and sTimeTo and iTimeDelta:

        sTimeFromFormat = defineTimeFormat(sTimeFrom)
        sTimeToFormat = defineTimeFormat(sTimeTo)

        oTimeFrom = datetime.datetime.strptime(sTimeFrom, sTimeFromFormat)
        oTimeTo = datetime.datetime.strptime(sTimeTo, sTimeToFormat)

    elif sTimeFrom and iTimeDelta and iTimeStep:

        [sTimeTo, sTimeToFormat] = getTimeTo(sTimeFrom, iTimeDelta, iTimeStep)
        sTimeFromFormat = defineTimeFormat(sTimeFrom)

        oTimeFrom = datetime.datetime.strptime(sTimeFrom, sTimeFromFormat)
        oTimeTo = datetime.datetime.strptime(sTimeTo, sTimeToFormat)

    elif sTimeTo and iTimeDelta and iTimeStep:

        [sTimeFrom, sTimeFromFormat] = getTimeFrom(sTimeTo, iTimeDelta, iTimeStep)
        sTimeToFormat = defineTimeFormat(sTimeTo)

        oTimeFrom = datetime.datetime.strptime(sTimeFrom, sTimeFromFormat)
        oTimeTo = datetime.datetime.strptime(sTimeTo, sTimeToFormat)

    else:

        sTimeFromFormat = defineTimeFormat(sTimeFrom)
        sTimeToFormat = defineTimeFormat(sTimeTo)
        oTimeFrom = datetime.datetime.strptime(sTimeFrom, sTimeFromFormat)
        oTimeTo = datetime.datetime.strptime(sTimeTo, sTimeToFormat)

    # Define a1oTimeSteps
    oTimeStep = oTimeFrom
    iTimeDelta = datetime.timedelta(seconds=iTimeDelta)

    if oTimeFrom != oTimeTo:

        a1oTimeSteps = []
        while oTimeStep <= oTimeTo:
            a1oTimeSteps.append(oTimeStep.strftime(sTimeToFormat))
            oTimeStep += iTimeDelta

    else:
        a1oTimeSteps = [oTimeFrom.strftime(sTimeFromFormat)]

    return a1oTimeSteps

# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to check max time interval
def checkTimeMaxInt(a1oTime_Max=None, a1oTime_Test=None):

    if a1oTime_Test:
        if a1oTime_Max:

            sTime_From_Max = a1oTime_Max[0]
            sFormat_From_Max = defineTimeFormat(sTime_From_Max)
            oTime_From_Max = datetime.datetime.strptime(sTime_From_Max, sFormat_From_Max)
            sTime_To_Max = a1oTime_Max[-1]
            sFormat_To_Max = defineTimeFormat(sTime_To_Max)
            oTime_To_Max = datetime.datetime.strptime(sTime_To_Max, sFormat_To_Max)
            sTime_From_Test = a1oTime_Test[0]
            sFormat_From_Test = defineTimeFormat(sTime_From_Test)
            oTime_From_Test = datetime.datetime.strptime(sTime_From_Test, sFormat_From_Test)
            sTime_To_Test = a1oTime_Test[-1]
            sFormat_To_Test = defineTimeFormat(sTime_To_Test)
            oTime_To_Test = datetime.datetime.strptime(sTime_To_Test, sFormat_To_Test)

            if oTime_From_Max >= oTime_From_Test:
                oTime_From_Upd = oTime_From_Max
                sTime_From_Upd = oTime_From_Upd.strftime(sFormat_From_Max)
            else:
                oTime_From_Upd = oTime_From_Test
                sTime_From_Upd = oTime_From_Upd.strftime(sFormat_From_Test)

            if oTime_To_Max >= oTime_To_Test:
                oTime_To_Upd = oTime_To_Max
                sTime_To_Upd = oTime_To_Upd.strftime(sFormat_To_Max)
            else:
                oTime_To_Upd = oTime_To_Test
                sTime_To_Upd = oTime_To_Upd.strftime(sFormat_From_Test)

        else:
            sTime_From_Upd = a1oTime_Test[0]
            sTime_To_Upd = a1oTime_Test[-1]
    else:
        sTime_From_Upd = None
        sTime_To_Upd = None

    return sTime_From_Upd, sTime_To_Upd

# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to find difference between time and a list of times
def findTimeDiff(sTimeCheck, sTimeTest):

    sTimeCheckFormat = defineTimeFormat(sTimeCheck)
    oTimeCheck = datetime.datetime.strptime(sTimeCheck, sTimeCheckFormat)

    sTimeTestFormat = defineTimeFormat(sTimeTest)
    oTimeTest = datetime.datetime.strptime(sTimeTest, sTimeTestFormat)

    # Calculating elapsed time
    if version_info[0] >= 2.7:
        # Python >=2.7
        dDV = (oTimeCheck - oTimeTest).total_seconds()
    else:
        # Python 2.6
        dDV_END = mktime(oTimeTest.timetuple())
        dDV_START = mktime(oTimeCheck.timetuple())
        dDV = dDV_END - dDV_START

    return abs(dDV)
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to compute time delta
def computeTimeDelta(sTimeFrom, sTimeTo, iTimeStep=1):
    iTimeElapsed = findTimeDiff(sTimeFrom, sTimeTo)
    iTimeDelta = iTimeElapsed/iTimeStep
    return iTimeDelta

# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to convert time frequency to seconds
def convertTimeFrequency(sTimeFreq):
    sTimeFreq = sTimeFreq.lower()

    if sTimeFreq in oSecondsUnits.keys():
        iTimeFreq = oSecondsUnits[sTimeFreq]
    else:
        iTimeFreq = None
    return iTimeFreq

# --------------------------------------------------------------------------------
