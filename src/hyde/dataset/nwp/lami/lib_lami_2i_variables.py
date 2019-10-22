"""
Library Features:

Name:          lib_lami_2i_variables
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20181210'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging
from numpy import sqrt, empty, nan, where, zeros, min

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

    # Conversion of data unit (from kg m**-2 to mm)
    if oVarUnits[0] == 'kg m**-2':
        oVarUnits[0] = 'mm'

    # Set variable units and types
    if oVarUnits is None:
        oVarUnits = ['mm']
    if oVarType is None:
        oVarType = ['accumulated']

    # Get variables dimensions
    iVarDim_Rain = oVarData_Rain.ndim

    # Check variables types
    if oVarType[0] != 'accumulated':
        Exc.getExc(' ---> Error: Rain allowed only in accumulated format! Check your data!', 1, 1)
    # Check variables units
    if oVarUnits[0] != 'mm' and oVarUnits[0] != 'm':
        Exc.getExc(' ---> Error: Rain units is not allowed! Check your data!', 1, 1)

    # Compute results using 2d or 3d format
    if iVarDim_Rain == 3:

        # Set variable indexes
        if iVarIdxStart is None:
            iIdxStart = 0
        else:
            iIdxStart = iVarIdxStart

        if iVarIdxEnd is None:
            iIdxEnd = oVarData_Rain.shape[2]
        else:
            iIdxEnd = iVarIdxEnd + 1

        # Iterate over field(s)
        a3dVarData_Rain = oVarData_Rain[:, :, iIdxStart:iIdxEnd]

        # Initialize dims
        iVarDims = a3dVarData_Rain.shape

        # Compute rain in accumulated mode and millimeters units
        oVarData_RainIst = empty((iVarDims[0], iVarDims[1], iVarDims[2]))
        oVarData_RainIst[:, :, :] = nan
        for iVarStep in range(0, iVarDims[2]):
            a2dVarData_Rain = a3dVarData_Rain[:, :, iVarStep]

            if oVarUnits[0] == 'm':
                a2dVarData_Rain = a2dVarData_Rain / 1000

            oVarData_RainIst[:, :, iVarStep] = a2dVarData_Rain

    elif iVarDim_Rain == 2:

        # Compute rain in accumulated mode and millimeters units
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

        # Set variable indexes
        if iVarIdxStart is None:
            iIdxStart = 0
        else:
            iIdxStart = iVarIdxStart

        if iVarIdxEnd is None:
            iIdxEnd = oVarData_T.shape[2]
        else:
            iIdxEnd = iVarIdxEnd + 1

        # Iterate over field(s)
        a3dVarData_T = oVarData_T[:, :, iIdxStart:iIdxEnd]

        # Initialize dims
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

    if oVarUnits.__len__() == 1:
        oVarUnits = [oVarUnits[0], oVarUnits[0]]

    if oVarUnits[0] == 'm s**-1':
        oVarUnits[0] = 'm s-1'
    if oVarUnits[1] == 'm s**-1':
        oVarUnits[1] = 'm s-1'

    if oVarType is None:
        oVarType = ['istantaneous', 'istantaneous']

    if oVarUnits.__len__() == 1:
        oVarUnits = [oVarUnits[0], oVarUnits[0]]

    if oVarType.__len__() == 1:
        oVarType = [oVarType[0], oVarType[0]]

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

        # Set variable indexes
        if iVarIdxStart is None:
            iIdxStart_U = 0
            iIdxStart_V = 0
        else:
            iIdxStart_U = iVarIdxStart
            iIdxStart_V = iVarIdxStart

        if iVarIdxEnd is None:
            iIdxEnd_U = oVarData_U.shape[2]
            iIdxEnd_V = oVarData_V.shape[2]
        else:
            iIdxEnd_U = iVarIdxEnd + 1
            iIdxEnd_V = iVarIdxEnd + 1

        # Iterate over field(s)
        a3dVarData_U = oVarData_U[:, :, iIdxStart_U:iIdxEnd_U]
        a3dVarData_V = oVarData_V[:, :, iIdxStart_V:iIdxEnd_V]

        # Initialize dims
        iVarDims_U = a3dVarData_U.shape
        iVarDims_V = a3dVarData_V.shape
        try:
            assert iVarDims_U == iVarDims_V
            iVarDims = iVarDims_U
        except BaseException:
            Exc.getExc(' ---> Warning: WindU and WindV have different dimensions!!', 2, 1)
            iVarDims = min(iVarDims_U, iVarDims_V)

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
# Method to compute surface albedo field(s)
def computeSurfaceAlbedo(oVarData_ALB, oVarUnits=None, oVarType=None,
                             iVarIdxStart=None, iVarIdxEnd=None):

    # Init results
    oVarData_SurfaceAlbedo = None

    # Set variable units and types
    if oVarUnits is None:
        oVarUnits = ['%']
    if oVarType is None:
        oVarType = ['istantaneous']

    # Get variables dimensions
    iVarDim_ALB = oVarData_ALB.ndim

    # Check variables types
    if oVarType[0] != 'istantaneous':
        Exc.getExc(' ---> Error: SurfaceAlbedo allowed only in istantaneous format! Check your data!', 1, 1)
    # Check variables units
    if oVarUnits[0] != '%':
        Exc.getExc(' ---> Error: SurfaceAlbedo units is not allowed! Check your data!', 1, 1)

    # Compute results using 2d or 3d format
    if iVarDim_ALB == 3:

        # Set variable indexes
        if iVarIdxStart is None:
            iIdxStart = 0
        else:
            iIdxStart = iVarIdxStart

        if iVarIdxEnd is None:
            iIdxEnd = oVarData_ALB.shape[2]
        else:
            iIdxEnd = iVarIdxEnd + 1

        # Iterate over field(s)
        a3dVarData_ALB = oVarData_ALB[:, :, iIdxStart:iIdxEnd]

        # Initialize dims
        iVarDims = a3dVarData_ALB.shape

        # Compute incoming radiation
        oVarData_SurfaceAlbedo = empty((iVarDims[0], iVarDims[1], iVarDims[2]))
        oVarData_SurfaceAlbedo[:, :, :] = nan

        for iVarStep in range(0, iVarDims[2]):
            a2dVarData_ALB = a3dVarData_ALB[:, :, iVarStep]
            oVarData_SurfaceAlbedo[:, :, iVarStep] = a2dVarData_ALB / 100

    elif iVarDim_ALB == 2:

        # Compute surface albedo in [-]
        oVarData_SurfaceAlbedo = oVarData_ALB / 100

    # Results
    return oVarData_SurfaceAlbedo
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute incoming radiation field(s)
def computeIncomingRadiation(oVarData_SW, oVarUnits=None, oVarType=None,
                             iVarIdxStart=None, iVarIdxEnd=None):

    # Init results
    oVarData_IncomingRadiation = None

    # Set variable units and types
    if oVarUnits is None:
        oVarUnits = ['W m-2']
    if oVarType is None:
        oVarType = ['average']

    # Get variables dimensions
    iVarDim_SW = oVarData_SW.ndim

    # Check variables types
    if oVarType[0] != 'istantaneous' and oVarType[0] != 'average':
        Exc.getExc(' ---> Error: ShortWaveRadiation allowed only in istantaneous or average format! Check your data!',
                   1, 1)
    # Check variables units
    if oVarUnits[0] != 'W m-2' and oVarUnits[0] != 'W m**-2':
        Exc.getExc(' ---> Error: ShortWaveRadiation units is not allowed! Check your data!', 1, 1)

    # Compute results using 2d or 3d format
    if iVarDim_SW == 3:

        # Set variable indexes
        if iVarIdxStart is None:
            iIdxStart = 0
        else:
            iIdxStart = iVarIdxStart

        if iVarIdxEnd is None:
            iIdxEnd = oVarData_SW.shape[2]
        else:
            iIdxEnd = iVarIdxEnd + 1

        # Iterate over field(s)
        a3dVarData_SW = oVarData_SW[:, :, iIdxStart:iIdxEnd]

        # Initialize dims
        iVarDims = a3dVarData_SW.shape

        # Compute incoming radiation
        oVarData_IncomingRadiation = empty((iVarDims[0], iVarDims[1], iVarDims[2]))
        oVarData_IncomingRadiation[:, :, :] = nan

        if oVarType[0] == 'istantaneous':

            for iVarStep in range(0, iVarDims[2]):
                a2dVarData_SW = a3dVarData_SW[:, :, iVarStep]
                oVarData_IncomingRadiation[:, :, iVarStep] = a2dVarData_SW

        elif oVarType[0] == 'average':

            # Rule to compute average:
            # VarMean_xhour_n = n(VarMean_nxhour_n) - VarMean_xhour_n-1
            a2dVarData_SW_SUM = zeros([iVarDims[0], iVarDims[1]])
            for iVarStep in range(0, iVarDims[2]):

                a2dVarData_SW_AVG = a3dVarData_SW[:, :, iVarStep]

                a2dVarData_SW_IST = iVarStep * a2dVarData_SW_AVG - a2dVarData_SW_SUM
                a2dVarData_SW_SUM = a2dVarData_SW_SUM + a2dVarData_SW_IST

                a2dVarData_SW_IST[a2dVarData_SW_IST < 0.0] = 0.0

                oVarData_IncomingRadiation[:, :, iVarStep] = a2dVarData_SW_IST

    elif iVarDim_SW == 2:

        # Compute incoming radiation in W m^2
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

        # Set variable indexes
        if iVarIdxStart is None:
            iIdxStart = 0
        else:
            iIdxStart = iVarIdxStart

        if iVarIdxEnd is None:
            iIdxEnd = oVarData_P.shape[2]
        else:
            iIdxEnd = iVarIdxEnd + 1

        # Iterate over field(s)
        a3dVarData_P = oVarData_P[:, :, iIdxStart:iIdxEnd]

        # Initialize dims
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
def computeRelativeHumidity(oVarData_RH, oVarUnits=None, oVarType=None,
                            iVarIdxStart=None, iVarIdxEnd=None):

    # Init results
    oVarData_RelativeHumidity = None

    # Set variable units and types
    if oVarUnits is None:
        oVarUnits = ['%']
    if oVarType is None:
        oVarType = ['istantaneous']
    pass

    # Get variables dimensions
    iVarDim_RH = oVarData_RH.ndim

    # Check variables types
    if oVarType[0] != 'istantaneous':
        Exc.getExc(' ---> Error: Relative humidity allowed only in istantaneous format! Check your data!', 1, 1)
    # Check variables units
    if oVarUnits[0] != '%':
        Exc.getExc(' ---> Warning: Relative humidity units are not allowed! Check your data!', 2, 1)

    # Compute results using 2d or 3d format
    if iVarDim_RH == 3:

        # Set variable indexes
        if iVarIdxStart is None:
            iIdxStart = 0
        else:
            iIdxStart = iVarIdxStart

        if iVarIdxEnd is None:
            iIdxEnd = oVarData_RH.shape[2]
        else:
            iIdxEnd = iVarIdxEnd + 1

        # Iterate over field(s)
        a3dVarData_RH = oVarData_RH[:, :, iIdxStart:iIdxEnd]

        # Initialize dims
        iVarDims = a3dVarData_RH.shape

        # Compute relative humidity
        oVarData_RelativeHumidity = empty((iVarDims[0], iVarDims[1], iVarDims[2]))
        oVarData_RelativeHumidity[:, :, :] = nan
        for iVarStep in range(0, iVarDims[2]):
            a2dVarData_RH = a3dVarData_RH[:, :, iVarStep]

            a2iVarData_IndexUp = where(a2dVarData_RH > 100)
            a2iVarData_IndexDown = where(a2dVarData_RH < 0)

            a2dVarData_RH[a2iVarData_IndexUp[0], a2iVarData_IndexUp[1]] = 100
            a2dVarData_RH[a2iVarData_IndexDown[0], a2iVarData_IndexDown[1]] = 0

            oVarData_RelativeHumidity[:, :, iVarStep] = a2dVarData_RH

    elif iVarDim_RH == 2:

        # Compute relative humidity
        a2dVarData_RH = oVarData_RH

        a2iVarData_IndexUp = where(a2dVarData_RH > 100)
        a2iVarData_IndexDown = where(a2dVarData_RH < 0)

        a2dVarData_RH[a2iVarData_IndexUp[0], a2iVarData_IndexUp[1]] = 100
        a2dVarData_RH[a2iVarData_IndexDown[0], a2iVarData_IndexDown[1]] = 0

        oVarData_RelativeHumidity = a2dVarData_RH

    # Results
    return oVarData_RelativeHumidity

# -------------------------------------------------------------------------------------
