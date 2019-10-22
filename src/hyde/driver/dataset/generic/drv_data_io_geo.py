"""
Class Features

Name:          drv_data_io_geo
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180521'
Version:       '2.0.7'
"""

######################################################################################
# Library
import logging

import numpy as np

from os.path import isfile, join

from src.common.default.lib_default_args import sLoggerName

from src.common.utils.lib_utils_apps_geo import defineGeoGrid, defineGeoCorner, defineGeoHeader, \
    readGeoBox, readGeoHeader, checkGeoDomain, correctGeoHeader

from src.hyde.driver.dataset.generic.drv_data_io_type import Drv_Data_IO
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
######################################################################################

# -------------------------------------------------------------------------------------
# Class Data object
class DataObj(object):
    pass
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Class DataGeo
class DataGeo:

    # -------------------------------------------------------------------------------------
    # Initialize class
    def __init__(self, sFileName=None, sDataName='a2dGeoData', a1oGeoBox=None, oGeoObject=None):

        # Pass variable to global class
        self.__sFileName = sFileName
        self.__a1oGeoBox = a1oGeoBox
        self.__oGeoObject = oGeoObject
        self.__sDataName = sDataName

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to get geographical Data
    def getDataGeo(self):

        # -------------------------------------------------------------------------------------
        # Info start
        oLogStream.info(' ---> Get geographical data ... ')

        # Method to check class input
        [bFileName, bGeoBox] = self.__checkInput()

        # Select method to define geographical information
        if bFileName and isfile(self.__sFileName):
            self.__readGrid()
        elif bGeoBox:
            self.__readBox()
        else:
            Exc.getExc(' =====> ERROR: both filename'
                       ' and geographical box are undefined! (' + self.__sFileName + ')', 1, 1)

        # Method to set variable name of Data
        self.__setName()
        # Method to add Data to an existing geographical object
        self.__addGrid()

        # Method to select output Data
        oData = self.__selectInfo()

        # Info end
        oLogStream.info(' ---> Get geographical data ... OK')

        # Return variable(s)
        return oData
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------
    # Method to select output Data
    def __selectInfo(self):

        oData = DataObj()
        for sVarName in vars(self):

            if not sVarName.startswith('_'):
                oVarName = getattr(self, sVarName)
                setattr(oData, sVarName, oVarName)
            else:
                pass

        return oData

    # -----------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to set specified Data name
    def __setName(self):
        if not hasattr(self, self.__sDataName):
            setattr(self, self.__sDataName, self.a2dGeoData)
        else:
            pass
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to add Data to existence geographical object
    def __addGrid(self):

        if self.__oGeoObject:

            # Get domain reference
            oGeoData_REF = self.__oGeoObject
            # Check if domains are equal
            bCheckDomain = checkGeoDomain(self.a1oGeoHeader, oGeoData_REF.a1oGeoHeader)

            if bCheckDomain:

                # Set Data into domain reference
                setattr(oGeoData_REF, self.__sDataName, self.a2dGeoData)

                for sVarName in vars(oGeoData_REF):
                    oVarName = getattr(oGeoData_REF, sVarName)
                    setattr(self, sVarName, oVarName)

            else:
                Exc.getExc(' =====> WARNING: add Data to domain reference failed! Domains are different!', 2, 1)
        else:
            pass

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Getting geographical information using an ascii grid file
    def __readGrid(self):
        
        # Read ascii grid file
        oFileDriver = Drv_Data_IO(self.__sFileName, 'r').oFileWorkspace
        oFileData = oFileDriver.oFileLibrary.openFile(join(oFileDriver.sFilePath, oFileDriver.sFileName),
                                                      oFileDriver.sFileMode)
        [a2dGeoData, a1oGeoHeader] = oFileDriver.oFileLibrary.readArcGrid(oFileData)
        oFileDriver.oFileLibrary.closeFile(oFileData)

        # Get information Data header
        [iRows, iCols, dGeoXMin, dGeoYMin, dGeoXStep, dGeoYStep, dNoData] = readGeoHeader(a1oGeoHeader)

        # Define Data, finite and nan value(s)
        a2dGeoData = np.asarray(a2dGeoData, dtype=np.float32)
        a2bGeoDataFinite = (a2dGeoData != dNoData)
        a2bGeoDataNaN = (a2dGeoData == dNoData)
        a1iGeoIndexNaN = np.where(a2bGeoDataFinite.ravel() == False)[0]
        a1iGeoIndexFinite = np.where(a2bGeoDataFinite.ravel() == True)[0]

        # Define Data using nan value(s)
        a2dGeoData[a2bGeoDataNaN] = np.nan

        # Define geographical corners
        [dGeoXMin, dGeoXMax, dGeoYMin, dGeoYMax] = defineGeoCorner(dGeoXMin, dGeoYMin,
                                                                   dGeoXStep, dGeoYStep, iCols, iRows)
        # Define geographical grid
        [a2dGeoX, a2dGeoY, a1dGeoBox] = defineGeoGrid(dGeoYMin, dGeoXMin, dGeoYMax, dGeoXMax, dGeoYStep, dGeoXStep)
        # Correct GeoHeader key(s) --> lower characters
        a1oGeoHeader = correctGeoHeader(a1oGeoHeader)

        # Save Data in self workspace
        self.a2dGeoData = a2dGeoData
        self.a2dGeoX = a2dGeoX
        self.a2dGeoY = a2dGeoY
        self.a1dGeoBox = a1dGeoBox
        self.a1oGeoHeader = a1oGeoHeader
        self.a1iGeoIndexNaN = a1iGeoIndexNaN
        self.a1iGeoIndexFinite = a1iGeoIndexFinite
        self.iRows = iRows
        self.iCols = iCols
        self.dGeoXMin = dGeoXMin
        self.dGeoXMax = dGeoXMax
        self.dGeoYMin = dGeoYMin
        self.dGeoYMax = dGeoYMax
        self.dNoData = dNoData
        self.dGeoXStep = dGeoXStep
        self.dGeoYStep = dGeoYStep
        self.a2bGeoDataFinite = a2bGeoDataFinite
        self.a2bGeoDataNaN = a2bGeoDataNaN

    # -------------------------------------------------------------------------------------
    
    # -------------------------------------------------------------------------------------
    # Getting geographical information using a bounding box
    def __readBox(self):
        
        # Retrieving Data from global class allocation
        [iRows, iCols, dGeoXMin, dGeoYMin, dGeoXMax, dGeoYMax, dGeoXStep, dGeoYStep] = readGeoBox(self.__a1oGeoBox)

        # Define Data mask
        a2dGeoData = np.zeros((iCols, iRows))
        a2dGeoData[:] = 1
        
        a2dGeoData = a2dGeoData
        dNoData = -9999.0
        
        a2bGeoDataFinite = (self.a2dGeoData != self.dNoData)
        a2bGeoDataNan = (self.a2dGeoData == self.dNoData)
        a1iGeoIndexNaN = np.where(a2bGeoDataFinite.ravel() == False)[0]
        a1iGeoIndexFinite = np.where(a2bGeoDataFinite.ravel() == True)[0]

        a1oGeoHeader = defineGeoHeader(iRows, iCols, dGeoXMin, dGeoYMin, dGeoXStep, dGeoYStep, dNoData)

        [a2dGeoX, a2dGeoY, a1dGeoBox] = defineGeoGrid(dGeoYMin, dGeoXMin, dGeoYMax, dGeoXMax, dGeoYStep, dGeoXStep)

        # Save Data in self workspace
        self.a2dGeoData = a2dGeoData
        self.a2dGeoX = a2dGeoX
        self.a2dGeoY = a2dGeoY
        self.a1dGeoBox = a1dGeoBox
        self.a1oGeoHeader = a1oGeoHeader
        self.a1iGeoIndexNaN = a1iGeoIndexNaN
        self.a1iGeoIndexFinite = a1iGeoIndexFinite
        self.iRows = iRows
        self.iCols = iCols
        self.dNoData = dNoData
        self.a2bGeoDataFinite = a2bGeoDataFinite
        self.a2bGeoDataNaN = a2bGeoDataNaN

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to check class input
    def __checkInput(self):

        if self.__sFileName and not self.__a1oGeoBox:
            bFileName = True
            bGeoBox = False
        elif self.__sFileName and self.__a1oGeoBox:
            bFileName = True
            bGeoBox = False
        elif not self.__sFileName and self.__a1oGeoBox:
            bFileName = False
            bGeoBox = True
        else:
            bFileName = False
            bGeoBox = False

        return bFileName, bGeoBox

        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
