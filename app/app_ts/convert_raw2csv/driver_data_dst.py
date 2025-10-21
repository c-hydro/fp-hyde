"""
Class Features

Name:          driver_data_destination
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20231010'
Version:       '1.0.0'
"""

# -------------------------------------------------------------------------------------
# libraries
import logging
import os
import pandas as pd
from copy import deepcopy

from lib_data_io_csv import write_file_csv
from lib_utils_io import merge_points_to_table, select_table_by_times
from lib_utils_obj import map_vars_dframe, fill_tags_time
from lib_utils_system import make_folder, fill_tags2string
from lib_info_args import logger_name

# logging
log_stream = logging.getLogger(logger_name)

# debugging
# import matplotlib.pylab as plt
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# class driver data
class DriverData:

    # -------------------------------------------------------------------------------------
    # initialize class
    def __init__(self, time_reference, time_range,
                 registry_dict, datasets_dict, ancillary_dict,
                 flags_dict=None, template_dict=None, tmp_dict=None):

        # set time reference and time range
        self.time_reference = time_reference
        self.time_range = time_range
        # set registry, ancillary and datasets dictionary
        self.registry_dict = registry_dict
        self.ancillary_dict = ancillary_dict
        self.datasets_dict = datasets_dict
        # set flags, template and tmp dictionary
        self.flags_dict = flags_dict
        self.template_time_tags = template_dict['time']
        self.template_datasets_tags = template_dict['datasets']
        self.tmp_dict = tmp_dict

        # registry and datasets tag(s)
        self.file_name_tag = 'file_name'
        self.folder_name_tag = 'folder_name'
        self.fields_tag = 'fields'
        self.format_tag = 'format'
        self.type_tag = 'type'
        self.no_data_tag = 'no_data'

        self.time_start_tag = "time_start"
        self.time_end_tag = "time_end"
        self.time_frequency_tag = "time_frequency"
        self.time_rounding_tag = "time_rounding"

        # reset flags
        self.reset_source = flags_dict['reset_source']
        self.reset_destination = flags_dict['reset_destination']

        # ancillary object(s)
        folder_name_ancillary = ancillary_dict[self.folder_name_tag]
        file_name_ancillary = ancillary_dict[self.file_name_tag]
        self.file_path_ancillary = os.path.join(folder_name_ancillary, file_name_ancillary)

        # registry object(s)
        folder_name_registry = self.registry_dict[self.folder_name_tag]
        file_name_registry = self.registry_dict[self.file_name_tag]
        self.file_path_registry = os.path.join(folder_name_registry, file_name_registry)
        self.format_registry = self.registry_dict[self.format_tag]
        self.fields_registry = self.registry_dict[self.fields_tag]
        self.no_data_registry = self.registry_dict[self.no_data_tag]

        # datasets object(s)
        folder_name_datasets = self.datasets_dict[self.folder_name_tag]
        file_name_datasets = self.datasets_dict[self.file_name_tag]
        self.file_path_datasets = os.path.join(folder_name_datasets, file_name_datasets)
        self.format_datasets = self.datasets_dict[self.format_tag]
        self.type_datasets = self.datasets_dict[self.type_tag]
        self.fields_datasets = self.datasets_dict[self.fields_tag]
        self.no_data_datasets = self.datasets_dict[self.no_data_tag]

        self.time_start_datasets = None
        if self.time_start_tag in list(self.datasets_dict.keys()):
            time_start_tmp = self.datasets_dict[self.time_start_tag]
            if time_start_tmp is not None:
                self.time_start_datasets = pd.Timestamp(self.datasets_dict[self.time_start_tag])
            else:
                self.time_start_datasets = None
        self.time_end_datasets = None
        if self.time_end_tag in list(self.datasets_dict.keys()):
            time_end_tmp = self.datasets_dict[self.time_end_tag]
            if time_end_tmp is not None:
                self.time_end_datasets = pd.Timestamp(self.datasets_dict[self.time_end_tag])
            else:
                self.time_end_datasets = None
        self.time_rounding_datasets = None
        if self.time_rounding_tag in list(self.datasets_dict.keys()):
            self.time_rounding_datasets = self.datasets_dict[self.time_rounding_tag]
        self.time_frequency_datasets = None
        if self.time_frequency_tag in list(self.datasets_dict.keys()):
            self.time_frequency_datasets = self.datasets_dict[self.time_frequency_tag]

        # tmp object(s)
        self.folder_name_tmp = tmp_dict[self.folder_name_tag]
        self.file_name_tmp = tmp_dict[self.file_name_tag]

        if self.type_datasets == 'all_pnt_one_var':
            fields_vars = deepcopy(self.fields_datasets)

            if 'time' in list(fields_vars.keys()):
                fields_vars.pop('time')

            fields_list = list(fields_vars.keys())

            if fields_list.__len__() > 1:
                self.var_name_in = list(fields_vars.keys())[0]
                self.var_name_out = list(fields_vars.values())[0]
                log_stream.warning(' ===> More than one variable is defined in the datasets settings for case'
                                   ' "all_pnt_one_var"')
                log_stream.warning(' ===> Only the first variable will be considered [var_name_in: "' +
                                   self.var_name_in + '", var_name_out: "' + self.var_name_out + '"]')
            else:
                self.var_name_in = list(fields_vars.keys())[0]
                self.var_name_out = list(fields_vars.values())[0]

        elif self.type_datasets == 'one_pnt_all_var':
            fields_vars = deepcopy(self.fields_datasets)

            if 'time' in list(fields_vars.keys()):
                fields_vars.pop('time')

            self.var_name_in = list(fields_vars.keys())
            self.var_name_out = list(fields_vars.values())
        else:
            log_stream.error(' ===> File type destination "' + self.type_datasets + '" is not expected')
            raise NotImplemented('Case not implemented yet')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # method to define file name
    @staticmethod
    def define_file_name(file_path_template,
                         time_reference=None, time_start=None, time_end=None,
                         template_time_tags=None,
                         template_datasets_tags=None, template_datasets_values=None):

        # fill datasets tags
        if template_datasets_tags is None:
            template_datasets_tags, template_datasets_values = {}, {}
        else:
            pass

        # fill time tags
        if template_time_tags is not None:
            template_time_values = fill_tags_time(
                template_time_tags,
                time_reference=time_reference, time_start=time_start, time_end=time_end)
        else:
            template_time_tags, template_time_values = {}, {}

        # create template tags and values
        template_generic_tags = {**template_time_tags, **template_datasets_tags}
        template_generic_values = {**template_time_values, **template_datasets_values}

        # define file path
        file_path_defined = fill_tags2string(
            file_path_template, tags_format=template_generic_tags, tags_filling=template_generic_values)[0]

        return file_path_defined

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # method to select time range (based on multiple selection)
    @staticmethod
    def select_time_boundaries(
            time_start_user=None, time_end_user=None,
            time_start_src=None, time_end_src=None, time_start_dst=None, time_end_dst=None,
            time_rounding='H', time_frequency='H'):

        if time_start_user is not None:
            time_start_selection = deepcopy(time_start_user)
        elif (time_start_user is None) and (time_start_dst is not None):
            time_start_selection = deepcopy(time_start_dst)
        elif (time_start_user is None) and (time_start_dst is None):
            time_start_selection = deepcopy(time_start_src)
        else:
            log_stream.error()
            raise NotImplemented('Case not implemented yet')

        if time_end_user is not None:
            time_end_selection = deepcopy(time_end_user)
        elif (time_end_user is None) and (time_end_dst is not None):
            time_end_selection = deepcopy(time_end_dst)
        elif (time_end_user is None) and (time_end_dst is None):
            time_end_selection = deepcopy(time_end_src)
        else:
            log_stream.error()
            raise NotImplemented('Case not implemented yet')

        time_start_selection = time_start_selection.floor(time_rounding)
        time_end_selection = time_end_selection.ceil(time_rounding)

        time_range_selection = pd.date_range(start=time_start_selection, end=time_end_selection, freq=time_frequency)

        return time_range_selection

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # method to dump datasets object
    def dump_obj_datasets(self, file_path_template, file_dframe_raw, file_time,
                          file_fields=None, file_var_in='vwc_10_cm', file_var_out='vwc_10_cm'):

        # info start method
        log_stream.info(' -----> Dump file datasets ... ')

        # check file format
        if self.format_datasets == 'csv':

            if self.type_datasets == 'all_pnt_one_var':

                # define file name
                if 'variable_name' not in file_path_template:
                    log_stream.warning(' ===> File name template should contain "variable_name" tag'
                                       'Files could be overwritten because the "variable_name" tag is not defined')

                # define file name
                file_path_defined = self.define_file_name(
                    file_path_template,
                    time_reference=self.time_reference, time_start=None, time_end=None,
                    template_time_tags=self.template_time_tags, template_datasets_tags=self.template_datasets_tags,
                    template_datasets_values={'point_name': 'all', "variable_name": file_var_out})

                # reset destination file(s)
                if self.reset_destination:
                    if os.path.exists(file_path_defined):
                        os.remove(file_path_defined)

                # info dump start
                log_stream.info(' ------> Datasets ... ')
                log_stream.info(' :: (1) File Type :: "' + self.type_datasets + '"')
                log_stream.info(' :: (2) File name :: "' + file_path_defined + '" ')

                # create datasets folder
                if not os.path.exists(file_path_defined):

                    # merge dframe datasets
                    file_dframe_merged = merge_points_to_table(file_dframe_raw, file_var_in)
                    # select dframe datasets
                    file_dframe_selected = select_table_by_times(file_dframe_merged, file_time, time_reverse=False)

                    # create datasets folder
                    folder_name, file_name = os.path.split(file_path_defined)
                    make_folder(folder_name)

                    # dump datasets dframe
                    write_file_csv(
                        file_path_defined, file_dframe_selected,
                        dframe_index_label='time', dframe_index_format='%Y-%m-%d %H:%M',
                        dframe_sep=';', dframe_decimal='.', dframe_float_format='%.1f',
                        dframe_index=True, dframe_header=True)

                    # info dump end
                    log_stream.info(' ------> Datasets ... DONE')

                else:
                    # info dump end
                    log_stream.info(' ------> Datasets ... SKIPPED')

            elif self.type_datasets == 'one_pnt_all_var':

                # define file name
                if 'point_name' not in file_path_template:
                    log_stream.warning(' ===> File name template should contain "point_name" tag. '
                                       'Files could be overwritten because the "point_name" tag is not defined')

                # info type start
                log_stream.info(' ------> Datasets ... ')
                log_stream.info(' :: (1) File Type :: "' + self.type_datasets + '"')

                # iterate over point(s)
                for point_id, (point_name, point_dframe_raw) in enumerate(file_dframe_raw.items()):

                    # define file name
                    file_path_defined = self.define_file_name(
                        file_path_template,
                        time_reference=self.time_reference, time_start=None, time_end=None,
                        template_time_tags=self.template_time_tags, template_datasets_tags=self.template_datasets_tags,
                        template_datasets_values={'point_name': point_name, "variable_name": 'all'})

                    # info point start
                    log_stream.info(' :: (2) File Name :: "' + file_path_defined + '"')
                    log_stream.info(' :: (3) Point ID :: "' + str(point_id) +
                                    '" -- Point Name :: "' + point_name + '" ... ')

                    # reset destination file(s)
                    if self.reset_destination:
                        if os.path.exists(file_path_defined):
                            os.remove(file_path_defined)

                    # create datasets folder
                    if not os.path.exists(file_path_defined):

                        # map registry fields
                        point_dframe_defined = map_vars_dframe(point_dframe_raw, file_fields, inverse_map=True)

                        # select dframe datasets
                        point_dframe_selected = select_table_by_times(point_dframe_defined, file_time)

                        # create datasets folder
                        folder_name, file_name = os.path.split(file_path_defined)
                        make_folder(folder_name)

                        # dump datasets dframe
                        write_file_csv(
                            file_path_defined, point_dframe_selected,
                            dframe_sep=',', dframe_decimal='.', dframe_float_format='%.2f',
                            dframe_index=True, dframe_header=True)

                        # info point end
                        log_stream.info(' :: (3) Point ID :: "' + str(point_id) +
                                        '" -- Point Name :: "' + point_name + '" ... DONE')

                    else:
                        # info point end
                        log_stream.info(' :: (3) Point ID :: "' + str(point_id) +
                                        '" -- Point Name :: "' + point_name + '" ... SKIPPED. File previously dumped.')

                # info type end
                log_stream.info(' ------> Datasets ... DONE')

            else:
                # error message for type not supported
                log_stream.error(' ===> File type "' + self.type_datasets + '" is not expected')
                raise NotImplemented('Case not implemented yet')
        else:
            # error message for format not supported
            log_stream.error(' ===> File format "' + self.format_datasets + '" not supported')
            raise NotImplemented('Case not implemented yet')

        # info end method
        log_stream.info(' -----> Dump file datasets ... DONE')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # method to dump registry object
    def dump_obj_registry(self, file_path_template, file_dframe_raw, file_fields=None):

        # define file name
        file_path_defined = self.define_file_name(file_path_template)

        # info start method
        log_stream.info(' -----> Dump file registry "' + file_path_defined + '" ... ')

        # reset destination file(s)
        if self.reset_destination:
            if os.path.exists(file_path_defined):
                os.remove(file_path_defined)

        # check file availability
        if not os.path.exists(file_path_defined):

            # check file format
            if self.format_registry == 'csv':

                # map registry fields
                file_dframe_map = map_vars_dframe(file_dframe_raw, file_fields, inverse_map=True)

                # fill nan(s) with no_data
                file_dframe_map = file_dframe_map.fillna(self.no_data_registry)

                # create registry folder
                folder_name, file_name = os.path.split(file_path_defined)
                make_folder(folder_name)

                # dump registry dframe
                write_file_csv(
                    file_path_defined, file_dframe_map,
                    dframe_index_format=None, dframe_index_label=False,
                    dframe_sep=';', dframe_decimal='.', dframe_float_format='%.3f',
                    dframe_index=False, dframe_header=True)

                # info end method
                log_stream.info(' -----> Dump file registry "' + file_path_defined +
                                '" ... DONE')

            else:
                log_stream.info(' -----> Dump file registry "' + file_path_defined +
                                '" ... FAILED')
                log_stream.error(' ===> File format is not supported')
                raise NotImplemented('Case not implemented yet')

        else:
            log_stream.info(' -----> Dump file registry "' + file_path_defined +
                            '" ... SKIPPED. File previously dumped.')

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # method to organize data
    def organize_data(self, data_source_obj):

        # method start info
        log_stream.info(' ----> Organize destination object(s) ... ')

        # get path(s)
        file_path_registry_generic, file_path_datasets_generic = self.file_path_registry, self.file_path_datasets

        # check source obj
        if data_source_obj is not None:

            # get source registry and datasets
            dframe_registry, dframe_datasets = data_source_obj['registry'], data_source_obj['datasets']

            # get source time start and end
            time_start_src, time_end_src = data_source_obj['time_start'], data_source_obj['time_end']
            time_start_dst, time_end_dst = self.time_start_datasets, self.time_end_datasets
            if self.time_range is not None:
                time_start_user, time_end_user = sorted(self.time_range)[0], sorted(self.time_range)[-1]
            else:
                time_start_user, time_end_user = None, None

            # select time range (based on multiple selection)
            time_range_selection = self.select_time_boundaries(
                time_start_user, time_end_user,
                time_start_src, time_end_src,
                time_start_dst, time_end_dst,
                time_rounding=self.time_rounding_datasets, time_frequency=self.time_frequency_datasets)

            # dump registry dframe
            self.dump_obj_registry(file_path_registry_generic, dframe_registry, self.fields_registry)
            # dump datasets dframe
            self.dump_obj_datasets(
                file_path_datasets_generic, dframe_datasets,
                file_time=time_range_selection, file_fields=self.fields_datasets,
                file_var_in=self.var_name_in, file_var_out=self.var_name_out)

            # method end info
            log_stream.info(' ----> Organize destination object(s) ... DONE')

        else:
            # method end info (no data available)
            log_stream.info(' ----> Organize destination object(s) ... SKIPPED. All datasets are not available')

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
