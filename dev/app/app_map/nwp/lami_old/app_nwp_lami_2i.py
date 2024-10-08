"""
HyDE Processing Tool - NWP LAMI 2i

__date__ = '20241001'
__version__ = '1.5.0'
__author__ = 'Fabio Delogu (fabio.delogu@cimafoundation.org'
__library__ = 'hyde'

General command line:
python app_nwp_lami_2i.py -settings_file configuration_product.json -time "YYYY-MM-DD HH:MM"

Version:
20241001 (1.5.0) --> Refactor and update code for hyde package
20181203 (1.0.0) --> Beta release for hyde package
"""
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Complete library
import time
import argparse

# Partial library
from os.path import exists

from lib_logging import setLoggingFile
from lib_utils_op_string import defineString
from lib_utils_op_dict import removeDictKey
from lib_utils_file_workspace import savePickle, restorePickle

from drv_data_io_geo import DataGeo
from drv_configuration_algorithm import DataAlgorithm
from drv_configuration_time import DataTime
from drv_configuration_tags import DataTags
from drv_configuration_debug import Exc

from drv_data_io_lami_2i import DataProductCleaner, DataProductTime, DataProductBuilder, \
    DataProductAnalyzer, DataProductFinalizer
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
        sSettingsFile = 'hyde_configuration_nwp_lami_2i.json'

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
    sProgramVersion = '1.0.0'
    sProjectName = 'Hyde'
    sAlgType = 'DataDynamic'
    sAlgName = 'NWP LAMI 2i'
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
    # Get algorithm time
    oLogStream.info(' --> Set algorithm time ... ')
    oDrv_Time = DataTime(sTimeArg,
                         sTimeNow=oData_Settings['time']['time_now'],
                         iTimeStep=int(oData_Settings['time']['time_step']),
                         iTimeDelta=int(oData_Settings['time']['time_delta']),
                         oTimeRefHH=oData_Settings['time']['time_refHH'])
    oData_Time = oDrv_Time.getDataTime(bTimeReverse=True, bTimeRestart=True)
    oLogStream.info(' --> Set algorithm time ... DONE')
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
        # Get data time
        oLogStream.info(' --> Get dynamic time ... ')
        oDrv_DataTime_Dynamic = DataProductTime(
            time=sTimeStep,
            settings=oData_Settings)
        oTimeStep = oDrv_DataTime_Dynamic.computeDataTime()
        oLogStream.info(' --> Get dynamic time ... DONE')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Set data tags $yyyy/$mm/$dd/
        sRunTime = sTimeStep[0:4] + '/' + sTimeStep[4:6] + '/' + sTimeStep[6:8] + '/' + sTimeStep[8:10] + sTimeStep[10:12]
        oDrv_Data_Tags = DataTags({'$yyyy': sTimeStep[0:4],
                                   '$mm': sTimeStep[4:6], '$dd': sTimeStep[6:8], '$HH': sTimeStep[8:10],
                                   '$MM': sTimeStep[10:12],
                                   '$RUNTIME': sRunTime,
                                   '$DOMAIN': oData_Settings['algorithm']['ancillary']['domain']})
        oData_Tags = oDrv_Data_Tags.setDataTags()
        # Info time
        oLogStream.info(' --> Set time step: ' + sTimeStep)

        # Clean ancillary and product dynamic files
        DataProductCleaner(
            flag=[oData_Flags['cleaning_dynamic_ancillary_data'],
                  oData_Flags['cleaning_dynamic_product_data']],
            file=[defineString(oData_Path['nwp_ancillary_data_collected'], oData_Tags),
                  defineString(oData_Path['nwp_product'], oData_Tags)]
        ).cleanDataProduct()
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Get data dynamic
        oLogStream.info(' --> Get dynamic data ... ')
        oDrv_DataBuilder_Dynamic = DataProductBuilder(
            time=sTimeStep,
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
            albedo_file=defineString(oData_Path['albedo_data'],
                                                removeDictKey(oData_Tags, ['Year', 'Month', 'Day', 'Hour', 'Minute'])),
            forecast_expected_step=oTimeStep,
            tmp_data=oData_Path['tmp'],
        )

        if not exists(defineString(oData_Path['nwp_ancillary_data_collected'], oData_Tags)):
            oData_Dynamic = oDrv_DataBuilder_Dynamic.getDataProduct()
            savePickle(defineString(oData_Path['nwp_ancillary_data_collected'], oData_Tags),
                       oData_Dynamic)
            oLogStream.info(' --> Get dynamic data ... DONE')
        else:
            oData_Dynamic = restorePickle(defineString(oData_Path['nwp_ancillary_data_collected'], oData_Tags))
            oLogStream.info(' --> Get dynamic data ... LOADED from ancillary saved file.')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Compute data dynamic
        oLogStream.info(' --> Compute dynamic data ... ')
        oDrv_DataAnalyzer_Dynamic = DataProductAnalyzer(
            time=sTimeStep,
            settings=oData_Settings,
            data=oData_Dynamic,
            grid_ref_file=defineString(oData_Path['grid_ref'], oData_Tags),
            forecast_expected_step=oTimeStep)
        if not exists(defineString(oData_Path['nwp_product'], oData_Tags)):
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
            nwp_product_file=defineString(oData_Path['nwp_product'], oData_Tags),
            nwp_colormap_file=defineString(oData_ColorMap, oData_Tags))
        if not exists(defineString(oData_Path['nwp_product'], oData_Tags)):
            oDrv_DataFinalizer_Dynamic.saveDataProduct(oData_Geo)
            oLogStream.info(' --> Save dynamic data ... DONE')
        else:
            oLogStream.info(' --> Save dynamic data ... SKIPPED! Data previously saved.')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Clean ancillary archive file(s)
        DataProductCleaner(
            flag=oData_Flags['cleaning_dynamic_ancillary_archive'],
            file=[defineString(oData_Path['nwp_ancillary_data_collected'], oData_Tags)]
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
