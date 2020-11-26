"""
Library Features:

Name:          lib_ws_ancillary_snow
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180918'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging
import tempfile
import rasterio

from time import sleep
from os.path import join
from numpy import zeros, sqrt, where, cos, sin, pi, \
    power, mean, nanmean, int32, linspace, meshgrid

from src.common.utils.lib_utils_apps_file import deleteFolder
from src.common.utils.lib_utils_apps_process import execProcess
from src.common.utils.lib_utils_op_string import randomString
from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to compute snow predictor(s)
def computeSnowPredictor(sFile_IN, sFile_OUT, sCommandLine_CMP):

    sString_TEMP = randomString()
    sFolder_TEMP = tempfile.mkdtemp()
    sFile_TEMP = join(sFolder_TEMP, sString_TEMP + '.tiff')

    sCommandLine_CMP = sCommandLine_CMP.replace('$FILE_REF', sFile_IN)
    sCommandLine_CMP = sCommandLine_CMP.replace('$FILE_ANCILLARY', sFile_TEMP)

    # Execute command line CMP
    [sStdOut, sStdErr, iStdExit] = execProcess(sCLine=sCommandLine_CMP, sCPath=sFolder_TEMP)
    # Wait 5 seconds for writing data on disk
    sleep(5)

    # Read data TEMP in tiff format and get values
    oData_TEMP = rasterio.open(sFile_TEMP)
    a3dData_TEMP = oData_TEMP.read()
    a2dData_TEMP = a3dData_TEMP[0, :, :]

    # Read data IN in ascii format and get values
    oData_IN = rasterio.open(sFile_IN)
    a3dData_IN = oData_IN.read()
    a2dData_IN = a3dData_IN[0, :, :]

    # Execute command line TRANSLATE from tiff to ascii
    sCommandLine_TRANSLATE = ('gdal_translate -of AAIGrid ' + sFile_TEMP + ' ' + sFile_OUT)
    [sStdOut, sStdErr, iStdExit] = execProcess(sCLine=sCommandLine_TRANSLATE, sCPath=sFolder_TEMP)

    # Read OUT data in ascii format and get values
    oData_OUT = rasterio.open(sFile_OUT)
    a3dData_OUT = oData_OUT.read()
    a2dData_OUT = a3dData_OUT[0, :, :]

    # Remove temporary folder and its content
    deleteFolder(sFolder_TEMP)

    # Debug
    # plt.figure(1)
    # plt.imshow(a2dData_IN); plt.colorbar()
    # plt.figure(2)
    # plt.imshow(a2dData_TEMP); plt.colorbar()
    # plt.figure(3)
    # plt.imshow(a2dData_OUT);plt.colorbar()
    # plt.show()

    return a2dData_OUT

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute snow kernel
def computeSnowKernel(a2dGeoData, a2dGeoX, a2dGeoY, dGeoXCellSize, dGeoYCellSize,
                      a1iXIndex, a1iYIndex, dRadiusInt):

    # -------------------------------------------------------------------------------------
    # Dynamic values (NEW)
    dR = 6378388  # (Radius)
    dE = 0.00672267  # (Ellipsoid)

    # dx = (R * cos(lat)) / (sqrt(1 - e2 * sqr(sin(lat)))) * PI / 180
    a2dDX = (dR * cos(a2dGeoY * pi / 180)) / (
        sqrt(1 - dE * sqrt(sin(a2dGeoY * pi / 180)))) * pi / 180
    # dy = (R * (1 - e2)) / pow((1 - e2 * sqr(sin(lat))),1.5) * PI / 180
    a2dDY = (dR * (1 - dE)) / power((1 - dE * sqrt(sin(a2dGeoY / 180))), 1.5) * pi / 180

    # a2dGeoAreaKm = ((a2dDX/(1/dGeoXCellSize)) * (a2dDY/(1/dGeoYCellSize))) / 1000000 # [km^2]
    a2dGeoAreaM = ((a2dDX / (1 / dGeoXCellSize)) * (a2dDY / (1 / dGeoYCellSize)))  # [m^2]

    # Area, Mean Dx and Dy values (meters)
    # a2dData = a2dGeoAreaM
    dGeoAreaMetersDxMean = sqrt(nanmean(a2dGeoAreaM))
    dGeoAreaMetersDyMean = sqrt(nanmean(a2dGeoAreaM))

    dGeoAreaMetersMean = mean([dGeoAreaMetersDxMean, dGeoAreaMetersDyMean])

    # --------------------------------------------------------------------------------
    # Pixel(s) interpolation
    iPixelInt = int32(dRadiusInt * 1000 / dGeoAreaMetersMean)
    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Compute gridded indexes
    a1iX = linspace(0, a2dGeoData.shape[1], a2dGeoData.shape[1])
    a1iY = linspace(0, a2dGeoData.shape[0], a2dGeoData.shape[0])
    a2iX, a2iY = meshgrid(a1iX, a1iY)
    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Cycle(s) on snow sensor(s)
    a2dW = zeros([a2dGeoData.shape[0], a2dGeoData.shape[1]])
    for iXIdx, iYIdx in zip(a1iXIndex, a1iYIndex):

        # --------------------------------------------------------------------------------
        # Compute distance index matrix
        a2dDistIdx = zeros([a2dGeoData.shape[0], a2dGeoData.shape[1]])
        a2dDistIdx = sqrt((a2iY - iYIdx) ** 2 + (a2iX - iXIdx) ** 2)

        # Weight(s) matrix
        a2iPixelIdx = zeros([a2dGeoData.shape[0], a2dGeoData.shape[1]])
        a2iPixelIdx = where(a2dDistIdx < iPixelInt)
        a2dW[a2iPixelIdx] = a2dW[a2iPixelIdx] + \
                            (iPixelInt ** 2 - a2dDistIdx[a2iPixelIdx] ** 2) / \
                            (iPixelInt ** 2 + a2dDistIdx[a2iPixelIdx] ** 2) / len(a1iXIndex)
        # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Debug
    # plt.figure(1)
    # plt.imshow(a2dW); plt.colorbar();
    # plt.show()
    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Return variable(s)
    return a2dW
    # --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
