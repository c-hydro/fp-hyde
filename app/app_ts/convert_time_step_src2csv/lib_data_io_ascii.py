"""
Library Features:

Name:          lib_data_io_ascii
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20231010'
Version:       '1.0.0'
"""

# ----------------------------------------------------------------------------------------------------------------------
# libraries
import logging
import os
import pandas as pd

from copy import deepcopy

from lib_data_io_generic import combine_data_point_by_time

from lib_utils_system import fill_tags2string
from lib_utils_obj import map_vars_dframe, sanitize_string, fill_tags_time
from lib_utils_time import replace_time_part
from lib_info_args import logger_name, time_format_algorithm

# logging
log_stream = logging.getLogger(logger_name)
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to wrap datasets in ascii format
def wrap_datasets_ascii(file_path_template,
                        file_fields, registry_fields,
                        time_reference, time_start, time_end,
                        time_rounding='H', time_frequency='Y', time_format='%Y%m%d%H%M',
                        template_time_tags=None, template_datasets_tags=None,
                        file_sep=' ', file_decimal='.',
                        ascending_index=False, sort_index=True):

    # check time frequency
    if time_frequency == 'Y':

        time_now_stamp = pd.Timestamp.now()
        time_start_stamp = pd.Timestamp(time_start)
        time_end_stamp = pd.Timestamp(time_end)
        if time_now_stamp > time_end_stamp and time_now_stamp > time_start_stamp:
            log_stream.warning(
                ' ===> "time_now" "' + str(time_now_stamp) + '" is greater than "time_end" "' +
                str(time_end_stamp) + '". Time end is set to time now. '
                                      'Change time end in the settings file to avoid this message')
            time_end_stamp = deepcopy(time_now_stamp)
            time_end_stamp = time_end_stamp.replace(month=12, day=31, hour=23, minute=0, second=0, microsecond=0)
            time_start_stamp = time_start_stamp.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

            time_start = time_start_stamp.strftime(time_format_algorithm)
            time_end = time_end_stamp.strftime(time_format_algorithm)

        time_range_start = pd.date_range(time_start, time_end, freq='AS')
        time_range_start = replace_time_part(time_range_start, time_rounding=time_rounding, time_value=0)
        time_range_end = pd.date_range(time_start, time_end, freq='Y')
        time_range_end = replace_time_part(time_range_end, time_rounding=time_rounding, time_value=23)
        time_range_reference = deepcopy(time_reference)

    else:
        log_stream.error(' ===> Time frequency "' + time_frequency + '" is not expected')
        raise NotImplementedError('Case not implemented yet')

    # iterate over registry fields
    section_data_collections, section_time_start, section_time_end = {}, None, None
    for registry_row in registry_fields.iterrows():

        # get point information
        registry_code, registry_tag = registry_row[1]['code'], registry_row[1]['tag']

        # info point start
        log_stream.info(' ------> Point (1) Code "' + registry_code + '" (2) Tag "' + registry_tag + '" ... ')

        # iterate over times
        fields_data_collections = None
        for time_step_start, time_step_end in zip(time_range_start, time_range_end):

            # info time period start
            log_stream.info(' -------> Time Reference :: "' + str(time_reference) +
                            '" -- Period "' + str(time_step_start) + '" :: "' + str(time_step_end) + '" ... ')

            # fill time tags
            template_time_values = fill_tags_time(
                template_time_tags,
                time_reference=time_reference, time_start=time_step_start, time_end=time_step_end)
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
                fields_data_raw = pd.read_table(
                    file_path_defined, sep=file_sep, decimal=file_decimal)
                fields_data_raw.columns = fields_data_raw.columns.str.strip()
                # map file fields
                fields_data_map = map_vars_dframe(fields_data_raw, file_fields)

                # parse time field
                if 'time' in list(fields_data_map.columns):
                    time_data_raw = fields_data_map['time'].values
                    time_data_index = pd.to_datetime(time_data_raw, format=time_format)
                    fields_data_map['time'] = time_data_index
                    fields_data_map.set_index('time', inplace=True)
                    fields_data_map.index.name = 'time'
                else:
                    log_stream.error(' ===> Field "time" is not defined in the file, but it is expected')
                    raise RuntimeError('Check your settings file and set the "time" field')

                # convert data to float (if integer are found)
                fields_data_map = fields_data_map.astype(float)

                # manage data collections
                if fields_data_collections is None:
                    fields_data_collections = deepcopy(fields_data_map)
                else:
                    fields_data_collections = pd.concat([fields_data_collections, fields_data_map])

                # info time period end
                log_stream.info(' -------> Time Reference :: "' + str(time_reference) +
                                '" -- Period "' + str(time_step_start) + '" :: "' + str(time_step_end) +
                                '" ... DONE')
            else:

                # info time period end (message for skipping)
                log_stream.info(' -------> Time Reference :: "' + str(time_reference) +
                                '" -- Period "' + str(time_step_start) + '" :: "' + str(time_step_end) +
                                '" ... SKIPPED. File "' + file_path_defined + '" does not exists.')

        if section_time_start is None:
            section_time_start = fields_data_collections.index[0]
        else:
            assert section_time_start == fields_data_collections.index[0], 'time start are not equal'
        if section_time_end is None:
            section_time_end = fields_data_collections.index[-1]
        else:
            assert section_time_end == fields_data_collections.index[-1], 'time end are not equal'

        # sort index
        if sort_index:
            if ascending_index:
                fields_data_collections = fields_data_collections.sort_index(ascending=True)
            else:
                fields_data_collections = fields_data_collections.sort_index(ascending=False)

        # store section data to common workspace
        section_data_collections[registry_tag] = fields_data_collections

        # info point end
        log_stream.info(' ------> Point (1) Code "' + registry_code + '" (2) Tag "' + registry_tag + '" ... DONE')

    return section_data_collections, section_time_start, section_time_end
# ----------------------------------------------------------------------------------------------------------------------
