"""
Library Features:

Name:          lib_data_io_csv
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20231010'
Version:       '1.0.0'
"""

# ----------------------------------------------------------------------------------------------------------------------
# libraries
import logging
import os
import numpy as np
import pandas as pd

from lib_utils_system import fill_tags2string
from lib_utils_obj import map_vars_dframe, sanitize_string, fill_tags_time
from lib_info_args import logger_name

# logging
log_stream = logging.getLogger(logger_name)
logging.getLogger('pandas').setLevel(logging.WARNING)
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to wrap datasets in csv format
def wrap_datasets_csv(file_path_template,
                      file_fields, registry_fields,
                      time_reference, time_start, time_end,
                      time_rounding='H', time_frequency='Y', time_format='%Y%m%d%H%M',
                      template_time_tags=None, template_datasets_tags=None,
                      file_sep=' ', file_decimal='.',
                      ascending_index=False, sort_index=True):

    # check time frequency
    if time_frequency == 'H':

        time_start = pd.Timestamp(time_start).floor(time_rounding.lower())
        time_end = pd.Timestamp(time_end).floor(time_rounding.lower())

        time_range_start = pd.date_range(time_start, time_end, freq=time_frequency.lower())
        time_range_end = pd.date_range(time_start, time_end, freq=time_frequency.lower())
        time_range_reference = pd.date_range(time_start, time_end, freq=time_frequency.lower())

    else:
        log_stream.error(' ===> Time frequency "' + time_frequency + '" is not expected')
        raise NotImplementedError('Case not implemented yet')

    # iterate over registry fields
    section_data_collections = {}
    for registry_row in registry_fields.iterrows():

        # get point information
        registry_code = registry_row[1]['code']
        registry_tag, registry_name = registry_row[1]['tag'], registry_row[1]['name']

        # info point start
        log_stream.info(' ------> Point (1) Code "' + registry_code + '" (2) Tag "' + registry_tag + '" ... ')

        # iterate over times
        point_values_collections, point_time_collections = None, None
        for time_step_start, time_step_end, time_step_reference in zip(
                time_range_start, time_range_end, time_range_reference):

            # info time period start
            log_stream.info(' -------> Time Reference :: "' + str(time_step_reference) +
                            '" -- Period "' + str(time_step_start) + '" :: "' + str(time_step_end) + '" ... ')

            # fill time tags
            template_time_values = fill_tags_time(
                template_time_tags,
                time_reference=time_step_reference, time_start=time_step_start, time_end=time_step_end)
            template_datasets_values = {'point_name': registry_code}

            # create template tags and values
            template_generic_tags = {**template_time_tags, **template_datasets_tags}
            template_generic_values = {**template_time_values, **template_datasets_values}

            # define file path
            file_path_defined = fill_tags2string(
                file_path_template, tags_format=template_generic_tags, tags_filling=template_generic_values)[0]

            # check file availability
            if os.path.exists(file_path_defined):

                # get file fields
                fields_data_raw = pd.read_csv(
                    file_path_defined, sep=file_sep, decimal=file_decimal, date_format=time_format)
                fields_data_raw.columns = fields_data_raw.columns.str.strip()
                # map file fields
                fields_data_map = map_vars_dframe(fields_data_raw, file_fields)

                # parse time field
                if 'time' in list(fields_data_map.columns):
                    time_data_raw = fields_data_map['time'].values

                    if time_data_raw.shape[0] == 0:
                        log_stream.error(' ===> Field "time" is defined in the file, but it is empty')
                        raise RuntimeError('Check your settings file and set the "time" field')
                    else:
                        time_n = time_data_raw.shape[0]

                    time_stamp_raw = pd.Timestamp(time_data_raw[0]).strftime(time_format)
                    time_data_arr = [time_stamp_raw] * time_n
                    time_data_index = pd.DatetimeIndex(time_data_arr)

                    fields_data_map['time'] = time_data_index
                    fields_data_map.set_index('time', inplace=True)
                    fields_data_map.index.name = 'time'
                else:
                    log_stream.error(' ===> Field "time" is not defined in the file, but it is expected')
                    raise RuntimeError('Check your settings file and set the "time" field')

                # get point time and value
                if 'name' in list(fields_data_map.columns):

                    name_data_obj = fields_data_map['name']
                    name_data_obj = name_data_obj.str.strip()
                    name_data_obj = name_data_obj.str.lower()
                    name_data_arr = name_data_obj.values
                    name_data_reg = registry_name.strip().lower()

                    idx_data_obj = np.argwhere(name_data_arr == name_data_reg)

                    if idx_data_obj.shape[0] == 1:

                        idx_data_step = idx_data_obj[0][0]

                        point_time_step = fields_data_map.index[idx_data_step]
                        point_data_step = fields_data_map.iloc[idx_data_step]

                        if 'values' in list(point_data_step.keys()):
                            point_value_step = point_data_step['values']
                            point_value_step = float(point_value_step)
                        else:
                            log_stream.error(' ===> Field "values" is not defined in the file, but it is expected')
                            raise RuntimeError('Check your settings file and set the "values" field')
                    else:
                        log_stream.warning(' ===> Point "' + registry_name + '" is not available in the file')
                        point_value_step = np.nan
                        point_time_step = time_step_reference

                else:
                    log_stream.error(' ===> Field "name" is not defined in the file, but it is expected')
                    raise RuntimeError('Check your settings file and set the "name" field')

                # manage data collections
                if point_values_collections is None:
                    point_values_collections, point_time_collections = [], []

                point_values_collections.append(point_value_step)
                point_time_collections.append(point_time_step)

                # info time period end
                log_stream.info(' -------> Time Reference :: "' + str(time_step_reference) +
                                '" -- Period "' + str(time_step_start) + '" :: "' + str(time_step_end) +
                                '" ... DONE')
            else:

                # info time period end (message for skipping)
                log_stream.info(' -------> Time Reference :: "' + str(time_step_reference) +
                                '" -- Period "' + str(time_step_start) + '" :: "' + str(time_step_end) +
                                '" ... SKIPPED. File "' + file_path_defined + '" does not exists.')

        # store point data to common workspace
        if point_values_collections is not None:
            point_series = pd.Series(point_values_collections, index=point_time_collections)

            # sort index
            if sort_index:
                if ascending_index:
                    point_series = point_series.sort_index(ascending=True)
                else:
                    point_series = point_series.sort_index(ascending=False)
        else:
            log_stream.warning(' ===> Data not available for selected point. Series is defined by NoneType')
            point_series = None

        section_data_collections[registry_tag] = point_series

        # info point end
        log_stream.info(' ------> Point (1) Code "' + registry_code + '" (2) Tag "' + registry_tag + '" ... DONE')

    return section_data_collections
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to wrap registry in csv format
def wrap_registry_csv(file_name, file_fields, file_filters=None, file_sep=',', file_decimal='.'):

    # get file fields
    fields_data_raw = pd.read_table(file_name, sep=file_sep, decimal=file_decimal)
    fields_data_raw.columns = fields_data_raw.columns.str.strip()
    # map file fields
    fields_data_map = map_vars_dframe(fields_data_raw, file_fields)

    # get name fields
    var_data_name = fields_data_map['name'].values
    # parser tag
    if 'tag' not in list(fields_data_map.keys()):
        var_data_tag = []
        for string_name in var_data_name:
            string_tag = sanitize_string(string_name)
            var_data_tag.append(string_tag)

        fields_data_map['tag'] = var_data_tag

    # create fields dframe
    fields_dframe = pd.DataFrame(data=fields_data_map)

    if 'valid' in list(fields_dframe.columns):
        fields_dframe = fields_dframe[fields_dframe['valid'] == 1]

    if 'code' in list(fields_dframe.columns):
        fields_dframe['code'] = fields_dframe['code'].apply(str)
    else:
        log_stream.warning(' ===> Code field is not available in the registry file. Set default values.')
        rows_dframe = fields_dframe.shape[0]
        fields_dframe['code'] = [str(i) for i in range(1, rows_dframe + 1)]

    if 'tag' in list(fields_dframe.columns):
        fields_dframe['tag'] = fields_dframe['tag'].str.strip()

    if file_filters is not None:
        for filter_key, filter_value in file_filters.items():
            if filter_key in list(fields_dframe.columns):
                filter_data = fields_dframe[filter_key].values
                filter_id_list = []
                for filter_id_step, filter_row in enumerate(filter_data):
                    filter_value = str(filter_value)
                    if filter_value in filter_row:
                        filter_id_list.append(filter_id_step)

                fields_dframe = fields_dframe.loc[filter_id_list]

    return fields_dframe
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to write file csv
def write_file_csv(file_name, file_dframe,
                   dframe_sep=',', dframe_decimal='.', dframe_float_format='%.2f',
                   dframe_index=False, dframe_header=True,
                   dframe_index_label='time', dframe_index_format='%Y-%m-%d %H:%M',
                   dframe_no_data=-9999):

    if np.isfinite(dframe_no_data):
        file_dframe.fillna(dframe_no_data, inplace=True)

    if dframe_index_format is not None:
        file_dframe.index = file_dframe.index.strftime(dframe_index_format)

    file_dframe.to_csv(
        file_name, mode='w',
        index=dframe_index, sep=dframe_sep, decimal=dframe_decimal,
        index_label=dframe_index_label,
        header=dframe_header, float_format=dframe_float_format,  quotechar='"')

# ----------------------------------------------------------------------------------------------------------------------
