"""
Library Features:

Name:          lib_utils_io_nc
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20230727'
Version:       '1.0.0'
"""

# ----------------------------------------------------------------------------------------------------------------------
# libraries
import logging
import os
import time
import numpy as np
import pandas as pd
import xarray as xr

from datetime import datetime
from netCDF4 import Dataset
from netCDF4 import date2num, num2date

from copy import deepcopy

from lib_info_args import logger_name, time_calendar, time_units, time_format_datasets as time_format
from lib_info_args import (crs_epsg_code, crs_grid_mapping_name, crs_longitude_of_prime_meridian,
                           crs_semi_major_axis, crs_inverse_flattening)
from lib_info_args import (file_conventions, file_title, file_institution, file_references, file_web_site,
                           file_comment, file_history, file_source, file_email, file_project_info, file_algorithm)

from lib_utils_io import create_darray

# set logger
alg_logger = logging.getLogger(logger_name)

# debug
import matplotlib.pylab as plt

# default netcdf encoded attributes
attrs_encoded = ["_FillValue", "dtype", "scale_factor", "add_offset", "grid_mapping"]
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to organize nc file (xarray)
def organize_file_nc_xarray(
        obj_variable, obj_time=None, obj_geo_x=None, obj_geo_y=None,
        obj_var_name=None,
        var_name_time='time', var_name_geo_x='longitude', var_name_geo_y='latitude',
        coord_name_time='time', coord_name_x='longitude', coord_name_y='latitude',
        dim_name_time='time', dim_name_x='longitude', dim_name_y='latitude'):

    # check data
    if not isinstance(obj_variable, xr.Dataset):

        # organize variable name(s)
        if obj_var_name is None:
            obj_var_name = {}

        # organize time information
        var_data_time = None
        if obj_time is not None:
            if isinstance(obj_time, str):
                var_data_time = pd.DatetimeIndex([pd.Timestamp(obj_time)])
            elif isinstance(obj_time, pd.DatetimeIndex):
                var_data_time = deepcopy(obj_time)
            elif isinstance(obj_time, pd.Timestamp):
                var_data_time = pd.DatetimeIndex([obj_time])
            elif isinstance(obj_time, np.ndarray):
                var_data_time = pd.DatetimeIndex(obj_time)
            else:
                alg_logger.error(' ===> Time obj format is not supported')
                raise NotImplemented('Case not implemented yet')

        # organize geo information
        var_geo_x_1d = np.unique(obj_geo_x.flatten())
        var_geo_y_1d = np.unique(obj_geo_y.flatten())

        # iterate over variable(s)
        variable_dset = xr.Dataset()
        for variable_name, variable_data in obj_variable.items():

            if variable_name in list(obj_var_name.keys()):
                variable_name = obj_var_name[variable_name]

            variable_da = create_darray(
                variable_data, obj_geo_x, obj_geo_y,
                geo_1d=True, time=var_data_time,
                coord_name_x=coord_name_x, coord_name_y=coord_name_y, coord_name_time=coord_name_time,
                dim_name_x=dim_name_x, dim_name_y=dim_name_y, dim_name_time=dim_name_time)

            variable_dset[variable_name] = variable_da.copy()

    else:
        variable_dset = obj_variable.copy()

    return variable_dset
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to read nc file
def read_file_nc(file_name, file_variables=None, file_time_reference=None,
                 var_name_geo_x='longitude', var_name_geo_y='latitude',
                 var_name_obs='obs',
                 var_time_creation='date_created_utc',
                 var_time_sensing_start='sensing_start_time_utc', var_time_sensing_end='sensing_end_time_utc'):

    # check file availability
    if os.path.exists(file_name):

        # check file time reference format
        if not isinstance(file_time_reference, pd.Timestamp):
            file_time_reference = pd.Timestamp(file_time_reference)

        # open file
        file_dset = xr.open_dataset(file_name)
        file_n_obs = file_dset.coords[var_name_obs].shape[0]

        # organize attrs obj
        attrs_obj = file_dset.attrs

        # organize time object
        time_creation, time_sensing_start, time_sensing_end = None, None, None
        if var_time_creation in list(attrs_obj):
            time_creation = attrs_obj[var_time_creation]
        if var_time_sensing_start in list(attrs_obj):
            time_sensing_start = attrs_obj[var_time_sensing_start]
        if var_time_sensing_end in list(attrs_obj):
            time_sensing_end = attrs_obj[var_time_sensing_end]

        time_obj = {'time_creation': time_creation, 'time_reference': file_time_reference,
                    'time_sensing_start': time_sensing_start, 'time_sensing_end': time_sensing_end}

        # organize data and geo object(s)
        data_obj, geo_obj = {}, {}
        for var_name_out, var_name_in in file_variables.items():
            if var_name_out == var_name_geo_x:
                geo_obj[var_name_out] = file_dset[var_name_in].values
            if var_name_out == var_name_geo_y:
                geo_obj[var_name_out] = file_dset[var_name_in].values

            if var_name_in != var_name_geo_x or var_name_in != var_name_geo_y:
                if var_name_in in list(file_dset.data_vars):
                    tmp_values = file_dset[var_name_in].values
                    data_values = np.squeeze(tmp_values)

                    ''' debug
                    plt.figure()
                    plt.imshow(data_values)
                    plt.colorbar()
                    plt.show()
                    '''

                    data_obj[var_name_out] = data_values
                else:
                    if var_name_in not in [var_name_geo_x, var_name_geo_y]:
                        alg_logger.warning(' ===> Variable "' + var_name_in + '" not found in the dataset')

        # add time creation
        time_creation_arr = [pd.Timestamp(time_creation)] * file_n_obs
        data_obj['time_creation'] = time_creation_arr

    else:
        alg_logger.warning(' ===> File name "' + file_name + '" not found')
        data_obj, attrs_obj, geo_obj, time_obj = None, None, None, None

    return data_obj, attrs_obj, geo_obj, time_obj

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# organize nc file (netcdf library)
def organize_file_nc_library(dset_variable, dset_attrs=None,
                             geo_system_attrs=None, geo_x_attrs=None, geo_y_attrs=None,
                             dset_map=None):

    # get variable(s) and map(s)
    variable_in_list, variable_out_list = list(dset_map.keys()), list(dset_map.values())
    variable_dset_list = list(dset_variable.variables)
    variable_dset_default = ['time', 'south_north', 'west_east']
    variable_attrs_default = [
        'units', 'long_name', 'standard_name', 'fill_value', 'missing_value', 'format']

    attrs_default = {'fill_value': -9999.0, 'missing_value': -9999.0, 'format': 'f4',
                     'standard_name': 'undefined', 'long_name': 'undefined', 'units': 'undefined',
                     'scale_factor': 1,
                     'grid_mapping': 'crs', 'coordinates': 'latitude longitude'}

    # rename variables
    for variable_in_step, variable_out_step in zip(variable_in_list, variable_out_list):
        if variable_in_step in list(dset_variable.keys()):
            dset_variable = dset_variable.rename({variable_in_step: variable_out_step})
        else:
            alg_logger.warning(' ===> Variable "' + variable_in_step + '" not found in the dataset')

        if variable_in_step in list(dset_attrs.keys()):
            attrs_variable = dset_attrs[variable_in_step]
            attrs_selected = {}
            for attrs_name in variable_attrs_default:
                if attrs_name in list(attrs_variable.keys()):
                    attrs_selected[attrs_name] = attrs_variable[attrs_name]

            attrs_defined = {**attrs_default, **attrs_selected}

            dset_attrs[variable_out_step] = attrs_defined
            dset_attrs.pop(variable_in_step)

    # drop variables
    variable_drop = []
    for variable_dset_step in variable_dset_list:
        if variable_dset_step not in variable_in_list:
            if variable_dset_step not in variable_dset_default:
                variable_drop.append(variable_dset_step)

    # filter variables and attributes
    dset_variable = dset_variable.drop(variable_drop)
    for variable_step in variable_drop:
        dset_attrs.pop(variable_step)

    # set geographical attributes
    if geo_system_attrs is None:
        geo_system_attrs = {
            'epsg_code': crs_epsg_code,
            'grid_mapping_name': crs_grid_mapping_name,
            'longitude_of_prime_meridian': crs_longitude_of_prime_meridian,
            'semi_major_axis': crs_semi_major_axis,
            'inverse_flattening': crs_inverse_flattening
        }

    if geo_x_attrs is None:
        geo_x_attrs = {'units': 'degrees_east', 'long_name': 'longitude', 'format': 'f4'}
    if geo_y_attrs is None:
        geo_y_attrs = {'units': 'degrees_north', 'long_name': 'latitude', 'format': 'f4'}

    return dset_variable, dset_attrs, geo_system_attrs, geo_x_attrs, geo_y_attrs

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to write nc file (netcdf library)
def write_file_nc_library(file_name, dset_data, dset_attrs, dset_time,
                          dset_geo_x, dset_geo_y,
                          geo_system_attrs=None, geo_x_attrs=None, geo_y_attrs=None,
                          file_format='NETCDF4',
                          variable_compression_flag=True, variable_compression_level=5,
                          var_name_geo_system='crs',
                          var_name_time='time', var_name_geo_x='longitude', var_name_geo_y='latitude',
                          var_dim_time='time', var_dim_x='west_east', var_dim_y='south_north',
                          var_type_time='float64', var_type_geo_x='float64', var_type_geo_y='float64'):

    # get dimensions
    dset_dims = dset_data.dims
    n_cols, n_rows, n_time = dset_dims['longitude'], dset_dims['latitude'], dset_dims['time']
    # get geographical coordinates
    geo_x, geo_y = deepcopy(dset_geo_x), deepcopy(dset_geo_y)

    # Define time dimension
    if not isinstance(dset_time, pd.DatetimeIndex):
        dset_time = pd.DataFrame(dset_time)
    time_steps = len(dset_time)

    # define time reference
    time_period = np.array(dset_time.values)
    time_labels = []
    for time_step in time_period:
        time_tmp = pd.to_datetime(str(time_step[0])).strftime(time_format)
        time_labels.append(time_tmp)
    time_start = time_labels[0]
    time_end = time_labels[-1]

    # Generate datetime from time(s)
    date_list = []
    for i, time_step in enumerate(time_period):

        date_stamp = pd.to_datetime(str(time_step[0]))
        date_str = date_stamp.strftime(time_format)

        date_list.append(datetime(int(date_str[0:4]), int(date_str[4:6]),
                                  int(date_str[6:8]), int(date_str[8:10]), int(date_str[10:12])))

    # open file
    file_handle = Dataset(file_name, 'w', format=file_format)

    # create dimensions
    file_handle.createDimension('west_east', n_cols)
    file_handle.createDimension('south_north', n_rows)
    file_handle.createDimension('time', n_time)
    file_handle.createDimension('nsim', 1)
    file_handle.createDimension('ntime', 2)
    file_handle.createDimension('nens', 1)

    # add file attributes
    file_handle.filedate = 'Created ' + time.ctime(time.time())
    file_handle.Conventions = file_conventions
    file_handle.title = file_title
    file_handle.institution = file_institution
    file_handle.source = file_source
    file_handle.history = file_history
    file_handle.references = file_references
    file_handle.comment = file_comment
    file_handle.email = file_email
    file_handle.web_site = file_web_site
    file_handle.project_info = file_project_info
    file_handle.algorithm = file_algorithm

    # variable time
    variable_time = file_handle.createVariable(
        varname=var_name_time, dimensions=(var_dim_time,), datatype=var_type_time)
    variable_time.calendar = time_calendar
    variable_time.units = time_units
    variable_time.time_date = time_labels
    variable_time.time_start = time_start
    variable_time.time_end = time_end
    variable_time.time_steps = time_steps
    variable_time.axis = 'T'
    variable_time[:] = date2num(date_list, units=variable_time.units, calendar=variable_time.calendar)

    # debug
    # date_check = num2date(variable_time[:], units=variable_time.units, calendar=variable_time.calendar)
    # print(date_check)

    # variable geo x
    variable_geo_x = file_handle.createVariable(
        varname='longitude', dimensions=(var_dim_y, var_dim_x), datatype=var_type_geo_x,
        zlib=variable_compression_flag, complevel=variable_compression_level)
    if geo_x_attrs is not None:
        for attr_key, attr_value in geo_x_attrs.items():
            if attr_key == 'fill_value':
                fill_value = attr_value
                variable_geo_x.setncattr(attr_key.lower(), float(attr_value))
            elif attr_key == 'scale_factor':
                scale_factor = attr_value
                variable_geo_x.setncattr(attr_key.lower(), float(attr_value))
            elif attr_key == 'units':
                variable_geo_x.setncattr(attr_key.lower(), str(attr_value))
            elif attr_key == 'format':
                variable_geo_x.setncattr(attr_key.lower(), str(attr_value))
            else:
                variable_geo_x.setncattr(attr_key.lower(), str(attr_value).lower())
    variable_geo_x[:, :] = np.transpose(np.rot90(geo_x, -1))

    # variable geo y
    variable_geo_y = file_handle.createVariable(
        varname='latitude', dimensions=(var_dim_y, var_dim_x), datatype=var_type_geo_y,
        zlib=variable_compression_flag, complevel=variable_compression_level)
    if geo_y_attrs is not None:
        for attr_key, attr_value in geo_y_attrs.items():
            if attr_key == 'fill_value':
                fill_value = attr_value
                variable_geo_y.setncattr(attr_key.lower(), float(attr_value))
            elif attr_key == 'scale_factor':
                scale_factor = attr_value
                variable_geo_y.setncattr(attr_key.lower(), float(attr_value))
            elif attr_key == 'units':
                variable_geo_y.setncattr(attr_key.lower(), str(attr_value))
            elif attr_key == 'format':
                variable_geo_y.setncattr(attr_key.lower(), str(attr_value))
            else:
                variable_geo_y.setncattr(attr_key.lower(), str(attr_value).lower())
    variable_geo_y[:, :] = np.transpose(np.rot90(geo_y, -1))

    # variable geo system
    variable_geo_system = file_handle.createVariable(var_name_geo_system, 'i')
    if geo_system_attrs is not None:
        for attr_key, attr_value in geo_system_attrs.items():
            if attr_key == 'fill_value':
                fill_value = attr_value
                variable_geo_system.setncattr(attr_key.lower(), float(attr_value))
            elif attr_key == 'scale_factor':
                scale_factor = attr_value
                variable_geo_system.setncattr(attr_key.lower(), float(attr_value))
            elif attr_key == 'units':
                variable_geo_system.setncattr(attr_key.lower(), str(attr_value))
            elif attr_key == 'format':
                variable_geo_system.setncattr(attr_key.lower(), str(attr_value))
            else:
                variable_geo_system.setncattr(attr_key.lower(), str(attr_value).lower())

    # iterate over variables
    for variable_name in dset_data.data_vars:

        variable_data = dset_data[variable_name].values
        variable_dims = variable_data.ndim

        variable_attrs = {}
        if variable_name in list(dset_attrs.keys()):
            variable_attrs = dset_attrs[variable_name]

        variable_format = 'f4'
        if 'format' in list(variable_attrs.keys()):
            variable_format = variable_attrs['format']

        fill_value = None
        if 'fill_value' in list(variable_attrs.keys()):
            fill_value = variable_attrs['fill_value']
        scale_factor = 1
        if 'scale_factor' in list(variable_attrs.keys()):
            scale_factor = variable_attrs['scale_factor']

        if variable_dims == 3:
            var_handle = file_handle.createVariable(
                varname=variable_name, datatype=variable_format, fill_value=fill_value,
                dimensions=(var_dim_time, var_dim_y, var_dim_x),
                zlib=variable_compression_flag, complevel=variable_compression_level)
        elif variable_dims == 2:
            var_handle = file_handle.createVariable(
                varname=variable_name, datatype=variable_format, fill_value=fill_value,
                dimensions=(var_dim_y, var_dim_x),
                zlib=variable_compression_flag, complevel=variable_compression_level)
        else:
            raise NotImplementedError('Case not implemented yet')

        fill_value, scale_factor = -9999.0, 1
        for attr_key, attr_value in variable_attrs.items():
            if attr_key not in ['add_offset']:
                if attr_key == 'fill_value':
                    fill_value = attr_value
                    var_handle.setncattr(attr_key.lower(), float(attr_value))
                elif attr_key == 'scale_factor':
                    scale_factor = attr_value
                    var_handle.setncattr(attr_key.lower(), float(attr_value))
                elif attr_key == 'units':
                    var_handle.setncattr(attr_key.lower(), str(attr_value))
                elif attr_key == 'format':
                    var_handle.setncattr(attr_key.lower(), str(attr_value))
                else:
                    var_handle.setncattr(attr_key.lower(), str(attr_value).lower())

        if variable_dims == 3:

            variable_tmp = np.zeros((n_time, n_rows, n_cols))
            for i, t in enumerate(dset_time.values):
                tmp_data = variable_data[i, :, :]
                tmp_data = np.transpose(np.rot90(tmp_data, -1))
                variable_tmp[i, :, :] = tmp_data

                '''
                import matplotlib
                matplotlib.use('TkAgg')
                plt.figure()
                plt.imshow(dset_data[variable_name].values[i, :, :])
                plt.colorbar(); plt.clim(2, 20)
                plt.figure()
                plt.imshow(variable_data[i, :, :])
                plt.colorbar(); plt.clim(2, 20)
                plt.figure()
                plt.imshow(tmp_data)
                plt.colorbar(); plt.clim(2, 20)
                plt.figure()
                plt.imshow(variable_tmp[i, :, :])
                plt.colorbar(); plt.clim(2, 20)
                plt.show()
                '''

            variable_tmp[np.isnan(variable_tmp)] = fill_value
            var_handle[:, :, :] = variable_tmp

        elif variable_dims == 2:
            variable_tmp = np.transpose(np.rot90(variable_data, -1))
            variable_tmp[np.isnan(variable_tmp)] = fill_value
            var_handle[:, :] = variable_tmp
        else:
            raise NotImplementedError('Case not implemented yet')

    # close file
    file_handle.close()
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to write nc file (xarray
def write_file_nc_xarray(file_name, dset_data,
                  dset_mode='w', dset_engine='netcdf4', dset_compression=9, dset_format='NETCDF4',
                  dim_key_time='time', no_data=-9999.0):

    dset_encoded = dict(zlib=True, complevel=dset_compression)

    dset_encoding = {}
    for var_name in dset_data.data_vars:

        if isinstance(var_name, bytes):
            tmp_name = var_name.decode("utf-8")
            dset_data.rename({var_name: tmp_name})
            var_name = deepcopy(tmp_name)

        var_data = dset_data[var_name]
        if len(var_data.dims) > 0:
            dset_encoding[var_name] = deepcopy(dset_encoded)

        var_attrs = dset_data[var_name].attrs
        if var_attrs:
            for attr_key, attr_value in var_attrs.items():
                if attr_key in attrs_encoded:

                    dset_encoding[var_name][attr_key] = {}

                    if isinstance(attr_value, list):
                        attr_string = [str(value) for value in attr_value]
                        attr_value = ','.join(attr_string)

                    dset_encoding[var_name][attr_key] = attr_value

        if '_FillValue' not in list(dset_encoding[var_name].keys()):
            dset_encoding[var_name]['_FillValue'] = no_data

    if dim_key_time in list(dset_data.coords):
        dset_encoding[dim_key_time] = {'calendar': 'gregorian'}

    dset_data.to_netcdf(path=file_name, format=dset_format, mode=dset_mode,
                        engine=dset_engine, encoding=dset_encoding)
# ----------------------------------------------------------------------------------------------------------------------
