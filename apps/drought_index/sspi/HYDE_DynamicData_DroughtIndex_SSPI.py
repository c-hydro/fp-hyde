#!/usr/bin/python3
"""
HyDE Processing Tool - DROUGHT INDEX SSPI

__date__ = '20200522'
__version__ = '1.0.1'
__author__ =
        'Fabio Delogu (fabio.delogu@cimafoundation.org',
        'Andrea Libertino (andrea.libertino@cimafoundation.org',
        'Lauro Rossi (lauro.rossi@cimafoundation.org'

__library__ = 'HyDE'

General command line:
python3 HYDE_DynamicData_DroughtIndex_SSPI.py -settings_file configuration.json -time "YYYY-MM-DD HH:MM"

Version(s):
20200522 (1.0.1) --> Fix bugs and minors
20200518 (1.0.0) --> Beta release
"""

# -------------------------------------------------------------------------------------
# Complete library
import logging
import time
import os

from argparse import ArgumentParser

from lib_utils_io import read_file_json
from lib_utils_system import make_folder
from lib_utils_time import set_time

from drv_satellite_smap_geo import DriverGeo
from drv_satellite_smap_statistics import DriverStatistics
from drv_satellite_smap_data import DriverData
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Algorithm information
alg_version = '1.0.1'
alg_release = '2020-05-22'
alg_name = 'DROUGHT INDEX SSPI Processing Tool'
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
    data_settings = read_file_json(alg_settings)

    # Set algorithm logging
    make_folder(data_settings['data']['log']['folder'])
    set_logging(logger_file=os.path.join(data_settings['data']['log']['folder'],
                                         data_settings['data']['log']['filename']))
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
    time_run = set_time(time_run_args=alg_time, time_run_file=data_settings['time']['time_now'],
                        time_format=time_format)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Organize geographical datasets
    logging.info(' --> Organize geographical information ... ')
    driver_geo = DriverGeo(
        src_dict=data_settings['data']['static']['source'],
        dest_dict=data_settings['data']['static']['outcome'],
        flag_cleaning_geo=data_settings['algorithm']['flags']['cleaning_static_data'])

    driver_geo.composer_geo()
    logging.info(' --> Organize geographical information ... DONE')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Organize statistics datasets
    logging.info(' --> Organize statistics information ... ')
    if data_settings['algorithm']['flags']['computing_statistics']:
        driver_stats = DriverStatistics(
            time_run,
            src_dict=data_settings['data']['statistics']['source'],
            dest_dict=data_settings['data']['statistics']['outcome'],
            ancillary_dict=data_settings['data']['statistics']['ancillary'],
            template_tags=data_settings['algorithm']['template'],
            data_geo=driver_geo.obj_geo_ref,
            data_proj=driver_geo.proj_geo_ref,
            data_transform=driver_geo.geotrans_geo_ref,
            flag_cleaning_statistics=data_settings['algorithm']['flags']['cleaning_statistics_data'])

        data_stats_obj, counter_all_obj, counter_filtered_obj = driver_stats.reader_data()
        moments_obj = driver_stats.composer_data(data_stats_obj, counter_all_obj, counter_filtered_obj)
        driver_stats.writer_data(moments_obj)
        logging.info(' --> Organize statistics information ... DONE')
    else:
        logging.info(' --> Organize statistics information ... PREVIOUSLY DONE')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Organize drought index datasets
    logging.info(' --> Organize drought index information ... ')
    driver_data = DriverData(time_run,
                             src_dict=data_settings['data']['dynamic']['source'],
                             dest_dict=data_settings['data']['dynamic']['outcome'],
                             stats_dict=data_settings['data']['statistics']['outcome'],
                             template_tags=data_settings['algorithm']['template'],
                             data_geo=driver_geo.obj_geo_ref,
                             data_proj=driver_geo.proj_geo_ref,
                             data_transform=driver_geo.geotrans_geo_ref,
                             file_ancillary='nrt_db.pickle',
                             time_offset=data_settings['data']['dynamic']['time']['time_offset'],
                             flag_cleaning_result=data_settings['algorithm']['flags']['cleaning_statistics_data'])

    data_nrt_obj = driver_data.reader_data()
    time_obj, analysis_obj = driver_data.composer_data(data_nrt_obj)
    driver_data.writer_data(time_obj, analysis_obj)
    logging.info(' --> Organize drought index information ... DONE')
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
if __name__ == '__main__':
    main()
# ----------------------------------------------------------------------------
