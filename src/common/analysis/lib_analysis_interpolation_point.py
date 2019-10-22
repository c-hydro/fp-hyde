"""
Library Features:

Name:          lib_analysis_interpolation_point
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190402'
Version:       '1.6.1'
"""

#######################################################################################
# Logging
import logging
import tempfile
import rasterio

from os.path import join
from numpy import zeros, min, max, reshape, flipud

from src.common.utils.lib_utils_apps_file import deleteFileName, deleteFolder
from src.common.utils.lib_utils_apps_process import execProcess
from src.common.utils.lib_utils_op_string import randomString
from src.common.analysis.lib_analysis_interpolation_ancillary import createPointFile_CSV, createPointFile_VRT

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to interpolate data using idw
def interpPointData(a1dData_IN, a1dGeoX_IN, a1dGeoY_IN, a2dGeoX_OUT, a2dGeoY_OUT, iCodeEPSG=4326,
                    dInterpNoData=-9999.0, dInterpRadiusX=None, dInterpRadiusY=None,
                    sInterpMethod='nearest', sInterpOption=None,
                    sFolderTemp=None, sVarData='values', sVarGeoX='x', sVarGeoY='y'):

    # Define layer name (using a random string)
    sLayerName = randomString()

    # Define temporary folder
    if sFolderTemp is None:
        sFolderTemp = tempfile.mkdtemp()

    # Check interpolation radius x and y
    if (dInterpRadiusX is None) or (dInterpRadiusY is None):
        Exc.getExc(' ====> ERROR: interpolation radius along x and/or y is undefined', 1, 1)

    # Define temporary file(s)
    sFileName_CSV = join(sFolderTemp, sLayerName + '.csv')
    sFileName_VRT = join(sFolderTemp, sLayerName + '.vrt')
    sFileName_TIFF = join(sFolderTemp, sLayerName + '.tif')

    # Define geographical information
    dGeoX_OUT_MIN = min(a2dGeoX_OUT)
    dGeoX_OUT_MAX = max(a2dGeoX_OUT)
    dGeoY_OUT_MIN = min(a2dGeoY_OUT)
    dGeoY_OUT_MAX = max(a2dGeoY_OUT)
    iGeoCols_OUT = a2dGeoX_OUT.shape[0]
    iGeoRows_OUT = a2dGeoY_OUT.shape[1]

    # Define dataset for interpolating function
    a2dData_IN = zeros(shape=[a1dData_IN.shape[0], 3])
    a2dData_IN[:, 0] = a1dGeoX_IN
    a2dData_IN[:, 1] = a1dGeoY_IN
    a2dData_IN[:, 2] = a1dData_IN

    # Create csv file
    createPointFile_CSV(sFileName_CSV, a2dData_IN, sVarData, sVarGeoX, sVarGeoY)

    # Create vrt file
    createPointFile_VRT(sFileName_VRT, sFileName_CSV, sLayerName, sVarData, sVarGeoX, sVarGeoY)

    # Grid option(s)
    if sInterpMethod == 'nearest':
        if sInterpOption is None:
            sInterpOption = ('-a nearest:radius1=' + str(dInterpRadiusX) + ':radius2=' +
                             str(dInterpRadiusY) + ':angle=0.0:nodata=' + str(dInterpNoData))
    elif sInterpMethod == 'idw':
        if sInterpOption is None:
            sInterpOption = ('-a invdist:power=2.0:smoothing=0.0:radius1=' + str(dInterpRadiusX) + ':radius2=' +
                             str(dInterpRadiusY) + ':angle=0.0:nodata=' + str(dInterpNoData))
    else:
        sInterpOption = None

    # Execute line command definition (using gdal_grid)
    sLineCommand = ('gdal_grid -zfield "' + sVarData + '"  -txe ' +
                    str(dGeoX_OUT_MIN) + ' ' + str(dGeoX_OUT_MAX) + ' -tye ' +
                    str(dGeoY_OUT_MIN) + ' ' + str(dGeoY_OUT_MAX) + ' -a_srs EPSG:' + str(iCodeEPSG) + ' ' +
                    sInterpOption + ' -outsize ' + str(iGeoRows_OUT) + ' ' + str(iGeoCols_OUT) +
                    ' -of GTiff -ot Float32 -l ' + sLayerName + ' ' +
                    sFileName_VRT + ' ' + sFileName_TIFF + ' --config GDAL_NUM_THREADS ALL_CPUS')

    # Execute algorithm
    [sStdOut, sStdErr, iStdExit] = execProcess(sCLine=sLineCommand, sCPath=sFolderTemp)

    # Read data in tiff format and get values
    oData_OUT = rasterio.open(sFileName_TIFF)
    a3dData_OUT = oData_OUT.read()

    # Image postprocessing to obtain 2d, south-north, east-west data
    a2dData_SQUEEZE = a3dData_OUT[0, :, :]
    a2dData_OUT = flipud(a2dData_SQUEEZE)

    # Delete tmp file(s)
    deleteFileName(sFileName_CSV)
    deleteFileName(sFileName_VRT)
    deleteFileName(sFileName_TIFF)

    return a2dData_OUT
# -------------------------------------------------------------------------------------
