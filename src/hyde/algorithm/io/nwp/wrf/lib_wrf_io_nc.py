# -------------------------------------------------------------------------------------
# Libraries
import logging
import re

import xarray as xr
import pandas as pd
import numpy as np

from src.hyde.algorithm.settings.nwp.wrf.lib_wrf_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)

# Debug
# import matplotlib.pylab as plt
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read data for wrf
def read_data_wrf(file_name, var_name=None,
                  tag_coord_time='time', tag_coord_geo_x='lon', tag_coord_geo_y='lat',
                  tag_dim_time='time', tag_dim_geo_x='lon', tag_dim_geo_y='lat', engine='netcdf'):

    # Starting info
    log_stream.info(' --> Open file ' + file_name + ' ... ')

    if var_name is None:
        log_stream.error(' ===> Variable name is undefined!')
        raise IOError(' ===> Variable name is a mandatory argument!')
    else:
        if not isinstance(var_name, list):
            var_name = [var_name]

    # Open datasets
    if engine=='netcdf':
        engine='netcdf4'

    dst = xr.open_dataset(file_name, engine=engine)

    # Get variables ALL and DATA
    var_list_all = list(dst.variables)
    var_list_data = list(dst.data_vars)

    reg_exp_time = re.compile(".*" + tag_coord_time)
    match_str_time = list(filter(reg_exp_time.match, var_list_data))

    # Get time, geo x and geo y
    log_stream.info(' ---> Get time, geo_x and geo_y data ... ')
    if tag_coord_time in var_list_all:
        da_time = dst[tag_coord_time]
        match_str_step = tag_coord_time
    else:

        log_stream.info(' ---> Time dimension name is not in the variables list of grib file. '
                        'Searching for regular expression with similar names')
        if match_str_time.__len__() > 0:
            for match_str_step in match_str_time:
                log_stream.info(' ---> Searching time values using another dim name: ' + match_str_step + ' ...')
                if match_str_step in var_list_all:
                    da_time = dst[match_str_step]
                    log_stream.info(' ---> Searching time values using another dim name: ' + match_str_step +
                                    ' ... DONE')
                    break
                else:
                    log_stream.warning(' ===> Searching time values using another dim name: ' + match_str_step +
                                       ' ... FAILED')
        else:
            log_stream.error(' ===> Time dimension name is not in the variables list of grib file')
            raise IOError(' ===> Check the time dimension!')

    if len(da_time) == 1:
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
        try:
            test_time_format = np.issubdtype(da_time[0].values, np.datetime64)
            datetime_idx = pd.to_datetime(da_time.astype(int)).round('H')
        except:
            for time_byte in da_time.values:
                time_str = time_byte.decode("utf-8")
                time_period.append(time_str)
            datetime_idx = pd.to_datetime(time_period, format='%Y-%m-%d_%H:%M:%S')
            datetime_idx = datetime_idx.round('H')

        log_stream.info(' ---> Get time, geo_x and geo_y data ... DONE')

        # Get data
        da_var = []
        for var_list_step in var_list_select:
            log_stream.info(' --->  Get ' + var_list_step + ' data ... ')
            da_step = dst[var_list_step]

            if tag_coord_time not in list(da_step.coords):
                da_step = da_step.squeeze(tag_dim_time)
                da_step = da_step.expand_dims({tag_dim_time: datetime_idx})

            da_var.append(da_step)
            log_stream.info(' --->  Get ' + var_list_step + ' data ... DONE')

        # Ending info
        log_stream.info(' --> Open file ' + file_name + ' ... DONE')

    elif len(da_time)>1:
        if tag_coord_geo_x in var_list_all:
            da_geo_x_tmp = dst[tag_coord_geo_x]
            if tag_dim_time in da_geo_x_tmp.dims:
                da_geo_x = da_geo_x_tmp.loc[da_geo_x_tmp[tag_dim_time]==da_geo_x_tmp[tag_dim_time][0].values].squeeze()
            else:
                da_geo_x = da_geo_x_tmp
        else:
            log_stream.error(' ===> GeoX dimension name is not in the variables list of grib file')
            raise IOError(' ===> Check the GeoX dimension!')
        if tag_coord_geo_y in var_list_all:
            da_geo_y_tmp = dst[tag_coord_geo_y]
            if tag_dim_time in da_geo_y_tmp.dims:
                da_geo_y = da_geo_y_tmp.loc[da_geo_y_tmp[tag_dim_time]==da_geo_y_tmp[tag_dim_time][0].values].squeeze()
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

        log_stream.info(' ---> Get time, geo_x and geo_y data ... DONE')

        # Get data
        da_var = []
        for var_list_step in var_list_select:
            log_stream.info(' --->  Get ' + var_list_step + ' data ... ')
            da_var = dst[var_list_step]
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
