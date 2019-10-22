"""
Library Features:

Name:          lib_wrf_variables
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190917'
Version:       '1.0.1'
"""

#######################################################################################
# Library
import logging
import warnings

from numpy import sqrt, empty, nan, exp, where

from src.common.default.lib_default_args import sLoggerName
from src.hyde.driver.configuration.generic.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to compute rain field(s)
def computeRain(oVarData_Rain, oVarUnits=None,  oVarType=None, iVarIdxStart=None, iVarIdxEnd=None):

    # Init results
    oVarData_RainIst = None

    # Set variable units and types
    if oVarUnits is None:
        oVarUnits = ['mm']
    if oVarType is None:
        oVarType = ['accumulated']

    # Get variables dimensions
    iVarDim_Rain = oVarData_Rain.ndim

    # Set variable indexes
    if iVarDim_Rain == 3:
        if iVarIdxStart is None:
            iIdxStart = 0
        else:
            iIdxStart = iVarIdxStart
    else:
        iIdxStart = None

    if iVarDim_Rain == 3:
        if iVarIdxEnd is None:
            iIdxEnd = oVarData_Rain.shape[2]
        else:
            iIdxEnd = iVarIdxEnd
    else:
        iIdxEnd = None

    # Check variables types
    if oVarType[0] != 'accumulated':
        Exc.getExc(' ---> Error: Rain allowed only in accumulated format! Check your data!', 1, 1)
    # Check variables units
    if oVarUnits[0] != 'mm' and oVarUnits[0] != 'm':
        Exc.getExc(' ---> Error: Rain units is not allowed! Check your data!', 1, 1)

    # Compute results using 2d or 3d format
    if iVarDim_Rain == 3:

        # Iterate over field(s)
        a3dVarData_Rain = oVarData_Rain[:, :, iIdxStart:iIdxEnd]

        iVarDims = a3dVarData_Rain.shape

        # Compute rain in instantaneous mode and millimeters units
        oVarData_RainIst = empty((iVarDims[0], iVarDims[1], iVarDims[2] - 1))
        oVarData_RainIst[:, :, :] = nan
        for iVarStep in range(1, iVarDims[2]):
            a2dVarData_Rain_PeriodEnd = a3dVarData_Rain[:, :, iVarStep]
            a2dVarData_Rain_PeriodStart = a3dVarData_Rain[:, :, iVarStep - 1]

            a2dVarData_Rain_PeriodIst = a2dVarData_Rain_PeriodEnd - a2dVarData_Rain_PeriodStart

            if oVarUnits[0] == 'm':
                a2dVarData_Rain_PeriodIst = a2dVarData_Rain_PeriodIst / 1000

            oVarData_RainIst[:, :, iVarStep - 1] = a2dVarData_Rain_PeriodIst

    elif iVarDim_Rain == 2:

        # Compute rain in instantaneous mode and millimeters units
        a2dVarData_Rain = oVarData_Rain
        if oVarUnits[0] == 'm':
            a2dVarData_Rain = a2dVarData_Rain / 1000
        oVarData_RainIst = a2dVarData_Rain

    # Results
    return oVarData_RainIst

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute temperature field(s)
def computeAirTemperature(oVarData_T, oVarUnits=None, oVarType=None, iVarIdxStart=None, iVarIdxEnd=None):

    # Init results
    oVarData_TC = None

    # Set variable units and types
    if oVarUnits is None:
        oVarUnits = ['K']
    if oVarType is None:
        oVarType = ['istantaneous']

    # Set variable indexes
    if iVarIdxStart is None:
        iIdxStart = 0
    else:
        iIdxStart = iVarIdxStart

    if iVarIdxEnd is None:
        if hasattr(oVarData_T, '__len__'):
            iIdxEnd = oVarData_T.__len__()
        else:
            iIdxEnd = 0
    else:
        iIdxEnd = iVarIdxEnd

    # Get variables dimensions
    iVarDim_T = oVarData_T.ndim

    # Check variables types
    if oVarType[0] != 'istantaneous':
        Exc.getExc(' ---> Error: Temperature allowed only in istantaneous format! Check your data!', 1, 1)
    # Check variables units
    if oVarUnits[0] != 'K':
        Exc.getExc(' ---> Error: Temperature units is not allowed! Check your data!', 1, 1)

    # Compute results using 2d or 3d format
    if iVarDim_T == 3:

        # Iterate over field(s)
        a3dVarData_T = oVarData_T[:, :, iIdxStart:iIdxEnd]

        iVarDims = a3dVarData_T.shape

        # Compute temperature in C degree
        oVarData_TC = empty((iVarDims[0], iVarDims[1], iVarDims[2]))
        oVarData_TC[:, :, :] = nan
        for iVarStep in range(0, iVarDims[2]):
            a2dVarData_T = a3dVarData_T[:, :, iVarStep]

            a2dVarData_T = a2dVarData_T - 273.15
            oVarData_TC[:, :, iVarStep] = a2dVarData_T

    elif iVarDim_T == 2:

        # Compute temperature in C degree
        oVarData_TC = oVarData_T - 273.15

    # Results
    return oVarData_TC

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute wind speed field(s)
def computeWindSpeed(oVarData_U, oVarData_V, oVarUnits=None, oVarType=None, iVarIdxStart=None, iVarIdxEnd=None):

    # Init results
    oVarData_WindSpeed = None

    # Set variable units and types
    if oVarUnits is None:
        oVarUnits = ['m s-1', 'm s-1']
    if oVarType is None:
        oVarType = ['istantaneous', 'istantaneous']

    if oVarUnits.__len__() == 1:
        oVarUnits = [oVarUnits[0], oVarUnits[0]]

    if oVarType.__len__() == 1:
        oVarType = [oVarType[0], oVarType[0]]

    # Set variable indexes
    if iVarIdxStart is None:
        iIdxStart = 0
    else:
        iIdxStart = iVarIdxStart

    if iVarIdxEnd is None:
        if hasattr(oVarData_U, '__len__') and hasattr(oVarData_U, '__len__'):
            iIdxEnd = oVarData_U.__len__()
        else:
            iIdxEnd = 0
    else:
        iIdxEnd = iVarIdxEnd

    # Get variables dimensions
    iVarDim_U = oVarData_U.ndim
    iVarDim_V = oVarData_V.ndim

    # Check variables types
    if oVarType[0] != 'istantaneous' or oVarType[1] != 'istantaneous':
        Exc.getExc(' ---> Error: WindU and WindV allowed only in istantaneous format! Check your data!', 1, 1)
    # Check variables units
    if oVarUnits[0] != 'm s-1' or oVarUnits[1] != 'm s-1':
        Exc.getExc(' ---> Error: WindU or WindV units are not allowed! Check your data!', 1, 1)
    # Check variables dimensions
    if iVarDim_U != iVarDim_V:
        Exc.getExc(' ---> Error: WindU or WindV dimensions are different! Check your data!', 1, 1)

    # Compute results using 2d or 3d format
    if iVarDim_U == 3 and iVarDim_V == 3:

        # Iterate over field(s)
        a3dVarData_U = oVarData_U[:, :, iIdxStart:iIdxEnd]
        a3dVarData_V = oVarData_V[:, :, iIdxStart:iIdxEnd]

        iVarDims = a3dVarData_U.shape

        # Compute wind speed
        oVarData_WindSpeed = empty((iVarDims[0], iVarDims[1], iVarDims[2]))
        oVarData_WindSpeed[:, :, :] = nan
        for iVarStep in range(0, iVarDims[2]):

            a2dVarData_U = a3dVarData_U[:, :, iVarStep]
            a2dVarData_V = a3dVarData_V[:, :, iVarStep]

            a2dVarData_WindSpeed = sqrt(a2dVarData_U ** 2 + a2dVarData_V ** 2)
            oVarData_WindSpeed[:, :, iVarStep] = a2dVarData_WindSpeed

    elif iVarDim_U == 2 and iVarDim_V == 2:

        # Compute wind speed
        oVarData_WindSpeed = sqrt(oVarData_U ** 2 + oVarData_V ** 2)

    # Results
    return oVarData_WindSpeed
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute incoming radiation field(s)
def computeIncomingRadiation(oVarData_SW, oVarUnits=None, oVarType=None, iVarIdxStart=None, iVarIdxEnd=None):

    # Init results
    oVarData_IncomingRadiation = None

    # Set variable units and types
    if oVarUnits is None:
        oVarUnits = ['W m-2']
    if oVarType is None:
        oVarType = ['istantaneous']

    # Set variable indexes
    if iVarIdxStart is None:
        iIdxStart = 0
    else:
        iIdxStart = iVarIdxStart

    if iVarIdxEnd is None:
        if hasattr(oVarData_SW, '__len__'):
            iIdxEnd = oVarData_SW.__len__()
        else:
            iIdxEnd = 0
    else:
        iIdxEnd = iVarIdxEnd

    # Get variables dimensions
    iVarDim_SW = oVarData_SW.ndim

    # Check variables types
    if oVarType[0] != 'istantaneous':
        Exc.getExc(' ---> Error: ShortWaveRadiation allowed only in istantaneous format! Check your data!', 1, 1)
    # Check variables units
    if oVarUnits[0] != 'W m-2':
        Exc.getExc(' ---> Error: ShortWaveRadiation units is not allowed! Check your data!', 1, 1)

    # Compute results using 2d or 3d format
    if iVarDim_SW == 3:
        # Iterate over field(s)
        a3dVarData_SW = oVarData_SW[:, :, iIdxStart:iIdxEnd]

        iVarDims = a3dVarData_SW.shape

        # Compute incoming radiation
        oVarData_IncomingRadiation = empty((iVarDims[0], iVarDims[1], iVarDims[2]))
        oVarData_IncomingRadiation[:, :, :] = nan
        for iVarStep in range(0, iVarDims[2]):
            a2dVarData_SW = a3dVarData_SW[:, :, iVarStep]
            oVarData_IncomingRadiation[:, :, iVarStep] = a2dVarData_SW

    elif iVarDim_SW == 2:

        # Compute incoming radiation in W m-2
        oVarData_IncomingRadiation = oVarData_SW

    # Results
    return oVarData_IncomingRadiation
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute air pressure field(s)
def computeAirPressure(oVarData_P, oVarUnits=None, oVarType=None, iVarIdxStart=None, iVarIdxEnd=None):

    # Init results
    oVarData_SurfacePressure = None

    # Set variable units and types
    if oVarUnits is None:
        oVarUnits = ['Pa']
    if oVarType is None:
        oVarType = ['istantaneous']

    # Set variable indexes
    if iVarIdxStart is None:
        iIdxStart = 0
    else:
        iIdxStart = iVarIdxStart

    if iVarIdxEnd is None:
        if hasattr(oVarData_P, '__len__'):
            iIdxEnd = oVarData_P.__len__()
        else:
            iIdxEnd = 0
    else:
        iIdxEnd = iVarIdxEnd

    # Get variables dimensions
    iVarDim_P = oVarData_P.ndim

    # Check variables types
    if oVarType[0] != 'istantaneous':
        Exc.getExc(' ---> Error: SurfacePressure allowed only in istantaneous format! Check your data!', 1, 1)
    # Check variables units
    if oVarUnits[0] != 'Pa':
        Exc.getExc(' ---> Error: SurfacePressure units is not allowed! Check your data!', 1, 1)

    # Compute results using 2d or 3d format
    if iVarDim_P == 3:
        # Iterate over field(s)
        a3dVarData_P = oVarData_P[:, :, iIdxStart:iIdxEnd]

        iVarDims = a3dVarData_P.shape

        # Compute surface pressure in kPa
        oVarData_SurfacePressure = empty((iVarDims[0], iVarDims[1], iVarDims[2]))
        oVarData_SurfacePressure[:, :, :] = nan
        for iVarStep in range(0, iVarDims[2]):
            a2dVarData_P = a3dVarData_P[:, :, iVarStep]

            # Convert from Pa to kPa
            a2dVarData_P = a2dVarData_P / 1000
            oVarData_SurfacePressure[:, :, iVarStep] = a2dVarData_P

    elif iVarDim_P == 2:

        # Compute surface pressure in kPa
        oVarData_SurfacePressure = oVarData_P / 1000

    # Results
    return oVarData_SurfacePressure
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute relative humidity field(s)
def computeRelativeHumidity(oVarData_Q, oVarData_T, oVarData_P, oVarUnits=None, oVarType=None,
                            iVarIdxStart=None, iVarIdxEnd=None):

    # Init results
    oVarData_RelativeHumidity = None

    # Set variable units and types
    if oVarUnits is None:
        oVarUnits = ['kg kg-1', 'K', 'Pa']    # Pa (1 kPa equal 1000 Pa)
    if oVarType is None:
        oVarType = ['istantaneous', 'istantaneous', 'istantaneous']
    pass

    if oVarType.__len__() == 1:
        oVarType = [oVarType[0], oVarType[0], oVarType[0]]

    # Set variable indexes
    if iVarIdxStart is None:
        iIdxStart = 0
    else:
        iIdxStart = iVarIdxStart

    if iVarIdxEnd is None:
        if hasattr(oVarData_Q, '__len__') and hasattr(oVarData_T, '__len__') and hasattr(oVarData_P, '__len__'):
            iIdxEnd = oVarData_Q.__len__()
        else:
            iIdxEnd = 0
    else:
        iIdxEnd = iVarIdxEnd

    # Get variables dimensions
    iVarDim_Q = oVarData_Q.ndim
    iVarDim_T = oVarData_T.ndim
    iVarDim_P = oVarData_P.ndim

    # Check variables types
    if oVarType[0] != 'istantaneous' or oVarType[1] != 'istantaneous' or oVarType[2] != 'istantaneous':
        Exc.getExc(' ---> Error: MixingRatio, Temperature or Pressure allowed only in istantaneous format!'
                   ' Check your data!', 1, 1)
    # Check variables units
    if oVarUnits[0] != 'kg kg-1' or oVarUnits[1] != 'K' or oVarUnits[2] != 'Pa':
        Exc.getExc(' ---> Warning: MixingRatio, Temperature or Pressure units are not allowed! Check your data!', 2, 1)
    # Check variables dimensions
    if iVarDim_Q != iVarDim_T or iVarDim_Q != iVarDim_P or iVarDim_T != iVarDim_P:
        Exc.getExc(' ---> Error: MixingRatio, Temperature or Pressure dimensions are different! Check your data!', 1, 1)

    # Compute results using 2d or 3d format
    if iVarDim_Q == 3 and iVarDim_T == 3 and iVarDim_P == 3:

        # Iterate over field(s)
        a3dVarData_Q = oVarData_Q[:, :, iIdxStart:iIdxEnd]
        a3dVarData_T = oVarData_T[:, :, iIdxStart:iIdxEnd]
        a3dVarData_P = oVarData_P[:, :, iIdxStart:iIdxEnd]

        iVarDims = a3dVarData_Q.shape

        # Compute relative humidity
        oVarData_RelativeHumidity = empty((iVarDims[0], iVarDims[1], iVarDims[2]))
        oVarData_RelativeHumidity[:, :, :] = nan
        for iVarStep in range(0, iVarDims[2]):
            a2dVarData_Q = a3dVarData_Q[:, :, iVarStep]
            a2dVarData_T = a3dVarData_T[:, :, iVarStep]
            a2dVarData_P = a3dVarData_P[:, :, iVarStep]

            a2dVarData_T = a2dVarData_T - 273.15
            a2dVarData_P = a2dVarData_P / 1000

            a2dVarData_ES = 0.611 * exp((17.3 * a2dVarData_T) / (a2dVarData_T + 237.3))
            a2dVarData_EA = (a2dVarData_P * a2dVarData_Q) / 0.622
            a2dVarData_RelativeHumidity = (a2dVarData_EA / a2dVarData_ES) * 100

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                a2iVarData_IndexUp = where(a2dVarData_RelativeHumidity > 100)
                a2iVarData_IndexDown = where(a2dVarData_RelativeHumidity < 0)

            a2dVarData_RelativeHumidity[a2iVarData_IndexUp[0], a2iVarData_IndexUp[1]] = 100
            a2dVarData_RelativeHumidity[a2iVarData_IndexDown[0], a2iVarData_IndexDown[1]] = 0

            oVarData_RelativeHumidity[:, :, iVarStep] = a2dVarData_RelativeHumidity

    elif iVarDim_Q == 2 and iVarDim_T == 2 and iVarDim_P == 2:

        # Compute relative humidity
        a2dVarData_T = oVarData_T - 273.15
        a2dVarData_P = oVarData_P / 1000
        a2dVarData_Q = oVarData_Q

        a2dVarData_ES = 0.611 * exp((17.3 * a2dVarData_T) / (a2dVarData_T + 237.3))
        a2dVarData_EA = (a2dVarData_P * a2dVarData_Q) / 0.622
        a2dVarData_RelativeHumidity = (a2dVarData_EA / a2dVarData_ES) * 100

        a2iVarData_IndexUp = where(a2dVarData_RelativeHumidity > 100)
        a2iVarData_IndexDown = where(a2dVarData_RelativeHumidity < 0)

        a2dVarData_RelativeHumidity[a2iVarData_IndexUp[0], a2iVarData_IndexUp[1]] = 100
        a2dVarData_RelativeHumidity[a2iVarData_IndexDown[0], a2iVarData_IndexDown[1]] = 0

        oVarData_RelativeHumidity = a2dVarData_RelativeHumidity

    # Results
    return oVarData_RelativeHumidity

# -------------------------------------------------------------------------------------
