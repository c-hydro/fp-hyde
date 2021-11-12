#!/usr/bin/python3
"""
HYDE Downloading Tool - MySQL Dams

__date__ = '20211110'
__version__ = '2.0.0'
__author__ = 'Fabio Delogu (fabio.delogu@cimafoundation.org'
__library__ = 'HyDE'

General command line:
python3 hyde_downloader_mysql_dams.py -settings_file configuration.json -time "YYYY-MM-DD HH:MM"

Version:
20211110 (2.0.0) --> Release 2.0 Beta (HyDE package)
20160902 (1.0.0) --> Release 1.0 Beta
"""
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Complete library
import logging
import os
import time

from bin.downloader.ground_network.mysql.lib_utils_io import read_file_settings
from bin.downloader.ground_network.mysql.lib_utils_system import make_folder
from bin.downloader.ground_network.mysql.lib_utils_time import set_time

from bin.downloader.ground_network.mysql.drv_downloader_dams_geo import DriverGeo
from bin.downloader.ground_network.mysql.drv_downloader_dams_data import DriverData

from argparse import ArgumentParser
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Algorithm information
alg_name = 'HYDE DOWNLOADING TOOL - MYSQL DAMS'
alg_version = '2.0.0'
alg_release = '2021-11-10'
# Algorithm parameter(s)
time_format = '%Y-%m-%d %H:%M'
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Script Main
def main():

    # -------------------------------------------------------------------------------------
    # Get algorithm settings
    alg_settings, alg_time = get_args()

    # Set algorithm settings
    data_settings = read_file_settings(alg_settings)

    # Set algorithm logging
    make_folder(data_settings['log']['folder_name'])
    set_logging(logger_file=os.path.join(data_settings['log']['folder_name'],
                                         data_settings['log']['file_name']),
                logger_format=data_settings['log']['format'])
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm
    logging.info(' ============================================================================ ')
    logging.info(' ==> ' + alg_name + ' (Version: ' + alg_version + ' Release_Date: ' + alg_release + ')')
    logging.info(' ==> START ... ')
    logging.info(' ')

    # Time algorithm information
    start_time = time.time()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Organize time run
    time_run, time_range = set_time(time_run_args=alg_time, time_run_file=data_settings['time']['time_now'],
                                    time_format=time_format)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get geographical information
    driver_geo = DriverGeo(src_dict=data_settings['data']['static'])
    dams_collections = driver_geo.read_data()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Iterate over time(S)
    for time_step in time_range:

        # -------------------------------------------------------------------------------------
        # Info time
        logging.info(' ---> TIME STEP: ' + str(time_step) + ' ... ')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Get datasets information
        driver_data = DriverData(time_step,
                                 dams_collection=dams_collections,
                                 src_dict=data_settings['data']['dynamic']['source'],
                                 ancillary_dict=data_settings['data']['dynamic']['ancillary'],
                                 dst_dict=data_settings['data']['dynamic']['destination'],
                                 time_dict=data_settings['time'],
                                 variable_dict=data_settings['variable'],
                                 template_dict=data_settings['template'],
                                 info_dict=data_settings['info'],
                                 flag_updating_ancillary=data_settings['flags']['update_dynamic_data_ancillary'],
                                 flag_updating_destination=data_settings['flags']['update_dynamic_data_destination'],
                                 flag_cleaning_tmp=data_settings['flags']['clean_tmp_file'])
        # Download datasets
        driver_data.download_data()
        # Organize and save datasets
        driver_data.organize_data()

        # Clean temporary file(s)
        driver_data.clean_tmp()
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Info time
        logging.info(' ---> TIME STEP: ' + str(time_step) + ' ... DONE')
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm
    time_elapsed = round(time.time() - start_time, 1)

    logging.info(' ')
    logging.info(' ==> ' + alg_name + ' (Version: ' + alg_version + ' Release_Date: ' + alg_release + ')')
    logging.info(' ==> TIME ELAPSED: ' + str(time_elapsed) + ' seconds')
    logging.info(' ==> ... END')
    logging.info(' ==> Bye, Bye')
    logging.info(' ============================================================================ ')

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get script argument(s)
def get_args():
    parser_handle = ArgumentParser()
    parser_handle.add_argument('-settings_file', action="store", dest="alg_settings")
    parser_handle.add_argument('-time', action="store", dest="alg_time")
    parser_values = parser_handle.parse_args()

    if parser_values.alg_settings:
        alg_settings = parser_values.alg_settings
    else:
        alg_settings = 'configuration.json'

    if parser_values.alg_time:
        alg_time = parser_values.alg_time
    else:
        alg_time = None

    return alg_settings, alg_time

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set logging information
def set_logging(logger_file='log.txt', logger_format=None):
    if logger_format is None:
        logger_format = '%(asctime)s %(name)-12s %(levelname)-8s ' \
                        '%(filename)s:[%(lineno)-6s - %(funcName)20s()] %(message)s'

    # Remove old logging file
    if os.path.exists(logger_file):
        os.remove(logger_file)

    # Set level of root debugger
    logging.root.setLevel(logging.DEBUG)

    # Open logging basic configuration
    logging.basicConfig(level=logging.DEBUG, format=logger_format, filename=logger_file, filemode='w')

    # Set logger handle
    logger_handle_1 = logging.FileHandler(logger_file, 'w')
    logger_handle_2 = logging.StreamHandler()
    # Set logger level
    logger_handle_1.setLevel(logging.DEBUG)
    logger_handle_2.setLevel(logging.DEBUG)
    # Set logger formatter
    logger_formatter = logging.Formatter(logger_format)
    logger_handle_1.setFormatter(logger_formatter)
    logger_handle_2.setFormatter(logger_formatter)

    # Add handle to logging
    logging.getLogger('').addHandler(logger_handle_1)
    logging.getLogger('').addHandler(logger_handle_2)

# -------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------
# Call script from external library
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------
