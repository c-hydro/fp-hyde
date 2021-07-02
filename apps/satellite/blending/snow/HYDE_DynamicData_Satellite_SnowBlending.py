"""
Satellite Processing Tool - SNOW SATELLITE BLENDING

__date__ = '20210504'
__version__ = '1.0.0'
__author__ = 'Francesco Avanzi (francesco.avanzi@cimafoundation.org)',
             'Fabio Delogu (fabio.delogu@cimdafoundation.org)'
__library__ = 'hyde'

General command line:
python3 HYDE_DynamicData_Satellite_SnowBlending.py -settings_file configuration.json -time "YYYY-MM-DD HH:MM"

Version:
20210510 (1.0.0) --> First Release
"""
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Complete library
import os.path
import numpy as np
import logging
import rasterio
from datetime import datetime
import matplotlib.pylab as plt

from argparse import ArgumentParser
from time import time, strftime, gmtime

from drv_configuration_algorithm_snowblending import DriverAlgorithm
from drv_configuration_time_snowblending import DriverTime
from lib_snowblending_geo import read_file_raster
from lib_snowblending_blending_tools import read_mosaic_s2, read_mask_modis, read_mask_hsaf, blend_satellite_data
from lib_snowblending_io_generic import create_darray_2d
from lib_snowblending_generic import fill_tags2string
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Algorithm information
alg_project = 'HyDE'
alg_name = 'SNOW SATELLITE BLENDING TOOL'
alg_version = '1.0.0'
alg_release = '2021-05-04'
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
    logging.info('[' + alg_project + '] Reference Time: ' + time_arg + ' GMT')
    logging.info('[' + alg_project + '] Start Program ... ')

    # Time algorithm information
    start_time = time()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get data time
    logging.info(' --> Set algorithm time ... ')
    driver_time = DriverTime(time_arg, data_settings['time'])
    time_run, time_exec, time_range = driver_time.set_algorithm_time()
    logging.info(' --> Set algorithm time ... DONE')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Set data geo
    # -------------------------------------------------------------------------------------
    logging.info(' --> Load domain data ... ')
    file_name_domain = \
        os.path.join(driver_algorithm.algorithm_settings['data']['static']['source']['terrain']['folder_name'],
                     driver_algorithm.algorithm_settings['data']['static']['source']['terrain']['file_name'])
    da_domain, wide_domain, high_domain, proj_domain, transform_domain, \
    bounding_box_domain, no_data_domain, crs_domain = read_file_raster(file_name_domain)
    logging.info(' --> Load domain data ... DONE')
    logging.info(' --> Filepath: ' + file_name_domain)
    # -------------------------------------------------------------------------------------
    # Iterate over time steps
    for time_step in time_range:

        # -------------------------------------------------------------------------------------
        # Upload and mosaic most recent S2 maps
        if driver_algorithm.algorithm_settings['algorithm']['flag']['S2']:
            logging.info(' --> Load sentinel data ... ')
            da_s2 = read_mosaic_s2(da_domain, transform_domain,
                                   time_step, driver_algorithm, dataset_paths, data_settings)
        elif driver_algorithm.algorithm_settings['algorithm']['flag']['S2'] is False:
            logging.info(' --> sentinel not required, will initizialize using no data value ... ')
            no_data_s2 = \
            driver_algorithm.algorithm_settings['variables']['source']['snow_cover_S2']['var_method_compute'][
                'no_data_value']
            s2_map_domain = np.empty(da_domain.shape)
            s2_map_domain[:, :] = no_data_s2
            da_s2 = create_darray_2d(s2_map_domain, da_domain.west_east, da_domain.south_north,
                             coord_name_x=da_domain.coords.dims[1], coord_name_y=da_domain.coords.dims[0],
                             dim_name_x=da_domain.coords.dims[1], dim_name_y=da_domain.coords.dims[0], name='s2')
        else:
            logging.error(' ===> Boolean for S2 flag was badly defined!')
            raise ValueError('S2 flag should be set to either True or False!')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Upload most recent MODIS map
        if driver_algorithm.algorithm_settings['algorithm']['flag']['modis']:
            logging.info(' --> Load MODIS data ... ')
            da_modis = read_mask_modis(da_domain, transform_domain,
                                   time_step, driver_algorithm, dataset_paths, data_settings)
        elif driver_algorithm.algorithm_settings['algorithm']['flag']['modis'] is False:
            logging.info(' --> MODIS not required, will initizialize using no data value ... ')
            no_data_modis = \
                driver_algorithm.algorithm_settings['variables']['source']['snow_cover_modis']['var_method_compute'][
                    'no_data_value']
            modis_domain = np.empty(da_domain.shape)
            modis_domain[:, :] = no_data_modis
            da_modis = create_darray_2d(modis_domain, da_domain.west_east, da_domain.south_north,
                              coord_name_x=da_domain.coords.dims[1], coord_name_y=da_domain.coords.dims[0],
                              dim_name_x=da_domain.coords.dims[1], dim_name_y=da_domain.coords.dims[0], name='modis')
        else:
            logging.error(' ===> Boolean for MODIS flag was badly defined!')
            raise ValueError('MODIS flag should be set to either True or False!')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Upload most recent HSAF map
        if driver_algorithm.algorithm_settings['algorithm']['flag']['hsaf']:
            da_hsaf = read_mask_hsaf(da_domain, transform_domain,
                                       time_step, driver_algorithm, dataset_paths, data_settings)
        elif driver_algorithm.algorithm_settings['algorithm']['flag']['hsaf'] is False:
            no_data_hsaf = \
                driver_algorithm.algorithm_settings['variables']['source']['snow_cover_hsaf']['var_method_compute'][
                    'no_data_value']
            hsaf_domain = np.empty(da_domain.shape)
            hsaf_domain[:, :] = no_data_hsaf
            da_hsaf = create_darray_2d(hsaf_domain, da_domain.west_east, da_domain.south_north,
                                  coord_name_x=da_domain.coords.dims[1], coord_name_y=da_domain.coords.dims[0],
                                  dim_name_x=da_domain.coords.dims[1], dim_name_y=da_domain.coords.dims[0], name='hsaf')
        else:
            logging.error(' ===> Boolean for HSAF flag was badly defined!')
            raise ValueError('HSAF flag should be set to either True or False!')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Blend maps
        logging.info(' --> Blending satellite maps ... ')
        da_sat_blended = blend_satellite_data(da_s2, da_modis, da_hsaf, da_domain, driver_algorithm)
        logging.info(' --> Blending satellite maps ... DONE')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Export
        path = os.path.join(dataset_paths['destination']['folder_name'],
                            dataset_paths['destination']['file_name'])
        drv_data_template = driver_algorithm.algorithm_settings['algorithm']['template']
        tag_filled = {'destination_sub_path_time': time_step,
                      'destination_datetime': time_step}
        path_export = fill_tags2string(path, drv_data_template, tag_filled)
        path_export_folder, path_export_file = os.path.split(path_export)

        # Create directory if missing
        if not os.path.isdir(path_export_folder):
            os.makedirs(path_export_folder, exist_ok=True)

        # Export file
        if path.endswith('.tif'):
            with rasterio.open(path_export, 'w', driver='GTiff',
                          height=da_sat_blended.shape[0], width=da_sat_blended.shape[1], count=1,
                               dtype=da_sat_blended.dtype, crs=crs_domain, transform=transform_domain) as dst:
                dst.write(da_sat_blended.values, 1)
        else:
            logging.error(' ===> Destination output is not GTiff! GTiff is the only format supported!')
            raise ValueError('Destination output is not GTiff! GTiff is the only format supported!')
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
