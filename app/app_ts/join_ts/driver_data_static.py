"""
Class Features

Name:          driver_data_static
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20231010'
Version:       '1.0.0'
"""

# ----------------------------------------------------------------------------------------------------------------------
# libraries
import logging
import os

from lib_data_io_geo import read_point_data

from lib_info_args import logger_name

# logging
log_stream = logging.getLogger(logger_name)

# debugging
# import matplotlib.pylab as plt
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Class DriverData
class DriverData:

    # ------------------------------------------------------------------------------------------------------------------
    # Initialize class
    def __init__(self, point_dict, tmp_dict=None):

        # get arg(s)
        self.point_dict = point_dict
        self.tmp_dict = tmp_dict
        # set tag(s)
        self.file_name_tag, self.folder_name_tag = 'file_name', 'folder_name'
        self.fields_tag, self.format_tag, self.filters_tag = 'fields', 'format', 'filters'

        # point object(s)
        folder_name_pnt = self.point_dict[self.folder_name_tag]
        file_name_pnt = self.point_dict[self.file_name_tag]
        self.file_path_pnt = os.path.join(folder_name_pnt, file_name_pnt)
        self.fields_pnt = self.point_dict[self.fields_tag]
        self.format_pnt = self.point_dict[self.format_tag]
        if self.filters_tag in list(self.point_dict.keys()):
            self.filters_pnt = self.point_dict[self.filters_tag]
        else:
            self.filters_pnt = None

        # tmp object(s)
        self.folder_name_tmp_raw = self.tmp_dict[self.folder_name_tag]
        self.file_name_tmp_raw = self.tmp_dict[self.file_name_tag]

    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
    # Method to get point file
    def get_point(self, file_name):

        # info start
        log_stream.info(' -----> Read file point "' + file_name + '" ... ')

        # check file availability
        if self.format_pnt == 'csv':
            # read data
            point_obj = read_point_data(file_name, file_filters=self.filters_pnt, file_columns_remap=self.fields_pnt)
            # info end
            log_stream.info(' -----> Read file point "' + file_name + '" ... DONE')
        else:
            # info end with error(s)
            log_stream.info(' -----> Read file point "' + file_name + '" ... FAILED')
            log_stream.error(' ===> File is mandatory to run the application')
            raise FileNotFoundError('File not found')

        return point_obj
    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------------------------------------------
    # method to organize data
    def organize_data(self):

        # method start info
        log_stream.info(' ----> Organize static object(s) ... ')

        # get file path(s)
        file_path_pnt = self.file_path_pnt

        # get point obj
        obj_point = self.get_point(file_path_pnt)
        # merge objects to collections
        obj_collections = {'point_obj': obj_point}

        # method end info
        log_stream.info(' ----> Organize static object(s) ... DONE')

        return obj_collections
    # ------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------
