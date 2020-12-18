"""
Library Features:

Name:          lib_ws_variables
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180918'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging
from numpy import argsort, polyfit, polyval, isnan, mean, delete, zeros, ones, any, argwhere, concatenate
from numpy.linalg import lstsq

from src.common.analysis.lib_analysis_interpolation_point import interpPointData
from src.common.analysis.lib_analysis_regression_stepwisefit import stepwisefit

from src.hyde.dataset.ground_network.ws.lib_ws_ancillary_snow import computeSnowKernel

from src.common.utils.lib_utils_apps_geo import findGeoIndex, Deg2Km

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to compute rain field(s)
def computeRain(a1dVarData, a1dVarGeoX, a1dVarGeoY,
                a2dDomainGeoX, a2dDomainGeoY,
                sVarUnits='mm', dVarMissValue=-9999.0, dVarFillValue=-9999.0,
                dInterpNodata=-9999.0,
                sInterpMethod='idw', dInterpRadiusX=None, dInterpRadiusY=None):

    # Init results
    a2dVarData_INTERP = None

    # Set variable units and types
    if sVarUnits is None:
        Exc.getExc(' =====> WARNING: rain units are not set! Default units are [mm]', 2, 1)
        sVarUnits = 'mm'
    # Check variables units
    if sVarUnits != 'mm':
        Exc.getExc(' =====> WARNING: rain units is not correct!'
                   ' Units used: [' + sVarUnits + '] - Units expected: [mm]. Check your data!', 2, 1)

    # Get variables dimensions
    iVarDim = a1dVarData.ndim

    # Compute results using 1d format
    if iVarDim == 1:

        # Interpolate point(s) data to grid
        a2dVarData_INTERP = interpPointData(a1dVarData,
                                            a1dVarGeoX, a1dVarGeoY,
                                            a2dDomainGeoX, a2dDomainGeoY,
                                            dInterpNoData=dInterpNodata,
                                            sInterpMethod=sInterpMethod,
                                            dInterpRadiusX=dInterpRadiusX,
                                            dInterpRadiusY=dInterpRadiusY)
        # Check NAN value
        a2dVarData_INTERP[isnan(a2dVarData_INTERP)] = dVarMissValue
    else:
        # Error for unexpected data dimension(s)
        Exc.getExc(' =====> ERROR: rain data dimension(s) unexpected! Check your data!', 1, 1)

    # Results
    return a2dVarData_INTERP

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute temperature field(s)
def computeAirTemperature(a1dVarData, a1dVarGeoX, a1dVarGeoY, a1dVarGeoZ,
                          a2dDomainGeoX, a2dDomainGeoY, a2dDomainGeoZ,
                          sVarUnits='C', dVarMissValue=-9999.0, dVarFillValue=-9999.0,
                          dInterpNodata=-9999.0,
                          sInterpMethod='idw', dInterpRadiusX=None, dInterpRadiusY=None):

    # Init results
    a2dVarData_INTERP = None

    # Set variable units and types
    if sVarUnits is None:
        Exc.getExc(' =====> WARNING: air temperature units are not set! Default units are [C]', 2, 1)
        sVarUnits = 'C'
    # Check variables units
    if sVarUnits != 'C':
        Exc.getExc(' =====> WARNING: air temperature units is not correct!'
                   ' Units used: [' + sVarUnits + '] - Units expected: [C]. Check your data!', 2, 1)

    # Get variables dimensions
    iVarDim = a1dVarData.ndim

    # Compute results 1d format
    if iVarDim == 1:

        # Sort altitude(s)
        a1iIndexGeoZ_SORT = argsort(a1dVarGeoZ)

        # Extract sorting value(s) from finite arrays
        a1dVarGeoX_SORT = a1dVarGeoX[a1iIndexGeoZ_SORT]
        a1dVarGeoY_SORT = a1dVarGeoY[a1iIndexGeoZ_SORT]
        a1dVarGeoZ_SORT = a1dVarGeoZ[a1iIndexGeoZ_SORT]
        a1dVarData_SORT = a1dVarData[a1iIndexGeoZ_SORT]

        # Polyfit parameters and value(s) (--> linear regression)
        a1dPolyParams = polyfit(a1dVarGeoZ_SORT, a1dVarData_SORT, 1)
        a1dPolyValues = polyval(a1dPolyParams, a1dVarGeoZ_SORT)

        # Define residual for point value(s)
        a1dVarData_RES = a1dVarData_SORT - a1dPolyValues

        # Interpolate point(s) data to grid
        a2dVarData_INTERP = interpPointData(a1dVarData_RES,
                                            a1dVarGeoX_SORT, a1dVarGeoY_SORT,
                                            a2dDomainGeoX, a2dDomainGeoY,
                                            dInterpNoData=dInterpNodata,
                                            sInterpMethod=sInterpMethod,
                                            dInterpRadiusX=dInterpRadiusX,
                                            dInterpRadiusY=dInterpRadiusY)

        # Interpolate polynomial parameters on z map
        a2dDomainPolyZ = polyval(a1dPolyParams, a2dDomainGeoZ)

        # Calculate temperature (using z regression and idw method(s))
        a2dVarData_INTERP = a2dDomainPolyZ + a2dVarData_INTERP

        # Check NAN value
        a2dVarData_INTERP[isnan(a2dVarData_INTERP)] = dVarMissValue

    else:
        # Error for unexpected data dimension(s)
        Exc.getExc(' =====> ERROR: air temperature data dimension(s) unexpected! Check your data!', 1, 1)

    # Results
    return a2dVarData_INTERP

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute wind speed field(s)
def computeWindSpeed(a1dVarData, a1dVarGeoX, a1dVarGeoY,
                     a2dDomainGeoX, a2dDomainGeoY,
                     sVarUnits='m s-1', dVarMissValue=-9999.0, dVarFillValue=-9999.0,
                     dInterpNodata=-9999.0,
                     sInterpMethod='idw', dInterpRadiusX=None, dInterpRadiusY=None):

    # Init results
    a2dVarData_INTERP = None

    # Set variable units and types
    if sVarUnits is None:
        Exc.getExc(' =====> WARNING: wind speed units are not set! Default units are [m s-1]', 2, 1)
        sVarUnits = 'm s-1'
    # Check variables units
    if sVarUnits != 'm s-1':
        Exc.getExc(' =====> WARNING: wind speed units is not correct!'
                   ' Units used: [' + sVarUnits + '] - Units expected: [m s-1]. Check your data!', 2, 1)

    # Get variables dimensions
    iVarDim = a1dVarData.ndim

    # Compute results using 1d format
    if iVarDim == 1:

        # Interpolate point(s) data to grid
        a2dVarData_INTERP = interpPointData(a1dVarData,
                                            a1dVarGeoX, a1dVarGeoY,
                                            a2dDomainGeoX, a2dDomainGeoY,
                                            dInterpNoData=dInterpNodata,
                                            sInterpMethod=sInterpMethod,
                                            dInterpRadiusX=dInterpRadiusX,
                                            dInterpRadiusY=dInterpRadiusY)
        # Check NAN value
        a2dVarData_INTERP[isnan(a2dVarData_INTERP)] = dVarMissValue
    else:
        # Error for unexpected data dimension(s)
        Exc.getExc(' =====> ERROR: wind speed data dimension(s) unexpected! Check your data!', 1, 1)

    # Results
    return a2dVarData_INTERP
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute incoming radiation field(s)
def computeIncomingRadiation(a1dVarData, a1dVarGeoX, a1dVarGeoY,
                             a2dDomainGeoX, a2dDomainGeoY,
                             sVarUnits='W m-2', dVarMissValue=-9999.0, dVarFillValue=-9999.0,
                             dInterpNodata=-9999.0,
                             sInterpMethod='idw', dInterpRadiusX=None, dInterpRadiusY=None):

    # Init results
    a2dVarData_INTERP = None

    # Set variable units and types
    if sVarUnits is None:
        Exc.getExc(' =====> WARNING: incoming radiation units are not set! Default units are [W m-2]', 2, 1)
        sVarUnits = 'W m-2'
    # Check variables units
    if sVarUnits != 'W m-2':
        Exc.getExc(' =====> WARNING: incoming radiation units is not correct!'
                   ' Units used: [' + sVarUnits + '] - Units expected: [W m-2]. Check your data!', 2, 1)

    # Get variables dimensions
    iVarDim = a1dVarData.ndim

    # Compute results using 1d format
    if iVarDim == 1:

        # Interpolate point(s) data to grid
        a2dVarData_INTERP = interpPointData(a1dVarData,
                                            a1dVarGeoX, a1dVarGeoY,
                                            a2dDomainGeoX, a2dDomainGeoY,
                                            dInterpNoData=dInterpNodata,
                                            sInterpMethod=sInterpMethod,
                                            dInterpRadiusX=dInterpRadiusX,
                                            dInterpRadiusY=dInterpRadiusY)
        # Check NAN value
        a2dVarData_INTERP[isnan(a2dVarData_INTERP)] = dVarMissValue
    else:
        # Error for unexpected data dimension(s)
        Exc.getExc(' =====> ERROR: incoming radiation data dimension(s) unexpected! Check your data!', 1, 1)

    # Results
    return a2dVarData_INTERP
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute air pressure field(s)
def computeAirPressure(a1dVarData, a1dVarGeoX, a1dVarGeoY,
                       a2dDomainGeoX, a2dDomainGeoY,
                       sVarUnits='hPa', dVarMissValue=-9999.0, dVarFillValue=-9999.0,
                       dInterpNodata=-9999.0,
                       sInterpMethod='idw', dInterpRadiusX=None, dInterpRadiusY=None):

    # Init results
    a2dVarData_INTERP = None

    # Set variable units and types
    if sVarUnits is None:
        Exc.getExc(' =====> WARNING: air pressure units are not set! Default units are [hPa]', 2, 1)
        sVarUnits = 'hPa'
    # Check variables units
    if sVarUnits != 'hPa':
        Exc.getExc(' =====> WARNING: air pressure units is not correct!'
                   ' Units used: [' + sVarUnits + '] - Units expected: [hPa]. Check your data!', 2, 1)

    # Get variables dimensions
    iVarDim = a1dVarData.ndim

    # Compute results using 1d format
    if iVarDim == 1:

        # Interpolate point(s) data to grid
        a2dVarData_INTERP = interpPointData(a1dVarData,
                                            a1dVarGeoX, a1dVarGeoY,
                                            a2dDomainGeoX, a2dDomainGeoY,
                                            dInterpNoData=dInterpNodata,
                                            sInterpMethod=sInterpMethod,
                                            dInterpRadiusX=dInterpRadiusX,
                                            dInterpRadiusY=dInterpRadiusY)
        # Check NAN value
        a2dVarData_INTERP[isnan(a2dVarData_INTERP)] = dVarMissValue
    else:
        # Error for unexpected data dimension(s)
        Exc.getExc(' =====> ERROR: air pressure data dimension(s) unexpected! Check your data!', 1, 1)

    # Results
    return a2dVarData_INTERP
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute snow height field(s)
def computeSnowHeight(a1dVarData, a1dVarGeoX, a1dVarGeoY,
                      a2dDomainGeoX, a2dDomainGeoY, a2dDomainGeoZ,
                      dDomainGeoCellSizeX, dDomainGeoCellSizeY,
                      oAncillaryData=None,
                      sVarUnits='cm', dVarMissValue=-9999.0, dVarFillValue=-9999.0,
                      dInterpNodata=-9999.0,
                      sInterpMethod='idw',
                      dInterpRadiusX=None, dInterpRadiusY=None, dInterRadiusInfluence=None):
    # --------------------------------------------------------------------------------
    # Init results
    a2dVarData_INTERP = None

    # Set variable units and types
    if sVarUnits is None:
        Exc.getExc(' =====> WARNING: snow height units are not set! Default units are [cm]', 2, 1)
        sVarUnits = 'cm'
    # Check variables units
    if sVarUnits != 'cm':
        Exc.getExc(' =====> WARNING: snow height units is not correct!'
                   ' Units used: [' + sVarUnits + '] - Units expected: [cm]. Check your data!', 2, 1)

    # Get variables dimensions
    iVarDim = a1dVarData.ndim
    # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Compute results using 1d format
    if iVarDim == 1:

        # --------------------------------------------------------------------------------
        # Convert influence radius from degree to meters
        dInterRadiusInfluence = float(int(Deg2Km(dInterRadiusInfluence) * 1000))

        # Control geo cellsize x and y
        if dDomainGeoCellSizeX == dDomainGeoCellSizeY:
            dGeoCellSize = dDomainGeoCellSizeX
        else:
            dGeoCellSize = mean(dDomainGeoCellSizeX, dDomainGeoCellSizeY)
            Exc.getExc(' =====> WARNING: cellsize x and y are different! Select average value.', 2, 1)

        # Find reference indexes for data x,y position(s)
        a1iIndexX, a1iIndexY = findGeoIndex(a2dDomainGeoX, a2dDomainGeoY, a1dVarGeoX, a1dVarGeoY, dGeoCellSize)
        # --------------------------------------------------------------------------------

        # --------------------------------------------------------------------------------
        # Get domain X, Y and Z (altitude)
        a1dDomainGeoX = a2dDomainGeoX[a1iIndexX, a1iIndexY]
        a1dDomainGeoY = a2dDomainGeoY[a1iIndexX, a1iIndexY]
        a1dDomainGeoZ = a2dDomainGeoZ[a1iIndexX, a1iIndexY]

        a1iDomainIdxNaN = argwhere(isnan(a1dDomainGeoZ)).ravel()
        # --------------------------------------------------------------------------------

        # --------------------------------------------------------------------------------
        # Update domain values excluded nan values
        a1dDomainGeoX = delete(a1dDomainGeoX, a1iDomainIdxNaN)
        a1dDomainGeoY = delete(a1dDomainGeoY, a1iDomainIdxNaN)
        a1dDomainGeoZ = delete(a1dDomainGeoZ, a1iDomainIdxNaN)
        # Update var values excluded nan values (from domain data)
        a1dVarData = delete(a1dVarData, a1iDomainIdxNaN)
        a1dVarGeoX = delete(a1dVarGeoX, a1iDomainIdxNaN)
        a1dVarGeoY = delete(a1dVarGeoY, a1iDomainIdxNaN)
        # --------------------------------------------------------------------------------

        # --------------------------------------------------------------------------------
        # Iterate over data predictor(s)
        a2dDomainPred = zeros([a1dDomainGeoZ.shape[0], oAncillaryData.__len__()])
        a2dDomainPred[:, :] = -9999.0
        a3dDomainPred = zeros(shape=[a2dDomainGeoX.shape[0], a2dDomainGeoY.shape[1], oAncillaryData.__len__()])
        for iPredID, (sPredName, a2dPredData) in enumerate(oAncillaryData.items()):

            # Get predictor data
            a1dDomainPred = a2dPredData[a1iIndexX, a1iIndexY]
            a1dDomainPred = delete(a1dDomainPred, a1iDomainIdxNaN)

            # Store predictor data
            a2dDomainPred[:, iPredID] = a1dDomainPred
            a3dDomainPred[:, :, iPredID] = a2dPredData
        # --------------------------------------------------------------------------------

        # Debug (to evaluate regression)
        # a1dVarData = [110, 100, 80, 120, 190, 126, 100, 102]

        # --------------------------------------------------------------------------------
        # Fit Data using stepwise function
        [a1dB, a1dSe, a1dPVal, a1bInModel, oStats, iNextStep, oHistory] = stepwisefit(
            a2dDomainPred, a1dVarData, [], 0.1)

        # Check variable X predictor(s) availability
        a1oInModel = a1bInModel.tolist()
        if any(a1oInModel):

            a1iModelIdxFalse = [iIdx for iIdx, bVx in enumerate(a1oInModel) if not bVx]
            a2dDomainPred = delete(a2dDomainPred, a1iModelIdxFalse, axis=1)
            a3dDomainPred = delete(a3dDomainPred, a1iModelIdxFalse, axis=2)

        elif not any(a1oInModel):

            a2dDomainPred = zeros(shape=[a1dDomainGeoZ.shape[0], 1])
            a3dDomainPred = zeros(shape=[a2dDomainGeoX.shape[0], a2dDomainGeoY.shape[1], 1])
            a2dDomainPred[:, 0] = a1dDomainGeoZ
            a3dDomainPred[:, :, 0] = a2dDomainGeoZ
        # --------------------------------------------------------------------------------

        # --------------------------------------------------------------------------------
        # Multivariate linear regression
        a2dVarA = concatenate((a2dDomainPred, ones([a2dDomainPred.__len__(), 1])), axis=1)
        a1dVarCoeff = lstsq(a2dVarA, a1dVarData, rcond=None)[0]
        # --------------------------------------------------------------------------------

        # --------------------------------------------------------------------------------
        # Define basemap
        a2dVarMap = ones([a2dDomainGeoX.shape[0], a2dDomainGeoY.shape[1]])
        a2dVarMap[:, :] = a1dVarCoeff[-1]

        a1dVarCoeff = a1dVarCoeff[:-1]
        for iPredID, dVarCoeff in enumerate(a1dVarCoeff):
            a2dVarMap = a2dVarMap + a3dDomainPred[:, :, iPredID] * dVarCoeff

        # Filter data to avoid nan(s) and negative value(s)
        a2dVarMap[isnan(a2dVarMap)] = -1
        a2dVarMap[a2dVarMap < 0] = 0

        a1dVarMap = a2dVarMap[[a1iIndexX, a1iIndexY]]
        a1dVarMap = delete(a1dVarMap, a1iDomainIdxNaN)
        # --------------------------------------------------------------------------------

        # --------------------------------------------------------------------------------
        # Compute and interpolate residual
        a1dVarRes = a1dVarMap - a1dVarData

        a2dVarRes_INTERP = interpPointData(a1dVarRes,
                                            a1dVarGeoX, a1dVarGeoY,
                                            a2dDomainGeoX, a2dDomainGeoY,
                                            dInterpNoData=dInterpNodata,
                                            sInterpMethod=sInterpMethod,
                                            dInterpRadiusX=dInterpRadiusX,
                                            dInterpRadiusY=dInterpRadiusY)

        # Variable estimantion (snow in cm)
        a2dVarData_INTERP = a2dVarMap + a2dVarRes_INTERP
        # Check for undefined data
        a2dVarData_INTERP[a2dVarData_INTERP < 1.0] = dVarFillValue
        # Check for NAN value
        a2dVarData_INTERP[isnan(a2dVarData_INTERP)] = dVarMissValue
        # --------------------------------------------------------------------------------

        # --------------------------------------------------------------------------------
        # Compute weight data (or kernel data)
        a2dVarW = computeSnowKernel(a2dDomainGeoZ, a2dDomainGeoX, a2dDomainGeoY,
                                    dDomainGeoCellSizeX, dDomainGeoCellSizeY,
                                    a1iIndexX, a1iIndexY, dInterRadiusInfluence)
        # --------------------------------------------------------------------------------

        # --------------------------------------------------------------------------------
        # Check NAN value(s)
        a2dVarData_INTERP[isnan(a2dVarData_INTERP)] = dVarMissValue
        a2dVarW[isnan(a2dVarW)] = dVarMissValue
        # Check domain value(s)
        a2dVarData_INTERP[isnan(a2dDomainGeoZ)] = dVarMissValue
        a2dVarW[isnan(a2dDomainGeoZ)] = dVarMissValue
        # --------------------------------------------------------------------------------

        # --------------------------------------------------------------------------------
        # Debug
        # plt.figure(1)
        # plt.imshow(a2dVarMap); plt.colorbar();plt.clim(0, 270)
        # plt.figure(2)
        # plt.imshow(a2dVarRes_INTERP); plt.colorbar();
        # plt.figure(3)
        # plt.imshow(a2dVarData_INTERP); plt.colorbar(); plt.clim(0, 270)
        # plt.figure(4)
        # plt.imshow(a2dVarW); plt.colorbar(); plt.clim(0, 1)
        # plt.figure(5)
        # plt.imshow(a2dDomainGeoZ); plt.colorbar(); plt.clim(0, 1500)
        # plt.show()
        # --------------------------------------------------------------------------------

    else:
        # --------------------------------------------------------------------------------
        # Error for unexpected data dimension(s)
        Exc.getExc(' =====> ERROR: snow height data dimension(s) unexpected! Check your data!', 1, 1)
        # --------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------
    # Return interpolation result
    return a2dVarData_INTERP, a2dVarW
    # --------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute relative humidity field(s)
def computeRelativeHumidity(a1dVarData, a1dVarGeoX, a1dVarGeoY,
                            a2dDomainGeoX, a2dDomainGeoY,
                            sVarUnits='%', dVarMissValue=-9999.0, dVarFillValue=-9999.0,
                            dInterpNodata=-9999.0,
                            sInterpMethod='idw', dInterpRadiusX=None, dInterpRadiusY=None):

    # Init results
    a2dVarData_INTERP = None

    # Set variable units and types
    if sVarUnits is None:
        Exc.getExc(' =====> WARNING: relative humidity units are not set! Default units are [%]', 2, 1)
        sVarUnits = '%'
    # Check variables units
    if sVarUnits != '%':
        Exc.getExc(' =====> WARNING: relative humidity units is not correct!'
                   ' Units used: [' + sVarUnits + '] - Units expected: [%]. Check your data!', 2, 1)

    # Get variables dimensions
    iVarDim = a1dVarData.ndim

    # Compute results using 1d format
    if iVarDim == 1:

        # Interpolate point(s) data to grid
        a2dVarData_INTERP = interpPointData(a1dVarData,
                                            a1dVarGeoX, a1dVarGeoY,
                                            a2dDomainGeoX, a2dDomainGeoY,
                                            dInterpNoData=dInterpNodata,
                                            sInterpMethod=sInterpMethod,
                                            dInterpRadiusX=dInterpRadiusX,
                                            dInterpRadiusY=dInterpRadiusY)
        # Check NAN value
        a2dVarData_INTERP[isnan(a2dVarData_INTERP)] = dVarMissValue
    else:
        # Error for unexpected data dimension(s)
        Exc.getExc(' =====> ERROR: relative humidity data dimension(s) unexpected! Check your data!', 1, 1)

    # Results
    return a2dVarData_INTERP

# -------------------------------------------------------------------------------------
