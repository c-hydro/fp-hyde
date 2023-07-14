"""
GROUND_NETWORK Processing Tool - WEATHER STATION(S) PRODUCT

__date__ = '20201102'
__version__ = '3.0.0'
__author__ = 'Fabio Delogu (fabio.delogu@cimafoundation.org'
__library__ = 'hyde'

General command line:
python3 HYDE_DynamicData_GroundNetwork_WS.py -settings_file configuration.json -time "YYYY-MM-DD HH:MM"

Version:
20230712 (3.0.1) --> Add possibility of choose idw coefficient
                     Add support to AIIGrid input raster
20201102 (3.0.0) --> Update code(s) for RegioneMarche operational chain
20200625 (2.5.1) --> Update code(s) for LEXIS project
20180914 (2.5.0) --> Beta release for HyDE library
20150925 (2.0.7) --> Latest release used in operational chain(s)
20150325 (2.0.0) --> Release 2.0
20140401 (1.0.1) --> Starting version used in DRIHM2US project
"""
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Libraries
import logging
import matplotlib.pylab as plt

from argparse import ArgumentParser
from time import time, strftime, gmtime

from src.hyde.driver.configuration.ground_network.ws.drv_configuration_algorithm_ws import DriverAlgorithm
from src.hyde.driver.configuration.ground_network.ws.drv_configuration_time_ws import DriverTime

from src.hyde.driver.dataset.ground_network.ws.drv_data_ws_geo import DriverGeo
from src.hyde.driver.dataset.ground_network.ws.drv_data_ws_io import DriverData
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Algorithm information
alg_project = 'HyDE'
alg_name = 'GROUND NETWORK PROCESSING TOOL WS'
alg_version = '3.0.0'
alg_release = '2020-11-02'
alg_type = 'DataDynamic'
# Algorithm parameter(s)
time_format = '%Y-%m-%d %H:%M'
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Script Main
def main():

    # -------------------------------------------------------------------------------------
    # Get script argument(s)
    [file_script, file_settings, time_arg] = get_args()

    # Set algorithm configuration
    driver_algorithm = DriverAlgorithm(file_settings)
    driver_algorithm.set_algorithm_logging()
    data_settings, dataset_paths, colormap_paths = driver_algorithm.set_algorithm_info()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Start Program
    logging.info('[' + alg_project + ' ' + alg_type + ' - ' + alg_name + ' (Version ' + alg_version + ')]')
    logging.info('[' + alg_project + '] Execution Time: ' + strftime("%Y-%m-%d %H:%M", gmtime()) + ' GMT')
    if time_arg is not None:
        logging.info('[' + alg_project + '] Reference Time: ' + time_arg + ' GMT')
    logging.info('[' + alg_project + '] Start Program ... ')

    # Time algorithm information
    start_time = time()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get data time
    logging.info(' --> Set algorithm time ... ')
    driver_time = DriverTime(time_arg, data_settings['time'])
    time_run, time_exec, time_range = \
        driver_time.set_algorithm_time(data_settings['time']['time_reverse'])
    logging.info(' --> Set algorithm time ... DONE')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Set data geo
    logging.info(' --> Set geographical data ... ')
    driver_geo = DriverGeo(src_dict=data_settings['data']['static']['source'],
                           ancillary_dict=data_settings['data']['static']['ancillary'],
                           dst_dict=data_settings['data']['static']['destination'],
                           flag_updating_ancillary=data_settings['algorithm']['flag']['update_static_data_ancillary'])
    geo_collections = driver_geo.composer_geo()
    logging.info(' --> Set geographical data ... DONE')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Iterate over time steps
    for time_step in time_range:

        # -------------------------------------------------------------------------------------
        # Get data dynamic
        driver_data_dynamic = DriverData(
            time_step=time_step,
            geo_collections=geo_collections,
            src_dict=data_settings['data']['dynamic']['source'],
            ancillary_dict=data_settings['data']['dynamic']['ancillary'],
            dst_dict=data_settings['data']['dynamic']['destination'],
            time_dict=data_settings['data']['dynamic']['time'],
            variable_src_dict=data_settings['variables']['source'],
            variable_dst_dict=data_settings['variables']['destination'],
            info_dict=data_settings['algorithm']['info'],
            template_dict=data_settings['algorithm']['template'],
            flag_updating_ancillary=data_settings['algorithm']['flag']['update_dynamic_data_ancillary'],
            flag_updating_destination=data_settings['algorithm']['flag']['update_dynamic_data_destination'],
            flag_cleaning_tmp=data_settings['algorithm']['flag']['clean_temporary_data'])

        # Method to organize datasets
        driver_data_dynamic.organize_data()
        # Method to dump datasets
        driver_data_dynamic.dump_data()
        # Method to delete tmp
        driver_data_dynamic.clean_tmp()
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Note about script parameter(s)
    logging.info('NOTE - Algorithm parameter(s)')
    logging.info('Script: ' + str(file_script))
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # End Program
    elapsed_time = round(time() - start_time, 1)

    logging.info('[' + alg_project + ' ' + alg_type + ' - ' + alg_name + ' (Version ' + alg_version + ')]')
    logging.info('End Program - Time elapsed: ' + str(elapsed_time) + ' seconds')
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get script argument(s)
def get_args():

    parser_handle = ArgumentParser()
    parser_handle.add_argument('-settings_file', action="store", dest="alg_settings")
    parser_handle.add_argument('-time', action="store", dest="alg_time")
    parser_values = parser_handle.parse_args()

    alg_script = parser_handle.prog

    if parser_values.alg_settings:
        alg_settings = parser_values.alg_settings
    else:
        alg_settings = 'configuration.json'

    if parser_values.alg_time:
        alg_time = parser_values.alg_time
    else:
        alg_time = None

    return alg_script, alg_settings, alg_time

# -------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------
# Call script from external library
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------
