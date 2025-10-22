#!/usr/bin/python3

"""
HYDE APP - CONVERT DATA RAW2CSV  - HYdrological Data Engines

__date__ = '20241016'
__version__ = '1.1.0'
__author__ =
    'Fabio Delogu (fabio.delogu@cimafoundation.org)'
__library__ = 'hyde'

General command line:
python app_point_convert_raw2csv.py -settings_file configuration.json -time "YYYY-MM-DD HH:MM"

Version(s):
20241016 (1.1.0) --> Update scripts for converting generic time-series point variables to csv
20240703 (1.0.0) --> First development
"""

# -------------------------------------------------------------------------------------
# Complete library
import logging
import time
import os

from driver_data_src import DriverData as DriverData_Source
from driver_data_dst import DriverData as DriverData_Destination

from argparse import ArgumentParser

from lib_data_io_json import read_file_json
from lib_utils_time import set_time
from lib_utils_logging import set_logging_file
from lib_info_args import logger_name, time_format_algorithm

# Logging
log_stream = logging.getLogger(logger_name)
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# algorithm information
project_name = 'hyde'
alg_name = 'Application for converting data raw2csv'
alg_type = 'Package'
alg_version = '1.1.0'
alg_release = '2024-10-16'
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Script Main
def main():

    # -------------------------------------------------------------------------------------
    # Get algorithm settings
    alg_settings, alg_time = get_args()

    # Set algorithm settings
    data_settings = read_file_json(alg_settings)

    # Set algorithm logging
    set_logging_file(
        logger_name=logger_name,
        logger_file=os.path.join(data_settings['log']['folder_name'], data_settings['log']['file_name']))
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm
    log_stream.info(' ============================================================================ ')
    log_stream.info(' ==> ' + alg_name + ' (Version: ' + alg_version + ' Release_Date: ' + alg_release + ')')
    log_stream.info(' ==> START ... ')
    log_stream.info(' ')

    # Time algorithm information
    start_time = time.time()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Organize time run
    time_reference, time_range = set_time(
        time_ref_args=alg_time,
        time_ref_file=data_settings['time']['time_reference'],
        time_ref_file_start=data_settings['time']['time_start'],
        time_ref_file_end=data_settings['time']['time_end'],
        time_format=time_format_algorithm,
        time_period=data_settings['time']['time_period'],
        time_frequency=data_settings['time']['time_frequency'],
        time_rounding=data_settings['time']['time_rounding']
    )
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Source datasets
    driver_data_source = DriverData_Source(
        time_reference=time_reference, time_range=time_range,
        registry_dict=data_settings['data']['source']['registry'],
        datasets_dict=data_settings['data']['source']['datasets'],
        ancillary_dict=data_settings['data']['ancillary'],
        template_dict=data_settings['algorithm']['template'],
        flags_dict=data_settings['algorithm']['flags'],
        tmp_dict=data_settings['tmp'])
    # method to organize source data
    data_source_obj = driver_data_source.organize_data()

    # Destination datasets
    driver_data_destination = DriverData_Destination(
        time_reference=time_reference,
        time_range=time_range,
        registry_dict=data_settings['data']['destination']['registry'],
        datasets_dict=data_settings['data']['destination']['datasets'],
        ancillary_dict=data_settings['data']['ancillary'],
        template_dict=data_settings['algorithm']['template'],
        flags_dict=data_settings['algorithm']['flags'],
        tmp_dict=data_settings['tmp'])
    # method to organize destination data
    driver_data_destination.organize_data(data_source_obj)
    # -------------------------------------------------------------------------------------

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

# -------------------------------------------------------------------------------------
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

# -------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------
# Call script from external library
if __name__ == '__main__':
    main()
# ----------------------------------------------------------------------------
