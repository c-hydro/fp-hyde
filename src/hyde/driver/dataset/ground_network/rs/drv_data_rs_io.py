"""
Class Features

Name:          drv_data_rs_io
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20201210'
Version:       '1.0.0'
"""

#######################################################################################

# -------------------------------------------------------------------------------------
# Libraries
import logging
import os
import time

import numpy as np
import xarray as xr
import pandas as pd

from src.hyde.algorithm.settings.ground_network.lib_rs_conventions import conventions_vars
from src.hyde.dataset.ground_network.rs.lib_rs_variables import convert_values2points

from src.hyde.algorithm.io.ground_network.lib_rs_io_generic import write_obj, read_obj, \
    create_dset, write_dset, read_file_csv, write_file_ascii
from src.hyde.algorithm.utils.ground_network.lib_rs_generic import make_folder, fill_tags2string, list_folder, \
    get_root_path

from src.hyde.algorithm.io.ground_network.lib_rs_io_gzip import zip_filename
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class driver geographical data
class DriverData:

    def __init__(self, time_step, geo_collections=None,
                 src_dict=None, ancillary_dict=None, dst_dict=None,
                 variable_src_dict=None, variable_dst_dict=None, time_dict=None, template_dict=None, info_dict=None,
                 flag_updating_ancillary=True, flag_updating_destination=True, flag_cleaning_tmp=True):

        self.time_step = time_step
        self.geo_collections = geo_collections

        self.src_dict = src_dict
        self.ancillary_dict = ancillary_dict
        self.dst_dict = dst_dict
        self.time_dict = time_dict
        self.variable_src_dict = variable_src_dict
        self.variable_dst_dict = variable_dst_dict
        self.template_dict = template_dict

        self.tag_folder_name = 'folder_name'
        self.tag_file_name = 'file_name'
        self.tag_file_fields = 'file_fields'
        self.tag_file_compression = 'file_compression'

        self.domain_name = info_dict['domain']
        self.variable_src_list = list(self.variable_src_dict.keys())
        self.variable_dst_list = list(self.variable_dst_dict.keys())

        self.time_range = self.collect_file_time()

        self.file_fields_collections = {}
        self.file_path_src_dset_collections = {}
        for variable_step in self.variable_src_list:
            folder_name_src_dset_raw = self.src_dict[variable_step][self.tag_folder_name]
            file_name_src_dset_raw = self.src_dict[variable_step][self.tag_file_name]
            file_path_src_dset_list = self.collect_file_list(folder_name_src_dset_raw, file_name_src_dset_raw,
                                                             variable_step)

            self.file_fields_collections[variable_step] = self.src_dict[variable_step][self.tag_file_fields]
            self.file_path_src_dset_collections[variable_step] = file_path_src_dset_list

        self.folder_name_anc_dset_raw = self.ancillary_dict[self.tag_folder_name]
        self.file_name_anc_dset_raw = self.ancillary_dict[self.tag_file_name]
        self.file_path_anc_dset_collections = self.collect_file_list(
            self.folder_name_anc_dset_raw, self.file_name_anc_dset_raw)

        self.folder_name_anc_dset_root = get_root_path(self.folder_name_anc_dset_raw)

        self.folder_name_dst_dset_raw = self.dst_dict[self.tag_folder_name]
        self.file_name_dst_dset_raw = self.dst_dict[self.tag_file_name]
        self.file_path_dst_dset_collections = self.collect_file_list(
            self.folder_name_dst_dset_raw, self.file_name_dst_dset_raw)

        if self.tag_file_compression in list(self.dst_dict.keys()):
            self.file_compression_dst = self.dst_dict[self.tag_file_compression]
        else:
            self.file_compression_dst = False
        self.file_zip_dst_dset_raw = self.add_file_extension(self.file_name_dst_dset_raw, file_extension='.gz')
        self.file_zip_dst_dset_collections = self.collect_file_list(
            self.folder_name_dst_dset_raw, self.file_zip_dst_dset_raw)

        self.flag_updating_ancillary = flag_updating_ancillary
        self.flag_updating_destination = flag_updating_destination
        self.flag_cleaning_tmp = flag_cleaning_tmp

        self.tag_dim_geo_x = 'longitude'
        self.tag_dim_geo_y = 'latitude'

        self.tag_var_file = ['code', 'discharge', 'tag']

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to add zip extension to filename
    @staticmethod
    def add_file_extension(file_name, file_extension='.gz'):
        if not file_name.endswith('.gz'):
            file_name_filled = file_name + file_extension
        else:
            file_name_filled = file_name
        return file_name_filled
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to collect time(s)
    def collect_file_time(self):

        time_period = self.time_dict["time_period"]
        time_frequency = self.time_dict["time_frequency"]
        time_rounding = self.time_dict["time_rounding"]

        time_end = self.time_step.floor(time_rounding)

        time_range = pd.date_range(end=time_end, periods=time_period, freq=time_frequency)

        return time_range
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to collect ancillary file
    def collect_file_list(self, folder_name_raw, file_name_raw, file_variable=None):

        domain_name = self.domain_name
        file_name_list = []
        for datetime_step in self.time_range:

            template_values_step = {
                'domain_name': domain_name,
                'source_var_name': file_variable,
                'ancillary_var_name': file_variable,
                'destination_var_name': file_variable,
                'source_datetime': datetime_step, 'source_sub_path_time': datetime_step,
                'ancillary_datetime': datetime_step, 'ancillary_sub_path_time': datetime_step,
                'destination_datetime': datetime_step, 'destination_sub_path_time': datetime_step}

            folder_name_def = fill_tags2string(
                folder_name_raw, self.template_dict, template_values_step)
            file_name_def = fill_tags2string(
                file_name_raw, self.template_dict, template_values_step)
            file_path_def = os.path.join(folder_name_def, file_name_def)

            file_name_list.append(file_path_def)

        return file_name_list

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to write dataset in dictionary format
    @staticmethod
    def write_dset_obj(file_name, file_dict):
        write_obj(file_name, file_dict)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to load dataset saved in dictionary format
    @staticmethod
    def read_dset_obj(file_name):
        file_dict = read_obj(file_name)
        return file_dict
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to add global attributes
    @staticmethod
    def add_global_attributes(global_attrs):
        if global_attrs is None:
            global_attrs = {}
        if 'file_date' not in list(global_attrs.keys()):
            global_attrs['file_date'] = 'Created ' + time.ctime(time.time())
        if 'nodata_value' not in list(global_attrs.keys()):
            global_attrs['nodata_value'] = -9999.0
        return global_attrs
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to dump datasets
    def dump_data(self):

        logging.info(' ----> Dump datasets ... ')

        time_range = self.time_range
        geo_collections = self.geo_collections

        global_attrs = self.add_global_attributes(geo_collections.attrs)

        file_path_anc_collections = self.file_path_anc_dset_collections
        file_path_dst_collections = self.file_path_dst_dset_collections
        file_path_zip_collections = self.file_zip_dst_dset_collections

        var_dict_dst = self.variable_dst_dict

        flag_upd_dst = self.flag_updating_destination

        for id, time_step in enumerate(time_range):

            logging.info(' -----> Time ' + str(time_step) + ' ... ')

            var_file_path_anc = file_path_anc_collections[id]
            var_file_path_dst = file_path_dst_collections[id]
            var_file_path_zip = file_path_zip_collections[id]

            if flag_upd_dst:
                if os.path.exists(var_file_path_dst):
                    os.remove(var_file_path_dst)
                if os.path.exists(var_file_path_zip):
                    os.remove(var_file_path_zip)

            if self.file_compression_dst:
                var_file_path_check = var_file_path_zip
            else:
                var_file_path_check = var_file_path_dst

            if not os.path.exists(var_file_path_check):
                if os.path.exists(var_file_path_anc):

                    logging.info(' ------> Create array object ... ')

                    var_dict_anc = self.read_dset_obj(var_file_path_anc)

                    # Iterate over variables
                    var_data_dict = {}
                    var_attrs_dict = {}
                    for var_key_anc in list(var_dict_anc.keys()):

                        logging.info(' -------> Variable ' + var_key_anc + ' ... DONE')

                        var_da_anc = var_dict_anc[var_key_anc]
                        var_name_dst = var_dict_dst[var_key_anc]['var_name']
                        var_mode_dst = var_dict_dst[var_key_anc]['var_mode']
                        var_attrs_dst = var_dict_dst[var_key_anc]['var_attributes']

                        if var_mode_dst:

                            var_value_list = []
                            for var_da_step in var_da_anc:
                                var_row_list = []
                                for var_file in self.tag_var_file:
                                    var_value_tmp = var_da_step[var_file].values[0]
                                    var_row_list.append(var_value_tmp)
                                var_value_list.append(var_row_list)

                            var_data_dict[var_name_dst] = var_value_list
                            var_attrs_dict[var_name_dst] = var_attrs_dst
                            logging.info(' -------> Variable ' + var_key_anc + ' ... DONE')
                        else:

                            logging.info(' -------> Variable ' + var_key_anc + ' ... SKIPPED. Variable not selected')

                    # Save data using a 1d ascii file
                    logging.info(' ------> Save file ascii ... ')
                    var_folder_name_dst, var_file_name_dst = os.path.split(var_file_path_dst)
                    make_folder(var_folder_name_dst)
                    for (var_dst, data_dst), attrs_dst in zip(var_data_dict.items(), var_attrs_dict.values()):
                        write_file_ascii(var_file_path_dst, data_dst,
                                         file_fields=self.tag_var_file, file_attrs=attrs_dst)
                    logging.info(' ------> Save file ascii ... DONE')

                    logging.info(' ------> Zip file ... ')
                    if self.file_compression_dst:

                        zip_filename(var_file_path_dst, var_file_path_zip)
                        if os.path.exists(var_file_path_dst):
                            os.remove(var_file_path_dst)

                        logging.info(' ------> Zip file ... DONE')
                    else:
                        logging.info(' ------> Zip file ... SKIPPED. Compression not activated')

                    logging.info(' -----> Time ' + str(time_step) + ' ... DONE.')
                else:
                    logging.info(' -----> Time ' + str(time_step) + ' ... SKIPPED. Ancillary file not found')
            else:
                logging.info(' -----> Time ' + str(time_step) + ' ... SKIPPED. Datasets file previously saved')

        logging.info(' ----> Dump datasets ... DONE')

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to organize datasets
    def organize_data(self):

        logging.info(' ----> Organize datasets ... ')

        time_range = self.time_range
        geo_collections = self.geo_collections

        file_fields_collections = self.file_fields_collections
        file_path_src_collections = self.file_path_src_dset_collections
        file_path_anc_collections = self.file_path_anc_dset_collections

        var_src_dict = self.variable_src_dict

        flag_upd_anc = self.flag_updating_ancillary

        for id, time_step in enumerate(time_range):

            logging.info(' -----> Time ' + str(time_step) + ' ... ')

            var_file_path_anc = file_path_anc_collections[id]

            if flag_upd_anc:
                if os.path.exists(var_file_path_anc):
                    os.remove(var_file_path_anc)

            if not os.path.exists(var_file_path_anc):

                var_dict = None
                for var_key, var_fields in var_src_dict.items():

                    logging.info(' ------> Variable ' + var_key + ' ... ')

                    var_mode = var_fields['var_mode']
                    var_name = var_fields['var_name']
                    var_method_compute = var_fields['var_method_compute']
                    var_attributes = var_fields['var_attributes']

                    var_file_path_src = file_path_src_collections[var_key][id]
                    var_file_list = file_fields_collections[var_key]

                    if var_mode:

                        logging.info(' -------> Get data ... ')
                        if os.path.exists(var_file_path_src):
                            var_file_data_src = read_file_csv(var_file_path_src,
                                                              tag_file_data='discharge',
                                                              file_time=time_step, file_header=var_file_list,
                                                              file_renamecols=None,
                                                              file_skipcols=None)
                            logging.info(' -------> Get data  ... DONE')
                        else:
                            logging.info(' -------> Get data  ... FAILED')
                            logging.warning(' ===> File not found ' + var_file_path_src)
                            var_file_data_src = None

                        logging.info(' -------> Compute data ... ')
                        if var_file_data_src is not None:

                            if var_dict is None:
                                var_dict = {}

                            if var_method_compute is None:
                                var_tag = var_key
                            else:
                                logging.error(' ===> Variable compute method is not allowed for river stations')
                                raise NotImplementedError('Case not implemented yet')

                            var_dict[var_tag] = convert_values2points(var_file_data_src, geo_collections,
                                                                      tag_file_fields=self.tag_var_file)

                            logging.info(' -------> Compute data ... DONE')
                            logging.info(' ------> Variable ' + var_key + ' ... DONE')
                        else:
                            logging.info(' -------> Compute data ... FAILED. Variable dataset is undefined')
                            logging.info(' ------> Variable ' + var_key + ' ... SKIPPED. Variable dataset is undefined')

                    else:
                        logging.info(' -----> Variable ' + var_key + ' ... SKIPPED. Variable mode not activated.')

                if var_dict is not None:
                    var_folder_name_anc, var_file_name_anc = os.path.split(var_file_path_anc)
                    make_folder(var_folder_name_anc)

                    self.write_dset_obj(var_file_path_anc, var_dict)

                    logging.info(' -----> Time ' + str(time_step) + ' ... DONE')

                else:
                    logging.info(' -----> Time ' + str(time_step) + ' ... SKIPPED. Datasets are undefined')

            else:
                logging.info(' -----> Time ' + str(time_step) + ' ... SKIPPED. Datasets are previously computed')

        logging.info(' ----> Organize datasets ... DONE')

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to clean temporary information
    def clean_tmp(self):

        file_path_anc_list = self.file_path_anc_dset_collections
        clean_tmp = self.flag_cleaning_tmp
        folder_name_anc_main = self.folder_name_anc_dset_root

        if clean_tmp:

            # Remove tmp file and folder(s)
            for file_path_step in file_path_anc_list:
                if os.path.exists(file_path_step):
                    os.remove(file_path_step)
                var_folder_name_step, var_file_name_step = os.path.split(file_path_step)
                if var_folder_name_step != '':
                    if os.path.exists(var_folder_name_step):
                        if not os.listdir(var_folder_name_step):
                            os.rmdir(var_folder_name_step)

            # Remove empty folder(s)
            folder_name_anc_list = list_folder(folder_name_anc_main)
            for folder_name_anc_step in folder_name_anc_list:
                if os.path.exists(folder_name_anc_step):
                    if not any(os.scandir(folder_name_anc_step)):
                        os.rmdir(folder_name_anc_step)

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
