# -------------------------------------------------------------------------------------
# Libraries
import logging
import re

import xarray as xr
import pandas as pd

from src.hyde.algorithm.settings.satellite.gsmap.lib_gsmap_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)

# Debug
# import matplotlib.pylab as plt
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read data for gsmap
def read_data_gsmap(file_name, var_name=None,
                  tag_coord_time='time', tag_coord_geo_x='lon', tag_coord_geo_y='lat',
                  tag_dim_time='time', tag_dim_geo_x='lon', tag_dim_geo_y='lat'):

    # Starting info
    log_stream.info(' --> Open file ' + file_name + ' ... ')

    if var_name is None:
        log_stream.error(' ===> Variable name is undefined!')
        raise IOError(' ===> Variable name is a mandatory argument!')
    else:
        if not isinstance(var_name, list):
            var_name = [var_name]

    # Open datasets
    dst = xr.open_dataset(file_name)

    # Get variables ALL and DATA
    var_list_all = list(dst.variables)
    var_list_data = list(dst.data_vars)

    # Get time, geo x and geo y
    log_stream.info(' ---> Get time, geo_x and geo_y data ... ')
    if tag_coord_time in var_list_all:
        da_time = dst[tag_coord_time]
    else:
        log_stream.error(' ===> Time dimension name is not in the variables list of grib file')
        raise IOError(' ===> Check the time dimension!')

    if tag_coord_geo_x in var_list_all:
        da_geo_x_tmp = dst[tag_coord_geo_x]
        if tag_dim_time in da_geo_x_tmp.dims:
            da_geo_x = da_geo_x_tmp.squeeze(tag_dim_time)
        else:
            da_geo_x = da_geo_x_tmp
    else:
        log_stream.error(' ===> GeoX dimension name is not in the variables list of grib file')
        raise IOError(' ===> Check the GeoX dimension!')
    if tag_coord_geo_y in var_list_all:
        da_geo_y_tmp = dst[tag_coord_geo_y]
        if tag_dim_time in da_geo_y_tmp.dims:
            da_geo_y = da_geo_y_tmp.squeeze(tag_dim_time)
        else:
            da_geo_y = da_geo_y_tmp
    else:
        log_stream.error(' ===> GeoY dimension name is not in the variables list of grib file')
        raise IOError(' ===> Check the GeoY dimension!')
    log_stream.info(' --->  Get time, geo_x and geo_y data ... DONE')

    var_list_select = []
    for var_step in var_name:
        if var_step in var_list_data:
            var_list_select.append(var_step)
        else:
            log_stream.warning(' ===> Variable name ' + var_step + ' is not available in the datasets')

    time_period = []
    for time_step in da_time.values:
        time_period.append(time_step)
    datetime_idx = pd.to_datetime(time_period, format='%Y-%m-%dT%H:%M:%S')
    datetime_idx = datetime_idx.round('H')

    log_stream.info(' ---> Get time, geo_x and geo_y data ... DONE')

    # Get data
    da_var = []
    for var_list_step in var_list_select:
        log_stream.info(' --->  Get ' + var_list_step + ' data ... ')

        da_step = dst[var_list_step]
        da_step.coords[tag_coord_time] = datetime_idx
        da_var.append(da_step)

        log_stream.info(' --->  Get ' + var_list_step + ' data ... DONE')

    # Ending info
    log_stream.info(' --> Open file ' + file_name + ' ... DONE')

    # Start Debug
    # mat = da_values[0].values
    # plt.figure()
    # plt.imshow(mat[0,:,:])
    # plt.colorbar()
    # plt.show()
    # End Debug

    return da_var, da_time, da_geo_x, da_geo_y
# -------------------------------------------------------------------------------------
