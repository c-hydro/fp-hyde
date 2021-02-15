"""
Library Features:

Name:          lib_ws_variables
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20201102'
Version:       '2.0.0'
"""

#######################################################################################
# Library
import logging
import numpy as np

from src.hyde.algorithm.geo.ground_network.lib_ws_geo import find_geo_index, deg_2_km

from src.hyde.algorithm.analysis.ground_network.lib_ws_analysis_interpolation_point import interp_point2grid
from src.hyde.algorithm.analysis.ground_network.lib_ws_analysis_regression_stepwisefit import stepwisefit

from src.hyde.dataset.ground_network.ws.lib_ws_ancillary_snow import compute_kernel

# Debug
import matplotlib.pylab as plt
logging.getLogger('matplotlib').setLevel(logging.WARNING)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to compute rain map
def compute_rain(var_data, var_geo_x, var_geo_y,
                 ref_geo_x, ref_geo_y, ref_geo_z, ref_epsg='4326', ref_no_data=-9999.0,
                 var_units='mm', var_missing_value=-9999.0, var_fill_value=-9999.0,
                 fx_nodata=-9999.0, fx_interp_name='idw',
                 fx_interp_radius_x=None, fx_interp_radius_y=None):

    if var_units is None:
        logging.warning(' ===> Rain variable unit is undefined; set to [mm]')
        var_units = 'mm'
    if var_units != 'mm':
        logging.warning(' ===> Rain variable units in wrong format; expected in [mm], passed in [' +
                        var_units + ']')

    if var_data.ndim > 1:
        logging.error(' ===> Rain variable dimensions are not allowed')
        raise IOError('Dimension must be equal to 1')

    if ref_geo_x.ndim == 1 and ref_geo_y.ndim == 1:
        grid_geo_x, grid_geo_y = np.meshgrid(ref_geo_x, ref_geo_y)
    elif ref_geo_x.ndim == 2 and ref_geo_y.ndim == 2:
        grid_geo_x = ref_geo_x
        grid_geo_y = ref_geo_y
    else:
        logging.error(' ===> Reference dimensions in bed format')
        raise IOError('Data format not allowed')

    # Interpolate point(s) data to grid
    grid_data = interp_point2grid(var_data, var_geo_x, var_geo_y, grid_geo_x, grid_geo_y, epsg_code=ref_epsg,
                                  interp_no_data=fx_nodata, interp_method=fx_interp_name,
                                  interp_radius_x=fx_interp_radius_x,
                                  interp_radius_y=fx_interp_radius_y)

    # Filter data nan and over domain
    grid_data[np.isnan(grid_data)] = var_missing_value
    grid_data[np.isnan(ref_geo_z)] = var_fill_value
    grid_data[ref_geo_z == ref_no_data] = np.nan

    return grid_data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute air temperature map
def compute_air_temperature(var_data, var_geo_x, var_geo_y, var_geo_z,
                            ref_geo_x, ref_geo_y, ref_geo_z, ref_epsg='4326', ref_no_data=-9999.0,
                            var_units='C', var_missing_value=-9999.0, var_fill_value=-9999.0,
                            fx_nodata=-9999.0, fx_interp_name='idw',
                            fx_interp_radius_x=None, fx_interp_radius_y=None):

    if var_units is None:
        logging.warning(' ===> Air temperature variable unit is undefined; set to [C]')
        var_units = 'C'
    if var_units != 'C':
        logging.warning(' ===> Air temperature variable units in wrong format; expected in [C], passed in [' +
                        var_units + ']')

    if var_data.ndim > 1:
        logging.error(' ===> Air temperature variable dimensions are not allowed')
        raise IOError('Dimension must be equal to 1')

    if ref_geo_x.ndim == 1 and ref_geo_y.ndim == 1:
        grid_geo_x, grid_geo_y = np.meshgrid(ref_geo_x, ref_geo_y)
    elif ref_geo_x.ndim == 2 and ref_geo_y.ndim == 2:
        grid_geo_x = ref_geo_x
        grid_geo_y = ref_geo_y
    else:
        logging.error(' ===> Reference dimensions in bed format')
        raise IOError('Data format not allowed')

    # Sort altitude(s)
    var_index_sort = np.argsort(var_geo_z)

    # Extract sorting value(s) from finite arrays
    var_geo_x_sort = var_geo_x[var_index_sort]
    var_geo_y_sort = var_geo_y[var_index_sort]
    var_geo_z_sort = var_geo_z[var_index_sort]
    var_data_sort = var_data[var_index_sort]

    # Polyfit parameters and value(s) (--> linear regression)
    var_poly_parameters = np.polyfit(var_geo_z_sort, var_data_sort, 1)
    var_poly_values = np.polyval(var_poly_parameters, var_geo_z_sort)

    # Define residual for point value(s)
    var_data_res = var_data_sort - var_poly_values

    # Interpolate point(s) data to grid
    grid_data_res = interp_point2grid(var_data_res, var_geo_x_sort, var_geo_y_sort, grid_geo_x, grid_geo_y,
                                      epsg_code=ref_epsg,
                                      interp_no_data=fx_nodata, interp_method=fx_interp_name,
                                      interp_radius_x=fx_interp_radius_x,
                                      interp_radius_y=fx_interp_radius_y)

    # Interpolate polynomial parameters on z map
    grid_poly_z = np.polyval(var_poly_parameters, ref_geo_z)

    # Calculate temperature (using z regression and idw method(s))
    grid_data = grid_poly_z + grid_data_res

    # Filter data nan and over domain
    grid_data[np.isnan(grid_data)] = var_missing_value
    grid_data[np.isnan(ref_geo_z)] = var_fill_value
    grid_data[ref_geo_z == ref_no_data] = np.nan

    # Debug
    # plt.figure()
    # plt.imshow(grid_data)
    # plt.colorbar()
    # plt.clim([-10, 30])
    # plt.show()

    return grid_data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute wind speed map
def compute_wind_speed(var_data, var_geo_x, var_geo_y,
                       ref_geo_x, ref_geo_y, ref_geo_z, ref_epsg='4326', ref_no_data=-9999.0,
                       var_units='m s-1', var_missing_value=-9999.0, var_fill_value=-9999.0,
                       fx_nodata=-9999.0, fx_interp_name='idw',
                       fx_interp_radius_x=None, fx_interp_radius_y=None):

    if var_units is None:
        logging.warning(' ===> Wind speed variable unit is undefined; set to [m s-1]')
        var_units = 'm s-1'
    if var_units != 'm s-1':
        logging.warning(' ===> Wind speed variable units in wrong format; expected in [m s-1], passed in [' +
                        var_units + ']')

    if var_data.ndim > 1:
        logging.error(' ===> Wind speed variable dimensions are not allowed')
        raise IOError('Dimension must be equal to 1')

    if ref_geo_x.ndim == 1 and ref_geo_y.ndim == 1:
        grid_geo_x, grid_geo_y = np.meshgrid(ref_geo_x, ref_geo_y)
    elif ref_geo_x.ndim == 2 and ref_geo_y.ndim == 2:
        grid_geo_x = ref_geo_x
        grid_geo_y = ref_geo_y
    else:
        logging.error(' ===> Reference dimensions in bed format')
        raise IOError('Data format not allowed')

    # Interpolate point(s) data to grid
    grid_data = interp_point2grid(var_data, var_geo_x, var_geo_y, grid_geo_x, grid_geo_y, epsg_code=ref_epsg,
                                  interp_no_data=fx_nodata, interp_method=fx_interp_name,
                                  interp_radius_x=fx_interp_radius_x,
                                  interp_radius_y=fx_interp_radius_y)

    # Filter data nan and over domain
    grid_data[np.isnan(grid_data)] = var_missing_value
    grid_data[np.isnan(ref_geo_z)] = var_fill_value
    grid_data[ref_geo_z == ref_no_data] = np.nan

    # Debug
    # plt.figure()
    # plt.imshow(grid_data)
    # plt.colorbar()
    # plt.clim([0, 10])
    # plt.show()

    return grid_data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute incoming radiation map
def compute_incoming_radiation(var_data, var_geo_x, var_geo_y,
                               ref_geo_x, ref_geo_y, ref_geo_z, ref_epsg='4326', ref_no_data=-9999.0,
                               var_units='W m-2', var_missing_value=-9999.0, var_fill_value=-9999.0,
                               fx_nodata=-9999.0, fx_interp_name='idw',
                               fx_interp_radius_x=None, fx_interp_radius_y=None):

    if var_units is None:
        logging.warning(' ===> Incoming radiation variable unit is undefined; set to [W m-2]')
        var_units = 'W m-2'
    if var_units != 'W m-2':
        logging.warning(' ===> Incoming radiation variable units in wrong format; expected in [W m-2], passed in [' +
                        var_units + ']')

    if var_data.ndim > 1:
        logging.error(' ===> Incoming radiation variable dimensions are not allowed')
        raise IOError('Dimension must be equal to 1')

    if ref_geo_x.ndim == 1 and ref_geo_y.ndim == 1:
        grid_geo_x, grid_geo_y = np.meshgrid(ref_geo_x, ref_geo_y)
    elif ref_geo_x.ndim == 2 and ref_geo_y.ndim == 2:
        grid_geo_x = ref_geo_x
        grid_geo_y = ref_geo_y
    else:
        logging.error(' ===> Reference dimensions in bed format')
        raise IOError('Data format not allowed')

    # Interpolate point(s) data to grid
    grid_data = interp_point2grid(var_data, var_geo_x, var_geo_y, grid_geo_x, grid_geo_y, epsg_code=ref_epsg,
                                  interp_no_data=fx_nodata, interp_method=fx_interp_name,
                                  interp_radius_x=fx_interp_radius_x,
                                  interp_radius_y=fx_interp_radius_y)

    # Filter data nan and over domain
    grid_data[np.isnan(grid_data)] = var_missing_value
    grid_data[np.isnan(ref_geo_z)] = var_fill_value
    grid_data[ref_geo_z == ref_no_data] = np.nan

    # Debug
    # plt.figure()
    # plt.imshow(grid_data)
    # plt.colorbar()
    # plt.clim([-50, 1200])
    # plt.show()

    return grid_data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute relative humidity map
def compute_relative_humidity(var_data, var_geo_x, var_geo_y,
                              ref_geo_x, ref_geo_y, ref_geo_z, ref_epsg='4326', ref_no_data=-9999.0,
                              var_units='%', var_missing_value=-9999.0, var_fill_value=-9999.0,
                              fx_nodata=-9999.0, fx_interp_name='idw',
                              fx_interp_radius_x=None, fx_interp_radius_y=None):

    if var_units is None:
        logging.warning(' ===> Relative humidity variable unit is undefined; set to [%]')
        var_units = '%'
    if var_units != '%':
        logging.warning(' ===> Relative humidity variable units in wrong format; expected in [%], passed in [' +
                        var_units + ']')

    if var_data.ndim > 1:
        logging.error(' ===> Relative humidity variable dimensions are not allowed')
        raise IOError('Dimension must be equal to 1')

    if ref_geo_x.ndim == 1 and ref_geo_y.ndim == 1:
        grid_geo_x, grid_geo_y = np.meshgrid(ref_geo_x, ref_geo_y)
    elif ref_geo_x.ndim == 2 and ref_geo_y.ndim == 2:
        grid_geo_x = ref_geo_x
        grid_geo_y = ref_geo_y
    else:
        logging.error(' ===> Reference dimensions in bed format')
        raise IOError('Data format not allowed')

    # Interpolate point(s) data to grid
    grid_data = interp_point2grid(var_data, var_geo_x, var_geo_y, grid_geo_x, grid_geo_y, epsg_code=ref_epsg,
                                  interp_no_data=fx_nodata, interp_method=fx_interp_name,
                                  interp_radius_x=fx_interp_radius_x,
                                  interp_radius_y=fx_interp_radius_y)

    # Filter data nan and over domain
    grid_data[np.isnan(grid_data)] = var_missing_value
    grid_data[np.isnan(ref_geo_z)] = var_fill_value
    grid_data[ref_geo_z == ref_no_data] = np.nan

    # Debug
    # plt.figure()
    # plt.imshow(grid_data)
    # plt.colorbar()
    # plt.clim([0, 100])
    # plt.show()

    return grid_data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute air pressure map
def compute_air_pressure(var_data, var_geo_x, var_geo_y,
                         ref_geo_x, ref_geo_y, ref_geo_z, ref_epsg='4326', ref_no_data=-9999.0,
                         var_units='hPa', var_missing_value=-9999.0, var_fill_value=-9999.0,
                         fx_nodata=-9999.0, fx_interp_name='idw',
                         fx_interp_radius_x=None, fx_interp_radius_y=None):

    if var_units is None:
        logging.warning(' ===> Air pressure variable unit is undefined; set to [hPa]')
        var_units = 'hPa'
    if var_units != 'hPa':
        logging.warning(' ===> Air pressure variable units in wrong format; expected in [hPa], passed in [' +
                        var_units + ']')

    if var_data.ndim > 1:
        logging.error(' ===> Air pressure variable dimensions are not allowed')
        raise IOError('Dimension must be equal to 1')

    if ref_geo_x.ndim == 1 and ref_geo_y.ndim == 1:
        grid_geo_x, grid_geo_y = np.meshgrid(ref_geo_x, ref_geo_y)
    elif ref_geo_x.ndim == 2 and ref_geo_y.ndim == 2:
        grid_geo_x = ref_geo_x
        grid_geo_y = ref_geo_y
    else:
        logging.error(' ===> Reference dimensions in bed format')
        raise IOError('Data format not allowed')

    # Interpolate point(s) data to grid
    grid_data = interp_point2grid(var_data, var_geo_x, var_geo_y, grid_geo_x, grid_geo_y, epsg_code=ref_epsg,
                                  interp_no_data=fx_nodata, interp_method=fx_interp_name,
                                  interp_radius_x=fx_interp_radius_x,
                                  interp_radius_y=fx_interp_radius_y)

    # Filter data nan and over domain
    grid_data[np.isnan(grid_data)] = var_missing_value
    grid_data[np.isnan(ref_geo_z)] = var_fill_value
    grid_data[ref_geo_z == ref_no_data] = np.nan

    # Debug
    # plt.figure()
    # plt.imshow(grid_data)
    # plt.colorbar()
    # plt.clim([-10, 30])
    # plt.show()

    return grid_data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute snow height and snow kernel maps
def compute_snow_height(var_data, var_geo_x, var_geo_y, var_geo_z,
                        ref_geo_x, ref_geo_y, ref_geo_z, ref_cell_size, ref_epsg='4326', ref_no_data=-9999.0,
                        ref_geo_aspect=None, ref_geo_slope=None, ref_geo_hillshade=None,
                        var_units='cm', var_missing_value=-9999.0, var_fill_value=-9999.0,
                        fx_nodata=-9999.0, fx_interp_name='idw',
                        fx_interp_radius_x=None, fx_interp_radius_y=None, fx_regression_radius_influence=None):

    if var_units is None:
        logging.warning(' ===> Snow height variable unit is undefined; set to [C]')
        var_units = 'cm'
    if var_units != 'cm':
        logging.warning(' ===> Snow height variable units in wrong format; expected in [C], passed in [' +
                        var_units + ']')

    if var_data.ndim > 1:
        logging.error(' ===> Snow height variable dimensions are not allowed')
        raise IOError('Dimension must be equal to 1')

    if ref_geo_x.ndim == 1 and ref_geo_y.ndim == 1:
        grid_geo_x, grid_geo_y = np.meshgrid(ref_geo_x, ref_geo_y)
    elif ref_geo_x.ndim == 2 and ref_geo_y.ndim == 2:
        grid_geo_x = ref_geo_x
        grid_geo_y = ref_geo_y
    else:
        logging.error(' ===> Reference dimensions in bed format')
        raise IOError('Data format not allowed')

    # Define geo predictors
    ref_predictors_collections = [i for i in [ref_geo_z, ref_geo_aspect, ref_geo_slope, ref_geo_hillshade] if i is not None]
    ref_predictors_n = ref_predictors_collections.__len__()

    # Convert influence radius from degree to meters
    fx_regression_radius_influence = float(int(deg_2_km(fx_regression_radius_influence) * 1000))
    # Find reference indexes for data x,y position(s)
    index_geo_x, index_geo_y = find_geo_index(ref_geo_x, ref_geo_y, var_geo_x, var_geo_y, ref_cell_size)

    # Get domain X, Y and Z (altitude)
    ref_point_x = grid_geo_x[index_geo_x, index_geo_y]
    ref_point_y = grid_geo_y[index_geo_x, index_geo_y]
    ref_point_z = ref_geo_z[index_geo_x, index_geo_y]

    ref_index_nan = np.argwhere(np.isnan(ref_point_z)).ravel()

    # Update domain values excluded nan values
    ref_point_x_select = np.delete(ref_point_x, ref_index_nan)
    ref_point_y_select = np.delete(ref_point_y, ref_index_nan)
    ref_point_z_select = np.delete(ref_point_z, ref_index_nan)
    # Update var values excluded nan values (from domain data)
    var_data_select = np.delete(var_data, ref_index_nan)
    var_point_x_select = np.delete(var_geo_x, ref_index_nan)
    var_point_y_select = np.delete(var_geo_y, ref_index_nan)

    # Organize predictors dataset(s)
    ref_point_predictors_container = np.zeros(shape=[ref_point_z_select.shape[0], ref_predictors_n])
    ref_point_predictors_container[:, :] = -9999.0
    ref_grid_predictors_container = np.zeros(shape=[grid_geo_x.shape[0], grid_geo_y.shape[1], ref_predictors_n])
    ref_grid_predictors_container[:, :, :] = -9999.0

    for id_item, ref_predictors_item in enumerate(ref_predictors_collections):
        ref_point_predictors = ref_predictors_item[index_geo_x, index_geo_y]
        ref_point_predictors_select = np.delete(ref_point_predictors, ref_index_nan)

        ref_point_predictors_container[:, id_item] = ref_point_predictors_select
        ref_grid_predictors_container[:, :, id_item] = ref_predictors_item

    # Debug (to evaluate regression)
    # var_data_select = [110, 100, 80, 120, 190, 126, 100, 102, 31, 49]

    # Fit Data using stepwise function
    [swf_b, swf_se, swf_pval, swf_inmodel, swf_stats, swf_nextstep, swf_history] = stepwisefit(
        ref_point_predictors_container, var_data_select, [], 0.1)

    # Check variable X predictor(s) availability
    swf_inmodel = swf_inmodel.tolist()
    if any(swf_inmodel):

        swf_inmodel_false = [idx for idx, vx in enumerate(swf_inmodel) if not vx]
        ref_point_predictors_container = np.delete(ref_point_predictors_container, swf_inmodel_false, axis=1)
        ref_grid_predictors_container = np.delete(ref_grid_predictors_container, swf_inmodel_false, axis=2)

    elif not any(swf_inmodel):

        ref_point_predictors_container = np.zeros(shape=[ref_point_z_select.shape[0], 1])
        ref_grid_predictors_container = np.zeros(shape=[grid_geo_x.shape[0], grid_geo_y.shape[1], 1])
        ref_point_predictors_container[:, 0] = ref_point_z_select
        ref_grid_predictors_container[:, :, 0] = ref_geo_z

    # Multivariate linear regression
    var_a = np.concatenate((ref_point_predictors_container,
                            np.ones([ref_point_predictors_container.__len__(), 1])), axis=1)
    var_coeff = np.linalg.lstsq(var_a, var_data_select, rcond=None)[0]

    # Define basemap
    grid_basemap = np.ones(shape=[grid_geo_x.shape[0], grid_geo_y.shape[1]])
    grid_basemap[:, :] = var_coeff[-1]

    var_coeff_reduced = var_coeff[:-1]
    for id, var_coeff_step in enumerate(var_coeff_reduced):
        grid_basemap = grid_basemap + ref_grid_predictors_container[:, :, id] * var_coeff_step

    # Filter data to avoid nan(s) and negative value(s)
    grid_basemap[np.isnan(grid_basemap)] = -1
    grid_basemap[grid_basemap < 0] = 0

    var_point_map = grid_basemap[index_geo_x, index_geo_y]
    var_point_map_select = np.delete(var_point_map, ref_index_nan)
    var_point_res_select = var_point_map_select - var_data_select

    # Interpolate point(s) data to grid
    grid_data_res = interp_point2grid(var_point_res_select, var_point_x_select, var_point_y_select,
                                      grid_geo_x, grid_geo_y,
                                      epsg_code=ref_epsg,
                                      interp_no_data=fx_nodata, interp_method=fx_interp_name,
                                      interp_radius_x=fx_interp_radius_x,
                                      interp_radius_y=fx_interp_radius_y)
    # Calculate data grid
    grid_data = grid_basemap + grid_data_res
    grid_data[np.isnan(grid_data)] = var_missing_value
    grid_data[np.isnan(ref_geo_z)] = var_fill_value
    grid_data[ref_geo_z == ref_no_data] = np.nan

    # Compute kernel data
    grid_kernel = compute_kernel(ref_geo_z, ref_geo_x, ref_geo_y,
                                 ref_cell_size, ref_cell_size,
                                 index_geo_x, index_geo_y, fx_regression_radius_influence)
    grid_kernel[np.isnan(grid_kernel)] = var_missing_value
    grid_kernel[np.isnan(ref_geo_z)] = var_fill_value
    grid_kernel[ref_geo_z == ref_no_data] = np.nan

    grid_data = grid_data * grid_kernel

    # Debug
    # plt.figure()
    # plt.imshow(grid_data)
    # plt.colorbar()
    # plt.clim([0, 50])
    # plt.show()
    # plt.figure()
    # plt.imshow(grid_kernel)
    # plt.colorbar()
    # plt.clim([0, 1])
    # plt.show()

    return grid_data, grid_kernel
# -------------------------------------------------------------------------------------
