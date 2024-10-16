"""
Class Features

Name:          driver_data_source
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20231120'
Version:       '1.5.0'
"""

# -------------------------------------------------------------------------------------
# libraries
import logging
import os

from lib_data_io_generic import combine_data_point_by_time, range_data_point
from lib_data_io_ascii import wrap_datasets_ascii
from lib_data_io_csv import wrap_registry_csv, wrap_datasets_csv
from lib_data_io_mat import wrap_registry_mat
from lib_data_io_pickle import read_obj, write_obj

from lib_utils_obj import fill_tags_time
from lib_utils_system import make_folder, fill_tags2string

from lib_info_args import logger_name, time_format_algorithm, time_format_datasets

# logging
log_stream = logging.getLogger(logger_name)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# class driver data
class DriverData:

    # -------------------------------------------------------------------------------------
    # initialize class
    def __init__(self, time_reference, time_range, registry_dict, datasets_dict, ancillary_dict,
                 flags_dict=None, template_dict=None, tmp_dict=None):

        # set time reference
        self.time_reference = time_reference
        self.time_range = time_range
        # set registry, ancillary and datasets dictionary
        self.registry_dict = registry_dict
        self.ancillary_dict = ancillary_dict
        self.datasets_dict = datasets_dict
        # set flags, template and tmp dictionary
        self.flags_dict = flags_dict
        self.template_dict_time = template_dict['time']
        self.template_dict_datasets = template_dict['datasets']
        self.tmp_dict = tmp_dict

        # registry and datasets tag(s)
        self.file_name_tag, self.folder_name_tag = 'file_name', 'folder_name'
        self.type_tag, self.filters_tag = 'type', 'filters'
        self.fields_tag, self.format_tag = 'fields', 'format'

        self.time_start_tag = "time_start"
        self.time_end_tag = "time_end"
        self.time_frequency_tag = "time_frequency"
        self.time_rounding_tag = "time_rounding"
        self.time_format_tag = 'time_format'

        # reset flags
        self.reset_source = flags_dict['reset_source']
        self.reset_destination = flags_dict['reset_destination']

        # registry object(s)
        folder_name_registry = self.registry_dict[self.folder_name_tag]
        file_name_registry = self.registry_dict[self.file_name_tag]
        self.format_registry = self.registry_dict[self.format_tag]
        self.fields_registry = self.registry_dict[self.fields_tag]
        self.type_registry = self.registry_dict[self.type_tag]
        self.filters_registry = self.registry_dict[self.filters_tag]
        self.file_path_registry = os.path.join(folder_name_registry, file_name_registry)

        # datasets object(s)
        folder_name_datasets = self.datasets_dict[self.folder_name_tag]
        file_name_datasets = self.datasets_dict[self.file_name_tag]
        self.format_datasets = self.datasets_dict[self.format_tag]
        self.fields_datasets = self.datasets_dict[self.fields_tag]
        self.filters_datasets = self.datasets_dict[self.filters_tag]
        self.type_datasets = self.datasets_dict[self.type_tag]

        self.time_start = None
        if self.time_start_tag in list(self.datasets_dict.keys()):
            self.time_start = self.datasets_dict[self.time_start_tag]
        self.time_end = None
        if self.time_end_tag in list(self.datasets_dict.keys()):
            self.time_end = self.datasets_dict[self.time_end_tag]
        self.time_rounding = None
        if self.time_rounding_tag in list(self.datasets_dict.keys()):
            self.time_rounding = self.datasets_dict[self.time_rounding_tag]
        self.time_frequency = None
        if self.time_frequency_tag in list(self.datasets_dict.keys()):
            self.time_frequency = self.datasets_dict[self.time_frequency_tag]
        self.time_format = '%Y-%m-%d %H:%M'
        if self.time_format_tag in list(self.datasets_dict.keys()):
            self.time_format = self.datasets_dict[self.time_format_tag]

        # to use in realtime run
        if self.time_start is None:
            time_range = time_range.sort_values(ascending=True)
            self.time_start = time_range[0].strftime(time_format_algorithm)
        if self.time_end is None:
            time_range = time_range.sort_values(ascending=True)
            self.time_end = time_range[-1].strftime(time_format_algorithm)

        self.file_path_datasets = os.path.join(folder_name_datasets, file_name_datasets)

        # ancillary object(s)
        folder_name_ancillary = ancillary_dict[self.folder_name_tag]
        file_name_ancillary = ancillary_dict[self.file_name_tag]
        self.file_path_ancillary = os.path.join(folder_name_ancillary, file_name_ancillary)

        # tmp object(s)
        self.folder_name_tmp = tmp_dict[self.folder_name_tag]
        self.file_name_tmp = tmp_dict[self.file_name_tag]

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # method to get datasets object
    def get_obj_datasets(self, file_path_generic, file_fields=None, registry_fields=None):

        # info start method
        log_stream.info(' -----> Read file datasets ... ')

        # check file format
        if self.format_datasets == 'ascii':

            # get datasets in ascii format
            fields_dframe_obj, fields_time_start, fields_time_end = wrap_datasets_ascii(
                file_path_generic,
                time_reference=self.time_reference, time_start=self.time_start, time_end=self.time_end,
                file_fields=file_fields, registry_fields=registry_fields,
                template_time_tags=self.template_dict_time, template_datasets_tags=self.template_dict_datasets,
                time_rounding=self.time_rounding, time_frequency=self.time_frequency,
                time_format=time_format_datasets,
                file_sep=' ', file_decimal='.')

        elif self.format_datasets == 'csv':

            # get datasets in ascii format
            fields_dframe_obj = wrap_datasets_csv(
                file_path_generic,
                time_reference=self.time_reference, time_start=self.time_start, time_end=self.time_end,
                file_fields=file_fields, registry_fields=registry_fields,
                template_time_tags=self.template_dict_time, template_datasets_tags=self.template_dict_datasets,
                time_rounding=self.time_rounding, time_frequency=self.time_frequency,
                time_format=self.time_format,
                file_sep=',', file_decimal='.')

        else:
            # exit with error if file format is not supported
            log_stream.error(' ===> File format "' + self.format_datasets + '" is not supported')
            raise NotImplemented('Case not implemented yet')

        # method to range data point
        time_frequency_expected, time_start_expected, time_end_expected = range_data_point(
            fields_dframe_obj, time_run_reference=self.time_reference,
            time_start_reference=self.time_start, time_end_reference=self.time_end)

        # method to combine data point to the expected time range
        fields_dframe_obj = combine_data_point_by_time(
            fields_dframe_obj, registry_fields,
            time_start_expected=time_start_expected, time_end_expected=time_end_expected,
            time_frequency_expected=time_frequency_expected, time_reverse=True)

        # info end method
        log_stream.info(' -----> Read file datasets ... DONE')

        return fields_dframe_obj, time_start_expected, time_end_expected
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # method to get registry object
    def get_obj_registry(self, file_name, file_fields=None, file_filters=None):

        # info start method
        log_stream.info(' -----> Read file registry "' + file_name + '" ... ')

        # check file format
        if self.format_registry == 'mat':
            # get registry in mat format
            fields_dframe = wrap_registry_mat(file_name, file_fields=file_fields, folder_tmp=self.folder_name_tmp)
        elif self.format_registry == 'csv':
            # get registry in csv format
            fields_dframe = wrap_registry_csv(file_name, file_fields=file_fields, file_filters=file_filters)
        else:
            # exit with error if file format is not supported
            log_stream.info(' -----> Read file registry "' + file_name + '" ... FAILED')
            log_stream.error(' ===> File format is not supported')
            raise NotImplemented('Case not implemented yet')

        # info end method
        log_stream.info(' -----> Read file registry "' + file_name + '" ... DONE')

        return fields_dframe

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # method to organize data
    def organize_data(self):

        # method start info
        log_stream.info(' ----> Organize source object(s) ... ')

        # get time reference
        time_step_reference = self.time_reference

        # get template tag(s)
        template_time_tags, template_datasets_tags = self.template_dict_time, self.template_dict_datasets

        # get path(s)
        file_path_registry_generic, file_path_datasets_generic = self.file_path_registry, self.file_path_datasets
        file_path_ancillary_generid = self.file_path_ancillary

        # get flag(s)
        reset_source = self.reset_source

        # fill time tags
        template_time_values = fill_tags_time(template_time_tags, time_reference=time_step_reference)
        template_datasets_values = {}

        # create template tags and values
        template_generic_tags = {**template_time_tags, **template_datasets_tags}
        template_generic_values = {**template_time_values, **template_datasets_values}

        # define file path
        file_path_ancillary_def = fill_tags2string(
            file_path_ancillary_generid, tags_format=template_generic_tags, tags_filling=template_generic_values)[0]

        # reset ancillary file
        if reset_source:
            if os.path.exists(file_path_ancillary_def):
                os.remove(file_path_ancillary_def)

        # check ancillary file availability
        if not os.path.exists(file_path_ancillary_def):

            # get registry dframe
            dframe_registry = self.get_obj_registry(
                file_path_registry_generic, self.fields_registry, self.filters_registry)
            # get datasets dframe
            dframe_datasets, dframe_time_start, dframe_time_end = self.get_obj_datasets(
                file_path_datasets_generic, self.fields_datasets, dframe_registry)

            # check time start and end to organize dframe data
            if (dframe_time_start is not None) and (dframe_time_end is not None):

                # organize dframe obj
                dframe_obj = {
                    'registry': dframe_registry, 'datasets': dframe_datasets,
                    'time_start': dframe_time_start, 'time_end': dframe_time_end
                }

                # dump dframe obj
                folder_name_ancillary, file_name_ancillary = os.path.split(file_path_ancillary_def)
                make_folder(folder_name_ancillary)
                write_obj(file_path_ancillary_def, dframe_obj)

                # method end info
                log_stream.info(' ----> Organize source object(s) ... DONE')
            else:
                # set dataframe to NoneType (all data are not available)
                dframe_obj = None
                # method end info
                log_stream.info(' ----> Organize source object(s) ... SKIPPED. All datasets are not available')

        else:
            # read source obj
            dframe_obj = read_obj(file_path_ancillary_def)
            # method end info
            log_stream.info(' ----> Organize source object(s) ... DONE. Datasets previously saved')

        return dframe_obj

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
