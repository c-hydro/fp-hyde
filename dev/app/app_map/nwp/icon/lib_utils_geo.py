"""
Library Features:

Name:          lib_utils_geo
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20231212'
Version:       '1.0.0'
"""

# ----------------------------------------------------------------------------------------------------------------------
# libraries
import logging
import numpy as np
import pandas as pd
import pyresample

from copy import deepcopy
from repurpose.resample import resample_to_grid

from lib_info_args import logger_name

# set logger obj
alg_logger = logging.getLogger(logger_name)

# debugging
import matplotlib.pyplot as plt
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to remove nan values from points
def filter_points_nans(var_data_1d_in, var_geo_x_1d_in, var_geo_y_1d_in, var_pivot='data'):

    # organize data 1d in data frame
    var_dframe = pd.DataFrame(data={'data': var_data_1d_in, 'lon': var_geo_x_1d_in, 'lat': var_geo_y_1d_in})
    # remove nans based on data
    var_dframe.dropna(subset=[var_pivot], inplace=True)

    # get finite data, longitude and latitude
    var_data_1d_out = var_dframe['data'].values
    geo_x_1d_out = var_dframe['lon'].values
    geo_y_1d_out = var_dframe['lat'].values

    return var_data_1d_out, geo_x_1d_out, geo_y_1d_out
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to convert data grid to data swath
def convert_grid_to_swath(var_data_grid,
                          var_geo_x_grid, var_geo_y_grid, var_geo_x_swath, var_geo_y_swath,
                          search_rad=50000, neighbours=1):

    # define geometry definition(s)
    grid_obj = pyresample.geometry.GridDefinition(lons=var_geo_x_grid, lats=np.flipud(var_geo_y_grid))
    swath_obj = pyresample.geometry.SwathDefinition(lons=var_geo_x_swath, lats=var_geo_y_swath)

    # determine nearest (w.r.t. great circle distance) neighbour in the grid.
    _, _, index_array_1d, distance_array_1d = pyresample.kd_tree.get_neighbour_info(
        source_geo_def=grid_obj, target_geo_def=swath_obj, radius_of_influence=search_rad,
        neighbours=neighbours)
    index_array_2d = np.unravel_index(index_array_1d, grid_obj.shape)

    # organize data grid in data swath
    var_data_swath = var_data_grid[index_array_2d[0], index_array_2d[1]]

    return var_data_swath
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to resample grid to points
def resample_grid_to_points(obj_map, obj_cell, geo_mask, geo_x_2d, geo_y_2d,
                            var_name_dset='k1',
                            var_name_data='soil_moisture_k1', var_name_geo_x='longitude', var_name_geo_y='latitude',
                            var_min=0, var_max=1, var_no_data=-9999.0, var_filled=np.nan,
                            search_rad=50000, fill_values=np.nan, min_neighbours=1, neighbours=1,
                            debug=True):

    # check object
    obj_mask = {}
    if obj_cell is not None:

        # get geo and data values
        var_cell_x_1d = obj_cell[var_name_geo_x].values
        var_cell_y_1d = obj_cell[var_name_geo_y].values
        var_cell_data_1d_in = deepcopy(obj_cell[var_name_data].values)
        var_cell_x_2d, var_cell_y_2d = np.meshgrid(np.unique(var_cell_x_1d), np.unique(var_cell_y_1d))

        # check dataset name (if available in the object)
        if var_name_dset in list(obj_map.keys()):

            # get map values
            var_map_data_2d_in = obj_map[var_name_dset]
            var_map_tmp_2d_in = deepcopy(var_map_data_2d_in)
            var_map_tmp_1d_in = var_map_tmp_2d_in.ravel()

            var_map_data_2d_in[geo_mask == 0] = np.nan
            var_map_data_2d_in[var_map_data_2d_in < var_min] = np.nan
            var_map_data_2d_in[var_map_data_2d_in > var_max] = np.nan

            # flat data 2d values
            var_map_data_1d_in = var_map_data_2d_in.ravel()
            geo_x_1d_in = geo_x_2d.ravel()
            geo_y_1d_in = geo_y_2d.ravel()
            var_dframe = pd.DataFrame(data={'data': var_map_data_1d_in, 'lon': geo_x_1d_in, 'lat': geo_y_1d_in})
            var_dframe.dropna(subset=['data'], inplace=True)

            var_map_data_1d_finite = var_dframe['data'].values
            geo_x_1d_finite = var_dframe['lon'].values
            geo_y_1d_finite = var_dframe['lat'].values

            # resample data 2d values into grid dimension(s)
            var_map_obj = resample_to_grid(
                {'data': var_map_data_1d_finite},
                geo_x_1d_finite, geo_y_1d_finite, var_cell_x_2d, var_cell_y_2d,
                search_rad=search_rad, fill_values=fill_values,
                min_neighbours=min_neighbours, neighbours=neighbours)
            var_map_data_2d_resampled = np.flipud(var_map_obj['data'])

            mask_map_obj = resample_to_grid(
                {'data': geo_mask.ravel()},
                geo_x_1d_in, geo_y_1d_in, var_cell_x_2d, var_cell_y_2d,
                search_rad=search_rad, fill_values=fill_values,
                min_neighbours=min_neighbours, neighbours=neighbours)
            var_map_mask_2d_resampled = np.flipud(mask_map_obj['data'])

            # resample data 2d values into grid dimension(s)
            var_map_obj = resample_to_grid(
                {'data': var_map_tmp_1d_in},
                geo_x_1d_in, geo_y_1d_in, var_cell_x_2d, var_cell_y_2d,
                search_rad=search_rad, fill_values=fill_values,
                min_neighbours=min_neighbours, neighbours=neighbours)
            var_map_tmp_2d_resampled = np.flipud(var_map_obj['data'])
            var_map_tmp_2d_resampled[var_map_tmp_2d_resampled < var_min] = var_no_data
            var_map_tmp_2d_resampled[var_map_tmp_2d_resampled < var_min] = var_no_data

            # resample cell 2d values into grid dimension(s)
            var_cell_obj = resample_to_grid(
                {'data': var_cell_data_1d_in},
                var_cell_x_1d, var_cell_y_1d, var_cell_x_2d, var_cell_y_2d,
                search_rad=search_rad, fill_values=fill_values,
                min_neighbours=min_neighbours, neighbours=neighbours)
            var_cell_data_2d_resampled = np.flipud(var_cell_obj['data'])

            # define geometry definition(s)
            map_obj = pyresample.geometry.GridDefinition(lons=var_cell_x_2d, lats=np.flipud(var_cell_y_2d))
            cell_obj = pyresample.geometry.SwathDefinition(lons=var_cell_x_1d, lats=var_cell_y_1d)

            # determine nearest (w.r.t. great circle distance) neighbour in the grid.
            _, _, index_array_1d, distance_array_1d = pyresample.kd_tree.get_neighbour_info(
                source_geo_def=map_obj, target_geo_def=cell_obj, radius_of_influence=search_rad,
                neighbours=neighbours)
            index_array_2d = np.unravel_index(index_array_1d, map_obj.shape)

            # apply map condition(s)
            idx_map_nodata_2d_tmp = np.argwhere(var_map_tmp_2d_resampled == var_no_data)
            var_map_tmp_2d_resampled[idx_map_nodata_2d_tmp[:, 0], idx_map_nodata_2d_tmp[:, 1]] = var_map_data_2d_resampled[
                idx_map_nodata_2d_tmp[:, 0], idx_map_nodata_2d_tmp[:, 1]]

            # organize data 2d in data 1d (using index array)
            var_map_data_1d_resampled = var_map_tmp_2d_resampled[index_array_2d[0], index_array_2d[1]]

            # check variable boundaries (if defined)
            if var_min is not None:
                var_map_data_1d_resampled[var_map_data_1d_resampled < var_min] = np.nan
            if var_max is not None:
                var_map_data_1d_resampled[var_map_data_1d_resampled > var_max] = np.nan

            # store data 1d in object
            obj_cell[var_name_data] = var_map_data_1d_resampled
            if 'mask' not in list(obj_mask.keys()):
                obj_mask['mask'] = var_map_mask_2d_resampled

            # active debug (to check the resampled variable)
            if debug:
                alg_logger.debug(' ===> Check resampled variable ... START')

                var_debug_data_1d = obj_cell[var_name_data].values
                var_debug_x_1d = obj_cell[var_name_geo_x].values
                var_debug_y_1d = obj_cell[var_name_geo_y].values
                var_debug_x_2d, var_debug_y_2d = np.meshgrid(np.unique(var_debug_x_1d), np.unique(var_debug_y_1d))

                var_debug_obj = resample_to_grid(
                    {'data': var_debug_data_1d},
                    var_debug_x_1d, var_debug_y_1d, var_debug_x_2d, var_debug_y_2d,
                    search_rad=search_rad, fill_values=fill_values,
                    min_neighbours=min_neighbours, neighbours=neighbours)
                var_debug_data_2d = np.flipud(var_debug_obj['data'])

                mask_debug_obj = resample_to_grid(
                    {'data': geo_mask.ravel()},
                    geo_x_2d.ravel(), geo_y_2d.ravel(), var_debug_x_2d, var_debug_y_2d,
                    search_rad=search_rad, fill_values=fill_values,
                    min_neighbours=min_neighbours, neighbours=neighbours)
                mask_debug_2d = np.flipud(mask_debug_obj['data'])

                var_debug_data_2d[mask_debug_2d == 0] = np.nan

                # check data
                plot_data_2d(var_map_data_2d_in, geo_x_2d, geo_y_2d)
                plot_data_2d(var_map_tmp_2d_resampled, geo_x_2d, geo_y_2d)
                plot_data_2d(var_map_data_2d_resampled, geo_x_2d, geo_y_2d)
                plot_data_2d(var_cell_data_2d_resampled, geo_x_2d, geo_y_2d)
                plot_data_2d(var_debug_data_2d, var_cell_x_2d, var_cell_y_2d)

                alg_logger.debug(' ===> Check resampled variable ... END')

        else:
            # dataset name is not available in the object
            alg_logger.warning(' ===> Dataset name "' + var_name_dset + '" is not available in the object')
            # initialize empty variable (to avoid issues in the no data case)
            var_map_data_1d_resampled = np.zeros(shape=(var_cell_data_1d_in.shape[0]))
            var_map_data_1d_resampled[:] = var_filled
            obj_cell[var_name_data] = var_map_data_1d_resampled

    else:
        # object is empty and defined by NoneType
        alg_logger.warning(' ===> Object is defined by NoneType')

    return obj_cell

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to resample points to grid
def resample_points_to_grid(var_data_in_1d, var_geox_1d_in, var_geoy_1d_in,
                            var_geox_1d_out, var_geoy_1d_out,
                            var_mask_2d_out=None,
                            search_rad=50000, fill_values=np.nan,
                            min_neighbours=1, neighbours=4, **kwargs):

    var_geox_2d_out, var_geoy_2d_out = np.meshgrid(np.unique(var_geox_1d_out), np.unique(var_geoy_1d_out))

    # search_rad = 50000; min_neighbours = 2; neighbours = 4
    values_obj = resample_to_grid(
        {'data': var_data_in_1d},
        var_geox_1d_in, var_geoy_1d_in, var_geox_2d_out, var_geoy_2d_out,
        search_rad=search_rad, fill_values=fill_values,
        min_neighbours=min_neighbours, neighbours=neighbours)

    var_data_out = values_obj['data']
    if var_mask_2d_out is not None:
        var_data_out[var_mask_2d_out == 0] = fill_values

    return var_data_out, var_geox_2d_out, var_geoy_2d_out
# ----------------------------------------------------------------------------------------------------------------------

