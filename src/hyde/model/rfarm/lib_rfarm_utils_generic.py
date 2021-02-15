"""
Library Features:

Name:           lib_rfarm_utils_generic
Author(s):      Fabio Delogu (fabio.delogu@cimafoundation.org)
                Mirko D'Andrea (mirko.dandrea@cimafoundation.org)
Date:           '20190905'
Version:        '3.5.2'
"""

#######################################################################################
# Logging
import logging

import datetime
import math
import os
import pickle
import hashlib
import numpy as np
import pandas as pd
import xarray as xr

from src.hyde.algorithm.settings.model.rfarm.lib_rfarm_args import logger_name
import src.hyde.model.rfarm.lib_rfarm_utils_regrid as lib_regrid

log_stream = logging.getLogger(logger_name)

# Debug
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to check if number is odd or even
def checkMod(iNum, iDiv):
    # Return True or False, depending on if the input number is odd. 
    # Odd numbers are 1, 3, 5, 7, and so on. 
    # Even numbers are 0, 2, 4, 6, and so on.
    
    iMod = iNum % iDiv
     
    return iMod
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to convert decimal degrees to km (2)
def convertDeg2Km_2(deg, lat=None):

    if lat is None:
        km = deg * 110.54
    else:
        km = deg * 111.32 * np.cos(np.deg2rad(lat))
    return km

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to convert decimal degrees to km (1)
def convertDeg2Km(deg): 
    
    # Earth radius
    dRE = 6378.1370 
    km = deg * (np.pi * dRE) / 180
    return km

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to convert km to decimal degrees
def convertKm2Deg(km): 
    
    # Earth radius
    dRE = 6378.1370 
    deg = 180 * km / (np.pi * dRE)
    return deg

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to find closest point
def findClosestIndex(a2dGeoX, a2dGeoY, dGeoX, dGeoY):

    # -------------------------------------------------------------------------------------
    # Compute distance
    a2dGeoDistance = ((a2dGeoX - dGeoX)**2 + (a2dGeoY - dGeoY)**2)
    dGeoDistanceMin = np.min(a2dGeoDistance)
    a1iGeoIndex = np.where(a2dGeoDistance == dGeoDistanceMin)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Indexes of the point in the reference grid
    iPointI = a1iGeoIndex[0][0]
    iPointJ = a1iGeoIndex[1][0]
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Return variable(s)
    return iPointI, iPointJ
    # --------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute ensemble(s)
def computeEnsemble(iEnsStart=1, iEnsEnd=1):

    # Get ensemble information
    iEnsTot = iEnsEnd - iEnsStart + 1

    if iEnsStart > iEnsEnd:
        log_stream.warning(' ====> ensemble min tag > ensemble max tag! Set to 1 default run!')
        iEnsStart = 1
        iEnsEnd = 1
        iEnsTot = 1
    else:
        pass

    a1iEnsRange = np.arange(iEnsStart, iEnsEnd + 1, 1)
    a1oEnsRange = [iEns for iEns in a1iEnsRange]

    return a1oEnsRange

# -------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------
# Method to select variable field(s)
def computeVar(a3dDataXYT_IN, iTimeRatio_RF,
               iIMin_RF, iIMax_RF, iJMin_RF, iJMax_RF):
    
    # RF 3D fields in XYT dimensions
    a3dDataXYT_RF = a3dDataXYT_IN[iIMin_RF: iIMax_RF + 1, iJMin_RF: iJMax_RF + 1, :]
    # Check data limits (just in case)
    a3dDataXYT_RF[a3dDataXYT_RF < 0.01] = 0
    # Convert from accumulated rain to istantaneous rain
    a3dDataXYT_RF = a3dDataXYT_RF/float(iTimeRatio_RF)

    return a3dDataXYT_RF
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to extend reference grid
def extendGrid(a2dGeoX_IN, a2dGeoY_IN, 
               a2dGeoX_REF, a2dGeoY_REF, dGeoXStep_REF, dGeoYStep_REF, 
               dGeoKm_EXT):

    # -------------------------------------------------------------------------------------
    # Check EXT definition
    if dGeoKm_EXT > 0:

        # -------------------------------------------------------------------------------------
        # Check grids (IN vs Ref)
        dGeoXMin_IN = np.min(a2dGeoX_IN)
        dGeoXMax_IN = np.max(a2dGeoX_IN)
        dGeoYMin_IN = np.min(a2dGeoY_IN)
        dGeoYMax_IN = np.max(a2dGeoY_IN)
        
        dGeoXMin_REF = np.min(a2dGeoX_REF)
        dGeoXMax_REF = np.max(a2dGeoX_REF)
        dGeoYMin_REF = np.min(a2dGeoY_REF)
        dGeoYMax_REF = np.max(a2dGeoY_REF)
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Convert Km to decimal degree
        dGeoDeg_EXT = convertKm2Deg(dGeoKm_EXT)
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Compute EXT point(s)
        dGeoXMin_EXT = dGeoXMin_REF - dGeoDeg_EXT/2
        dGeoXMax_EXT = dGeoXMax_REF + dGeoDeg_EXT/2
        dGeoYMin_EXT = dGeoYMin_REF - dGeoDeg_EXT/2
        dGeoYMax_EXT = dGeoYMax_REF + dGeoDeg_EXT/2
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Check EXT vs IN grid
        if dGeoXMin_EXT <= dGeoXMin_IN:
            dGeoXMin_EXT = dGeoXMin_IN + 0.5*dGeoXStep_REF
        
        if dGeoXMax_EXT >= dGeoXMax_IN:
            dGeoXMax_EXT = dGeoXMax_IN - 0.5*dGeoXStep_REF
        
        if dGeoYMin_EXT <= dGeoYMin_IN:
            dGeoYMin_EXT = dGeoYMin_IN + 0.5*dGeoYStep_REF
        
        if dGeoYMax_EXT >= dGeoYMax_IN:
            dGeoYMax_EXT = dGeoYMax_IN - 0.5*dGeoYStep_REF
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Compute dimensions of new grid
        iJ = int((dGeoXMax_EXT - dGeoXMin_EXT)/dGeoXStep_REF)
        iI = int((dGeoYMax_EXT - dGeoYMin_EXT)/dGeoYStep_REF)
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Create EXT grid
        a1dGeoX_EXT = np.linspace(dGeoXMin_EXT, dGeoXMax_EXT, iJ, endpoint=True)
        a1dGeoY_EXT = np.linspace(dGeoYMin_EXT, dGeoYMax_EXT, iI, endpoint=True)
        
        a2dGeoX_EXT, a2dGeoY_EXT = np.meshgrid(a1dGeoX_EXT, a1dGeoY_EXT)
        a2dGeoY_EXT = np.flipud(a2dGeoY_EXT)
        # -------------------------------------------------------------------------------------
    
    else:

        # -------------------------------------------------------------------------------------
        # No grid EXT (if dGeoKm_EXT == 0)
        a2dGeoX_EXT = a2dGeoX_REF
        a2dGeoY_EXT = a2dGeoY_REF
        dGeoDeg_EXT = 0.0
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
    # Info
    dGeoXMin_EXT = np.min(a2dGeoX_EXT)
    dGeoXMax_EXT = np.max(a2dGeoX_EXT)
    dGeoYMin_EXT = np.min(a2dGeoY_EXT)
    dGeoYMax_EXT = np.max(a2dGeoY_EXT)
    
    dGeoXMin_REF = np.min(a2dGeoX_REF)
    dGeoXMax_REF = np.max(a2dGeoX_REF)
    dGeoYMin_REF = np.min(a2dGeoY_REF)
    dGeoYMax_REF = np.max(a2dGeoY_REF)

    log_stream.info(' -------> Grid EXT Value: ' + str(dGeoDeg_EXT) + ' degree')
    log_stream.info(' -------> Grid REF -- GeoXMin: ' + str(dGeoXMin_REF) + ' GeoXMax: ' + str(dGeoXMax_REF) +
                    ' GeoYMin: ' + str(dGeoYMin_REF) + ' GeoYMax: ' + str(dGeoYMax_REF))
    log_stream.info(' -------> Grid EXT -- GeoXMin: ' + str(dGeoXMin_EXT) + ' GeoXMax: ' + str(dGeoXMax_EXT) +
                    ' GeoYMin: ' + str(dGeoYMin_EXT) + ' GeoYMax: ' + str(dGeoYMax_EXT))
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Return variable(s)
    return a2dGeoX_EXT, a2dGeoY_EXT
    # -------------------------------------------------------------------------------------
    
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create RF grid
def computeGrid(a2dGeoX_IN, a2dGeoY_IN,
                a2dGeoX_REF, a2dGeoY_REF, dGeoXStep_REF, dGeoYStep_REF,
                iRatioS):

    # -------------------------------------------------------------------------------------
    # Check grid orientation
    # iGeoX_Dim = a2dGeoX_IN.shape[0]
    # iGeoY_Dim = a2dGeoY_IN.shape[1]
    dGeoY_IN_MinTEST = a2dGeoY_IN[-1, 0]
    dGeoY_IN_MaxTEST = a2dGeoY_IN[0, 0]

    # Print message(s) about grid orientation
    log_stream.info(
        ' -------> Checking SOUTH_NORTH GEOY_IN orientation  (GEOY_IN Min: ' +
        str(dGeoY_IN_MinTEST) + ' GEOY_IN Max: ' + str(dGeoY_IN_MaxTEST) + ')')

    if dGeoY_IN_MinTEST > dGeoY_IN_MaxTEST:
        log_stream.info(' -------> Changing grid GEOY_IN orientation ... SOUTH_NORTH BAD ORIENTATION!')
        a2dGeoY_IN = np.flipud(a2dGeoY_IN)
        log_stream.info(' -------> Changing grid GEOY_IN orientation ... OK')
    else:
        log_stream.info(' -------> Changing grid GEOY_IN orientation ... SOUTH_NORTH CORRECT ORIENTATION')
        log_stream.info(' -------> Changing grid GEOY_IN orientation ... SKIPPED')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Check grids (IN vs Ref)
    dGeoXMin_IN = np.min(a2dGeoX_IN)
    dGeoXMax_IN = np.max(a2dGeoX_IN)
    dGeoYMin_IN = np.min(a2dGeoY_IN)
    dGeoYMax_IN = np.max(a2dGeoY_IN)
    
    dGeoXMin_REF = np.min(a2dGeoX_REF)
    dGeoXMax_REF = np.max(a2dGeoX_REF)
    dGeoYMin_REF = np.min(a2dGeoY_REF)
    dGeoYMax_REF = np.max(a2dGeoY_REF)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Choose type grid
    if(((dGeoYMin_IN == dGeoYMin_REF) and (dGeoYMax_IN == dGeoYMax_REF)) and
           ((dGeoXMin_IN == dGeoXMin_REF) and (dGeoXMax_IN == dGeoXMax_REF))):

        # -------------------------------------------------------------------------------------
        # ==> Grids are equal
        log_stream.info(' -------> Grid IN == Grid REF')
        # Lower Left Corner 
        iIMax_REF = a2dGeoX_IN.shape[0] - 1
        iJMin_REF = 0
        # Upper Right Corner 
        iIMin_REF = 0
        iJMax_REF = a2dGeoX_IN.shape[1] - 1
        # Type Grid
        bGrid = 1
        # -------------------------------------------------------------------------------------
        
    else:

        # -------------------------------------------------------------------------------------
        # ==> Grids are different
        log_stream.info(' -------> Grid IN != Grid REF')
        # Lower Left Corner
        iIMax_REF, iJMin_REF = findClosestIndex(a2dGeoX_IN, a2dGeoY_IN, dGeoXMin_REF, dGeoYMin_REF)
        # Upper Right Corner
        iIMin_REF, iJMax_REF = findClosestIndex(a2dGeoX_IN, a2dGeoY_IN, dGeoXMax_REF, dGeoYMax_REF)
        
        # Check corner(s)
        if a2dGeoX_IN[iIMax_REF, iJMin_REF] > dGeoXMin_REF:
            iJMin_REF = iJMin_REF - 1
        if a2dGeoX_IN[iIMin_REF, iJMax_REF] < dGeoXMax_REF:
            iJMax_REF = iJMax_REF + 1
    
        if a2dGeoY_IN[iIMax_REF, iJMin_REF] > dGeoYMin_REF:
            iIMax_REF = iIMax_REF + 1
        if a2dGeoY_IN[iIMin_REF, iJMax_REF] < dGeoYMax_REF:
            iIMin_REF = iIMin_REF - 1
            
        # Type Grid
        bGrid = 2
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Find values of x, y and steps of grid RF
    dGeoXMin_CUT = a2dGeoX_IN[iIMax_REF, iJMin_REF]
    dGeoXMax_CUT = a2dGeoX_IN[iIMin_REF, iJMax_REF]
    dGeoYMin_CUT = a2dGeoY_IN[iIMax_REF, iJMin_REF]
    dGeoYMax_CUT = a2dGeoY_IN[iIMin_REF, iJMax_REF]

    dGeoXStep_CUT = (dGeoXMax_CUT - dGeoXMin_CUT)/(iJMax_REF - iJMin_REF)
    dGeoYStep_CUT = (dGeoYMax_CUT - dGeoYMin_CUT)/(iIMax_REF - iIMin_REF)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Define pixels number (max dimension for square matrix) and redefine spatial ratio
    if bGrid == 1:
        iNPixels_REF = max((iJMax_REF - iJMin_REF) + 1, (iIMax_REF - iIMin_REF) + 1)
    elif bGrid == 2:
        iNPixels_REF = max((iJMax_REF - iJMin_REF) + 1, (iIMax_REF - iIMin_REF) + 1)
    else:
        iNPixels_REF = None

    dRatioS = float(iRatioS)
    if dRatioS == 0:
        dRatioS = np.max((dGeoXStep_CUT/dGeoXStep_REF), dGeoYStep_CUT/dGeoYStep_REF)
        iRatioS = int(2**(math.floor(math.log(dRatioS, 2))))
        iResolution_REF = int(iNPixels_REF*iRatioS)
    else:
        iResolution_REF = int(iNPixels_REF*iRatioS)
    
    # Check res%2
    if iResolution_REF % 2 != 0:
        iResolution_REF = iResolution_REF + 1
        iNPixels_REF = iResolution_REF
    else:
        pass
    
    # Cast spatial ratio to float
    dRatioS = float(iRatioS)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Default method to search grid index
    # iIMax_RF = iIMax_REF
    # iJMin_RF = iJMin_REF
    # iIMin_RF = iIMax_REF - (iNPixels - 1)
    # iJMax_RF = iJMin_REF + (iNPixels - 1)

    # Extend method to search grid index
    [iIMin_RF, iIMax_RF, 
     iJMin_RF, iJMax_RF,
     iNPixels_RF, iResolution_RF] = searchGridIndex(iIMax_REF, iJMin_REF, 
                                                    a2dGeoX_REF.shape[0], a2dGeoY_REF.shape[1],
                                                    iNPixels_REF, iRatioS)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Define grid rainfarm
    if bGrid == 1:
        dGeoXMin_RF = np.min(a2dGeoX_IN)
        dGeoYMin_RF = np.min(a2dGeoY_IN)
        dGeoXMax_RF = np.max(a2dGeoX_IN)
        dGeoYMax_RF = np.max(a2dGeoY_IN)
    elif bGrid == 2:
        dGeoXMin_RF = a2dGeoX_IN[iIMax_RF, iJMin_RF] - .5 * ((dRatioS - 1) / dRatioS) * dGeoXStep_CUT
        dGeoYMin_RF = a2dGeoY_IN[iIMax_RF, iJMin_RF] - .5 * ((dRatioS - 1) / dRatioS) * dGeoYStep_CUT
        dGeoXMax_RF = a2dGeoX_IN[iIMin_RF, iJMax_RF] + .5 * ((dRatioS - 1) / dRatioS) * dGeoXStep_CUT
        dGeoYMax_RF = a2dGeoY_IN[iIMin_RF, iJMax_RF] + .5 * ((dRatioS - 1) / dRatioS) * dGeoYStep_CUT

    a1dGeoX_RF = np.linspace(dGeoXMin_RF, dGeoXMax_RF, iResolution_RF, endpoint=True)
    a1dGeoY_RF = np.linspace(dGeoYMin_RF, dGeoYMax_RF, iResolution_RF, endpoint=True)
    
    a2dGeoX_RF, a2dGeoY_RF = np.meshgrid(a1dGeoX_RF, a1dGeoY_RF)
    a2dGeoY_RF = np.flipud(a2dGeoY_RF)

    # LL corner
    if bGrid == 1:
        dGeoXLL_RF = np.nanmin(a2dGeoX_IN)
        dGeoYLL_RF = np.nanmin(a2dGeoY_IN)
    elif bGrid == 2:
        dGeoXLL_RF = a2dGeoX_IN[iIMax_RF, iJMin_RF]
        dGeoYLL_RF = a2dGeoY_IN[iIMax_RF, iJMin_RF]
    else:
        pass

    # Compute grid indexes using nearest interpolation
    a2iIndex_RF = lib_regrid.gridIndex(a2dGeoX_RF, a2dGeoY_RF, a2dGeoX_REF, a2dGeoY_REF)
    
    # Info
    log_stream.info(' -------> Grid IN -- GeoXMin: ' + str(dGeoXMin_IN) + ' GeoXMax: ' + str(dGeoXMax_IN) +
                    ' GeoYMin: ' + str(dGeoYMin_IN) + ' GeoYMax: ' + str(dGeoYMax_IN))
    log_stream.info(' -------> Grid REF -- GeoXMin: ' + str(dGeoXMin_REF) + ' GeoXMax: ' + str(dGeoXMax_REF) +
                    ' GeoYMin: ' + str(dGeoYMin_REF) + ' GeoYMax: ' + str(dGeoYMax_REF))
    log_stream.info(' -------> Grid RF -- GeoXMin: ' + str(dGeoXMin_RF) + ' GeoXMax: ' + str(dGeoXMax_RF) +
                    ' GeoYMin: ' + str(dGeoYMin_RF) + ' GeoYMax: ' + str(dGeoYMax_RF))
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Define output
    return(a2dGeoX_RF, a2dGeoY_RF, a2iIndex_RF, 
           dGeoXLL_RF, dGeoYLL_RF, iIMin_RF, iIMax_RF, iJMin_RF, iJMax_RF,
           iRatioS, iResolution_RF, iNPixels_RF)
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to compute volume 
def computeVolume(a2dGeoX_IN, a2dGeoY_IN, a2dGeoX_REF, a2dGeoY_REF, a2dGeoX_RF, a2dGeoY_RF,
                  iIMin_RF, iIMax_RF, iJMin_RF, iJMax_RF,
                  sPathCache):
    
    # --------------------------------------------------------------------------------
    # Initialize GeoX and GeoY to volume control
    a2dGeoX_CVOL = a2dGeoX_IN[iIMin_RF : iIMax_RF + 1, iJMin_RF : iJMax_RF + 1]
    a2dGeoY_CVOL = a2dGeoY_IN[iIMin_RF : iIMax_RF + 1, iJMin_RF : iJMax_RF + 1]
    # --------------------------------------------------------------------------------
    
    # --------------------------------------------------------------------------------
    # Check cache folder availability
    if sPathCache:
        
        # --------------------------------------------------------------------------------
        # Create cache folder 
        if not os.path.isdir(sPathCache):
            os.makedirs(sPathCache)
        else:
            pass
        # --------------------------------------------------------------------------------
        
        # --------------------------------------------------------------------------------
        # Create re-grid filenames
        sHash_CVOL = hashlib.sha1(np.dstack((a2dGeoX_CVOL, a2dGeoY_CVOL)).ravel()).hexdigest()
        sHash_RF = hashlib.sha1(np.dstack((a2dGeoX_RF, a2dGeoY_RF)).ravel()).hexdigest()
        sHash_REF = hashlib.sha1(np.dstack((a2dGeoX_REF, a2dGeoY_REF)).ravel()).hexdigest()
  
        sFileCache_CVOL = os.path.join(sPathCache, 'RF_KVol_' + sHash_CVOL + '_' + sHash_REF + '.pk')
        sFileCache_RF = os.path.join(sPathCache,'RF_KVol_' + sHash_RF + '_' + sHash_REF + '.pk')
        # --------------------------------------------------------------------------------
        
        # --------------------------------------------------------------------------------
        # Load or compute re-grid files
        try:
            
            # --------------------------------------------------------------------------------
            # Load re-grid files (if re-grid files are computed previously)
            oVol_CVOL = pickle.load(open(sFileCache_CVOL, 'r'))
            oVol_RF = pickle.load(open(sFileCache_RF,'r'))
            # --------------------------------------------------------------------------------
   
        except Exception:
            
            # --------------------------------------------------------------------------------
            # Compute re-grid files (if re-grid files are not computed previously) 
            oVol_RF = RFRegrid.KVolumeRegridder(a2dGeoX_RF, a2dGeoY_RF,
                                                      a2dGeoX_REF, a2dGeoY_REF)
            
            oVol_CVOL = RFRegrid.KVolumeRegridder(a2dGeoX_CVOL, a2dGeoY_CVOL,
                                                                   a2dGeoX_REF, a2dGeoY_REF)
            
            # Save re-grid files in cache folder
            with open(sFileCache_CVOL, 'wb') as oFile:
                pickle.dump(oVol_CVOL, oFile, pickle.HIGHEST_PROTOCOL)
   
            with open(sFileCache_RF, 'wb') as oFile:
                pickle.dump(oVol_RF, oFile, pickle.HIGHEST_PROTOCOL)
            # --------------------------------------------------------------------------------
                
        # --------------------------------------------------------------------------------
    else:
        
        # --------------------------------------------------------------------------------
        # Compute re-grid method (if cache is not available) 
        oVol_CVOL = RFRegrid.KVolumeRegridder(a2dGeoX_CVOL, a2dGeoY_CVOL,
                                              a2dGeoX_REF, a2dGeoY_REF)

        oVol_RF = RFRegrid.KVolumeRegridder(a2dGeoX_RF, a2dGeoY_RF,
                                            a2dGeoX_REF, a2dGeoY_REF)
        # --------------------------------------------------------------------------------
        
    # --------------------------------------------------------------------------------
    
    # --------------------------------------------------------------------------------
    # Return variable(s)
    return(oVol_CVOL, oVol_RF)
    # --------------------------------------------------------------------------------
    
# --------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute time steps
def computeTimeSteps(sTimeFrom, sTimeTo, iTimeDelta_IN, iTimeDelta_OUT, sTimeFormat='%Y%m%d%H%M'):

    # -------------------------------------------------------------------------------------
    # Get time from and time to information
    oTimeFrom = datetime.datetime.strptime(sTimeFrom, sTimeFormat)
    oTimeTo = datetime.datetime.strptime(sTimeTo, sTimeFormat)

    oTimeDelta_IN = datetime.timedelta(seconds=iTimeDelta_IN)
    oTimeDelta_OUT = datetime.timedelta(seconds=iTimeDelta_OUT)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Compute initial step
    oTimeStep = oTimeFrom - oTimeDelta_IN
    oTimeStep = oTimeStep + oTimeDelta_OUT
    
    # Compute time steps OUT
    a1oTimeSteps = []
    while oTimeStep <= oTimeTo:
        a1oTimeSteps.append(oTimeStep.strftime(sTimeFormat))
        oTimeStep += oTimeDelta_OUT

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info
    sTimeFrom = a1oTimeSteps[0]
    sTimeTo = a1oTimeSteps[-1]
    log_stream.info(' -------> Time -- From: ' + sTimeFrom + ' To: ' + str(sTimeTo))
    
    # Return variable(s)
    return a1oTimeSteps
    # -------------------------------------------------------------------------------------
    
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define grid index
def searchGridIndex(iIMax_REF, iJMin_REF, iRows_REF, iCols_REF, iNPixels, 
                    iRatioS):

    # -------------------------------------------------------------------------------------
    # Define IJ CUT indexes
    iIMax_RF = iIMax_REF
    iJMin_RF = iJMin_REF
    iIMin_RF = iIMax_REF - (iNPixels - 1)
    iJMax_RF = iJMin_REF + (iNPixels - 1)
    
    # Check mod
    iIDelta_RF = iIMax_RF - iIMin_RF + 1
    iJDelta_RF = iJMax_RF - iJMin_RF + 1
    iIMod_RF = checkMod(iIDelta_RF, iRatioS)
    iJMod_RF = checkMod(iJDelta_RF, iRatioS)
    
    # Info
    log_stream.info(' -------> Grid RF Index -- Initial Values -- IMin: ' + str(iIMin_RF) + ' IMax: ' + str(iIMax_RF) +
                    ' JMin: ' + str(iJMin_RF) + ' JMax: ' + str(iJMax_RF))
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Check if grid CUT is almost 8x8 grids --> to take care fft properties
    while iIDelta_RF < 8 + 2*iIMod_RF:
        iIMax_RF = iIMax_RF + 1
        iIMin_RF = iIMin_RF - 1
        iIDelta_RF = iIMax_RF - iIMin_RF + 1
    while iJDelta_RF < 8 + 2*iJMod_RF:
        iJMax_RF = iJMax_RF + 1
        iJMin_RF = iJMin_RF - 1
        iJDelta_RF = iJMax_RF - iJMin_RF + 1
    
    # Check mod
    # iIDelta_RF = iIMax_RF - iIMin_RF + 1
    # iJDelta_RF = iJMax_RF - iJMin_RF + 1
    # iIMod_RF = checkMod(iIDelta_RF, iRatioS)
    # iJMod_RF = checkMod(iJDelta_RF, iRatioS)
    
    # Info
    log_stream.info(
        ' -------> Grid RF Index -- After corrections for FFT -- IMin: ' + str(iIMin_RF) + ' IMax: ' + str(iIMax_RF) +
        ' JMin: ' + str(iJMin_RF) + ' JMax: ' + str(iJMax_RF))
    # --------------------------------------------------------------------------------------
    # '''
    # --------------------------------------------------------------------------------------
    # Check if grid CUT is included in grid IN (squared grid) --> latitude and longitude adjustment
    # This section has unfixed bug(s) for >= conditions -->
    if iIMin_RF < 0:
        iIMinShift_RF = -iIMin_RF
        iIMin_RF = iIMin_RF + iIMinShift_RF
        iIMax_RF = iIMax_RF + iIMinShift_RF
    else:
        pass

    iIDiff_RF = iIMax_RF - iIMin_RF + 1
    if iIDiff_RF >= iCols_REF:
        iIMaxShift_RF = iIMax_RF - (iCols_REF - 1)
        iIMax_RF = iIMax_RF - iIMaxShift_RF
        iIMin_RF = iIMin_RF - iIMaxShift_RF
        log_stream.warning(' ====> Unfixed index I condition. Check your case at this point!')
    else:
        pass
    
    if iJMin_RF < 0:
        iJMinShift_RF = -iJMin_RF
        iJMin_RF = iJMin_RF + iJMinShift_RF
        iJMax_RF = iJMax_RF + iJMinShift_RF 
    else:
        pass

    iJDiff_RF = iJMax_RF - iJMin_RF + 1
    if iJDiff_RF >= iRows_REF:
        iJMaxShift_RF = iJMax_RF - (iRows_REF - 1)
        iJMax_RF = iJMax_RF - iJMaxShift_RF
        iJMin_RF = iJMin_RF - iJMaxShift_RF
        log_stream.warning(' ====> Unfixed index J condition. Check your case at this point!')
    else:
        pass
    
    # Check mod
    #iIDelta_RF = iIMax_RF - iIMin_RF + 1
    #iJDelta_RF = iJMax_RF - iJMin_RF + 1
    #iIMod_RF = checkMod(iIDelta_RF, iRatioS)
    #iJMod_RF = checkMod(iJDelta_RF, iRatioS)
    
    # Info
    log_stream.info(
        ' -------> Grid RF Index -- After corrections for domain dims -- IMin: ' +
        str(iIMin_RF) + ' IMax: ' + str(iIMax_RF) + ' JMin: ' + str(iJMin_RF) + ' JMax: ' + str(iJMax_RF))
    # --------------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------------
    # Compute grid index taking care spatial disaggregation factor
    # I index
    while iIDelta_RF % iRatioS != 0:
        
        if iIMax_RF < iCols_REF:
            iIMax_RF = iIMax_RF + 1
        elif iIMax_RF >= iCols_REF:
            
            log_stream.warning('====> IMax_RF >= Cols_REF ')
            if iIMin_RF > 0:
                iIMin_RF = iIMin_RF - 1
            elif iIMin_RF <= 0:
                log_stream.warning(' ====> IMin_RF <= 0 ')
                pass
        
        iIDelta_RF = iIMax_RF - iIMin_RF + 1
    # J index
    while iJDelta_RF % iRatioS != 0:
        
        if iJMax_RF < iRows_REF:
            iJMax_RF = iJMax_RF + 1
        elif iJMax_RF >= iRows_REF:
            
            log_stream.warning(' ====> JMax_RF >= Rows_REF ')
            if iJMin_RF > 0:
                iJMin_RF = iJMin_RF - 1
            elif iJMin_RF <= 0:
                log_stream.warning(' ====> JMin_RF <= 0 ')
                pass
        
        iJDelta_RF = iJMax_RF - iJMin_RF + 1
    
    # Control mod
    iIMod_RF = checkMod(iIDelta_RF, iRatioS)
    iJMod_RF = checkMod(iJDelta_RF, iRatioS)
    
    if (iIMod_RF != 0) or (iJMod_RF != 0):
        log_stream.warning(' ====> grid RF is not divisible to spatial resolution! Check grid RF!')
    else:
        pass
    
    # Info
    log_stream.info(' -------> Grid RF Index -- Final Values -- IMin: ' + str(iIMin_RF) + ' IMax: ' + str(iIMax_RF) +
                    ' JMin: ' + str(iJMin_RF) + ' JMax: ' + str(iJMax_RF))
    # --------------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------------
    # Define pixels number (max dimension for square matrix) and redefine spatial ratio
    iNPixels_RF = max((iJMax_RF - iJMin_RF) + 1, (iIMax_RF - iIMin_RF) + 1)
    iResolution_RF = int(iNPixels_RF*iRatioS)
    # --------------------------------------------------------------------------------------

    # --------------------------------------------------------------------------------------
    # Return variable(s)
    return iIMin_RF, iIMax_RF, iJMin_RF, iJMax_RF, iNPixels_RF, iResolution_RF
    # --------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------
# Method to check disaggregated result(s)
def checkResult(a3dData_IN, a3Data_RF, iXScale, iTScale):

    # Scale factor(s)
    iYScale = iXScale

    # Check volume disaggregation
    dData_IN_ACC = np.sum(np.sum(np.sum(a3dData_IN))) * iXScale * iYScale * iTScale
    dData_RF_ACC = np.sum(np.sum(np.sum(a3Data_RF)))

    # Info
    log_stream.info(' -------> Check X VOLUME: X_IN: ' + str(dData_IN_ACC) + ' X_RF: ' + str(dData_RF_ACC))

# --------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to save model result(s)
def saveResult(filename, varname, data_in,
               geox_in, geoy_in, time_in,
               geox_out, geoy_out, time_out,
               geoindex_in=None):

    # -------------------------------------------------------------------------------------
    # Compute time accumulation ratio
    time_ratio_agg = time_in.__len__() / time_out.__len__()

    # Counter(s)
    time_idx_agg = 1
    time_idx_out = 0

    time_steps_out = []

    data_agg = np.zeros([geox_out.shape[0], geoy_out.shape[1]])
    data_out = np.zeros([time_out.__len__(), geox_out.shape[0], geoy_out.shape[1], ])
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Cycle(s) over time step(s)
    for time_idx_in, time_step_in in enumerate(sorted(time_in)):

        # -------------------------------------------------------------------------------------
        # Get data
        data_step = data_in[:, :, time_idx_in]

        # Interpolate data
        if geoindex_in is None:
            data_regrid = lib_regrid.gridData(data_step, geox_in, geoy_in, geox_out, geoy_out)
        else:
            data_indexed = data_step.ravel()[geoindex_in.ravel()]
            data_regrid = np.reshape(data_indexed, [geox_out.shape[0], geoy_out.shape[1]])

        # Debug
        # plt.figure(1); plt.imshow(data_step);plt.colorbar()
        # plt.figure(2); plt.imshow(data_regrid); plt.colorbar()
        # plt.show()

        # Aggregate data using time ratio between IN and OUT time(s)
        data_agg = data_agg + data_regrid

        # Save data in OUT time step format
        if time_idx_agg == time_ratio_agg:

            # Store data
            data_out[time_idx_out, :, :] = data_agg
            time_steps_out.append(time_step_in)

            # Re-initialize counter(s)
            time_idx_out += 1
            time_idx_agg = 1
            data_agg = np.zeros([geox_out.shape[0], geoy_out.shape[1]])

        else:
            time_idx_agg += 1
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Create a data array
    time_index_out = pd.to_datetime(time_steps_out)
    da_out = xr.DataArray(data_out, name=varname,
                          dims=['time', 'south_north', 'west_east'],
                          coords={'time': (['time'], time_index_out),
                                  'longitude': (['south_north', 'west_east'], geox_out),
                                  'latitude': (['south_north', 'west_east'], np.flipud(geoy_out))})

    # Save data in tmp file to free memory
    with open(filename, 'wb') as handle:
        pickle.dump(da_out, handle, protocol=pickle.HIGHEST_PROTOCOL)
    # -------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------------
