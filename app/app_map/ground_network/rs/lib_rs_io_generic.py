"""
Library Features:

Name:          lib_ws_io_generic
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20201102'
Version:       '1.0.0'
"""
#######################################################################################
# Libraries
import logging
import tempfile
import os
import json
import pickle

import pandas as pd
import numpy as np
import xarray as xr

from copy import deepcopy
#######################################################################################

# -------------------------------------------------------------------------------------
# Defined attributes look-up table
attributes_defined_lut = {
    'blocking_attrs': ['coordinates'],
    'encoding_attrs': {
        '_FillValue': ['_FillValue', 'fill_value'],
        'scale_factor': ['scale_factor', 'ScaleFactor']
    },
    'filtering_attrs': {
        'Valid_range': ['Valid_range', 'valid_range'],
        'Missing_value': ['Missing_value', 'missing_value']
    }
}
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to convert data raster to data array
def convert_values2da(values, lons, lats, var_name='geo_data',
                      coord_name_x='west_east', coord_name_y='south_north',
                      dim_name_x='west_east', dim_name_y='south_north'):

    da = create_darray_2d(values, lons, lats, coord_name_x=coord_name_x, coord_name_y=coord_name_y,
                          dim_name_x=dim_name_x, dim_name_y=dim_name_y, name=var_name)
    return da
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create a tmp name
def create_filename_tmp(prefix='tmp_', suffix='.tiff', folder=None):

    if folder is None:
        folder = '/tmp'

    with tempfile.NamedTemporaryFile(dir=folder, prefix=prefix, suffix=suffix, delete=False) as tmp:
        temp_file_name = tmp.name
    return temp_file_name
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write ascii 1d
def write_file_ascii(file_name, file_data, file_fields=None,
                     file_attrs=None, file_format=None, file_write_engine=None, file_new_line='\n'):

    if file_fields is None:
        file_fields = ['code', 'discharge', 'tag']
    if file_format is None:
        file_format = ['%10.0f', '%10.1f', '%s']
    if file_write_engine is None:
        file_write_engine = ['i', 'f', 'U256']

    if file_format.__len__() != file_fields.__len__():
        logging.error(' ===> Columns "format" length is not equal to fields length')
        raise IOError('Bad "file format" definition')
    if file_write_engine.__len__() != file_fields.__len__():
        logging.error(' ===> Columns "write engine" length is not equal to fields length')
        raise IOError('Bad "file write engine" definition')

    file_dict_generic = {}
    file_type = []
    for id_data_rows, file_data_cols in enumerate(file_data):
        for col_id, (col_format, col_write_engine, col_value) in enumerate(zip(file_format, file_write_engine, file_data_cols)):
            col_var = 'var' + str(col_id)
            if col_var not in list(file_dict_generic.keys()):
                file_dict_generic[col_var] = [col_value]
                file_type.append(tuple([col_var, col_write_engine]))
            else:
                col_data_tmp = file_dict_generic[col_var]
                col_data_tmp.append(col_value)
                file_dict_generic[col_var] = col_data_tmp

    file_dict_array = None
    for file_key, file_data in file_dict_generic.items():
        if file_dict_array is None:
            file_dict_array = np.zeros(file_data.__len__(), dtype=file_type)
        file_dict_array[file_key] = np.array(file_data)

    np.savetxt(file_name, file_dict_array, fmt=file_format, newline=file_new_line)

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read file csv
def read_file_csv(file_name, file_time=None, file_header=None,
                  file_sep=',', file_skiprows=1, file_skipcols=None,
                  file_renamecols=None, file_time_format='%Y-%m-%d %H:%M',
                  tag_file_index='time',
                  tag_file_geo_x='longitude', tag_file_geo_y='latitude', tag_file_data='data',
                  scale_factor_geo_x=1, scale_factor_geo_y=1, scale_factor_data=1):

    if file_header is None:
        file_header = ['code', 'name', 'longitude', 'latitude', 'time', 'data']

    file_dframe = pd.read_table(file_name, sep=file_sep, names=file_header, skiprows=file_skiprows)
    if file_renamecols is not None:
        file_dframe = file_dframe.rename(columns=file_renamecols)
    file_dframe = file_dframe.reset_index()
    file_dframe = file_dframe.set_index(tag_file_index)
    file_dframe.index.name = tag_file_index

    file_dframe.index = pd.to_datetime(file_dframe.index, format=file_time_format)
    file_dframe[tag_file_geo_x] = file_dframe[tag_file_geo_x] / scale_factor_geo_x
    file_dframe[tag_file_geo_y] = file_dframe[tag_file_geo_y] / scale_factor_geo_y
    file_dframe[tag_file_data] = file_dframe[tag_file_data] / scale_factor_data

    if file_skipcols is not None:
        if not isinstance(file_skipcols, list):
            file_skipcols = [file_skipcols]
        file_dframe = file_dframe.drop(columns=file_skipcols)

    if file_time is not None:
        if file_time in file_dframe.index:
            file_dframe_select = file_dframe.loc[file_time]
        else:
            file_dframe_select = None
            logging.warning(' ===> Time ' + str(file_time) + ' is not available in file: ' + file_name)
    else:
        file_dframe_select = file_dframe

    return file_dframe_select

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get file settings in json format
def read_file_settings(file_name_settings):
    if os.path.exists(file_name_settings):
        with open(file_name_settings) as file_handle:
            data_settings = json.load(file_handle)
    else:
        logging.error(' ===> Error in reading algorithm settings file')
        raise IOError('File not found')
    return data_settings
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create a data array
def create_darray_3d(data, time, geo_x, geo_y, geo_1d=True,
                     coord_name_x='west_east', coord_name_y='south_north', coord_name_time='time',
                     dim_name_x='west_east', dim_name_y='south_north', dim_name_time='time',
                     dims_order=None):

    if dims_order is None:
        dims_order = [dim_name_y, dim_name_x, dim_name_time]

    if geo_1d:
        if geo_x.shape.__len__() == 2:
            geo_x = geo_x[0, :]
        if geo_y.shape.__len__() == 2:
            geo_y = geo_y[:, 0]

        data_da = xr.DataArray(data,
                               dims=dims_order,
                               coords={coord_name_time: (dim_name_time, time),
                                       coord_name_x: (dim_name_x, geo_x),
                                       coord_name_y: (dim_name_y, geo_y)})
    else:
        logging.error(' ===> Longitude and Latitude must be 1d')
        raise IOError('Variable shape is not valid')

    return data_da
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create a data array
def create_darray_2d(data, geo_x, geo_y, geo_1d=True, name='geo',
                     coord_name_x='west_east', coord_name_y='south_north',
                     dim_name_x='west_east', dim_name_y='south_north',
                     dims_order=None):

    if dims_order is None:
        dims_order = [dim_name_y, dim_name_x]

    if geo_1d:
        if geo_x.shape.__len__() == 2:
            geo_x = geo_x[0, :]
        if geo_y.shape.__len__() == 2:
            geo_y = geo_y[:, 0]

        data_da = xr.DataArray(data,
                               dims=dims_order,
                               coords={coord_name_x: (dim_name_x, geo_x),
                                       coord_name_y: (dim_name_y, geo_y)},
                               name=name)
    else:
        logging.error(' ===> Longitude and Latitude must be 1d')
        raise IOError('Variable shape is not valid')

    return data_da
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to select attributes
def select_attrs(attrs_var_raw):

    if attrs_var_raw is not None:

        attrs_var_tmp = deepcopy(attrs_var_raw)
        for attrs_def_key, attrs_def_items in attributes_defined_lut.items():

            if isinstance(attrs_def_items, dict):
                for field_key, field_items in attrs_def_items.items():
                    if isinstance(field_items, list):
                        for field_name in field_items:
                            if field_name in attrs_var_tmp:
                                if field_name != field_key:
                                    field_value = attrs_var_tmp[field_name]
                                    attrs_var_tmp.pop(field_name, None)
                                    attrs_var_tmp[field_key] = field_value
                    else:
                        logging.error(' ===> Type variable not allowed')
                        raise NotImplemented('Attributes values type not implemented yet')

            elif isinstance(attrs_def_items, list):
                pass
            else:
                logging.error(' ===> Type variable not allowed')
                raise NotImplemented('Attributes values type not implemented yet')

        blocked_attrs = attributes_defined_lut['blocking_attrs']
        encoded_attrs = list(attributes_defined_lut['encoding_attrs'].keys())

        attrs_var_info = {}
        attrs_var_encoded = {}
        for attrs_var_key, attrs_var_value in attrs_var_tmp.items():

            if attrs_var_value is not None:
                if isinstance(attrs_var_value, list):
                    var_string = [str(value) for value in attrs_var_value]
                    attrs_var_value = ','.join(var_string)
                if isinstance(attrs_var_value, dict):
                    var_string = json.dumps(attrs_var_value)
                    attrs_var_value = var_string

                if attrs_var_key in encoded_attrs:
                    attrs_var_encoded[attrs_var_key] = attrs_var_value
                elif attrs_var_key in blocked_attrs:
                    pass
                else:
                    attrs_var_info[attrs_var_key] = attrs_var_value
    else:
        attrs_var_info = None
        attrs_var_encoded = None

    return attrs_var_info, attrs_var_encoded
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create datasets
def create_dset(var_data_dict, geo_data_values, geo_x_values, geo_y_values, time_data_values,
                var_attrs_dict=None,
                geo_data_attrs_dict=None, geo_data_name='terrain',
                geo_x_attrs_dict=None, geo_x_name='longitude',
                geo_y_attrs_dict=None, geo_y_name='latitude',
                geo_data_1d=False,
                global_attrs_dict=None,
                coord_name_x='longitude', coord_name_y='latitude', coord_name_time='time',
                dim_name_x='west_east', dim_name_y='south_north', dim_name_time='time',
                dims_order_2d=None, dims_order_3d=None,
                missing_value_default=-9999.0, fill_value_default=-9999.0):

    geo_x_values_tmp = geo_x_values
    geo_y_values_tmp = geo_y_values
    if geo_data_1d:
        if (geo_x_values.shape.__len__() == 2) and (geo_y_values.shape.__len__() == 2):
            geo_x_values_tmp = geo_x_values[0, :]
            geo_y_values_tmp = geo_y_values[:, 0]
    else:
        if (geo_x_values.shape.__len__() == 1) and (geo_y_values.shape.__len__() == 1):
            geo_x_values_tmp, geo_y_values_tmp = np.meshgrid(geo_x_values, geo_y_values)

    if dims_order_2d is None:
        dims_order_2d = [dim_name_y, dim_name_x]
    if dims_order_3d is None:
        dims_order_3d = [dim_name_y, dim_name_x, dim_name_time]

    if not isinstance(time_data_values, list):
        time_data_values = [time_data_values]

    if var_attrs_dict is None:
        var_attrs_dict = {}
        for var_name_step in var_data_dict.keys():
            var_attrs_dict[var_name_step] = None

    var_dset = xr.Dataset(coords={coord_name_time: ([dim_name_time], time_data_values)})
    if global_attrs_dict is not None:
        for global_attrs_name, global_attrs_value in global_attrs_dict.items():
            var_dset.attrs[global_attrs_name] = global_attrs_value
        if 'nodata_value' not in list(global_attrs_dict.keys()):
            global_attrs_dict['nodata_value'] = -9999.0
    var_dset.coords[coord_name_time] = var_dset.coords[coord_name_time].astype('datetime64[ns]')

    var_da_terrain = xr.DataArray(np.flipud(geo_data_values),  name=geo_data_name,
                                  dims=dims_order_2d,
                                  coords={coord_name_x: ([dim_name_y, dim_name_x], geo_x_values_tmp),
                                          coord_name_y: ([dim_name_y, dim_name_x], np.flipud(geo_y_values_tmp))})
    var_dset[geo_data_name] = var_da_terrain

    if geo_data_attrs_dict is not None:
        geo_attrs_dict_info, geo_attrs_dict_encoded = select_attrs(geo_data_attrs_dict)
        if geo_attrs_dict_info is not None:
            var_dset[geo_data_name].attrs = geo_attrs_dict_info
        if geo_attrs_dict_encoded is not None:
            var_dset[geo_data_name].encoding = geo_attrs_dict_encoded

    if geo_x_name in list(var_dset.coords):
        if geo_x_attrs_dict is not None:
            geo_attrs_dict_info, geo_attrs_dict_encoded = select_attrs(geo_x_attrs_dict)
            if geo_attrs_dict_info is not None:
                var_dset[geo_x_name].attrs = geo_attrs_dict_info
            if geo_attrs_dict_encoded is not None:
                var_dset[geo_x_name].encoding = geo_attrs_dict_encoded

    if geo_y_name in list(var_dset.coords):
        if geo_y_attrs_dict is not None:
            geo_attrs_dict_info, geo_attrs_dict_encoded = select_attrs(geo_y_attrs_dict)
            if geo_attrs_dict_info is not None:
                var_dset[geo_y_name].attrs = geo_attrs_dict_info
            if geo_attrs_dict_encoded is not None:
                var_dset[geo_y_name].encoding = geo_attrs_dict_encoded

    for (var_name_step, var_data_step), var_attrs_step in zip(var_data_dict.items(), var_attrs_dict.values()):

        if var_data_step.shape.__len__() == 2:
            var_da_data = xr.DataArray(np.flipud(var_data_step), name=var_name_step,
                                       dims=dims_order_2d,
                                       coords={coord_name_x: ([dim_name_y, dim_name_x], geo_x_values_tmp),
                                               coord_name_y: ([dim_name_y, dim_name_x], np.flipud(geo_y_values_tmp))})
        elif var_data_step.shape.__len__() == 3:
            var_da_data = xr.DataArray(np.flipud(var_data_step), name=var_name_step,
                                       dims=dims_order_3d,
                                       coords={coord_name_time: ([dim_name_time], time_data),
                                               coord_name_x: ([dim_name_y, dim_name_x], geo_x_values_tmp),
                                               coord_name_y: ([dim_name_y, dim_name_x], np.flipud(geo_y_values_tmp))})
        else:
            raise NotImplemented

        if var_attrs_step is not None:

            missing_value = None
            for attrs_name in attributes_defined_lut['filtering_attrs']['Missing_value']:
                if attrs_name in list(var_attrs_step.keys()):
                    missing_value = var_attrs_step[attrs_name]
            if missing_value is None:
                missing_value = missing_value_default
            for attrs_name in attributes_defined_lut['filtering_attrs']['Valid_range']:
                if attrs_name in list(var_attrs_step.keys()):
                    valid_range = var_attrs_step[attrs_name]
                    var_da_data = clip_data(var_da_data, valid_range, missing_value=missing_value)

            fill_value = None
            for attrs_name in attributes_defined_lut['encoding_attrs']['_FillValue']:
                if attrs_name in list(var_attrs_step.keys()):
                    fill_value = var_attrs_step[attrs_name]
            if fill_value is None:
                fill_value = fill_value_default
            var_da_data = var_da_data.where(var_da_terrain > global_attrs_dict['nodata_value'], other=fill_value)

        var_dset[var_name_step] = var_da_data

        if var_attrs_step is not None:
            var_attrs_step_info, var_attrs_step_encoded = select_attrs(var_attrs_step)
        else:
            var_attrs_step_info = None
            var_attrs_step_encoded = None

        if var_attrs_step_info is not None:
            var_dset[var_name_step].attrs = var_attrs_step_info
        if var_attrs_step_encoded is not None:
            var_dset[var_name_step].encoding = var_attrs_step_encoded

    return var_dset
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to clip data 2D/3D using a min/max threshold(s) and assign a missing value
def clip_data(map, valid_range=None, missing_value=None):

    # Set variable valid range
    if valid_range is None:
        valid_range = [None, None]

    if valid_range is not None:
        if valid_range[0] is not None:
            valid_range_min = float(valid_range[0])
        else:
            valid_range_min = None
        if valid_range[1] is not None:
            valid_range_max = float(valid_range[1])
        else:
            valid_range_max = None
        # Set variable missing value
        if missing_value is None:
            missing_value_min = valid_range_min
            missing_value_max = valid_range_max
        else:
            missing_value_min = missing_value
            missing_value_max = missing_value

        # Apply min and max condition(s)
        if valid_range_min is not None:
            map = map.where(map >= valid_range_min, missing_value_min)
        if valid_range_max is not None:
            map = map.where(map <= valid_range_max, missing_value_max)
        return map
    else:
        return map

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write dataset
def write_dset(file_name,
               dset_data, dset_mode='w', dset_engine='h5netcdf', dset_compression_level=0, dset_format='NETCDF4',
               dim_key_time='time', fill_value=-9999.0):

    dset_encoding = {}
    for var_name in dset_data.data_vars:

        if isinstance(var_name, bytes):
            var_name_upd = var_name.decode("utf-8")
            dset_data = var_name.rename({var_name: var_name_upd})
            var_name = var_name_upd

        var_attrs_encoding = dset_data[var_name].encoding

        if '_FillValue' not in list(var_attrs_encoding.keys()):
            var_attrs_encoding['_FillValue'] = fill_value
        if dset_compression_level > 0:
            if 'zlib' not in list(var_attrs_encoding.keys()):
                var_attrs_encoding['zlib'] = True
            if 'complevel' not in list(var_attrs_encoding.keys()):
                var_attrs_encoding['complevel'] = dset_compression_level

        dset_encoding[var_name] = var_attrs_encoding

    if dim_key_time in list(dset_data.coords):
        dset_encoding[dim_key_time] = {'calendar': 'gregorian'}

    dset_data.to_netcdf(path=file_name, format=dset_format, mode=dset_mode, engine=dset_engine,
                        encoding=dset_encoding)

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read data obj
def read_obj(filename):
    if os.path.exists(filename):
        data = pickle.load(open(filename, "rb"))
    else:
        data = None
    return data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write data obj
def write_obj(filename, data):
    if os.path.exists(filename):
        os.remove(filename)
    with open(filename, 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)
# -------------------------------------------------------------------------------------
