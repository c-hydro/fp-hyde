"""
RFarm Model Processing Tool

__date__ = '20210503'
__version__ = '4.0.3'
__author__ = 'Fabio Delogu            (fabio.delogu@cimafoundation.org,
              Simone Gabellani        (simone.gabellani@cimafoundation.org)
              Francesco Silvestro     (francesco.silvestro@cimafoundation.org)
              Nicola Rebora           (nicola.rebora@cimafoundation.org)'
__library__ = 'hyde'

General command line:
python3 HYDE_Model_RFarm.py -settings_file configuration.json -time "YYYY-MM-DD HH:MM"

Version(s):
20210503 (4.0.3) --> Add gfs025 routines
20210202 (4.0.2) --> Adapt scripts and fix bugs; add expert forecast routines
20210125 (4.0.1) --> Adapt scripts and fix bugs
20190902 (4.0.0) --> Porting in Hyde package and python 3.x
20171114 (3.5.1) --> Fix bugs (accumulated and istantaneous rain)
20170530 (3.5.0) --> Update version
20150924 (3.0.2) --> Final release for FP Marche project
20150823 (3.0.0) --> Final release for DRIHM project
20140408 (2.0.1) --> Final release based on Rainfarm 1.0
"""

# ----------------------------------------------------------------------------------------------------------------------
# Library
import logging

from argparse import ArgumentParser
from time import time, strftime, gmtime

from src.hyde.algorithm.settings.model.rfarm.lib_rfarm_args import logger_formatter, logger_handle, logger_name

from src.hyde.driver.configuration.model.rfarm.drv_configuration_algorithm_rfarm import DriverAlgorithm
from src.hyde.driver.configuration.model.rfarm.drv_configuration_time_rfarm import DataTime

from src.hyde.driver.model.rfarm.drv_model_rfarm_geo import DataGeo
from src.hyde.driver.model.rfarm.drv_model_rfarm_base import ModelTime, ModelRunner

# Log
log_stream = logging.getLogger(logger_name)
# ----------------------------------------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Algorithm information
alg_project = 'HyDE'
alg_name = 'RainFarm Processing Tool'
alg_version = '4.0.2'
alg_release = '2021-02-02'
alg_type = 'Model'
# Algorithm parameter(s)
time_format = '%Y-%m-%d %H:%M'
# -------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Script Main
def main():

    # -------------------------------------------------------------------------------------
    # Get script argument(s)
    [script_name, file_settings, time_arg] = get_args()

    # Set algorithm configuration
    driver_algorithm = DriverAlgorithm(file_settings)
    driver_algorithm.set_algorithm_logging()
    data_settings, data_paths, colormap_paths = driver_algorithm.set_algorithm_info()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Start Program
    log_stream.info('[' + alg_project + ' ' + alg_type + ' - ' + alg_name + ' (Version ' + alg_version + ')]')
    log_stream.info('[' + alg_project + '] Execution Time: ' + strftime("%Y-%m-%d %H:%M", gmtime()) + ' GMT')
    log_stream.info('[' + alg_project + '] Reference Time: ' + time_arg + ' GMT')
    log_stream.info('[' + alg_project + '] Start Program ... ')

    # Time algorithm information
    start_time = time()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get data time
    log_stream.info(' --> Set time information ... ')
    driver_algorithm_time = DataTime(
        time_arg,
        time_settings=data_settings['time']['time_now'],
        time_period_past=int(data_settings['time']['time_period']),
        time_frequency=data_settings['time']['time_frequency'],
        time_rounding=data_settings['time']['time_rounding'])
    data_time = driver_algorithm_time.getDataTime()
    log_stream.info(' --> Set time information ... DONE')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get data geo
    log_stream.info(' --> Set static datasets ... ')
    data_algorithm_geo = DataGeo(
        src_dict=data_settings['data']['static']['land'],
        cleaning_static_data=data_settings['algorithm']['flags']['cleaning_static_data'])
    data_geo = data_algorithm_geo.compose()
    log_stream.info(' --> Set static datasets ... DONE')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Iterate over time steps
    for time_step in data_time['time_steps']:

        # -------------------------------------------------------------------------------------
        # Compute dynamic time
        log_stream.info(' --> Configure time ... ')
        driver_dynamic_time = ModelTime(
            time_step=time_step,
            time_run=data_time['time_run'],
            time_settings=data_settings['data']['dynamic']['time'])
        data_dynamic_time = driver_dynamic_time.computeModelTime()
        log_stream.info(' --> Configure time ... DONE')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Configure and execute model
        log_stream.info(' --> Initialize RainFarm instance ... ')
        driver_model_runner = ModelRunner(
            time_step=data_dynamic_time.time_step,
            time_range=data_dynamic_time.time_range,
            variable_in=data_settings['variables']['input']['rain_data'],
            variable_out=data_settings['variables']['outcome']['rain_data'],
            data_geo=data_geo,
            template=data_settings['data']['dynamic']['template'],
            parameters=data_settings['algorithm']['parameters'],
            file_dict_ancillary_in=data_paths['rain_input_ancillary'],
            file_dict_ancillary_out=data_paths['rain_outcome_ancillary'],
            file_dict_in=data_paths['rain_input_data'],
            file_dict_out=data_paths['rain_outcome_data'],
            file_ancillary_in_updating=data_settings['algorithm']['flags']['cleaning_dynamic_ancillary_in'],
            file_ancillary_out_updating=data_settings['algorithm']['flags']['cleaning_dynamic_ancillary_out'],
            file_out_updating=data_settings['algorithm']['flags']['cleaning_dynamic_out'],
            file_out_zipping=data_settings['algorithm']['flags']['zipping_dynamic_out'],
            file_domain_name=data_settings['algorithm']['ancillary']['domain'], file_dim_type='domain',
            file_write_engine=data_settings['algorithm']['ancillary']['write_engine'],
            tag_model_algorithm=data_settings['algorithm']['ancillary']['algorithm_mode']
        )
        log_stream.info(' --> Initialize RainFarm instance ... DONE')

        # Collect data
        log_stream.info(' --> Collect RainFarm datasets ... ')
        data_dynamic = driver_model_runner.collect(data_dynamic_time)
        log_stream.info(' --> Collect RainFarm datasets ... DONE!')

        # Configure model
        log_stream.info(' --> Configure RainFarm instance ... ')
        driver_model_runner.configure(data_dynamic)
        log_stream.info(' --> Configure RainFarm instance ... DONE!')

        # Execute model
        log_stream.info(' --> Execute RainFarm instance ... ')
        data_run = driver_model_runner.exec()
        log_stream.info(' --> Execute RainFarm instance ... DONE')

        # Finalize model
        log_stream.info(' --> Save RainFarm results ... ')
        driver_model_runner.save(data_run)
        log_stream.info(' --> Save RainFarm results ... DONE')

        # Clean tmp file(s)
        driver_model_runner.clean(cleaning_dynamic_tmp=data_settings['algorithm']['flags']['cleaning_dynamic_tmp'])
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------------------------
    # Note about script parameter(s)
    log_stream.info('NOTE - Algorithm parameter(s)')
    log_stream.info('Script: ' + str(script_name))
    # ----------------------------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------------------------
    # End Program
    elapsed_time = round(time() - start_time, 1)

    log_stream.info('[' + alg_project + ' ' + alg_type + ' - ' + alg_name + ' (Version ' + alg_version + ')]')
    log_stream.info('End Program - Time elapsed: ' + str(elapsed_time) + ' seconds')
    # ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Method to get script argument(s)
def get_args():
    args_parser = ArgumentParser()
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
# Call script from external library
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------------------------------------------------
