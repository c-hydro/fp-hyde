"""
Class Features

Name:          drv_data_ef_io
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20201202'
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

from src.hyde.algorithm.analysis.expert_forecast.lib_ef_analysis import find_slopes
from src.hyde.algorithm.settings.expert_forecast.lib_ef_conventions import conventions_vars

from src.hyde.algorithm.io.expert_forecast.lib_ef_io_generic import write_obj, read_obj, read_file_csv, \
    save_file_json, create_default_dframe
from src.hyde.algorithm.utils.expert_forecast.lib_ef_generic import make_folder, fill_tags2string, list_folder, \
    get_root_path, get_dict_values

#from src.hyde.algorithm.analysis.satellite.modis.lib_modis_analysis_interpolation_grid import interp_grid2index
#from src.hyde.driver.dataset.satellite.modis.cpl_data_variables_modis import DriverVariable
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class driver dynamic data
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
        self.tag_file_compression = 'file_compression'

        self.tag_file_path_grid = 'file_path_grid'

        self.domain_info = info_dict['domain']

        self.group_collection = info_dict['group']

        self.group_variables_list_in = ['rain_average', 'rain_peak']
        self.group_variables_list_out = ['slope_x', 'slope_y', 'slope_t']

        self.group_subdomain_list = []
        for group_key, group_data in self.group_collection.items():
            self.group_subdomain_list.append(group_data['name'])

        self.variable_src_list = list(self.variable_src_dict.keys())
        self.variable_dst_list = list(self.variable_dst_dict.keys())

        self.time_file_range = self.collect_file_time()
        self.time_dataset_collection = self.collect_dataset_time(self.time_file_range)

        self.folder_name_src_raw = self.src_dict[self.tag_folder_name]
        self.file_name_src_raw = self.src_dict[self.tag_file_name]
        self.file_path_src_collections = self.collect_file_list(self.folder_name_src_raw, self.file_name_src_raw,
                                                                file_time=self.time_file_range)

        self.folder_name_anc_raw = self.ancillary_dict[self.tag_folder_name]
        self.file_name_anc_raw = self.ancillary_dict[self.tag_file_name]
        self.file_path_anc = self.collect_file_list(self.folder_name_anc_raw, self.file_name_anc_raw,
                                                    file_time=self.time_step)[0]

        self.folder_name_dst_raw = self.dst_dict[self.tag_folder_name]
        self.file_name_dst_raw = self.dst_dict[self.tag_file_name]
        self.file_path_dst_collections = self.collect_file_list(
            self.folder_name_dst_raw, self.file_name_dst_raw,
            file_time=self.time_step, file_extra_info={'alert_area_name': self.group_subdomain_list})

        self.flag_updating_ancillary = flag_updating_ancillary
        self.flag_updating_destination = flag_updating_destination
        self.flag_cleaning_tmp = flag_cleaning_tmp

        self.folder_name_anc_root = get_root_path(self.folder_name_anc_raw)

        self.tag_dim_time = 'time'
        self.tag_coord_time = 'time'

        self.tag_slopes_data = 'slopes'
        self.tag_geo_data = 'terrain'

        self.vm_data = self.geo_collections[self.tag_slopes_data]['vm']
        self.rain_avg_array = self.geo_collections[self.tag_slopes_data]['r_avg']
        self.slope_x_array = self.geo_collections[self.tag_slopes_data]['sx']
        self.slope_y_array = self.geo_collections[self.tag_slopes_data]['sy']
        self.slope_t_array = self.geo_collections[self.tag_slopes_data]['st']

        self.var_nodata = 0.0

        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to collect time(s)
    def collect_file_time(self, reverse=True):

        time_period = self.time_dict["time_file_period"]
        time_frequency = self.time_dict["time_file_frequency"]
        time_rounding = self.time_dict["time_file_rounding"]
        time_eta = self.time_dict["time_file_eta"]

        time_end = self.time_step.floor(time_rounding)
        time_end = time_end.replace(hour=int(time_eta))

        time_range = pd.date_range(end=time_end, periods=time_period, freq=time_frequency)

        if reverse:
            time_range = time_range[::-1]

        return time_range
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to collect dataset time(s)
    def collect_dataset_time(self, time_file_range):

        time_period = self.time_dict["time_dataset_period"]
        time_frequency = self.time_dict["time_dataset_frequency"]
        time_rounding = self.time_dict["time_dataset_rounding"]
        time_eta = self.time_dict["time_dataset_eta"]

        time_dataset_collection = {}
        for time_step in time_file_range:

            time_start = time_step.floor(time_rounding)
            time_start = time_start.replace(hour=int(time_eta))
            time_dataset_range = pd.date_range(start=time_start, periods=time_period, freq=time_frequency)
            time_dataset_collection[time_step] = time_dataset_range

        return time_dataset_collection
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to collect ancillary file
    def collect_file_list(self, folder_name_raw, file_name_raw, file_time=None, file_variable=None,
                          file_extra_info=None):

        domain_info = self.domain_info
        file_name_list = []

        if file_time is None:
            file_time = self.time_file_range

        if isinstance(file_time, pd.Timestamp):
            file_time = pd.DatetimeIndex([file_time])
        elif isinstance(file_time, pd.DatetimeIndex):
            pass
        else:
            logging.error(' ===> File time list format is not allowed')
            raise NotImplementedError('Case not implemented yet')

        for datetime_step in file_time:

            template_values_step = {
                'domain_name': domain_info,
                'source_var_name': file_variable,
                'ancillary_var_name': file_variable,
                'destination_var_name': file_variable,
                'source_datetime': datetime_step, 'source_sub_path_time': datetime_step,
                'ancillary_datetime': datetime_step, 'ancillary_sub_path_time': datetime_step,
                'destination_datetime': datetime_step, 'destination_sub_path_time': datetime_step}

            if file_extra_info is None:
                folder_name_def = fill_tags2string(
                    folder_name_raw, self.template_dict, template_values_step)
                file_name_def = fill_tags2string(
                    file_name_raw, self.template_dict, template_values_step)
                file_path_def = os.path.join(folder_name_def, file_name_def)

                file_name_list.append(file_path_def)

            else:

                for file_key, file_fields in file_extra_info.items():
                    for file_field in file_fields:
                        template_values_step[file_key] = file_field
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
    def write_dset_obj(file_name, file_obj):
        if isinstance(file_obj, xr.Dataset):
            file_data = file_obj.to_dict()
        else:
            file_data = file_obj
        write_obj(file_name, file_data)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to load dataset saved in dictionary format
    @staticmethod
    def read_dset_obj(file_name, data_format='dictionary'):
        file_data = read_obj(file_name)
        if data_format == 'dataset':
            file_obj = xr.Dataset.from_dict(file_data)
        else:
            file_obj = file_data
        return file_obj
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to add global attributes
    def add_global_attributes(self, global_attrs=None):
        if global_attrs is None:
            global_attrs = {}
        if 'file_date' not in list(global_attrs.keys()):
            global_attrs['file_date'] = 'Created ' + time.ctime(time.time())
        if 'nodata_value' not in list(global_attrs.keys()):
            global_attrs['nodata_value'] = self.var_nodata
        return global_attrs
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to dump datasets
    def dump_data(self):

        logging.info(' ----> Dump datasets ... ')

        time_step = self.time_step
        var_file_path_anc = self.file_path_anc
        var_file_path_dst_collections = self.file_path_dst_collections

        var_dict_dst = self.variable_dst_dict
        flag_upd_dst = self.flag_updating_destination

        logging.info(' -----> Time ' + str(time_step) + ' ... ')
        if flag_upd_dst:
            for var_file_path_dst in var_file_path_dst_collections:
                if os.path.exists(var_file_path_dst):
                    os.remove(var_file_path_dst)

        if os.path.exists(var_file_path_anc):

            logging.info(' ------> Save dataset object ... ')

            # Get data
            var_dict_anc = self.read_dset_obj(var_file_path_anc)

            # Iterate over variables
            for (var_key_anc, var_dframe_anc), var_file_path_dst in zip(
                    var_dict_anc.items(), var_file_path_dst_collections):

                logging.info(' -------> Alert area ' + var_key_anc + ' ... ')

                global_attrs = self.add_global_attributes({'name': var_key_anc})

                var_folder_name_dst, var_file_name_dst = os.path.split(var_file_path_dst)
                make_folder(var_folder_name_dst)

                var_dict_anc = var_dframe_anc.to_dict()
                save_file_json(var_file_path_dst, var_dict_anc, file_attrs=global_attrs)

                logging.info(' -------> Alert area ' + var_key_anc + ' ... DONE')

            logging.info(' ------> Save dataset object ... DONE')

            logging.info(' -----> Time ' + str(time_step) + ' ... DONE.')
        else:
            logging.info(' -----> Time ' + str(time_step) + ' ... SKIPPED. All datasets are undefined')

        logging.info(' ----> Dump datasets ... DONE')

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to organize datasets
    def organize_data(self):

        logging.info(' ----> Organize datasets ... ')

        time_step = self.time_step
        time_file_range = self.time_file_range
        time_dataset_collection = self.time_dataset_collection

        slopes_collections = self.geo_collections[self.tag_slopes_data]
        group_collection = self.group_collection

        group_variables_list_in = self.group_variables_list_in
        group_variables_list_out = self.group_variables_list_out

        file_path_src_list = self.file_path_src_collections

        var_src_name = self.variable_src_list[0]
        var_src_dict = self.variable_src_dict

        flag_upd_anc = self.flag_updating_ancillary

        var_file_path_anc = self.file_path_anc
        if flag_upd_anc:
            if os.path.exists(var_file_path_anc):
                os.remove(var_file_path_anc)

        if not os.path.exists(var_file_path_anc):

            var_src_collection = {}
            for id, time_file_step in enumerate(time_file_range):

                logging.info(' -----> Time ' + str(time_file_step) + ' ... ')

                var_src_fields = var_src_dict[var_src_name]

                var_src_mode = var_src_fields['var_mode']
                var_src_name = var_src_fields['var_name']
                var_src_method_compute = var_src_fields['var_method_compute']
                var_src_attributes = var_src_fields['var_attributes']

                var_file_path_src = file_path_src_list[id]

                logging.info(' ------> Get data ... ')
                if var_src_mode:
                    if os.path.exists(var_file_path_src):
                        var_file_data_src = read_file_csv(var_file_path_src)
                        logging.info(' ------> Get data ... DONE')
                    else:
                        logging.info(' ------> Get data ... FAILED')
                        logging.warning(' ===> File not found ' + var_file_path_src)
                        var_file_data_src = None
                else:
                    logging.info(' ------> Get data ... SKIPPED. Variable ' + var_src_name + ' not activated')
                    var_file_data_src = None

                var_src_collection[time_file_step] = {}
                var_src_collection[time_file_step] = var_file_data_src

                logging.info(' -----> Time ' + str(time_file_step) + ' ... DONE')

            logging.info(' -----> Compute data ... ')

            for var_src_key, var_src_data in var_src_collection.items():
                var_src_check = False
                if var_src_data is not None:
                    var_src_shape = var_src_data.shape
                    var_src_columns = list(var_src_data.columns)
                    var_default_data = create_default_dframe(var_src_columns, var_src_shape,
                                                             df_nodata=self.var_nodata)
                    var_src_check = True
                    break

            if var_src_check:

                var_collections = None
                for (var_src_key, var_src_data), var_time_data in zip(var_src_collection.items(),
                                                                      time_dataset_collection.values()):

                    if var_collections is None:
                        var_collections = {}

                    for group_key, group_data in group_collection.items():
                        group_variables = group_data['variables']

                        var_dict = {}
                        for group_key_step_in in group_variables_list_in:
                            group_data_step = group_variables[group_key_step_in]
                            for var_time, (var_key, var_data) in zip(var_time_data, group_data_step.items()):

                                var_tag = var_data['tag']

                                if var_src_data is not None:
                                    if var_tag in list(var_src_data.columns):
                                        var_value = var_src_data[var_tag].values[0]
                                        var_value = np.float64(var_value)
                                    else:
                                        var_value = self.var_nodata
                                else:
                                    var_value = var_default_data[var_tag].values[0]

                                if group_key_step_in not in var_dict:
                                    var_dict[group_key_step_in] = {}
                                var_dict[group_key_step_in][var_time] = var_value

                        var_df_step = pd.DataFrame.from_dict(var_dict)
                        var_df_step.index.name = self.tag_dim_time

                        # compute slope(s)
                        var_rain_avg_step = var_df_step[self.group_variables_list_in[0]].values
                        var_rain_peak_step = var_df_step[self.group_variables_list_in[1]].values

                        var_slope_step = find_slopes(var_rain_avg_step, var_rain_peak_step, self.rain_avg_array,
                            self.slope_x_array, self.slope_y_array, self.slope_t_array, self.vm_data)

                        for group_key_step_out, var_slope_step_out in zip(group_variables_list_out, var_slope_step):
                            var_df_step[group_key_step_out] = var_slope_step_out

                        # select datasets by time step
                        var_df_step = var_df_step.loc[var_df_step.index >= time_step]

                        if group_key not in list(var_collections.keys()):
                            var_collections[group_key] = var_df_step
                        else:
                            var_df_tmp = var_collections[group_key]
                            var_df_concatenated = pd.concat([var_df_tmp, var_df_step], axis=0)
                            var_df_concatenated = var_df_concatenated[~var_df_concatenated.index.duplicated(keep='first')]
                            var_df_concatenated.sort_index(inplace=True)
                            var_df_step.index.name = self.tag_dim_time
                            var_collections[group_key] = var_df_concatenated

                if var_collections is not None:
                    var_folder_name_anc, var_file_name_anc = os.path.split(var_file_path_anc)
                    make_folder(var_folder_name_anc)

                    self.write_dset_obj(var_file_path_anc, var_collections)

                logging.info(' -----> Compute data ... DONE')
            else:
                logging.info(' -----> Compute data ... SKIPPED. All datasets are not available')

            logging.info(' ----> Organize datasets ... DONE')

        else:
            logging.info(' ----> Organize datasets ... SKIPPED. Datasets are previously computed')

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to clean temporary information
    def clean_tmp(self):

        file_path_anc_list = self.file_path_anc
        clean_tmp = self.flag_cleaning_tmp
        folder_name_anc_main = self.folder_name_anc_root

        if not isinstance(file_path_anc_list, list):
            file_path_anc_list = [file_path_anc_list]

        if clean_tmp:

            # Remove tmp file and folder(s)
            for file_path_step in file_path_anc_list:
                if os.path.exists(file_path_step):
                    if os.path.isfile(file_path_step):
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
                    os.rmdir(folder_name_anc_step)

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
