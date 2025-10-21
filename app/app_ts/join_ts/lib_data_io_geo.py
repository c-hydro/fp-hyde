"""
Library Features:

Name:          lib_data_io_geo
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20230307'
Version:       '1.0.0'
"""
# ----------------------------------------------------------------------------------------------------------------------
# Library
import logging
import os

import numpy as np
import pandas as pd
import rasterio
from rasterio.crs import CRS

from lib_info_args import logger_name
from lib_info_args import (geo_coord_name_x, geo_coord_name_y,
                           geo_var_name_x, geo_var_name_y,
                           geo_dim_name_x, geo_dim_name_y)
from lib_utils_obj import create_darray_2d, sanitize_string

# set logger level
logging.getLogger('rasterio').setLevel(logging.WARNING)
# set logger obj
alg_logger = logging.getLogger(logger_name)

# debug
# import matplotlib.pylab as plt
# ----------------------------------------------------------------------------------------------------------------------##


# ----------------------------------------------------------------------------------------------------------------------
# method to check grid data
def check_obj_data(data_file_name, data_obj=None, data_attrs=None, data_mandatory=True):
    if (data_obj is None) and (data_attrs is None):
        if data_mandatory:
            alg_logger.error(' ===> Data object "' + data_file_name + '" is not available')
            raise FileNotFoundError('File is mandatory to correctly run the algorithm')
        else:
            alg_logger.warning(' ===> Data object "' + data_file_name + '" is not available')
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to read point data
def read_point_data(file_name, file_filters=None,
                    file_delimiter=',', file_header=0, file_columns_remap=None,
                    file_units_default='%', file_description_default='NA',
                    file_location_default='NA', file_tag_default='NA',
                    file_amm_level_1_default='NA', file_amm_level_2_default='NA'):

    if file_columns_remap is None:
        file_columns_remap = {"altitude": "altitude", "amm_level_1": "amm_level_1", "amm_level_2": "amm_level_2",
                              "code": "code", "longitude": "longitude", "latitude": "latitude",
                              "description": "description", "name": "name", "valid": "valid",
                              "units": "units", "location": "locations", "tag": "tag"}
    remap_keys, remap_values = list(file_columns_remap.keys()), list(file_columns_remap.values())

    df_point = pd.read_csv(file_name, delimiter=file_delimiter, header=file_header)
    df_point.columns = df_point.columns.str.replace(' ', '')
    columns_keys = list(df_point.columns)

    df_remap = {}
    for remap_key, remap_value in zip(remap_keys, remap_values):
        if remap_value in columns_keys:
            df_remap[remap_value] = remap_key
        else:
            alg_logger.warning(' ===> Column "' + remap_value + '" is not available in the source registry')

    df_point_remap = df_point.rename(columns=df_remap)

    select_keys, select_values = list(df_remap.keys()), list(df_remap.values())
    if "units" not in columns_keys:
        df_point_remap['units'] = file_units_default
        select_values.append('units')
    if "description" not in columns_keys:
        df_point_remap['description'] = file_description_default
        select_values.append('description')
    if "location" not in columns_keys:
        df_point_remap['location'] = file_location_default
        select_values.append('location')
    if "tag" not in columns_keys:
        df_point_remap['tag'] = file_tag_default
        select_values.append('tag')
    if "amm_level_1" not in columns_keys:
        df_point_remap['amm_level_1'] = file_amm_level_1_default
        select_values.append('amm_level_1')
    if "amm_level_2" not in columns_keys:
        df_point_remap['amm_level_2'] = file_amm_level_2_default
        select_values.append('amm_level_2')

    df_point_remap['name'] = df_point_remap['name'].str.strip()
    df_point_remap['description'] = df_point_remap['description'].str.strip()
    df_point_remap['amm_level_1'] = df_point_remap['amm_level_1'].str.strip()
    df_point_remap['amm_level_2'] = df_point_remap['amm_level_2'].str.strip()
    df_point_remap['tag'] = df_point_remap['tag'].str.strip()

    select_values = list(set(select_values))

    df_point_select = df_point_remap[select_values]

    if 'valid' in list(df_point_remap.columns):
        df_point_select = df_point_select.loc[df_point_remap['valid'] == 1]

    if 'tag' in list(df_point_remap.columns):
        if all(df_point_remap['tag'] == 'NA'):

            point_name = df_point_select['name']
            list_tag = []
            for string_name in point_name.values:
                string_tag = sanitize_string(string_name)
                list_tag.append(string_tag)

            df_point_select['tag'] = list_tag

    if file_filters is not None:
        for filter_key, filter_value in file_filters.items():
            if filter_key in list(df_point_select.columns):
                filter_data = df_point_select[filter_key].values
                filter_id_list = []
                for filter_id_step, filter_row in enumerate(filter_data):
                    filter_value = str(filter_value)
                    if filter_value in filter_row:
                        filter_id_list.append(filter_id_step)

                df_point_select = df_point_select.loc[filter_id_list]

    return df_point_select
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to read grid data
def read_grid_data(file_name, output_format='data_array', output_dtype='float32',
                   var_limit_min=None, var_limit_max=None, var_proj='EPSG:4326',
                   coord_name_x=geo_coord_name_x, coord_name_y=geo_coord_name_y,
                   dim_name_x=geo_dim_name_x, dim_name_y=geo_dim_name_y, binary_mask=False):

    try:
        dset = rasterio.open(file_name)
        bounds, res, transform = dset.bounds, dset.res, dset.transform
        data = dset.read()

        if dset.crs is None:
            crs = CRS.from_string(var_proj)
        else:
            crs = dset.crs

        if output_dtype == 'float32':
            values = np.float32(data[0, :, :])
        else:
            alg_logger.error(' ===> Data type is not allowed.')
            raise NotImplementedError('Case not implemented yet')

        if var_limit_min is not None:
            var_limit_min = np.float32(var_limit_min)
            values[values < var_limit_min] = np.nan
        if var_limit_max is not None:
            var_limit_max = np.float32(var_limit_max)
            values[values > var_limit_max] = np.nan

        if binary_mask:
            values[(values >= 0) & (values <= 1)] = 1
            values[values < 0] = 0
            values[values > 1] = 0
            values[np.isnan(values)] = 0

        decimal_round_geo = 7
        # 6.5199,47.2175
        center_right = bounds.right - (res[0] / 2)
        center_left = bounds.left + (res[0] / 2)
        center_top = bounds.top - (res[1] / 2)
        center_bottom = bounds.bottom + (res[1] / 2)

        if center_bottom > center_top:
            alg_logger.warning(' ===> Coords "center_bottom": ' + str(center_bottom) + ' is greater than "center_top": '
                            + str(center_top) + '. Try to inverse the bottom and top coords. ')
            center_tmp = center_top
            center_top = center_bottom
            center_bottom = center_tmp

        lon = np.arange(center_left, center_right + np.abs(res[0] / 2), np.abs(res[0]), float)
        lat = np.flip(np.arange(center_bottom, center_top + np.abs(res[1] / 2), np.abs(res[1]), float), axis=0)
        lons, lats = np.meshgrid(lon, lat)

        lat_upper = lats[0, 0]
        lat_lower = lats[-1, 0]
        if lat_lower > lat_upper:
            lats = np.flipud(lats)
            values = np.flipud(values)

        min_lon_round = round(np.min(lons), decimal_round_geo)
        max_lon_round = round(np.max(lons), decimal_round_geo)
        min_lat_round = round(np.min(lats), decimal_round_geo)
        max_lat_round = round(np.max(lats), decimal_round_geo)

        center_right_round = round(center_right, decimal_round_geo)
        center_left_round = round(center_left, decimal_round_geo)
        center_bottom_round = round(center_bottom, decimal_round_geo)
        center_top_round = round(center_top, decimal_round_geo)

        assert min_lon_round == center_left_round
        assert max_lon_round == center_right_round
        assert min_lat_round == center_bottom_round
        assert max_lat_round == center_top_round

        data_attrs = {'transform': transform, 'crs': crs,
                      'bbox': [bounds.left, bounds.bottom, bounds.right, bounds.top],
                      'bb_left': bounds.left, 'bb_right': bounds.right,
                      'bb_top': bounds.top, 'bb_bottom': bounds.bottom,
                      'res_lon': res[0], 'res_lat': res[1]}

        if output_format == 'dictionary':

            data_var = {'values': values, geo_var_name_x: lons[0, :], geo_var_name_y: lats[:, 0]}
            data_obj = {**data_var, **data_attrs}

        elif output_format == 'data_array':

            data_obj = create_darray_2d(
                values, lons[0, :], lats[:, 0],
                coord_name_x=coord_name_x, coord_name_y=coord_name_y,
                dim_name_x=dim_name_x, dim_name_y=dim_name_y)

            data_obj.attrs = data_attrs
        else:

            alg_logger.error(' ===> File static "' + file_name + '" output format not allowed')
            raise NotImplementedError('Case not implemented yet')

    except IOError as io_error:

        data_obj, data_attrs = None, None
        alg_logger.warning(' ===> File static grid was not correctly open with error "' + str(io_error) + '"')
        logging.warning(' ===> Filename "' + os.path.split(file_name)[1] + '"')

    return data_obj, data_attrs
# ----------------------------------------------------------------------------------------------------------------------
