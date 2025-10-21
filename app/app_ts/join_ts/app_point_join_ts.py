#!/usr/bin/python3
"""
HYDE APP - TIME-SERIES JOIN PERIODS  - HYdrological Data Engines
__date__ = '20241023'
__version__ = '1.0.0'
__author__ = 'Fabio Delogu (fabio.delogu@cimafoundation.org',
__library__ = 'hyde'

General command line:
python app_point_joint_ts.py -settings_file configuration.json -time "YYYY-MM-DD HH:MM"

Version(s):
20241023 (1.0.0) --> Beta release
"""

# ----------------------------------------------------------------------------------------------------------------------
# Complete library
import logging
import time
import os
from argparse import ArgumentParser

from lib_data_io_json import read_file_json
from lib_utils_time import set_time
from lib_utils_logging import set_logging_file

from driver_data_static import DriverData as DriverData_Static
from driver_data_dynamic import DriverData as DriverData_Dynamic

# default logger information
from lib_info_args import logger_name, time_format_algorithm

# logging
log_stream = logging.getLogger(logger_name)
# ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------
# algorithm information
project_name = 'hyde'
alg_name = 'Application for joining time-series'
alg_type = 'Package'
alg_version = '1.0.0'
alg_release = '2024-10-23'
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Script Main
def main():

    # ------------------------------------------------------------------------------------------------------------------
    # get algorithm settings
    alg_settings, alg_time = get_args()

    # set algorithm settings
    data_settings = read_file_json(alg_settings)

    # set algorithm logging
    set_logging_file(
        logger_name=logger_name,
        logger_file=os.path.join(data_settings['log']['folder_name'], data_settings['log']['file_name']))
    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
    # Info algorithm
    log_stream.info(' ============================================================================ ')
    log_stream.info(' ==> ' + alg_name + ' (Version: ' + alg_version + ' Release_Date: ' + alg_release + ')')
    log_stream.info(' ==> START ... ')
    log_stream.info(' ')

    # Time algorithm information
    start_time = time.time()
    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
    # Organize time run
    time_reference, time_range = set_time(
        time_ref_args=alg_time,
        time_ref_file=data_settings['time']['algorithm']['time_reference'],
        time_ref_file_start=data_settings['time']['algorithm']['time_start'],
        time_ref_file_end=data_settings['time']['algorithm']['time_end'],
        time_format=time_format_algorithm,
        time_period=data_settings['time']['algorithm']['time_period'],
        time_frequency=data_settings['time']['algorithm']['time_frequency'],
        time_rounding=data_settings['time']['algorithm']['time_rounding']
    )
    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
    # initialize data static obj
    driver_data_static = DriverData_Static(
        point_dict=data_settings['data']['static'],
        tmp_dict=data_settings['tmp']
    )
    # method to organize data
    static_collections = driver_data_static.organize_data()

    # initialize data dynamic obj
    driver_data_dynamic = DriverData_Dynamic(
        time_reference, time_obj=time_range,
        static_obj=static_collections,
        source_dict=data_settings['data']['dynamic']['source'],
        ancillary_dict=data_settings['data']['dynamic']['ancillary'],
        destination_dict=data_settings['data']['dynamic']['destination'],
        flags_dict=data_settings['algorithm']['flags'],
        template_dict=data_settings['algorithm']['template'],
        tmp_dict=data_settings['tmp']
    )
    # method to organize data
    dynamic_collections = driver_data_dynamic.organize_data()
    # method to dump data
    driver_data_dynamic.dump_data(dynamic_collections)
    # ------------------------------------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm
    time_elapsed = round(time.time() - start_time, 1)

    log_stream.info(' ')
    log_stream.info(' ==> ' + alg_name + ' (Version: ' + alg_version + ' Release_Date: ' + alg_release + ')')
    log_stream.info(' ==> TIME ELAPSED: ' + str(time_elapsed) + ' seconds')
    log_stream.info(' ==> ... END')
    log_stream.info(' ==> Bye, Bye')
    log_stream.info(' ============================================================================ ')
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Method to get script argument(s)
def get_args():
    parser_handle = ArgumentParser()
    parser_handle.add_argument('-settings_file', action="store", dest="alg_settings")
    parser_handle.add_argument('-time', action="store", dest="alg_time")
    parser_values = parser_handle.parse_args()

    alg_settings, alg_time = 'configuration.json', None
    if parser_values.alg_settings:
        alg_settings = parser_values.alg_settings
    if parser_values.alg_time:
        alg_time = parser_values.alg_time

    return alg_settings, alg_time

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Call script from external library
if __name__ == '__main__':
    main()
# ----------------------------------------------------------------------------------------------------------------------
