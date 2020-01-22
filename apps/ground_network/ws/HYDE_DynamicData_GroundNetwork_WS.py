"""
GROUND_NETWORK Processing Tool - WEATHER STATION(S) PRODUCT

__date__ = '20180914'
__version__ = '2.5.0'
__author__ = 'Fabio Delogu (fabio.delogu@cimafoundation.org'
__library__ = 'hyde'

General command line:
python3 HYDE_DynamicData_GroundNetwork_WS.py -settings_file configuration.json -time YYYYMMDDHHMM

Version:
20180914 (2.5.0) --> Beta release for HyDE library
20150925 (2.0.7) --> Latest release used in operational chain(s)
20150325 (2.0.0) --> Release 2.0
20140401 (1.0.1) --> Starting version used in DRIHM2US project
"""
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Libraries
from argparse import ArgumentParser
from os.path import exists
from time import time, strftime, gmtime

from src.common.log.lib_logging import setLoggingFile
from src.common.utils.lib_utils_op_string import defineString
from src.common.utils.lib_utils_op_dict import removeDictKey
from src.common.utils.lib_utils_file_workspace import savePickle, restorePickle

from src.hyde.driver.dataset.generic.drv_data_io_geo import DataGeo
from src.hyde.driver.configuration.generic.drv_configuration_algorithm import DataAlgorithm
from src.hyde.driver.configuration.generic.drv_configuration_time import DataTime
from src.hyde.driver.configuration.generic.drv_configuration_tags import DataTags
from src.hyde.driver.configuration.generic.drv_configuration_debug import Exc

from src.hyde.driver.dataset.ground_network.ws.drv_data_io_ws import DataProductCleaner, DataProductTime, \
    DataProductBuilder, DataProductAnalyzer, DataProductFinalizer
from src.hyde.driver.dataset.ground_network.ws.drv_data_ancillary_ws import DataAncillaryBuilder
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get script argument(s)
def GetArgs():
    oParser = ArgumentParser()
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
    sProgramVersion = '2.5.0'
    sProjectName = 'HyDE'
    sAlgType = 'DataDynamic'
    sAlgName = 'GROUND NETWORK PROCESSING TOOL WS'
    # Time algorithm information
    dStartTime = time()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get script argument(s)
    [sScriptName, sFileSetting, sTimeArg] = GetArgs()

    # Set algorithm configuration
    oDrv_Data_Settings = DataAlgorithm(sFileSetting)
    [oData_Settings, oData_Path, oData_Flags, oData_ColorMap] = oDrv_Data_Settings.getDataSettings()

    # Set logging file
    oLogStream = setLoggingFile(oData_Path['log'], bLoggerHistory=oData_Settings['data']['log']['history'])
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Start Program
    oLogStream.info('[' + sProjectName + ' ' + sAlgType + ' - ' + sAlgName + ' (Version ' + sProgramVersion + ')]')
    oLogStream.info('[' + sProjectName + '] Execution Time: ' + strftime("%Y%m%d%H%M", gmtime()) + ' GMT')
    oLogStream.info('[' + sProjectName + '] Reference Time: ' + sTimeArg + ' GMT')
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
        file=[oData_Path['land_ancillary'], oData_Path['grid_ref'], oData_Path['predictor_ancillary']]
    ).cleanDataProduct()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Set data geo
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
    # Get data geo
    oLogStream.info(' --> Get ancillary data ... ')
    oDrv_Data_Ancillary = DataAncillaryBuilder(
        settings=oData_Settings,
        slope_file=oData_Path['slope_data'],
        aspect_file=oData_Path['aspect_data'],
        hillshade_file=oData_Path['hillshade_data'],
        roughness_file=oData_Path['roughness_data'],
    )
    if not exists(oData_Path['predictor_ancillary']):
        oData_Ancillary = oDrv_Data_Ancillary.getDataAncillary(oData_Path['land_ref'])
        savePickle(oData_Path['predictor_ancillary'], oData_Ancillary)
        oLogStream.info(' --> Get ancillary data ... DONE')
    else:
        oData_Ancillary = restorePickle(oData_Path['predictor_ancillary'])
        oLogStream.info(' --> Get ancillary data ... LOADED from ancillary saved file.')
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
            flag=[oData_Flags['cleaning_dynamic_ancillary_source'],
                  oData_Flags['cleaning_dynamic_ancillary_outcome'],
                  oData_Flags['cleaning_dynamic_product']],
            file=[defineString(oData_Path['source_ancillary'], oData_Tags),
                  defineString(oData_Path['outcome_ancillary'], oData_Tags),
                  defineString(oData_Path['ws_product'],
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
                                   removeDictKey(oData_Tags, ['Year', 'Month', 'Day', 'Hour', 'Minute'])),
            air_temperature_file=defineString(oData_Path['air_temperature_data'],
                                              removeDictKey(oData_Tags, ['Year', 'Month', 'Day', 'Hour', 'Minute'])),
            incoming_radiation_file=defineString(oData_Path['incoming_radiation_data'],
                                                 removeDictKey(oData_Tags, ['Year', 'Month', 'Day', 'Hour', 'Minute'])),
            wind_file=defineString(oData_Path['wind_data'],
                                   removeDictKey(oData_Tags, ['Year', 'Month', 'Day', 'Hour', 'Minute'])),
            relative_humidity_file=defineString(oData_Path['relative_humidity_data'],
                                                removeDictKey(oData_Tags, ['Year', 'Month', 'Day', 'Hour', 'Minute'])),
            air_pressure_file=defineString(oData_Path['air_pressure_data'],
                                           removeDictKey(oData_Tags, ['Year', 'Month', 'Day', 'Hour', 'Minute'])),
            snow_height_file=defineString(oData_Path['snow_height_data'],
                                          removeDictKey(oData_Tags, ['Year', 'Month', 'Day', 'Hour', 'Minute'])))

        if not exists(defineString(oData_Path['source_ancillary'], oData_Tags)):
            oData_Dynamic = oDrv_DataBuilder_Dynamic.getDataProduct(oData_Geo.a1dGeoBox)
            savePickle(defineString(oData_Path['source_ancillary'], oData_Tags), oData_Dynamic)
            oLogStream.info(' --> Get dynamic data ... DONE')
        else:
            oData_Dynamic = restorePickle(defineString(oData_Path['source_ancillary'], oData_Tags))
            oLogStream.info(' --> Get dynamic data ... LOADED from ancillary saved file.')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Compute data dynamic
        oLogStream.info(' --> Compute dynamic data ... ')
        oDrv_DataAnalyzer_Dynamic = DataProductAnalyzer(
            time=oTimeStep,
            settings=oData_Settings,
            data=oData_Dynamic,
            grid_ref_file=defineString(oData_Path['grid_ref'], oData_Tags))
        if not exists(defineString(oData_Path['ws_product'], oData_Tags)):
            if not exists(defineString(oData_Path['outcome_ancillary'], oData_Tags)):
                oData_Dynamic = oDrv_DataAnalyzer_Dynamic.computeDataProduct(oData_Geo, oData_Ancillary)
                savePickle(defineString(oData_Path['outcome_ancillary'], oData_Tags), oData_Dynamic)
                oLogStream.info(' --> Compute dynamic data ... DONE')
            else:
                oData_Dynamic = restorePickle(defineString(oData_Path['outcome_ancillary'], oData_Tags))
                oLogStream.info(' --> Compute dynamic data ... LOADED from ancillary saved file.')
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
            ws_product_file=defineString(oData_Path['ws_product'],
                                           removeDictKey(oData_Tags, ['Year', 'Month', 'Day', 'Hour', 'Minute'])),
            ws_colormap_file=defineString(oData_ColorMap, oData_Tags))
        if not exists(defineString(oData_Path['ws_product'], oData_Tags)):
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
            flag=[oData_Flags['cleaning_dynamic_ancillary_source'],
                  oData_Flags['cleaning_dynamic_ancillary_outcome']],
            file=[defineString(oData_Path['source_ancillary'], oData_Tags),
                  defineString(oData_Path['outcome_ancillary'], oData_Tags)]
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
    dTimeElapsed = round(time() - dStartTime, 1)

    oLogStream.info('[' + sProjectName + ' ' + sAlgType + ' - ' + sAlgName + ' (Version ' + sProgramVersion + ')]')
    oLogStream.info('End Program - Time elapsed: ' + str(dTimeElapsed) + ' seconds')

    Exc.getExc('', 0, 0)
    # -------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------
# Call script from external library
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------
