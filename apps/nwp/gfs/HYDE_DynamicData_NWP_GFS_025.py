"""
HyDE Processing Tool - NWP GFS 025

__date__ = '20200313'
__version__ = '1.1.0'
__author__ =
        'Andrea Libertino (andrea.libertino@cimafoundation.org',
        'Fabio Delogu (fabio.delogu@cimafoundation.org',
        'Alessandro Masoero (alessandro.masoero@cimafoundation.org',
__library__ = 'hyde'

General command line:
python HYDE_DynamicData_NWP_GFS_025.py -settings_file configuration.json -time YYYY-MM-DD HH:MM

Version(s):
20200313 (1.1.0) --> Fix input data in netcdf format
20200228 (1.0.0) --> Beta release for hyde package
"""
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Complete library
import time
import argparse

from src.common.log.lib_logging import setLoggingFile

from src.hyde.algorithm.settings.nwp.gfs.lib_gfs_args import logger_formatter, logger_handle, logger_name
from src.hyde.driver.configuration.nwp.gfs.drv_configuration_time_gfs import DataTime
from src.hyde.driver.dataset.nwp.gfs.drv_data_gfs_geo import DataGeo

from src.hyde.driver.configuration.generic.drv_configuration_algorithm import DataAlgorithm
from src.hyde.driver.dataset.nwp.gfs.drv_data_gfs_base import DataProductTime, DataProductBuilder
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get script argument(s)
def GetArgs():
    parser_handle = argparse.ArgumentParser()
    parser_handle.add_argument('-settings_file', action="store", dest="settings_file")
    parser_handle.add_argument('-time', action="store", dest="time")
    parser_values = parser_handle.parse_args()

    script_name = parser_handle.prog

    if parser_values.settings_file:
        script_settings_file = parser_values.settings_file
    else:
        script_settings_file = 'configuration.json'

    if parser_values.time:
        script_time = parser_values.time
    else:
        script_time = None

    return script_name, script_settings_file, script_time
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Script Main
def main():

    # -------------------------------------------------------------------------------------
    # Version and algorithm information
    project_name = 'HYDE'
    alg_version = '1.0.0'
    alg_type = 'DataDynamic'
    alg_name = 'NWP GFS 025 Processing Tool'
    # Time algorithm information
    time_start = time.time()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get script argument(s)
    [script_name, script_file_settings, script_time] = GetArgs()

    # Set algorithm configuration
    driver_algorithm_settings = DataAlgorithm(script_file_settings)
    [data_algorithm_settings, data_algorithm_path,
     data_algorithm_flags, data_algorithm_colormap] = driver_algorithm_settings.getDataSettings()

    # Set logging file
    log_stream = setLoggingFile(data_algorithm_path['log'], logger_name, logger_handle, logger_formatter)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Start Program
    log_stream.info('[' + project_name + ' ' + alg_type + ' - ' + alg_name + ' (Version ' + alg_version + ')]')
    log_stream.info('[' + project_name + '] Start Program ... ')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get algorithm time
    log_stream.info(' --> Set algorithm time ... ')
    driver_algorithm_time = DataTime(
        script_time,
        time_now=data_algorithm_settings['time']['time_now'],
        time_period_past=int(data_algorithm_settings['time']['time_period']),
        time_frequency=data_algorithm_settings['time']['time_frequency'],
        time_rounding=data_algorithm_settings['time']['time_rounding'])
    data_algorithm_time = driver_algorithm_time.getDataTime()
    log_stream.info(' --> Set algorithm time ... DONE')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get data geo
    log_stream.info(' --> Set grid data ... ')
    data_algorithm_geo = DataGeo(
        data_algorithm_path['terrain_data'], data_algorithm_path['grid_data'],
        file_updating=data_algorithm_flags['cleaning_static_data'])
    data_geo = data_algorithm_geo.getDataGeo()
    log_stream.info(' --> Set grid data ... DONE')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Iterate over time steps
    for time_step in data_algorithm_time['time_steps']:

        # -------------------------------------------------------------------------------------
        # Get data time
        log_stream.info(' --> Get dynamic time ... ')
        driver_dynamic_time = DataProductTime(
            time_step=time_step,
            time_run=data_algorithm_time['time_run'],
            time_settings=data_algorithm_settings['data']['dynamic']['time'])
        data_dynamic_time = driver_dynamic_time.computeDataTime()
        log_stream.info(' --> Get dynamic time ... DONE')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Build, compute and save product
        log_stream.info(' --> Initialize product driver ... ')
        driver_product = DataProductBuilder(
            time_run=data_dynamic_time.time_step,
            time_range=data_dynamic_time.time_range,
            variable_info_in=data_algorithm_settings['variables']['source'],
            variable_info_out=data_algorithm_settings['variables']['outcome'],
            data_domain=data_algorithm_settings['algorithm']['ancillary']['domain'],
            data_geo=data_geo,
            template=data_algorithm_settings['data']['dynamic']['template'],
            parameters=data_algorithm_settings['algorithm']['parameters'],
            file_ancillary_in=data_algorithm_path['nwp_source_ancillary'],
            file_ancillary_processing=data_algorithm_path['nwp_processing_ancillary'],
            file_ancillary_out=data_algorithm_path['nwp_outcome_ancillary'],
            file_data=data_algorithm_path,
            file_ancillary_in_updating=data_algorithm_flags['cleaning_dynamic_ancillary_source'],
            file_ancillary_processing_updating=data_algorithm_flags['cleaning_dynamic_ancillary_processing'],
            file_ancillary_out_updating=data_algorithm_flags['cleaning_dynamic_ancillary_outcome'],
            file_ancillary_tmp_cleaning=data_algorithm_flags['cleaning_dynamic_tmp'],
            file_out_updating=data_algorithm_flags['cleaning_dynamic_product'],
            file_out_write_engine=data_algorithm_settings['algorithm']['ancillary']['write_engine'],
            file_out_mode_zipping=data_algorithm_flags['zipping_dynamic_product'],
            file_out_ext_zipping=data_algorithm_settings['algorithm']['ancillary']['zip_format'],
        )
        log_stream.info(' --> Initialize product driver ... DONE')

        # Collect product datasets
        log_stream.info(' --> Collect product datasets ... ')
        data_dynamic_collected = driver_product.collect()
        log_stream.info(' --> Collect product data ... DONE')

        # Process product datasets
        log_stream.info(' --> Process product datasets ... ')
        data_dynamic_processed = driver_product.process(data_dynamic_collected)
        log_stream.info(' --> Process product datasets ... DONE')

        # Save product datasets
        log_stream.info(' --> Save product datasets ... ')
        driver_product.save(data_dynamic_processed)
        log_stream.info(' --> Save product datasets ... DONE')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Clean ancillary archive file(s)
        driver_product.clean()
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Note about script parameter(s)
    log_stream.info('NOTE - Algorithm parameter(s)')
    log_stream.info('Script: ' + str(script_name))
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # End Program
    time_elapsed = round(time.time() - time_start, 1)

    log_stream.info('[' + project_name + ' ' + alg_type + ' - ' + alg_name + ' (Version ' + alg_version + ')]')
    log_stream.info('End Program - Time elapsed: ' + str(time_elapsed) + ' seconds')
    # -------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Call script from external library
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------
