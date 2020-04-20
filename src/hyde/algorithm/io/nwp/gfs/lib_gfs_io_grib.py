# -------------------------------------------------------------------------------------
# Libraries
import xarray as xr
import logging

from src.hyde.algorithm.settings.nwp.gfs.lib_gfs_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)

# Debug
# import matplotlib.pylab as plt
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read data for ecmwf 0100
def read_data_gfs_025(file_name, var_name=None, data_filters=None,
                      tag_time='valid_time', tag_geo_x='longitude', tag_geo_y='latitude'):

    # Starting info
    log_stream.info(' --> Open file ' + file_name + ' ... ')

    # Define data filter for default configuration
    if data_filters is None:
        data_filters = {'filter_by_keys': {'dataType': 'fc'}}

    # Open datasets
    dst = xr.open_dataset(file_name, engine='cfgrib', backend_kwargs=data_filters)

    # Get variables ALL and DATA
    var_list_all = list(dst.variables)
    var_list_data = list(dst.data_vars)

    # Get time, geo x and geo y
    log_stream.info(' --->  Get time, geo_x and geo_y data ... ')
    if tag_time in var_list_all:
        da_time = dst[tag_time]
    else:
        log_stream.error(' ==> Time dimension name is not in the variables list of grib file')
        raise IOError(' ==> Check the time dimension!')
    if tag_geo_x in var_list_all:
        da_geo_x = dst[tag_geo_x]
    else:
        log_stream.error(' ==> GeoX dimension name is not in the variables list of grib file')
        raise IOError(' ==> Check the GeoX dimension!')
    if tag_geo_y in var_list_all:
        da_geo_y = dst[tag_geo_y]
    else:
        log_stream.error(' ==> GeoY dimension name is not in the variables list of grib file')
        raise IOError(' ==> Check the GeoY dimension!')
    log_stream.info(' --->  Get time, geo_x and geo_y data ... DONE')

    # Get data
    da_var = []
    for var_list_step in var_list_data:
        log_stream.info(' --->  Get ' + var_list_step + ' data ... ')
        da_step = dst[var_list_step]
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
