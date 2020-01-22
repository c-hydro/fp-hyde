"""
HSAF Processing Tool - SNOW PRODUCT H13

__date__ = '20191004'
__version__ = '1.0.1'
__author__ = 'Fabio Delogu (fabio.delogu@cimafoundation.org'
__library__ = 'hyde'

General command line:
python3 HYDE_DynamicData_HSAF_H13.py -settings_file configuration.json -time YYYYMMDDHHMM

Version:
20191004 (1.0.1) --> Hyde package refactor
20180726 (1.0.0) --> Beta release
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
from src.common.utils.lib_utils_file_workspace import savePickle, restorePickle

from src.hyde.driver.dataset.generic.drv_data_io_geo import DataGeo
from src.hyde.driver.configuration.generic.drv_configuration_algorithm import DataAlgorithm
from src.hyde.driver.configuration.generic.drv_configuration_time import DataTime
from src.hyde.driver.configuration.generic.drv_configuration_tags import DataTags
from src.hyde.driver.configuration.generic.drv_configuration_debug import Exc

from src.hyde.driver.dataset.satellite.hsaf.drv_data_io_h13 import DataProductBuilder, DataProductAnalyzer, \
    DataProductFinalizer, DataProductCleaner
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
    sProgramVersion = '1.0.1'
    sProjectName = 'HyDE'
    sAlgType = 'DataDynamic'
    sAlgName = 'HSAF PROCESSING TOOL H13'
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
        file=[oData_Path['land_ancillary'], oData_Path['grid_ref']]
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
            flag=[oData_Flags['cleaning_dynamic_ancillary_data'],
                  oData_Flags['cleaning_dynamic_product_data']],
            file=[defineString(oData_Path['snow_cover_ancillary'], oData_Tags),
                  defineString(oData_Path['snow_cover_product'], oData_Tags)]
        ).cleanDataProduct()
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Get data dynamic
        oLogStream.info(' --> Get dynamic data ... ')
        oDrv_DataBuilder_Dynamic = DataProductBuilder(
            time=sTimeStep,
            settings=oData_Settings,
            snow_cover_data_file=defineString(oData_Path['snow_cover_data'], oData_Tags),
            snow_cover_quality_file=defineString(oData_Path['snow_cover_quality'], oData_Tags))

        if not exists(defineString(oData_Path['snow_cover_ancillary'], oData_Tags)):
            oData_Dynamic = oDrv_DataBuilder_Dynamic.getDataProduct(oData_Geo.a1dGeoBox)
            savePickle(defineString(oData_Path['snow_cover_ancillary'], oData_Tags), oData_Dynamic)
            oLogStream.info(' --> Get dynamic data ... DONE')
        else:
            oData_Dynamic = restorePickle(defineString(oData_Path['snow_cover_ancillary'], oData_Tags))
            oLogStream.info(' --> Get dynamic data ... LOADED from ancillary saved file.')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Compute data dynamic
        oLogStream.info(' --> Compute dynamic data ... ')
        oDrv_DataAnalyzer_Dynamic = DataProductAnalyzer(
            time=sTimeStep,
            data=oData_Dynamic,
            grid_ref_file=defineString(oData_Path['grid_ref'], oData_Tags))
        if not exists(defineString(oData_Path['snow_cover_product'], oData_Tags)):
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
            snow_cover_product_file=defineString(oData_Path['snow_cover_product'], oData_Tags),
            snow_cover_colormap_file=defineString(oData_Path['snow_cover_colormap'], oData_Tags))
        if not exists(defineString(oData_Path['snow_cover_product'], oData_Tags)):
            oDrv_DataFinalizer_Dynamic.saveDataProduct(oData_Geo)
            oLogStream.info(' --> Save dynamic data ... DONE')
        else:
            oLogStream.info(' --> Save dynamic data ... SKIPPED! Data previously computed.')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Clean ancillary archive file(s)
        DataProductCleaner(
            flag=oData_Flags['cleaning_dynamic_ancillary_archive'],
            file=defineString(oData_Path['snow_cover_ancillary'], oData_Tags)
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
