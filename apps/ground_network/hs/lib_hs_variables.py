"""
Library Features:

Name:          lib_hs_variables
Author(s):     Francesco Avanzi (francesco.avanzi@cimafoundation.org), Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210525'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging
import numpy as np
from copy import deepcopy

from lib_hs_geo import find_geo_index, deg_2_km

from lib_hs_analysis_interpolation_point import interp_point2grid
from lib_hs_analysis_regression_stepwisefit import stepwisefit

from lib_hs_ancillary_snow import compute_kernel

# Debug
import matplotlib.pylab as plt
logging.getLogger('matplotlib').setLevel(logging.WARNING)
#######################################################################################

# -------------------------------------------------------------------------------------
# Method to compute snow height and snow kernel maps
def compute_snow_height(var_data, var_geo_x, var_geo_y, var_geo_z,
                        ref_geo_x, ref_geo_y, ref_geo_z, ref_cell_size, ref_epsg='4326', ref_no_data=-9999.0,
                        ref_geo_aspect=None, ref_geo_slope=None, ref_geo_hillshade=None,
                        ref_geo_homogeneous_region=None,
                        var_units='cm', var_missing_value=-9999.0, var_fill_value=-9999.0,
                        fx_nodata=-9999.0, fx_interp_name='idw', fx_min_sensor_number=10,
                        fx_interp_radius_x=None, fx_interp_radius_y=None, fx_regression_radius_influence=None,
                        fx_n_cpu=1):

    if var_units is None:
        logging.warning(' ===> Snow height variable unit is undefined; set to [cm]')
        var_units = 'cm'
    if var_units != 'cm':
        logging.warning(' ===> Snow height variable units in wrong format; expected in [cm], passed in [' +
                        var_units + ']')

    if ref_geo_homogeneous_region is None:
        ref_geo_homogeneous_region = np.zeros([var_data.shape[0], var_data.shape[1]])
        ref_geo_homogeneous_region[:, :] = 1
        logging.warning(' ===> Homogeneous-region layer not provided, all region set to 1')

    if var_data.ndim > 1:
        logging.error(' ===> Snow height variable dimensions are not allowed')
        raise IOError('Dimension must be equal to 1')

    #create mesh
    if ref_geo_x.ndim == 1 and ref_geo_y.ndim == 1:
        grid_geo_x, grid_geo_y = np.meshgrid(ref_geo_x, ref_geo_y)
    elif ref_geo_x.ndim == 2 and ref_geo_y.ndim == 2:
        grid_geo_x = ref_geo_x
        grid_geo_y = ref_geo_y
    else:
        logging.error(' ===> Reference dimensions in bad format')
        raise IOError('Data format not allowed')

    # Define geo predictors
    ref_predictors_collections = [i for i in [ref_geo_z, ref_geo_aspect, ref_geo_slope, ref_geo_hillshade] if i is not None]
    ref_predictors_n = ref_predictors_collections.__len__()

    # Convert influence radius from degree to meters
    fx_regression_radius_influence = float(int(deg_2_km(fx_regression_radius_influence) * 1000))

    # Find reference indexes for data x,y position(s)
    index_geo_x, index_geo_y = find_geo_index(ref_geo_x, ref_geo_y, var_geo_x, var_geo_y, ref_cell_size)

    # Get domain X, Y and Z (altitude)
    ref_point_x = grid_geo_x[index_geo_y, index_geo_x]
    ref_point_y = grid_geo_y[index_geo_y, index_geo_x]
    ref_point_z = ref_geo_z[index_geo_y, index_geo_x]

    # Get and remove NaNs
    ref_index_nan = np.argwhere(np.isnan(ref_point_z)).ravel()
    ref_point_x_select = np.delete(ref_point_x, ref_index_nan)
    ref_point_y_select = np.delete(ref_point_y, ref_index_nan)
    ref_point_z_select = np.delete(ref_point_z, ref_index_nan)
    var_data_select = np.delete(var_data, ref_index_nan)
    var_point_x_select = np.delete(var_geo_x, ref_index_nan)
    var_point_y_select = np.delete(var_geo_y, ref_index_nan)

    # Organize predictors dataset(s)
    ref_point_predictors_container = np.zeros(shape=[ref_point_z_select.shape[0], ref_predictors_n])
    ref_point_predictors_container[:, :] = -9999.0
    ref_grid_predictors_container = np.zeros(shape=[grid_geo_x.shape[0], grid_geo_y.shape[1], ref_predictors_n])
    ref_grid_predictors_container[:, :, :] = -9999.0
    for id_item, ref_predictors_item in enumerate(ref_predictors_collections):

        ref_point_predictors = ref_predictors_item[index_geo_y, index_geo_x]
        ref_point_predictors_select = np.delete(ref_point_predictors, ref_index_nan)
        #we delete NaNs based on ref_index_nan, so originally on the DEM

        ref_point_predictors_container[:, id_item] = ref_point_predictors_select
        ref_grid_predictors_container[:, :, id_item] = ref_predictors_item

    # Debug (to evaluate regression)
    # var_data_select = [110, 100, 80, 120, 190, 126, 100, 102, 31, 49]

    #derive homogeneous-regions information
    ref_point_homog_ID = ref_geo_homogeneous_region[index_geo_y, index_geo_x]
    homogeneous_regions_IDs = np.unique(ref_geo_homogeneous_region.flatten())
    homogeneous_regions_IDs = homogeneous_regions_IDs[~np.isnan(homogeneous_regions_IDs)]

    # Initialize snow-depth map
    grid_map_all_regions = np.zeros(shape=[grid_geo_x.shape[0], grid_geo_y.shape[1]])
    grid_map_all_regions[:, :] = np.nan
    grid_kernel_all_regions = np.zeros(shape=[grid_geo_x.shape[0], grid_geo_y.shape[1]])
    grid_kernel_all_regions[:, :] = np.nan

    for i_homog_reg, homog_region_this_round in enumerate(homogeneous_regions_IDs):

        # take data and predictors for this region
        ref_point_predictors_container_this_region = \
            ref_point_predictors_container[ref_point_homog_ID == homog_region_this_round, :]
        var_data_select_this_region = var_data_select[ref_point_homog_ID == homog_region_this_round]
        var_data_n_this_region_n = var_data_select_this_region.__len__()
        index_geo_x_this_region = index_geo_x[ref_point_homog_ID == homog_region_this_round]
        index_geo_y_this_region = index_geo_y[ref_point_homog_ID == homog_region_this_round]
        var_point_x_select_this_region = var_point_x_select[ref_point_homog_ID == homog_region_this_round]
        var_point_y_select_this_region = var_point_y_select[ref_point_homog_ID == homog_region_this_round]

        logging.info('[ Homogeneous region: ' + str(homog_region_this_round) + ']')
        logging.info('[ Available data for this homogeneous region: ' + str(var_data_n_this_region_n) + ']')

        #Determine whether to compute snow depth map or not
        if (fx_min_sensor_number is None):
            comput = True
        elif (var_data_n_this_region_n >= fx_min_sensor_number):
            comput = True
        else:
            comput = False

        if comput:
            logging.info('[ ===> Snow-depth map PRODUCED for this region! ]')

            # stepwise fit for this region
            [swf_b, swf_se, swf_pval, swf_inmodel, swf_stats, swf_nextstep, swf_history] = stepwisefit(
                ref_point_predictors_container_this_region, var_data_select_this_region, [], 0.1)

            # we force elevation if not included already!
            if not(swf_inmodel[0]):
                swf_inmodel[0]=True
                logging.warning(' ===> Elevation was not identified as predictor by stepwisefit ===> FORCED! ')

            # restrict predictor space to allowed predictors
            swf_inmodel = swf_inmodel.tolist()
            swf_inmodel_false = [idx for idx, vx in enumerate(swf_inmodel) if not vx]
            ref_point_predictors_container_this_region = \
                    np.delete(ref_point_predictors_container_this_region, swf_inmodel_false, axis=1)
            ref_grid_predictors_container_this_region = \
                    np.delete(ref_grid_predictors_container, swf_inmodel_false, axis=2)

            # Multivariate linear regression
            var_a = np.concatenate((ref_point_predictors_container_this_region,
                                    np.ones([ref_point_predictors_container_this_region.__len__(), 1])), axis=1)
            var_coeff = np.linalg.lstsq(var_a, var_data_select_this_region, rcond=None)[0]

            # Basemap
            grid_basemap_this_region = np.ones(shape=[grid_geo_x.shape[0], grid_geo_y.shape[1]])
            grid_basemap_this_region[:, :] = var_coeff[-1]
            var_coeff_reduced = var_coeff[:-1]
            for id, var_coeff_step in enumerate(var_coeff_reduced):
                grid_basemap_this_region = grid_basemap_this_region + \
                                           ref_grid_predictors_container[:, :, id] * var_coeff_step

            # Filter data to avoid nan(s) and negative value(s), as well as to restrict to this homogeneous region
            grid_basemap_this_region[grid_basemap_this_region < 0] = 0
            grid_basemap_this_region[ref_geo_homogeneous_region != homog_region_this_round] = np.nan

            # Compute residuals
            var_point_map = grid_basemap_this_region[index_geo_y_this_region, index_geo_x_this_region]
            var_point_res = var_point_map - var_data_select_this_region
            var_point_res_select = np.delete(var_point_res, np.isnan(var_point_res), axis=0)

            # Distribute residuals
            grid_data_res_this_region = interp_point2grid(var_point_res_select, var_point_x_select_this_region,
                                                          var_point_y_select_this_region,
                                              grid_geo_x, grid_geo_y,
                                              epsg_code=ref_epsg,
                                              interp_no_data=fx_nodata, interp_method=fx_interp_name,
                                              interp_radius_x=fx_interp_radius_x,
                                              interp_radius_y=fx_interp_radius_y,
                                              n_cpu=fx_n_cpu)
            grid_data_res_this_region[ref_geo_homogeneous_region != homog_region_this_round] = np.nan
            grid_data_res_this_region[grid_data_res_this_region == fx_nodata] = np.nan
            #note: we set grid_data_res_this_region to nan also where it shows missing value, because this is not the final
            #map. We will add it to basemap.

            #final map
            grid_data_this_region = grid_basemap_this_region + grid_data_res_this_region
            grid_data_this_region[grid_data_this_region < 0] = 0
            grid_map_all_regions[ref_geo_homogeneous_region == homog_region_this_round] = deepcopy(\
                grid_data_this_region[ref_geo_homogeneous_region == homog_region_this_round])

            # Kernel
            grid_kernel_this_region = compute_kernel(ref_geo_z, ref_geo_x, ref_geo_y,
                                         ref_cell_size, ref_cell_size,
                                         index_geo_x_this_region, index_geo_y_this_region, fx_regression_radius_influence)
            grid_kernel_this_region[grid_kernel_this_region < 0] = 0
            grid_kernel_this_region[grid_kernel_this_region > 1] = 1
            grid_kernel_this_region[np.isnan(grid_kernel_this_region)] = var_missing_value
            grid_kernel_all_regions[ref_geo_homogeneous_region == homog_region_this_round] = \
                deepcopy(grid_kernel_this_region[ref_geo_homogeneous_region == homog_region_this_round])

        else:
            logging.warning(' ===> Snow-depth map NOT PRODUCED for this region! ')
            grid_map_all_regions[ref_geo_homogeneous_region == homog_region_this_round] = var_missing_value
            grid_kernel_all_regions[ref_geo_homogeneous_region == homog_region_this_round] = var_missing_value


    # Final housekeeping
    grid_map_all_regions[np.isnan(ref_geo_z)] = var_fill_value
    grid_map_all_regions[np.isnan(grid_map_all_regions)] = var_fill_value
    grid_map_all_regions[ref_geo_z == var_fill_value] = var_fill_value

    grid_kernel_all_regions[ref_geo_z == ref_no_data] = var_fill_value
    grid_kernel_all_regions[np.isnan(ref_geo_z)] = var_fill_value
    grid_kernel_all_regions[np.isnan(grid_kernel_all_regions)] = var_fill_value

    return grid_map_all_regions, grid_kernel_all_regions
# -------------------------------------------------------------------------------------
