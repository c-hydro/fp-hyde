"""
HSAF Processing Tool - PRECIPITATION PRODUCT H03B

__date__ = '20191004'
__version__ = '4.0.5'
__author__ = 'Fabio Delogu (fabio.delogu@cimafoundation.org'
__library__ = 'hyde'

General command line:
python3 HYDE_DynamicData_HSAF_H03B.py -settings_file configuration.json -time YYYYMMDDHHMM

NOTE:
    works with h5py==2.7.0 and netCDF4==1.4.0
    pip2 uninstall -y h5py netCDF4
    pip2 install h5py==2.7.0 netCDF4==1.4.0

Version:
20191004 (4.0.5) --> Hyde package refactor
20190620 (4.0.4) --> Fix bug in outcome data
20190418 (4.0.3) --> Use source data in netcdf format and add quality index
20190401 (4.0.2) --> Fix bug about geographical references of grib file(s) and interpolation method
20180730 (4.0.0) --> Beta release to put algorithm into FloodProofs library
20141204 (3.0.0) --> Release starting on version 2.0.0
"""
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Complete library
import time
import argparse

# Partial library
from os.path import exists

from src.common.log.lib_logging import setLoggingFile
from src.common.utils.lib_utils_op_string import defineString
from src.common.utils.lib_utils_op_dict import removeDictKey
from src.common.utils.lib_utils_file_workspace import savePickle, restorePickle

from src.hyde.driver.dataset.generic.drv_data_io_geo import DataGeo
from src.hyde.driver.configuration.generic.drv_configuration_algorithm import DataAlgorithm
from src.hyde.driver.configuration.generic.drv_configuration_time import DataTime
from src.hyde.driver.configuration.generic.drv_configuration_tags import DataTags
from src.hyde.driver.configuration.generic.drv_configuration_debug import Exc

from src.hyde.driver.dataset.satellite.hsaf.drv_data_io_h03b import DataProductCleaner, DataProductTime, \
    DataProductBuilder, DataProductAnalyzer, DataProductFinalizer
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get script argument(s)
def GetArgs():
    oParser = argparse.ArgumentParser()
    oParser.add_argument('-settings_file', action="store", dest="sSettingFile")
    oParser.add_argument('-time', action="store", dest="sTimeArg")
    oParserValue = oParser.parse_args()

    sScriptName = oParser.prog

    if oParserValue.sSettingFile:
        sSettingsFile = oParserValue.sSettingFile
    else:
        sSettingsFile = 'configuration.json'

    if oParserValue.sTimeArg:
        sTimeArg = oParserValue.sTimeArg
    else:
        sTimeArg = ''

    return sScriptName, sSettingsFile, sTimeArg
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Script Main
def main():

    # -------------------------------------------------------------------------------------
    # Version and algorithm information
    sProgramVersion = '4.0.5'
    sProjectName = 'HYDE'
    sAlgType = 'DataDynamic'
    sAlgName = 'HSAF PROCESSING TOOL H03B'
    # Time algorithm information
    dStartTime = time.time()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get script argument(s)
    [sScriptName, sFileSetting, sTimeArg] = GetArgs()

    # Set algorithm configuration
    oDrv_Data_Settings = DataAlgorithm(sFileSetting)
    [oData_Settings, oData_Path, oData_Flags, oData_ColorMap] = oDrv_Data_Settings.getDataSettings()

    # Set logging file
    oLogStream = setLoggingFile(oData_Path['log'])
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Start Program
    oLogStream.info('[' + sProjectName + ' ' + sAlgType + ' - ' + sAlgName + ' (Version ' + sProgramVersion + ')]')
    oLogStream.info('[' + sProjectName + '] Start Program ... ')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get data time
    oLogStream.info(' --> Set time data ... ')
    oDrv_Time = DataTime(sTimeArg,
                         iTimeStep=int(oData_Settings['time']['time_step']),
                         iTimeDelta=int(oData_Settings['time']['time_delta']),
                         oTimeRefHH=oData_Settings['time']['time_refHH'])
    oData_Time = oDrv_Time.getDataTime()
    oLogStream.info(' --> Set time data ... DONE')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Clean ancillary static file
    DataProductCleaner(
        flag=oData_Flags['cleaning_static_ancillary_data'],
        file=[oData_Path['land_ancillary']]
    ).cleanDataProduct()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get data geo
    oLogStream.info(' --> Set land data ... ')
    oDrv_Data_Geo = DataGeo(oData_Path['land_ref'])
    if not exists(oData_Path['land_ancillary']):
        oData_Geo = oDrv_Data_Geo.getDataGeo()
        savePickle(oData_Path['land_ancillary'], oData_Geo)
        oLogStream.info(' --> Set land data ... DONE')
    else:
        oData_Geo = restorePickle(oData_Path['land_ancillary'])
        oLogStream.info(' --> Set land data ... LOADED from ancillary saved file.')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Iterate over time steps
    for sTimeStep in oData_Time['a1oTimeStep']:

        # -------------------------------------------------------------------------------------
        # Get data time
        oLogStream.info(' --> Get dynamic time ... ')
        oDrv_DataTime_Dynamic = DataProductTime(
            timestep=sTimeStep,
            timerun=oData_Time['sTimeRun'],
            settings=oData_Settings)
        oTimeStep = oDrv_DataTime_Dynamic.computeDataTime()
        oLogStream.info(' --> Get dynamic time ... DONE')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Set data tags
        oDrv_Data_Tags = DataTags({'$yyyy': sTimeStep[0:4],
                                   '$mm': sTimeStep[4:6], '$dd': sTimeStep[6:8], '$HH': sTimeStep[8:10],
                                   '$MM': sTimeStep[10:12],
                                   '$DOMAIN': oData_Settings['algorithm']['ancillary']['domain']})
        oData_Tags = oDrv_Data_Tags.setDataTags()
        # Info time
        oLogStream.info(' --> Set time step: ' + sTimeStep)

        # Clean ancillary and product dynamic files
        DataProductCleaner(
            time=oTimeStep,
            flag=[oData_Flags['cleaning_dynamic_ancillary_data'],
                  oData_Flags['cleaning_dynamic_product_data']],
            file=[defineString(oData_Path['rain_ancillary'], oData_Tags),
                  defineString(oData_Path['rain_product'],
                               removeDictKey(oData_Tags, ['Year', 'Month', 'Day', 'Hour', 'Minute']))]
        ).cleanDataProduct()
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Get data dynamic
        oLogStream.info(' --> Get dynamic data ... ')
        oDrv_DataBuilder_Dynamic = DataProductBuilder(
            time=oTimeStep,
            settings=oData_Settings,
            rain_file=defineString(oData_Path['rain_data'],
                                   removeDictKey(oData_Tags, ['Year', 'Month', 'Day', 'Hour', 'Minute'])))

        if not exists(defineString(oData_Path['rain_ancillary'], oData_Tags)):
            oData_Dynamic = oDrv_DataBuilder_Dynamic.getDataProduct(oData_Geo.a1dGeoBox)
            savePickle(defineString(oData_Path['rain_ancillary'], oData_Tags), oData_Dynamic)
            oLogStream.info(' --> Get dynamic data ... DONE')
        else:
            oData_Dynamic = restorePickle(defineString(oData_Path['rain_ancillary'], oData_Tags))
            oLogStream.info(' --> Get dynamic data ... LOADED from ancillary saved file.')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Compute data dynamic
        oLogStream.info(' --> Compute dynamic data ... ')
        oDrv_DataAnalyzer_Dynamic = DataProductAnalyzer(
            time=sTimeStep,
            settings=oData_Settings,
            data=oData_Dynamic,
            temp_data_file=defineString(oData_Path['temp'],
                                        removeDictKey(oData_Tags, ['Year', 'Month', 'Day', 'Hour', 'Minute'])))
        if not exists(defineString(oData_Path['rain_product'], oData_Tags)):
            oData_Dynamic = oDrv_DataAnalyzer_Dynamic.computeDataProduct(oData_Geo)
            oLogStream.info(' --> Compute dynamic data ... DONE')
        else:
            oLogStream.info(' --> Compute dynamic data ... SKIPPED! Data previously computed.')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Save data dynamic
        oLogStream.info(' --> Save dynamic data ... ')
        oDrv_DataFinalizer_Dynamic = DataProductFinalizer(
            time=sTimeStep,
            settings=oData_Settings,
            data=oData_Dynamic,
            rain_product_file=defineString(oData_Path['rain_product'],
                                           removeDictKey(oData_Tags, ['Year', 'Month', 'Day', 'Hour', 'Minute'])),
            rain_colormap_file=defineString(oData_ColorMap, oData_Tags))
        if not exists(defineString(oData_Path['rain_product'], oData_Tags)):
            oDrv_DataFinalizer_Dynamic.saveDataProduct(
                oData_Geo,
                oDrv_DataFinalizer_Dynamic.subsetData(oData_Dynamic, iData_Index=None))
            oLogStream.info(' --> Save dynamic data ... DONE')
        else:
            oLogStream.info(' --> Save dynamic data ... SKIPPED! Data previously computed.')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Clean ancillary archive file(s)
        DataProductCleaner(
            flag=oData_Flags['cleaning_dynamic_ancillary_archive'],
            file=defineString(oData_Path['rain_ancillary'], oData_Tags)
        ).cleanDataProduct()
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Note about script parameter(s)
    oLogStream.info('NOTE - Algorithm parameter(s)')
    oLogStream.info('Script: ' + str(sScriptName))
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # End Program
    dTimeElapsed = round(time.time() - dStartTime, 1)

    oLogStream.info('[' + sProjectName + ' ' + sAlgType + ' - ' + sAlgName + ' (Version ' + sProgramVersion + ')]')
    oLogStream.info('End Program - Time elapsed: ' + str(dTimeElapsed) + ' seconds')

    Exc.getExc('', 0, 0)
    # -------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------
# Call script from external library
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------
