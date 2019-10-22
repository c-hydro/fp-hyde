"""
Library Features:

Name:          lib_generic_utils_land
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190312'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging
import numpy as np

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to compute drainage area in m^2
def computeDrainageArea(a2dTerrain, dCellArea, dNoData=-9999, sUnits='km^2'):

    iN = np.where(a2dTerrain.ravel() != dNoData)[0].size
    dDrainageArea = iN * dCellArea

    if sUnits == 'km^2':
        dDrainageArea = dDrainageArea / 1000000
    elif sUnits == 'm^2':
        dDrainageArea = dDrainageArea

    return dDrainageArea

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute cell area taking care pixels latitude
def computeCellArea(a2dGeoY, dGeoXCellSize, dGeoYCellSize):

    # Method constant(s)
    dR = 6378388  # (Radius)
    dE = 0.00672267  # (Ellipsoid)

    # dx = (R * cos(lat)) / (sqrt(1 - e2 * sqr(sin(lat)))) * PI / 180
    a2dDX = (dR * np.cos(a2dGeoY * np.pi / 180)) \
            / (np.sqrt(1 - dE * np.sqrt(np.sin(a2dGeoY * np.pi / 180)))) * np.pi / 180
    # dy = (R * (1 - e2)) / pow((1 - e2 * sqr(sin(lat))),1.5) * PI / 180
    a2dDY = (dR * (1 - dE)) / np.power((1 - dE * np.sqrt(np.sin(a2dGeoY / 180))), 1.5) * np.pi / 180

    # Compute cell area in m^2
    a2dVarCAREA = ((a2dDX / (1 / dGeoXCellSize)) * (a2dDY / (1 / dGeoYCellSize)))  # [m^2]

    return a2dVarCAREA

# -------------------------------------------------------------------------------------
