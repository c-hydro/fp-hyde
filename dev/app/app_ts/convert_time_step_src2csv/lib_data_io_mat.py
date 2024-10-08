"""
Library Features:

Name:          lib_data_io_mat
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20231010'
Version:       '1.0.0'

NOTE:
    matlab file .mat should not have string.java format
    convert string.java to cell;
    >> cell_var = {cell(string_var)}
    save the file:
    >> save file_name.mat -v7
"""

# ----------------------------------------------------------------------------------------------------------------------
# libraries
import logging
import scipy.io
import os
import numpy as np
import pandas as pd

from datetime import datetime
from copy import deepcopy

from lib_data_io_pickle import read_obj, write_obj
from lib_info_args import logger_name

from lib_utils_obj import map_vars_dict, sanitize_string

# logging
log_stream = logging.getLogger(logger_name)

# Debug
# import matplotlib.pylab as plt
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to read file mat
def read_file_mat(file_name, file_mandatory=True, file_fields_excluded=None):

    if file_fields_excluded is None:
        file_fields_excluded = ['__header__', '__version__', '__globals__']

    file_data_raw = None
    if os.path.exists(file_name):
        file_data_raw = scipy.io.loadmat(file_name, struct_as_record=True)
    else:
        if file_mandatory:
            log_stream.error(' ===> File "' + file_name + '" does not exists.')
            raise FileNotFoundError('File is mandatory to run the algorithm')
        else:
            log_stream.warning(' ===> File "' + file_name + '" does not exists. Datasets will be defined by NoneType')

    key_data = deepcopy(list(file_data_raw.keys()))
    if file_data_raw is not None:
        for key_name in key_data:
            if key_name in file_fields_excluded:
                file_data_raw.pop(key_name)

    return file_data_raw
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to convert variable
def convert_var_mat(var_data_in, var_type='time', string_no_data='-',
                    reset_tmp=True, folder_tmp=None, file_tmp='times.workspace',
                    time_format='%d/%m/%Y %H:%M'):

    path_tmp = os.path.join(folder_tmp, file_tmp)
    if reset_tmp:
        if os.path.exists(path_tmp):
            os.remove(path_tmp)

    if not os.path.exists(path_tmp):
        os.makedirs(folder_tmp, exist_ok=True)

        tmp_values = var_data_in
        tmp_values = tmp_values[:, 0][0][:, 0]

        var_data_out = []
        for tmp_value in tmp_values:

            if tmp_value:
                tmp_value = str(tmp_value[0])
                if var_type == 'time':
                    tmp_time = datetime.strptime(tmp_value, time_format)
                    obj_step = pd.Timestamp(tmp_time)
                else:
                    obj_step = deepcopy(tmp_value)
            else:
                obj_step = string_no_data
            var_data_out.append(obj_step)

        write_obj(path_tmp, var_data_out)

    else:
        var_data_out = read_obj(path_tmp)

    return var_data_out
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to wrap datasets in mat format
def wrap_datasets_mat(file_name, file_fields, registry_fields, folder_tmp=None, var_name='sm'):
    # get fields data raw
    fields_data_raw = read_file_mat(
        file_name, file_mandatory=True,
        file_fields_excluded=['__header__', '__version__', '__globals__'])
    # map fields
    fields_data_map = map_vars_dict(fields_data_raw, file_fields)

    # parser time(s)
    var_data_time = convert_var_mat(
        fields_data_map['time'], var_type='time',
        reset_tmp=False, folder_tmp=folder_tmp, file_tmp='time.workspace')
    fields_data_map.pop('time')

    # parser name(s)
    var_data_name = convert_var_mat(
        fields_data_map['name'], var_type='other',
        reset_tmp=True, folder_tmp=folder_tmp, file_tmp='name.workspace')
    fields_data_map.pop('name')

    # parser description(s)
    var_data_description = convert_var_mat(
        fields_data_map['description'], var_type='other',
        reset_tmp=True, folder_tmp=folder_tmp, file_tmp='description.workspace')
    fields_data_map.pop('description')

    # parser tag
    if 'tag' not in list(fields_data_map.keys()):

        if 'tag' in list(registry_fields.columns):
            var_data_tag = list(registry_fields['tag'].values)
        else:
            var_data_tag = []
            for string_name in var_data_name:
                string_tag = sanitize_string(string_name)
                var_data_tag.append(string_tag)
    else:
        var_data_tag = convert_var_mat(
            fields_data_map['tag'], var_type='other',
            reset_tmp=True, folder_tmp=folder_tmp, file_tmp='tag.workspace')
        fields_data_map.pop('tag')

    # create fields data update
    fields_data_upd = {
        'sm': fields_data_map['sm'].T,
        'time': var_data_time, 'tag': var_data_tag,
        'name': var_data_name, 'description': var_data_description
    }

    # create fields data merge
    fields_data_merge = {**fields_data_map, **fields_data_upd}

    # adapt data dict to dataframe
    data_values = fields_data_merge['sm']
    data_time = fields_data_merge['time']
    data_name, data_description = fields_data_merge['name'], fields_data_merge['description']
    data_tag = fields_data_merge['tag']
    # no data values
    data_values[data_values < -99] = np.nan

    data_obj, columns_obj = {}, []
    for var_id, (var_tag, var_description) in enumerate(zip(data_tag, data_description)):
        data_obj[var_tag] = data_values[:, var_id]
        columns_obj.append([(var_tag, var_description)])

    # create dframe
    fields_dframe = pd.DataFrame(data=data_obj, index=data_time)
    fields_dframe.index.name = 'time'

    # check dframe consistency
    start_time, end_time = data_time[0], data_time[-1]
    time_range_expected = pd.date_range(start=start_time, end=end_time, freq='H')
    expected_dframe = pd.DataFrame(index=time_range_expected)
    expected_dframe = expected_dframe.join(fields_dframe)

    if expected_dframe.__len__() != fields_dframe.__len__():
        log_stream.error(' ===> Time range consistency is not verified')
        raise RuntimeError('Check the time range and the time format to adjust the consistency')

    # search indexes for columns with values greater than 100
    fields_index = np.argwhere(fields_dframe.max().values > 100)[:, 0]
    # update dframe with scaling factor 10 for selected indexes
    fields_dframe.iloc[:, fields_index] = fields_dframe.iloc[:, fields_index] / 10
    # update columns for multiindex (not needed)
    # fields_dframe.columns = pd.MultiIndex.from_tuples(columns_obj)

    # iterate over columns
    point_data_collections, point_time_start, point_time_end = {}, None, None
    for column_name in fields_dframe.columns:

        # get fields
        column_fields = fields_dframe[column_name]
        # get and operate over values and index
        column_fields[column_fields < -99] = np.nan
        point_data = {var_name: column_fields.values}
        point_index = fields_dframe.index

        # get time start and time end
        if point_time_start is None:
            point_time_start = fields_dframe.index[0]
        if point_time_end is None:
            point_time_end = fields_dframe.index[-1]

        # create point dframe
        point_dframe = pd.DataFrame(index=point_index, data=point_data)
        # store dframe in a common workspace
        point_data_collections[column_name] = point_dframe

    return point_data_collections, point_time_start, point_time_end

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to wrap registry mat
def wrap_registry_mat(file_name, file_fields, folder_tmp=None):

    # get fields data raw
    fields_data_raw = read_file_mat(
        file_name, file_mandatory=True,
        file_fields_excluded=['__header__', '__version__', '__globals__', 'data', 'times'])
    # map fields
    fields_data_map = map_vars_dict(fields_data_raw, file_fields)

    # parser name(s)
    var_data_name = convert_var_mat(
        fields_data_map['name'], var_type='other',
        reset_tmp=True, folder_tmp=folder_tmp, file_tmp='names.workspace')
    fields_data_map.pop('name')

    # parser description(s)
    var_data_description = convert_var_mat(
        fields_data_map['description'], var_type='other',
        reset_tmp=True, folder_tmp=folder_tmp, file_tmp='description.workspace')
    fields_data_map.pop('description')

    # parser amm bnd 1
    var_data_amm_bnd_1 = convert_var_mat(
        fields_data_map['amm_level_1'], var_type='other',
        reset_tmp=True, folder_tmp=folder_tmp, file_tmp='amm_level_1.workspace')
    fields_data_map.pop('amm_level_1')

    # parser amm bnd 2
    var_data_amm_bnd_2 = convert_var_mat(
        fields_data_map['amm_level_2'], var_type='other',
        reset_tmp=True, folder_tmp=folder_tmp, file_tmp='amm_level_2.workspace')
    fields_data_map.pop('amm_level_2')

    # parser tag
    if 'tag' not in list(fields_data_map.keys()):
        var_data_tag = []
        for string_name in var_data_name:
            string_tag = sanitize_string(string_name)
            var_data_tag.append(string_tag)
    else:
        var_data_tag = convert_var_mat(
            fields_data_map['tag'], var_type='other',
            reset_tmp=True, folder_tmp=folder_tmp, file_tmp='tag.workspace')
        fields_data_map.pop('tag')

    # define valid fields
    fields_n = np.squeeze(fields_data_map['altitude']).shape[0]
    var_data_valid = np.ones(shape=[fields_n], dtype=int)

    # create fields data update
    fields_data_upd = {
        'altitude': np.squeeze(fields_data_map['altitude']),
        'longitude': np.squeeze(fields_data_map['longitude']),
        'latitude': np.squeeze(fields_data_map['latitude']),
        'code': np.squeeze(fields_data_map['code']),
        'name': var_data_name, 'description': var_data_description,
        'amm_level_1': var_data_amm_bnd_1, 'amm_level_2': var_data_amm_bnd_2,
        'valid': var_data_valid, 'tag': var_data_tag
    }

    # create fields data merge
    fields_data_merge = {**fields_data_map, **fields_data_upd}
    # create fields dframe
    fields_dframe = pd.DataFrame(data=fields_data_merge)

    return fields_dframe
# ----------------------------------------------------------------------------------------------------------------------
