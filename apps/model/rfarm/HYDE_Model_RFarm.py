"""
RFarm Model Processing Tool

__date__ = '20190902'
__version__ = '4.0.0'
__author__ = 'Fabio Delogu            (fabio.delogu@cimafoundation.org,
              Simone Gabellani        (simone.gabellani@cimafoundation.org)
              Francesco Silvestro     (francesco.silvestro@cimafoundation.org)
              Nicola Rebora           (nicola.rebora@cimafoundation.org)'
__library__ = 'hyde'

General command line:
python3 HYDE_Model_RFarm.py -settings_file configuration.json -time YYYYMMDDHHMM

Version(s):
20190902 (4.0.0) --> Porting in Hyde package and python 3.x
20171114 (3.5.1) --> Fix bugs (accumulated and istantaneous rain)
20170530 (3.5.0) --> Update version
20150924 (3.0.2) --> Final release for FP Marche project
20150823 (3.0.0) --> Final release for DRIHM project
20140408 (2.0.1) --> Final release based on Rainfarm 1.0
"""

# ----------------------------------------------------------------------------------------------------------------------
# Library
import time
import argparse

from src.common.log.lib_logging import setLoggingFile

from src.hyde.algorithm.settings.model.rfarm.lib_rfarm_args import logger_formatter, logger_handle, logger_name

from src.hyde.driver.configuration.generic.drv_configuration_algorithm import DataAlgorithm
from src.hyde.driver.configuration.model.rfarm.drv_configuration_time_rfarm import DataTime

from src.hyde.driver.model.rfarm.drv_model_rfarm_geo import DataGeo
from src.hyde.driver.model.rfarm.drv_model_rfarm_base import ModelTime, ModelRunner
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Method to get script argument(s)
def getArgs():
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('-settings_file', action="store", dest="settings_file")
    args_parser.add_argument('-time', action="store", dest="time_arg")
    args_values = args_parser.parse_args()

    script_name = args_parser.prog

    if 'settings_file' in args_values:
        settings_file = args_values.settings_file
    else:
        settings_file = 'configuration.json'

    if 'time_arg' in args_values:
        time_arg = args_values.time_arg
    else:
        time_arg = None

    return script_name, settings_file, time_arg
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Script Main
def main():

    # -------------------------------------------------------------------------------------
    # Version and algorithm information
    project_name = 'HYDE'
    alg_version = '4.0.0'
    alg_type = 'Model'
    alg_name = 'RFarm Processing Tool'
    # Time algorithm information
    alg_start_time = time.time()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get script argument(s)
    [script_name, file_setting, time_arg] = getArgs()

    # Set algorithm configuration
    driver_algorithm_settings = DataAlgorithm(file_setting)
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
    # Get data time
    log_stream.info(' --> Set algorithm time ... ')
    driver_algorithm_time = DataTime(
        time_arg,
        time_settings=data_algorithm_settings['time']['time_now'],
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
        # Compute dynamic time
        log_stream.info(' --> Compute time ... ')
        driver_dynamic_time = ModelTime(
            time_step=time_step,
            time_run=data_algorithm_time['time_run'],
            time_settings=data_algorithm_settings['data']['dynamic']['time'])
        data_dynamic_time = driver_dynamic_time.computeModelTime()
        log_stream.info(' --> Compute time ... DONE')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Configure and execute model
        log_stream.info(' --> Initialize model ... ')
        driver_model_runner = ModelRunner(
            time_step=data_dynamic_time.time_step,
            time_range=data_dynamic_time.time_range,
            variable_in=data_algorithm_settings['variables']['input']['rain_data'],
            variable_out=data_algorithm_settings['variables']['outcome']['rain_data'],
            data_geo=data_geo,
            template=data_algorithm_settings['data']['dynamic']['template'],
            parameters=data_algorithm_settings['algorithm']['parameters'],
            file_ancillary_in=data_algorithm_path['rain_input_ancillary'],
            file_ancillary_out=data_algorithm_path['rain_outcome_ancillary'],
            file_in=data_algorithm_path['rain_input_data'],
            file_out=data_algorithm_path['rain_outcome_data'],
            file_ancillary_in_updating=data_algorithm_flags['cleaning_dynamic_ancillary_in'],
            file_ancillary_out_updating=data_algorithm_flags['cleaning_dynamic_ancillary_out'],
            file_out_updating=data_algorithm_flags['cleaning_dynamic_out'],
            file_out_zipping=data_algorithm_flags['zipping_dynamic_out'],
            file_write_engine=data_algorithm_settings['algorithm']['ancillary']['write_engine']
        )
        log_stream.info(' --> Initialize model ... DONE')

        # Collect data
        log_stream.info(' --> Collect model data ... ')
        data_dynamic = driver_model_runner.collect(data_dynamic_time)
        log_stream.info(' --> Collect model data ... DONE!')

        # Configure model
        log_stream.info(' --> Configure model ... ')
        driver_model_runner.configure(data_dynamic)
        log_stream.info(' --> Configure model ... DONE!')

        # Execute model
        log_stream.info(' --> Execute model ... ')
        data_run = driver_model_runner.exec()
        log_stream.info(' --> Execute model ... DONE')

        # Finalize model
        log_stream.info(' --> Save model result ... ')
        driver_model_runner.save(data_run)
        log_stream.info(' --> Save model result ... DONE')

        # Clean tmp file(s)
        driver_model_runner.clean(cleaning_dynamic_tmp=data_algorithm_flags['cleaning_dynamic_tmp'])
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------------------------
    # Note about script parameter(s)
    log_stream.info('NOTE - Algorithm parameter(s)')
    log_stream.info('Script: ' + str(script_name))
    # ----------------------------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------------------------
    # End Program
    alg_time_elapsed = round(time.time() - alg_start_time, 1)

    log_stream.info('[' + project_name + ' ' + alg_type + ' - ' + alg_name + ' (Version ' + alg_version + ')]')
    log_stream.info('End Program - Time elapsed: ' + str(alg_time_elapsed) + ' seconds')
    # ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Call script from external library
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------------------------------------------------
