"""
Class Features

Name:          drv_configuration_algorithm_rfarm
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20201102'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging
import os
import re

from collections import OrderedDict

from src.hyde.algorithm.io.model.rfarm.lib_rfarm_io_generic import read_file_settings
from src.hyde.algorithm.utils.rfarm.lib_rfarm_generic import make_folder, get_dict_values
from src.hyde.algorithm.utils.rfarm.lib_rfarm_logging import set_logging_file

from src.hyde.algorithm.settings.model.rfarm.lib_rfarm_args import  logger_name, \
    logger_formatter, logger_handle

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Class Tags
class DriverAlgorithm:

    # -------------------------------------------------------------------------------------
    # Method class initialization
    def __init__(self, file_name_settings,
                 tag_folder_name='folder', tag_file_name='filename', tag_file_history='file_history',
                 tag_algorithm_dataset='data', tag_algorithm_colormap='colormap', tag_algorithm_flag='flags',
                 tag_algorithm_logging='log'):

        # -------------------------------------------------------------------------------------
        # Store information in global workspace
        self.file_name_settings = file_name_settings

        self.tag_folder_name = tag_folder_name
        self.tag_file_name = tag_file_name
        self.tag_file_history = tag_file_history
        self.tag_algorithm_dataset = tag_algorithm_dataset
        self.tag_algorithm_colormap = tag_algorithm_colormap
        self.tag_algorithm_flag = tag_algorithm_flag
        self.tag_algorithm_logging = tag_algorithm_logging

        self.file_defined_keys = dict(key_1=self.tag_folder_name, key_2=self.tag_file_name)

        self.algorithm_settings = read_file_settings(self.file_name_settings)

        algorithm_data = self.algorithm_settings['data']
        self.folder_name_logging = algorithm_data[self.tag_algorithm_logging][self.tag_folder_name]
        self.file_name_logging = algorithm_data[self.tag_algorithm_logging][self.tag_file_name]

        if self.tag_file_history in list(algorithm_data[self.tag_algorithm_logging].keys()):
            self.file_history_logging = algorithm_data[self.tag_algorithm_logging][self.tag_file_history]
        else:
            self.file_history_logging = True

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to set file path(s)
    @staticmethod
    def define_file_path(file_obj, file_keys_list=None):

        if file_keys_list is None:
            file_keys_list = ['folder_name', 'file_name']

        file_keys_order = OrderedDict(sorted(file_keys_list.items()))

        file_path_def = {}
        for file_type_str, file_type_obj in file_obj.items():

            file_path_parts = []
            for file_order_key, file_order_value in file_keys_order.items():

                file_ext = get_dict_values(file_type_obj, file_order_value)

                if file_ext is not None:
                    if not file_path_parts:
                        file_path_parts = file_ext
                    else:
                        file_path_parts = os.path.join(file_path_parts, file_ext)

            if not file_path_parts:
                file_path_parts = None

            file_path_def[file_order_key] = file_path_parts

        return file_path_def

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to search root path
    @staticmethod
    def define_root_path(generic_paths):

        if not isinstance(generic_paths, list):
            generic_paths = [generic_paths]

        root_paths = []
        for step_path in generic_paths:
            string_patterns = re.findall(r"\{([A-Za-z0-9_]+)\}", step_path)

            dict_patterns = {}
            for string_pattern in string_patterns:
                dict_patterns[string_pattern] = ''

            root_path = step_path.format(**dict_patterns)

            root_paths.append(root_path)

        for root_path in root_paths:
            make_folder(root_path)

        return root_paths

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to filter data in settings file
    def filter_data(self, data_collections, data_keys_list=None):

        if data_keys_list is None:
            data_keys_list = ['folder_name', 'file_name']

        data_dict = {}
        for data_step in data_collections:

            if isinstance(data_step, list):
                data_name = data_step[0]
                data_field = data_step[1]
            elif isinstance(data_step, str):
                data_name = data_step
                data_field = data_collections[data_step]
            else:
                logging.error(' ===> Filtering data failed in collections obj')
                raise NotImplementedError('Datatype not allowed yet')

            if isinstance(data_field, dict):

                if all(data_keys_ref in data_field for data_keys_ref in data_keys_list):
                    data_dict[data_name] = data_field
                else:
                    data_dict_upd = self.filter_data(data_field, data_keys_list)

                    if data_dict:
                        for data_key, data_value in data_dict_upd.items():
                            data_dict[data_key] = data_value
                    else:
                        data_dict = data_dict_upd

            elif isinstance(data_field, str):
                data_dict[data_name] = data_field

        return data_dict

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to select data
    @staticmethod
    def select_data(file_data, key_data='folder_name'):
        data = get_dict_values(file_data, key_data, [])
        return data
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Set algorithm default values (for backward compatibility)
    @staticmethod
    def set_algorithm_default(algorithm_settings):
        if 'algorithm_mode' not in list(algorithm_settings['algorithm']['ancillary'].keys()):
            algorithm_settings['algorithm']['ancillary']['algorithm_mode'] = 'exec_nwp'
        return algorithm_settings
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to set algorithm info
    def set_algorithm_info(self):

        # Get data settings
        algorithm_settings = self.algorithm_settings
        algorithm_settings = self.set_algorithm_default(algorithm_settings)

        # Set algorithm root path(s)
        algorithm_generic_paths = self.select_data(algorithm_settings, self.tag_folder_name)
        algorithm_root_info = self.define_root_path(algorithm_generic_paths)

        # Set algorithm dataset info
        algorithm_dataset_obj = self.select_data(algorithm_settings, self.tag_algorithm_dataset)
        algorithm_dataset_info = self.filter_data(algorithm_dataset_obj, [self.tag_folder_name, self.tag_file_name])

        # Set algorithm colormap info
        algorithm_colormap_obj = self.select_data(algorithm_settings, self.tag_algorithm_colormap)
        algorithm_colormap_info = self.filter_data(algorithm_colormap_obj, [self.tag_folder_name, self.tag_file_name])

        return algorithm_settings, algorithm_dataset_info, algorithm_colormap_info
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to set algorithm logging
    def set_algorithm_logging(self):

        folder_name = self.folder_name_logging
        file_name = self.file_name_logging
        file_history = self.file_history_logging

        if not os.path.exists(folder_name):
            make_folder(folder_name)

        set_logging_file(
            os.path.join(folder_name, file_name), logger_name=logger_name, logger_formatter=logger_formatter,
            logger_handle=logger_handle, logger_history=file_history)

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
