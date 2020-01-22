#!/usr/bin/python3

"""
HyDE Downloading Tool - NWP GFS

__date__ = '20191022'
__version__ = '1.0.0'
__author__ = '
Fabio Delogu (fabio.delogu@cimafoundation.org,
Alessandro Masoero (alessandro.masoero@cimafoundation.org,
Andrea Libertino (andrea.libertino@cimafoundation.org'
__library__ = 'HyDE'

General command line:
python3 hyde_downloader_nwp_gfs.py -settings_file configuration.json

Version(s):
20191022 (1.0.0) --> Beta release
"""
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Complete library
import logging
import time
import datetime
import gzip
import rasterio

from shutil import rmtree, copyfileobj
from os import makedirs, stat, chmod, remove, rename
from os.path import join, exists, isfile
from pandas import date_range
from argparse import ArgumentParser
from json import load

from src.common.utils.lib_utils_apps_time import convertTimeFrequency

from src.hyde.dataset.db.drops.lib_db_drops_apps_generic import initDropsDB
from src.hyde.dataset.db.drops.lib_db_drops_apps_sensor import getSensorType, getSensorRegistry, getSensorData
from src.hyde.dataset.db.drops.lib_db_drops_utils_sensor_ws import parseSensorData, parseSensorRegistry, createSensorDataFrame
from src.hyde.dataset.db.drops.lib_db_drops_utils_io import writeSensorDataFrame
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Algorithm information
sAlgName = 'HYDE DOWNLOADING TOOL - NWP GFS'
sAlgVersion = '1.0.0'
sAlgRelease = '2019-10-22'
# Algorithm parameter(s)
sTimeFormat = '%Y%m%d%H%M'
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Script Main
def main():

    # -------------------------------------------------------------------------------------
    # Get algorithm settings
    with open(getSettings(), "r") as oFileSettings:
        oDataSettings = load(oFileSettings)

    # Set algorithm logging
    makeFolder(oDataSettings['data_info']['log']['folder'])
    setLogging(sLoggerFile=join(oDataSettings['data_info']['log']['folder'], oDataSettings['data_info']['log']['file']),
               sLoggerMsgFmt=oDataSettings['data_info']['log']['format'])
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm
    logging.info(' ============================================================================ ')
    logging.info(' ==> ' + sAlgName + ' (Version: ' + sAlgVersion + ' Release_Date: ' + sAlgRelease + ')')
    logging.info(' ==> START ... ')
    logging.info(' ')

    # Time algorithm information
    dStartTime = time.time()

    # Initialize drops connection db
    oDrops_CONN, oDrops_EXPDATA = initDropsDB(oDataSettings['drops_info'])
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Define time information
    if oDataSettings['time_info']['time_get'] is None:
        sTime_GET = datetime.datetime.now().strftime('%Y%m%d%H00')
    else:
        sTime_GET = oDataSettings['time_info']['time_get']

    oTime_STEPS = date_range(end=sTime_GET,
                             periods=oDataSettings['time_info']['time_period'],
                             freq=oDataSettings['time_info']['time_frequency'])
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Define domain information
    oData_LAND = rasterio.open(join(oDataSettings['data_info']['land']['folder'],
                                    oDataSettings['data_info']['land']['file']))
    oData_BOX = oData_LAND.bounds
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Iterate over time(S)
    for oTime_STEP in oTime_STEPS:

        # -------------------------------------------------------------------------------------
        # Select time step
        sTime_STEP = oTime_STEP.strftime('%Y%m%d%H00')
        sYear_STEP = oTime_STEP.strftime('%Y')
        sMonth_STEP = oTime_STEP.strftime('%m')
        sDay_STEP = oTime_STEP.strftime('%d')
        sHour_STEP = oTime_STEP.strftime('%H')
        sMinute_STEP = oTime_STEP.strftime('%M')

        # Info time
        logging.info(' ===> TIME STEP: ' + sTime_STEP + ' ... ')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Iterate over variable(s)
        oData_VAR = oDataSettings['variable_info']
        for sVarKey, oVarAttributes in oData_VAR.items():

            # -------------------------------------------------------------------------------------
            # Get variable attribute(s)
            sVarName = oVarAttributes['name']
            bVarDownload = oVarAttributes['download']
            sVarSensor = oVarAttributes['sensor']
            sVarUnits = oVarAttributes['units']
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Info variable
            logging.info(' ====> VARIABLE: ' + sVarKey + ' ... ')

            # Define data tags
            oData_TAGS = {'$DOMAIN': oDataSettings['data_info']['domain'],
                          '$VAR': sVarName,
                          '$time': sTime_STEP,
                          '$yyyy': sYear_STEP, '$mm': sMonth_STEP, '$dd': sDay_STEP,
                          '$HH': sHour_STEP, '$MM': sMinute_STEP}
            # -------------------------------------------------------------------------------------

            # -------------------------------------------------------------------------------------
            # Download activation
            if bVarDownload is True:

                # -------------------------------------------------------------------------------------
                # Define WS folder
                sFolder_WS = setTags(oDataSettings['data_info']['ws']['folder'], oData_TAGS)
                makeFolder(sFolder_WS)

                # Define WS filename
                sFileName_WS = setTags(oDataSettings['data_info']['ws']['file'], oData_TAGS)
                # Get WS flag
                bFileName_WS = oDataSettings['data_info']['ws']['update']
                # Get WS order
                oDataSettings['data_info']['ws']['fields']
                # -------------------------------------------------------------------------------------

                # -------------------------------------------------------------------------------------
                # Check outcome data availability
                if (not exists(join(sFolder_WS, sFileName_WS))) or (bFileName_WS is True):
                    
                    # -------------------------------------------------------------------------------------
                    # Define time_from and time_to
                    oTime_RANGE = date_range(end=sTime_STEP, periods=2,
                                             freq=oDataSettings['time_info']['time_frequency'])
                    sTime_FROM = oTime_RANGE[0].strftime(sTimeFormat)
                    sTime_TO = oTime_RANGE[1].strftime(sTimeFormat)
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Info getting data
                    logging.info(' ======> GET DATA ... ')
                    # Get sensor type object
                    oDrops_SENSOR = getSensorType(sVarSensor, oDrops_CONN)
                    # Get sensor registry object
                    oDrops_REGISTRY = getSensorRegistry(oData_BOX[0], oData_BOX[1], oData_BOX[2], oData_BOX[3],
                                                        oDrops_SENSOR, oDrops_CONN, oDrops_EXPDATA)
                    # Get sensor data object
                    iTime_FREQ = convertTimeFrequency(oDataSettings['time_info']['time_frequency'])
                    oDrops_DATA = getSensorData(sTime_FROM, sTime_TO, iTime_FREQ, 
                                            oDrops_REGISTRY, oDrops_SENSOR, oDrops_CONN, oDrops_EXPDATA)
                    # Info getting data
                    logging.info(' ======> GET DATA ... DONE')
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Info parsering data
                    logging.info(' ======> PARSER DATA ... ')
                    # Parse sensor(s) registry and data
                    oVarRegistry = parseSensorRegistry(oDrops_REGISTRY)
                    oVarData, oVarName = parseSensorData(oDrops_DATA, sTimeFormat)

                    # Create variable data frame
                    oVarData_WS = createSensorDataFrame(oVarData, oVarName, oVarRegistry, 
                                                        sVarUnits, oDataSettings['time_info']['time_frequency'])

                    # Info parsering data
                    logging.info(' ======> PARSER DATA ... DONE')
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Info writing file
                    logging.info(' ======> WRITE DATA: ' + sFileName_WS + ' ... ')
                    # Write variable data frame
                    writeSensorDataFrame(join(sFolder_WS, sFileName_WS), oVarData_WS)
                    # Info writing file
                    logging.info(' ======> WRITE DATA: ' + sFileName_WS + ' ... DONE')
                    # -------------------------------------------------------------------------------------

                    # -------------------------------------------------------------------------------------
                    # Info variable
                    logging.info(' ====> VARIABLE: ' + sVarKey + ' ... DONE')
                    # -------------------------------------------------------------------------------------
                else:
                    # -------------------------------------------------------------------------------------
                    # Info variable
                    logging.info(' ====> VARIABLE: ' + sVarKey + ' ... SKIPPED. File ' + sFileName_WS + ' previously saved.')
                    # -------------------------------------------------------------------------------------
            else:
                # -------------------------------------------------------------------------------------
                # Info variable
                logging.info(' ====> VARIABLE: ' + sVarKey + ' ... SKIPPED. Download not activated.')
                # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Info time
        logging.info(' ===> TIME STEP: ' + sTime_STEP + ' ... DONE')
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm
    dTimeElapsed = round(time.time() - dStartTime, 1)

    logging.info(' ')
    logging.info(' ==> ' + sAlgName + ' (Version: ' + sAlgVersion + ' Release_Date: ' + sAlgRelease + ')')
    logging.info(' ==> TIME ELAPSED: ' + str(dTimeElapsed) + ' seconds')
    logging.info(' ==> ... END')
    logging.info(' ==> Bye, Bye')
    logging.info(' ============================================================================ ')
    # -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to gzip existing file
def zipFile(sFileName_UNCOMPRESSED, sFileName_COMPRESSED):
    if isfile(sFileName_UNCOMPRESSED):
        if not isfile(sFileName_COMPRESSED):
            if sFileName_UNCOMPRESSED != sFileName_COMPRESSED:
                with open(sFileName_UNCOMPRESSED, 'rb') as oFile_IN:
                    with gzip.open(sFileName_COMPRESSED, 'wb') as oFile_OUT:
                        copyfileobj(oFile_IN, oFile_OUT)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to remove file
def deleteFile(sFileName):
    if isfile(sFileName):
        remove(sFileName)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to delete folder and its content
def deleteFolder(sPathFolder):
    if exists(sPathFolder):
        rmtree(sPathFolder)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to make folder
def makeFolder(sPathFolder):
    if not exists(sPathFolder):
        makedirs(sPathFolder)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to make executable a bash file
def makeExec(path):
    mode = stat(path).st_mode
    mode |= (mode & 0o444) >> 2    # copy R bits to X
    chmod(path, mode)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set tag(s) in generic string
def setTags(sString, oTags):
    for sTagKey, sTagValue in oTags.items():
        sString = sString.replace(sTagKey, sTagValue)
    return sString
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get script argument(s)
def getSettings():
    oParser = ArgumentParser()
    oParser.add_argument('-settingfile', action="store", dest="sFileSettings")
    oParserValue = oParser.parse_args()

    if oParserValue.sFileSettings:
        sFileSettings = oParserValue.sFileSettings
    else:
        sFileSettings = 'fp_downloader_drops_ws.json'

    return sFileSettings
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set logging information
def setLogging(sLoggerFile='log.txt',
               sLoggerMsgFmt='%(asctime)s %(name)-12s %(levelname)-8s %(filename)s:[%(lineno)-6s - '
                             '%(funcName)20s()] %(message)s'):

    # Remove old logging file
    if exists(sLoggerFile):
        remove(sLoggerFile)

    # Open logging basic configuration
    logging.basicConfig(level=logging.INFO,
                        format=sLoggerMsgFmt,
                        filename=sLoggerFile,
                        filemode='w')

    # Set logger handle
    oLogHandle_1 = logging.FileHandler(sLoggerFile, 'w')
    oLogHandle_2 = logging.StreamHandler()
    # Set logger level
    oLogHandle_1.setLevel(logging.DEBUG)
    oLogHandle_2.setLevel(logging.DEBUG)
    # Set logger formatter
    oLogFormatter = logging.Formatter(sLoggerMsgFmt)
    oLogHandle_1.setFormatter(oLogFormatter)
    oLogHandle_2.setFormatter(oLogFormatter)
    # Add handle to logging
    logging.getLogger('').addHandler(oLogHandle_1)
    logging.getLogger('').addHandler(oLogHandle_2)
# -------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------
# Call script from external library
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------
