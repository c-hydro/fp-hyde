"""
Class Features

Name:          driver_data_dynamic
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20240301'
Version:       '1.0.0'
"""

# ----------------------------------------------------------------------------------------------------------------------
# libraries
import logging
import warnings

import os
import numpy as np
import pandas as pd
from copy import deepcopy

from lib_data_io_generic import organize_data_point, join_data_point, range_data_point, combine_data_point_by_time
from lib_data_io_csv import read_file_csv, write_file_csv
from lib_data_io_pickle import read_obj, write_obj

from lib_utils_obj import create_dict_from_list, convert_dict_to_dframe
from lib_utils_system import fill_tags2string

from lib_info_args import logger_name, time_var_name, time_format_algorithm

# logging
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)
# logging.getLogger('pandas').setLevel(logging.INFO)
log_stream = logging.getLogger(logger_name)

# debugging
# import matplotlib.pylab as plt
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# class driver data
class DriverData:

    # ------------------------------------------------------------------------------------------------------------------
    # initialize class
    def __init__(self, time_reference, time_obj, static_obj,
                 source_dict, ancillary_dict, destination_dict,
                 flags_dict=None, template_dict=None,
                 tmp_dict=None):

        self.time_reference = pd.Timestamp(time_reference)
        self.time_obj = time_obj
        self.time_end, self.time_start = time_obj[0], time_obj[-1]

        self.static_obj = static_obj

        self.source_dict = source_dict
        self.ancillary_dict = ancillary_dict
        self.destination_dict = destination_dict

        self.flags_dict = flags_dict
        self.template_dict = template_dict
        self.tmp_dict = tmp_dict

        self.file_name_tag, self.folder_name_tag = 'file_name', 'folder_name'
        self.type_tag, self.no_data_tag, self.delimiter_tag = 'type', 'no_data', 'delimiter'
        self.fields_tag = 'fields'
        self.date_format_tag, self.decimal_precision_tag = 'date_format', 'decimal_precision'

        self.reset_data_src = flags_dict['reset_dynamic_source']
        self.reset_data_dst = flags_dict['reset_dynamic_destination']

        self.point_static_collections = self.static_obj['point_obj']

        # source object(s)
        folder_name_src = self.source_dict[self.folder_name_tag]
        file_name_src = self.source_dict[self.file_name_tag]
        self.file_path_src = os.path.join(folder_name_src, file_name_src)
        self.fields_src = self.source_dict[self.fields_tag]
        self.type_src = self.source_dict[self.type_tag]
        self.delimiter_src = self.source_dict[self.delimiter_tag]
        # ancillary object(s)
        folder_name_anc = ancillary_dict[self.folder_name_tag]
        file_name_anc = ancillary_dict[self.file_name_tag]
        self.file_path_anc = os.path.join(folder_name_anc, file_name_anc)
        # destination object(s)
        folder_name_dst = self.destination_dict[self.folder_name_tag]
        file_name_dst = self.destination_dict[self.file_name_tag]
        self.file_path_dst = os.path.join(folder_name_dst, file_name_dst)
        self.fields_dst = self.destination_dict[self.fields_tag]
        self.type_dst = self.destination_dict[self.type_tag]
        self.date_format_dst = self.destination_dict[self.date_format_tag]
        self.delimiter_dst = self.destination_dict[self.delimiter_tag]
        self.decimal_precision_dst = self.destination_dict[self.decimal_precision_tag]
        self.no_data_dst = self.destination_dict[self.no_data_tag]

        # tmp object(s)
        self.folder_name_tmp = tmp_dict[self.folder_name_tag]
        self.file_name_tmp = tmp_dict[self.file_name_tag]

    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
    # method to define file name
    def define_file_name(self, file_path_raw,
                         name_step=None,
                         time_step=None, time_start=None, time_end=None):

        if time_step is None:
            time_step = deepcopy(time_end)

        template_tags_generic = deepcopy(self.template_dict)

        generic_list = list(template_tags_generic.keys())
        values_dict_generic = create_dict_from_list(generic_list, time_step)

        if time_end is not None:
            time_end_list = [key for key, value in values_dict_generic.items() if 'end' in key.lower()]
            values_dict_tmp = create_dict_from_list(time_end_list, time_end)
            values_dict_generic.update(**values_dict_tmp)

        if time_start is not None:
            time_start_list = [key for key, value in values_dict_generic.items() if 'start' in key.lower()]
            values_dict_tmp = create_dict_from_list(time_start_list, time_start)
            values_dict_generic.update(**values_dict_tmp)

        if name_step is not None:
            for name_key, name_value in name_step.items():
                values_dict_generic[name_key] = name_value
                template_tags_generic[name_key] = 'generic_string'

        file_path_def = fill_tags2string(file_path_raw, template_tags_generic, values_dict_generic)[0]
        return file_path_def

    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
    # method to dump data
    def dump_data(self, point_dynamic_collections):

        # method start info
        log_stream.info(' ----> Dump dynamic object(s) ... ')

        # get time(s)
        time_reference = self.time_reference
        # get static
        point_static_collections = self.point_static_collections

        # get path(s)
        file_path_dst_raw = self.file_path_dst

        # get flag(s)
        reset_dst = self.reset_data_dst

        # update dynamic collections
        tmp_data_collections = {}
        for data_key, data_tag in self.fields_dst.items():
            if data_key in list(point_dynamic_collections.keys()):
                tmp_data_collections[data_tag] = point_dynamic_collections[data_key]
        point_dynamic_collections = deepcopy(tmp_data_collections)

        # iterate over collections
        for collection_name, collection_data in point_dynamic_collections.items():

            # dump collections start
            log_stream.info(' -----> Collections "' + collection_name + '" ... ')

            # check destination file type
            if self.type_dst == 'csv_1d':

                # iterate over point(s)
                for point_id, point_data in point_static_collections.iterrows():

                    # get point information
                    point_tag, point_name = point_data['tag'], point_data['name']

                    # dump point start
                    log_stream.info(' ------> Dataframe point "' + point_tag + '" ... ')

                    # define source file name
                    file_path_dst_def = self.define_file_name(
                        file_path_dst_raw, name_step={'point_name': point_tag, 'data_name': collection_name},
                        time_step=time_reference)

                    # reset destination file
                    if reset_dst:
                        if os.path.exists(file_path_dst_def):
                            os.remove(file_path_dst_def)

                    # check destination file availability
                    if not os.path.exists(file_path_dst_def):

                        # get point time-series
                        point_series = collection_data.loc[point_tag]
                        point_dframe = pd.DataFrame({collection_name: point_series})

                        # create folder(s)
                        folder_name, file_name = os.path.split(file_path_dst_def)
                        os.makedirs(folder_name, exist_ok=True)

                        # method to write data
                        write_file_csv(file_path_dst_def, point_dframe,
                                       dframe_sep=self.delimiter_dst, dframe_decimal='.',
                                       dframe_float_format='%.{:}f'.format(self.decimal_precision_dst),
                                       dframe_index=True, dframe_header=True,
                                       dframe_index_label=time_var_name, dframe_index_format=self.date_format_dst,
                                       dframe_no_data=self.no_data_dst)
                        # dump point end
                        log_stream.info(' ------> Dataframe point "' + point_tag + '" ... DONE')

                    else:
                        # dump point end
                        log_stream.info(' ------> Dataframe point "' + point_tag +
                                        '" ...  SKIPPED, Datasets previously saved')

            # check destination file type
            elif self.type_dst == 'csv_2d':

                # dump point start
                log_stream.info(' ------> Dataframe points ... ')

                # define source file name
                file_path_dst_def = self.define_file_name(
                    file_path_dst_raw, time_step=time_reference)

                # reset destination file
                if reset_dst:
                    if os.path.exists(file_path_dst_def):
                        os.remove(file_path_dst_def)

                # check destination file availability
                if not os.path.exists(file_path_dst_def):

                    # create folder(s)
                    folder_name, file_name = os.path.split(file_path_dst_def)
                    os.makedirs(folder_name, exist_ok=True)

                    # method to write data
                    write_file_csv(file_path_dst_def, collection_data,
                                   dframe_sep=self.delimiter_dst, dframe_decimal='.',
                                   dframe_float_format='%.{:}f'.format(self.decimal_precision_dst),
                                   dframe_index=True, dframe_header=True,
                                   dframe_index_label=time_var_name, dframe_index_format=self.date_format_dst,
                                   dframe_no_data=self.no_data_dst)

                    # dump point end
                    log_stream.info(' ------> Dataframe points ... DONE')

                else:
                    # dump point end
                    log_stream.info(' -----> Dataframe points ... SKIPPED, Datasets previously saved')

            else:
                # file type not expected (error message)
                log_stream.error(' ===> File type "' + self.type_dst + "' not expected")
                raise NotImplementedError('File type not implemented yet')

            # dump collections end
            log_stream.info(' -----> Collections "' + collection_name + '" ... DONE')

        # method end info
        log_stream.info(' ----> Dump dynamic object(s) ... DONE')

    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
    # method to organize data
    def organize_data(self):

        # method start info
        log_stream.info(' ----> Organize dynamic object(s) ... ')

        # get time(s)
        time_obj = self.time_obj
        # get static
        point_static_collections = self.point_static_collections

        # get path(s)
        file_path_src_raw, file_path_anc_raw = self.file_path_src, self.file_path_anc

        # get flag(s)
        reset_src = self.reset_data_src

        # define ancillary file
        file_path_anc_def = self.define_file_name(file_path_anc_raw, time_start=self.time_start, time_end=self.time_end)
        # reset ancillary file
        if reset_src:
            if os.path.exists(file_path_anc_def):
                os.remove(file_path_anc_def)

        # check destination file availability
        if not os.path.exists(file_path_anc_def):

            # get data start
            log_stream.info(' -----> Get datasets ... ')

            # iterate over time step(s)
            point_dynamic_collections, point_dynamic_workspace = None, None
            for time_step in time_obj:

                # time start info
                log_stream.info(' ------> Time "' + time_step.strftime(time_format_algorithm) + '" ... ')

                # check source file type
                if self.type_src == 'csv_2d':

                    # define source file name
                    file_path_src_step = self.define_file_name(file_path_src_raw, time_step=time_step)

                    # check source file availability
                    if os.path.exists(file_path_src_step):

                        # method to get data
                        point_dynamic_dframe = read_file_csv(
                            file_path_src_step, dframe_index='name', dframe_fields=self.fields_src)

                        # method to organize data
                        point_dynamic_obj, point_dynamic_time = organize_data_point(
                            point_dynamic_dframe, ref_time=time_step, ref_registry=point_static_collections)

                        # method to join data
                        point_dynamic_collections = join_data_point(
                            point_dynamic_obj, point_dynamic_collections,
                            point_time=None, name_index='name')

                    else:
                        # file not found (warning message)
                        log_stream.warning(' ===> File "' + file_path_src_step + "' does not exists")

                elif self.type_src == 'csv_1d':

                    point_dynamic_db = None
                    for point_id, point_data in point_static_collections.iterrows():

                        point_name, point_tag = point_data['name'], point_data['tag']

                        # define source file name
                        file_path_src_step = self.define_file_name(
                            file_path_src_raw, name_step={'point_name': point_tag}, time_step=time_step)

                        # check source file availability
                        if os.path.exists(file_path_src_step):

                            # method to get data
                            point_dynamic_dframe = read_file_csv(
                                file_path_src_step, dframe_index='time',
                                dframe_fields=self.fields_src, dframe_sep=self.delimiter_src)

                        else:
                            # file not found (warning message)
                            log_stream.warning(' ===> File "' + file_path_src_step + "' does not exists")

                        point_values = point_dynamic_dframe.values
                        point_times = point_dynamic_dframe.index
                        point_obj = dict(zip(point_times, point_values))
                        point_dframe = pd.DataFrame(data=point_obj, index=[point_tag])

                        if point_dynamic_db is None:
                            point_dynamic_db = deepcopy(point_dframe)
                        else:
                            point_dynamic_db = pd.concat([point_dynamic_db, point_dframe])

                    if point_dynamic_workspace is None:
                        point_dynamic_workspace = {}
                    point_dynamic_workspace[time_step] = point_dynamic_db

                else:
                    # file type not expected (error message)
                    log_stream.error(' ===> File type "' + self.type_src + "' not expected")
                    raise NotImplementedError('File type not implemented yet')

                # time end info
                log_stream.info(' ------> Time "' + time_step.strftime(time_format_algorithm) + '" ... DONE')

            # get data end
            log_stream.info(' -----> Get datasets ... ')

            # combine data start
            log_stream.info(' -----> Combine datasets ... ')

            # check data according with type
            if self.type_src == 'csv_2d':

                # defined expected data and times
                expected_time = list(time_obj)
                expected_index = point_static_collections['tag'].values
                default_values = np.zeros(shape=(expected_index.shape[0]))
                default_values[:] = np.nan

                # adapt dataframe to expected time range
                for collections_name, collections_db in point_dynamic_collections.items():
                    # remove nan(s)
                    collections_db[np.isnan(collections_db)] = -9999.0
                    # iterate over times
                    expected_dframe = pd.DataFrame(index=expected_index)
                    for time_step in expected_time:

                        # time start info
                        log_stream.info(' ------> Time "' + time_step.strftime(time_format_algorithm) + '" ... ')
                        if time_step in pd.DatetimeIndex(collections_db.columns):

                            if time_step.hour == 0:
                                time_string = time_step.strftime('%Y-%m-%d')
                            else:
                                time_string = time_step.strftime('%Y-%m-%d %H:%M:00')

                            time_check = [time_string, time_step,
                                          time_step.strftime('%Y-%m-%d %H:%M:00'), time_step.strftime('%Y-%m-%d')]

                            tmp_values = None
                            for time_tmp in time_check:

                                try:
                                    tmp_values = collections_db[time_tmp]
                                except BaseException as base_exp:
                                    log_stream.warning(
                                        ' ===> Warning in handling data ''"' +
                                        str(base_exp) + '". This format in the dataframe causes '
                                                        'an error for unknown reason')
                                    tmp_values = None

                                if tmp_values is not None:
                                    break

                            if tmp_values is None:
                                log_stream.error(' ===> Error in handling data. Data is available '
                                                 'but data format is not properly defined')
                                raise RuntimeError('Check data format and try to add a case to manage it')

                            expected_dframe[time_step] = tmp_values
                        else:
                            expected_dframe[time_step] = default_values

                        # time start end
                        log_stream.info(' ------> Time "' + time_step.strftime(time_format_algorithm) + '" ... DONE')

                    point_dynamic_collections[collections_name] = expected_dframe

            elif self.type_src == 'csv_1d':

                if isinstance(point_dynamic_workspace, dict):
                    merged_dynamic_collections = None
                    for point_key, point_db in point_dynamic_workspace.items():
                        if merged_dynamic_collections is None:
                            merged_dynamic_collections = deepcopy(point_db)
                        else:
                            merged_dynamic_collections = merged_dynamic_collections.join(point_db)
                    ordered_dynamic_collections = merged_dynamic_collections.reindex(
                        sorted(merged_dynamic_collections.columns), axis=1)

                    point_dynamic_collections = {'data': ordered_dynamic_collections}
                else:
                    log_stream.error(' ===> ')
                    raise RuntimeError()

            # combine data start
            log_stream.info(' -----> Combine datasets ... ')

            # dump data start
            log_stream.info(' -----> Save datasets ... ')
            # check data availability
            if point_dynamic_collections is not None:

                # method to dump data
                folder_name_anc, file_name_anc = os.path.split(file_path_anc_def)
                os.makedirs(folder_name_anc, exist_ok=True)
                write_obj(file_path_anc_def, point_dynamic_collections)

                # dump data end
                log_stream.info(' -----> Save datasets ... DONE')

            else:
                # dump data end
                point_dynamic_collections = None
                log_stream.info(' -----> Save datasets ... SKIPPED. Datasets is not available')

        else:
            # read ancillary file
            point_dynamic_collections = read_obj(file_path_anc_def)

        # method end info
        log_stream.info(' ----> Organize dynamic object(s) ... DONE')

        return point_dynamic_collections

    # ------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------
