"""
Library Features:

Name:          lib_time
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190213'
Version:       '2.0.8'
"""

#######################################################################################
# Library
import logging

import numpy as np

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# --------------------------------------------------------------------------------
# Method to define corrivation time
def computeTimeCorrivation(a2dGeoZ, a2dGeoY, dGeoXCSize, dGeoYCSize):

    # -------------------------------------------------------------------------------------
    # Dynamic values
    dR = 6378388  # (Radius)
    dE = 0.00672267  # (Ellipsoid)

    # dx = (R * cos(lat)) / (sqrt(1 - e2 * sqr(sin(lat)))) * PI / 180
    a2dDX = (dR * np.cos(a2dGeoY * np.pi / 180)) / (np.sqrt(1 - dE * np.sqrt(np.sin(a2dGeoY * np.pi / 180)))) * np.pi / 180
    # dy = (R * (1 - e2)) / pow((1 - e2 * sqr(sin(lat))),1.5) * PI / 180
    a2dDY = (dR * (1 - dE)) / np.power((1 - dE * np.sqrt(np.sin(a2dGeoY / 180))), 1.5) * np.pi / 180

    # a2dGeoAreaKm = ((a2dDX / (1 / dGeoXCSize)) * (a2dDY / (1 / dGeoYCSize))) / 1000000  # [km^2]
    a2dGeoAreaM = ((a2dDX / (1 / dGeoXCSize)) * (a2dDY / (1 / dGeoYCSize)))  # [m^2]

    # Area, Mean Dx and Dy values (meters)
    dGeoDxMean = np.sqrt(np.nanmean(a2dGeoAreaM))
    dGeoDyMean = np.sqrt(np.nanmean(a2dGeoAreaM))

    # Compute domain pixels and area
    iGeoPixels = np.sum(np.isfinite(a2dGeoZ))
    dGeoArea = float(iGeoPixels) * dGeoDxMean * dGeoDyMean / 1000000

    # Debug
    # plt.figure(1)
    # plt.imshow(a2dGeoZ); plt.colorbar()
    # plt.show()

    # Concentration time [hour]
    iGeoTc = np.int(0.27 * np.sqrt(0.6 * dGeoArea) + 0.25)

    return iGeoTc

    # -------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
