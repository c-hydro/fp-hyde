"""
Library Features:

Name:          lib_snowblending_blending_tools
Author(s):     Francesco Avanzi (francesco.avanzi@cimafoundation.org), Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210525'
Version:       '1.0.0'
"""



# -------------------------------------------------------------------------------------
# Library
import logging
import numpy as np
import rasterio
import rasterio.crs
import os
import matplotlib.pylab as plt
import pandas as pd
from datetime import datetime

import netCDF4
from lib_snowblending_io_generic import create_darray_2d, read_file_hdf4
from lib_snowblending_generic import fill_tags2string
from lib_snowblending_geo import read_file_raster
from lib_snowblending_variables import mask_data
from lib_snowblending_io_gzip import unzip_filename
from scipy.interpolate import griddata

logging.getLogger('rasterio').setLevel(logging.WARNING)
# -------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to convert decimal degrees to km (2)
def deg_2_km(deg):
    # Earth radius
    earth_radius = 6378.1370
    km = deg * (np.pi * earth_radius) / 180
    return km
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to load S2 data and blend them
def read_mosaic_s2(da_domain, transform_domain, time_step, driver_algorithm, dataset_paths, data_settings):

    list_subdomains = driver_algorithm.algorithm_settings['algorithm']['info']['subdomains_S2_source']
    info_max_age = driver_algorithm.algorithm_settings['algorithm']['info']['max_days_age_S2']
    drv_data_template = driver_algorithm.algorithm_settings['algorithm']['template']
    scale_factor = \
    driver_algorithm.algorithm_settings['variables']['source']['snow_cover_S2']['var_method_compute']['scale_factor']
    fx_flag_masks =    \
        driver_algorithm.algorithm_settings['variables']['source']['snow_cover_S2']['var_method_compute']['params'][
        'flag_masks']
    fx_flag_values = \
        driver_algorithm.algorithm_settings['variables']['source']['snow_cover_S2']['var_method_compute']['params']['flag_values']
    fx_flag_meanings = \
        driver_algorithm.algorithm_settings['variables']['source']['snow_cover_S2']['var_method_compute']['params']['flag_meanings']
    fx_pixel_size_aggregation = \
        driver_algorithm.algorithm_settings['variables']['source']['snow_cover_S2']['var_method_compute']['params']['pixel_size_aggregation']
    no_data_s2 = driver_algorithm.algorithm_settings['variables']['source']['snow_cover_S2']['var_method_compute']['no_data_value']
    ground_value_s2 = driver_algorithm.algorithm_settings['variables']['source']['snow_cover_S2']['var_method_compute']['ground_value']

    max_julian_day = time_step.dayofyear
    min_julian_day = time_step.dayofyear - info_max_age + 1

    # Create list of compatible dates
    timestamps_dates = pd.date_range(end=time_step, periods=info_max_age, freq="D")

    # Find most recent image for each subdomain based on these dates
    paths_subdomains = []
    for tag_subdomain in list_subdomains:
        paths_this_subdomain = None
        for tag_timestamp in timestamps_dates:

            candidate_path = os.path.join(dataset_paths['source_s2']['folder_name'],
                                          dataset_paths['source_s2']['file_name'])
            tag_filled = {'source_sub_path_time': tag_timestamp, 's2_subdomain_name': str(tag_subdomain),
                          'source_datetime_daily': tag_timestamp}
            candidate_path = fill_tags2string(candidate_path, drv_data_template, tag_filled)
            if os.path.isfile(candidate_path):
                paths_this_subdomain = candidate_path

        paths_subdomains.append(paths_this_subdomain)
        if paths_this_subdomain is not None:
            logging.info(' --> Path for subdomain ' + str(tag_subdomain) + ' : ' + paths_this_subdomain)

    # Open one subdomain at a time and resample
    s2_map_domain = np.empty(da_domain.shape)
    s2_map_domain[:,:] = np.nan
    for tag_path_subdomain in paths_subdomains:

        if tag_path_subdomain is not None:

            logging.info(' --> Opening and rescaling file ... ' + tag_path_subdomain)

            da_this_subdomain, wide_this_subdomain, high_this_subdomain, proj_this_subdomain, \
            transform_this_subdomain, bounding_box_this_subdomain, no_data_this_subdomain, crs_this_subdomain = \
                read_file_raster(tag_path_subdomain, var_name='s2', scale_factor=scale_factor)

            logging.info(' --> Opening and rescaling file ... DONE ')

            # Clean based on julian day
            logging.info(' --> Applying julian day ... ')
            values_this_subdomain = da_this_subdomain.values
            values_this_subdomain = values_this_subdomain.astype(float)
            values_this_subdomain[values_this_subdomain > max_julian_day] = no_data_s2
            values_this_subdomain[values_this_subdomain < ground_value_s2] = no_data_s2
            values_this_subdomain[(values_this_subdomain > ground_value_s2) &
                                  (values_this_subdomain < min_julian_day)] = no_data_s2
            values_this_subdomain[(values_this_subdomain >= min_julian_day)
                                  & (values_this_subdomain <= max_julian_day)] = 1
            logging.info(' --> Applying julian day ... DONE ')
            if ground_value_s2 != 0.0:
                logging.warning('Ground value is not zero! The algorithm implicitly assumes ground value is zero! Check results!')

            # Remap on reference grid
            logging.info(' --> Masking and regridding ... ')
            values_this_subdomain_on_ref_grid = mask_data(var_data=values_this_subdomain,
                                                          var_geo_x=da_this_subdomain.west_east.values,
                                                          var_geo_y=da_this_subdomain.south_north.values,
                                                          ref_geo_y=da_domain.south_north.values,
                                                          ref_geo_x=da_domain.west_east.values,
                                                          ref_geo_z=da_domain.values,
                                                          var_missing_value=no_data_s2, fx_nodata=no_data_s2,
                                                          var_fill_value=no_data_s2,
                                                          fx_flag_masks=fx_flag_masks, fx_flag_values=fx_flag_values,
                                                          fx_flag_meanings=fx_flag_meanings,
                                                          fx_pixel_size_aggregation=fx_pixel_size_aggregation)
            logging.info(' --> Masking and regridding ... DONE ')

            # Clip based on bounding box
            if da_domain.west_east.values.ndim == 1 and da_domain.south_north.values.ndim == 1:
                ref_grid_geo_x, ref_grid_geo_y = np.meshgrid(da_domain.west_east.values, da_domain.south_north.values)
            elif da_domain.west_east.values.ndim == 2 and da_domain.south_north.values.ndim == 2:
                ref_grid_geo_x = da_domain.west_east.values
                ref_grid_geo_y = da_domain.south_north.values
            else:
                logging.error(' ===> Reference dimensions in bed format')
                raise IOError('Geographical data format not allowed')

            logging.info(' --> Clipping ...  ')

            mask = ((ref_grid_geo_x >= bounding_box_this_subdomain[0]) &
                          (ref_grid_geo_y <= bounding_box_this_subdomain[1]) &
                          (ref_grid_geo_x <= bounding_box_this_subdomain[2]) &
                          (ref_grid_geo_y >= bounding_box_this_subdomain[3]))
            np.putmask(s2_map_domain, mask, values_this_subdomain_on_ref_grid)

            logging.info(' --> Clipping ...  DONE ')

    s2_map_domain[np.isnan(s2_map_domain)] = no_data_s2
    da = create_darray_2d(s2_map_domain, da_domain.west_east, da_domain.south_north,
                          coord_name_x=da_domain.coords.dims[1], coord_name_y=da_domain.coords.dims[0],
                          dim_name_x=da_domain.coords.dims[1], dim_name_y=da_domain.coords.dims[0], name='s2')
    return da
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to prepare modis data
def read_mask_modis(da_domain, transform_domain, time_step, driver_algorithm, dataset_paths, data_settings):

    # Create filepath
    path = os.path.join(dataset_paths['source_modis']['folder_name'],
                                  dataset_paths['source_modis']['file_name'])
    drv_data_template = driver_algorithm.algorithm_settings['algorithm']['template']
    tag_filled = {'source_sub_path_time': time_step,
                  'source_datetime': time_step}
    path = fill_tags2string(path, drv_data_template, tag_filled)

    # Check file existence
    if os.path.isfile(path):
        logging.info(' --> Opening file ... ' + path)

        #unzip
        path_unzip, extension = path.split(dataset_paths['source_modis']['extension_zip'])
        unzip_filename(path, path_unzip)
        logging.info(' --> File unzipped ... ' + path)

        #read
        modis_NDSI = read_file_hdf4(path_unzip,
                                  var_name=driver_algorithm.algorithm_settings['variables']['source']['snow_cover_modis']['var_method_compute']['var_name'])
        logging.info(' --> File loaded ... ' + path_unzip)
        logging.info(' --> Read variable: ... ' +
                     driver_algorithm.algorithm_settings['variables']['source']['snow_cover_modis']['var_method_compute']['var_name'])

        #mask and resample
        no_data_modis = driver_algorithm.algorithm_settings['variables']['source']['snow_cover_modis']['var_method_compute']['no_data_value']
        fx_flag_masks = \
            driver_algorithm.algorithm_settings['variables']['source']['snow_cover_modis']['var_method_compute']['params']['flag_masks']
        fx_flag_values = \
            driver_algorithm.algorithm_settings['variables']['source']['snow_cover_modis']['var_method_compute']['params']['flag_values']
        fx_flag_meanings = \
            driver_algorithm.algorithm_settings['variables']['source']['snow_cover_modis']['var_method_compute']['params']['flag_meanings']
        fx_pixel_size_aggregation = \
            driver_algorithm.algorithm_settings['variables']['source']['snow_cover_modis']['var_method_compute']['params']['pixel_size_aggregation']

        logging.info(' --> Masking and regridding ... ')
        modis_NDSI_masked_on_ref_grid = mask_data(var_data=modis_NDSI.NDSI_Snow_Cover.values,
                                                      var_geo_x=modis_NDSI.west_east.values,
                                                      var_geo_y=modis_NDSI.south_north.values,
                                                      ref_geo_y=da_domain.south_north.values,
                                                      ref_geo_x=da_domain.west_east.values,
                                                      ref_geo_z=da_domain.values,
                                                      var_missing_value=no_data_modis, fx_nodata=no_data_modis,
                                                      var_fill_value=no_data_modis,
                                                      fx_flag_masks=fx_flag_masks, fx_flag_values=fx_flag_values,
                                                      fx_flag_meanings=fx_flag_meanings,
                                                      fx_pixel_size_aggregation=fx_pixel_size_aggregation)

        logging.info(' --> Masking and regridding ... DONE!')

        os.remove(path_unzip)

        logging.info(' --> Remove unzipped file ... DONE!')

    else:

        logging.warning(' --> File not found! An empty dataset will be created!' + path)
        no_data_modis = \
        driver_algorithm.algorithm_settings['variables']['source']['snow_cover_modis']['var_method_compute'][
            'no_data_value']
        modis_NDSI_masked_on_ref_grid = np.empty(da_domain.shape)
        modis_NDSI_masked_on_ref_grid[:, :] = no_data_modis

    da = create_darray_2d(modis_NDSI_masked_on_ref_grid, da_domain.west_east, da_domain.south_north,
                              coord_name_x=da_domain.coords.dims[1], coord_name_y=da_domain.coords.dims[0],
                              dim_name_x=da_domain.coords.dims[1], dim_name_y=da_domain.coords.dims[0], name='modis')
    return da

# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to prepare hsaf data
def read_mask_hsaf(da_domain, transform_domain, time_step, driver_algorithm, dataset_paths, data_settings):

    # Create filepath
    path = os.path.join(dataset_paths['source_hsaf']['folder_name'],
                        dataset_paths['source_hsaf']['file_name'])
    drv_data_template = driver_algorithm.algorithm_settings['algorithm']['template']
    tag_filled = {'source_sub_path_time': time_step,
                  'source_datetime_daily': time_step}
    path = fill_tags2string(path, drv_data_template, tag_filled)

    # Check file existence
    if os.path.isfile(path):
        logging.info(' --> Opening file ... ' + path)

        # unzip
        path_unzip, extension = path.split(dataset_paths['source_hsaf']['extension_zip'])
        unzip_filename(path, path_unzip)
        logging.info(' --> File unzipped ... ' + path)

        # read
        hsaf_dset = netCDF4.Dataset(path_unzip,'r')
        hsaf_values = \
            hsaf_dset.variables[driver_algorithm.algorithm_settings['variables']['source']['snow_cover_hsaf']['var_method_compute']['var_name']][:]
        hsaf_lon = \
            hsaf_dset.variables[driver_algorithm.algorithm_settings['variables']['source']['snow_cover_hsaf']['var_method_compute']['lon_name']][:]
        hsaf_lat = \
            hsaf_dset.variables[
                driver_algorithm.algorithm_settings['variables']['source']['snow_cover_hsaf']['var_method_compute'][
                    'lat_name']][:]

        #scale factor for lat e lon
        hsaf_lon = hsaf_lon/driver_algorithm.algorithm_settings['variables']['source']['snow_cover_hsaf']['var_method_compute']['scale_factor_lon_lat_values']
        hsaf_lat = hsaf_lat/driver_algorithm.algorithm_settings['variables']['source']['snow_cover_hsaf']['var_method_compute']['scale_factor_lon_lat_values']

        logging.info(' --> File loaded ... ' + path_unzip)

        os.remove(path_unzip)
        logging.info(' --> Remove unzipped file ... DONE!')

        # mask and resample
        logging.info(' --> Regridding ... ')

        #remove space
        hsaf_values_unf_tmp = np.ravel(hsaf_values)
        hsaf_lon_unf_tmp = np.ravel(hsaf_lon)
        hsaf_lat_unf_tmp = np.ravel(hsaf_lat)

        space_value = driver_algorithm.algorithm_settings['variables']['source']['snow_cover_hsaf']['var_method_compute']['space_value']
        hsaf_values_unf = hsaf_values_unf_tmp[hsaf_values_unf_tmp != space_value]
        hsaf_lon_unf = hsaf_lon_unf_tmp[hsaf_values_unf_tmp != space_value]
        hsaf_lat_unf = hsaf_lat_unf_tmp[hsaf_values_unf_tmp != space_value]

        # griddata
        no_data_hsaf = \
            driver_algorithm.algorithm_settings['variables']['source']['snow_cover_hsaf']['var_method_compute'][
                'no_data_value']
        if da_domain.west_east.values.ndim == 1 and da_domain.south_north.values.ndim == 1:
            ref_grid_geo_x, ref_grid_geo_y = np.meshgrid(da_domain.west_east.values, da_domain.south_north.values)
        elif da_domain.west_east.values.ndim == 2 and da_domain.south_north.values.ndim == 2:
            ref_grid_geo_x = da_domain.west_east.values
            ref_grid_geo_y = da_domain.south_north.values
        else:
            logging.error(' ===> Reference dimensions in bed format')
            raise IOError('Geographical data format not allowed')

        hsaf_values_on_ref_grid = griddata((hsaf_lon_unf, hsaf_lat_unf), hsaf_values_unf,
                                                     (ref_grid_geo_x, ref_grid_geo_y), method='nearest',
                                                     fill_value=no_data_hsaf)

        # mask data
        logging.info(' --> Applying mask ... ')

        fx_flag_masks = \
            driver_algorithm.algorithm_settings['variables']['source']['snow_cover_hsaf']['var_method_compute'][
                'params']['flag_masks']
        fx_flag_values = \
            driver_algorithm.algorithm_settings['variables']['source']['snow_cover_hsaf']['var_method_compute'][
                'params']['flag_values']
        fx_flag_meanings = \
            driver_algorithm.algorithm_settings['variables']['source']['snow_cover_hsaf']['var_method_compute'][
                'params']['flag_meanings']
        fx_pixel_size_aggregation = \
            driver_algorithm.algorithm_settings['variables']['source']['snow_cover_hsaf']['var_method_compute'][
                'params']['pixel_size_aggregation']
        hsaf_values_on_ref_grid = hsaf_values_on_ref_grid.astype(float)
        hsaf_values_on_ref_grid = mask_data(var_data=hsaf_values_on_ref_grid,
                                                  var_geo_x=ref_grid_geo_x,
                                                  var_geo_y=ref_grid_geo_y,
                                                  ref_geo_y=ref_grid_geo_y,
                                                  ref_geo_x=ref_grid_geo_x,
                                                  ref_geo_z=da_domain.values,
                                                  var_missing_value=no_data_hsaf, fx_nodata=no_data_hsaf,
                                                  var_fill_value=no_data_hsaf,
                                                  fx_flag_masks=fx_flag_masks, fx_flag_values=fx_flag_values,
                                                  fx_flag_meanings=fx_flag_meanings,
                                                  fx_pixel_size_aggregation=fx_pixel_size_aggregation)

    else:

        logging.warning(' --> File not found! An empty dataset will be created!' + path)
        no_data_hsaf = \
            driver_algorithm.algorithm_settings['variables']['source']['snow_cover_hsaf']['var_method_compute'][
                'no_data_value']
        hsaf_values_on_ref_grid = np.empty(da_domain.shape)
        hsaf_values_on_ref_grid[:, :] = no_data_hsaf

    da = create_darray_2d(hsaf_values_on_ref_grid, da_domain.west_east, da_domain.south_north,
                          coord_name_x=da_domain.coords.dims[1], coord_name_y=da_domain.coords.dims[0],
                          dim_name_x=da_domain.coords.dims[1], dim_name_y=da_domain.coords.dims[0], name='hsaf')
    return da

# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# Method to prepare hsaf data
def blend_satellite_data(da_s2, da_modis, da_hsaf, da_domain, driver_algorithm):

    no_data_s2 = \
        driver_algorithm.algorithm_settings['variables']['source']['snow_cover_S2']['var_method_compute'][
            'no_data_value']
    no_data_modis = \
    driver_algorithm.algorithm_settings['variables']['source']['snow_cover_modis']['var_method_compute'][
        'no_data_value']
    no_data_hsaf = \
        driver_algorithm.algorithm_settings['variables']['source']['snow_cover_hsaf']['var_method_compute'][
            'no_data_value']
    no_data_destination = driver_algorithm.algorithm_settings['data']['dynamic']['destination']['no_data']

    #we use s2 as a starting point here
    s2_blended = da_s2.values
    logging.info(' --> Initial amount of no data: ' + str(np.count_nonzero(s2_blended == no_data_s2)))
    logging.info(' --> Initial amount of no data as percentage of matrix: ' + str(round(np.count_nonzero(s2_blended == no_data_s2)/s2_blended.size*100)))

    #we blend with modis first
    s2_blended = np.where((s2_blended == float(no_data_s2)), da_modis.values, s2_blended)
    logging.info(' --> Amount of no data after MODIS: ' + str(np.count_nonzero(s2_blended == no_data_modis)))
    logging.info(' --> New amount of no data as percentage of matrix: ' + str(
        round(np.count_nonzero(s2_blended == no_data_modis) / s2_blended.size * 100)))

    #now use hsaf
    s2_blended = np.where((s2_blended == float(no_data_modis)), da_hsaf.values, s2_blended)
    logging.info(' --> Amount of no data after HSAF: ' + str(np.count_nonzero(s2_blended == no_data_hsaf)))
    logging.info(' --> New amount of no data as percentage of matrix: ' + str(
        round(np.count_nonzero(s2_blended == no_data_hsaf) / s2_blended.size * 100)))

    #final cleaning
    s2_blended = np.where((s2_blended == no_data_s2), no_data_destination, s2_blended)
    s2_blended = np.where((s2_blended == no_data_modis), no_data_destination, s2_blended)
    s2_blended = np.where((s2_blended == no_data_hsaf), no_data_destination, s2_blended)

    sca_blended_da = create_darray_2d(s2_blended, da_s2.west_east, da_s2.south_north,
                          coord_name_x=da_s2.coords.dims[1], coord_name_y=da_s2.coords.dims[0],
                          dim_name_x=da_s2.coords.dims[1], dim_name_y=da_s2.coords.dims[0], name='sca_blended')
    return sca_blended_da





