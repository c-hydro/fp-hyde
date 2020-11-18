# -------------------------------------------------------------------------------------
# Libraries
import logging
import os

import pandas as pd

from copy import deepcopy

from bin.downloader.ws.odbc.lib_utils_io import write_file_csv, write_obj, read_obj
from bin.downloader.ws.odbc.lib_utils_system import fill_tags2string, make_folder, get_root_path, list_folder

from bin.downloader.ws.odbc.lib_utils_db_sirmip import define_db_settings, get_db_credential, \
    parse_query_time, get_data_ws, organize_data_ws, order_data_ws
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class driver geographical data
class DriverData:

    def __init__(self, time_step, src_dict=None, ancillary_dict=None, dst_dict=None,
                 time_dict=None, variable_dict=None, template_dict=None, info_dict=None,
                 flag_updating_ancillary=True, flag_updating_destination=True, flag_cleaning_tmp=True):

        self.time_step = time_step

        self.src_dict = src_dict
        self.ancillary_dict = ancillary_dict
        self.dst_dict = dst_dict
        self.time_dict = time_dict
        self.variable_dict = variable_dict
        self.template_dict = template_dict

        self.tag_folder_name = 'folder_name'
        self.tag_file_name = 'file_name'

        self.tag_file_fields = 'fields'

        self.domain_name = info_dict['domain']
        self.variable_list = list(self.variable_dict.keys())

        self.time_range = self.collect_file_time()

        self.db_info = self.collect_db_settings(self.src_dict)
        self.db_settings = define_db_settings(self.db_info)

        self.folder_name_anc_dset_raw = self.ancillary_dict[self.tag_folder_name]
        self.file_name_anc_dset_raw = self.ancillary_dict[self.tag_file_name]
        self.file_path_anc_dset_obj = self.collect_file_list(self.folder_name_anc_dset_raw, self.file_name_anc_dset_raw)

        self.folder_name_dst_dset_raw = self.dst_dict[self.tag_folder_name]
        self.file_name_dst_dset_raw = self.dst_dict[self.tag_file_name]
        self.file_path_dst_dset_obj = self.collect_file_list(self.folder_name_dst_dset_raw, self.file_name_dst_dset_raw)

        self.file_fields_dst_dset = self.dst_dict[self.tag_file_fields]

        self.flag_updating_ancillary = flag_updating_ancillary
        self.flag_updating_destination = flag_updating_destination

        self.flag_cleaning_tmp = flag_cleaning_tmp

        self.folder_name_anc_main = get_root_path(self.folder_name_anc_dset_raw)

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to collect database information
    @staticmethod
    def collect_db_settings(db_info):

        db_info_upd = deepcopy(db_info)

        if 'server_mode' not in list(db_info_upd.keys()):
            logging.error(' ===> Server mode field not defined')
            raise IOError('Check your server information.')

        if 'server_ip' not in list(db_info_upd.keys()):
            logging.error(' ===> Server ip field not defined')
            raise IOError('Check your server information.')

        if 'server_name' not in list(db_info_upd.keys()):
            logging.error(' ===> Server name field not defined')
            raise IOError('Check your server information.')

        if 'server_user' not in list(db_info_upd.keys()):
            logging.error(' ===> Server user field not defined')
            raise IOError('Check your server information.')

        if 'server_password' not in list(db_info_upd.keys()):
            logging.error(' ===> Server password field not defined')
            raise IOError('Check your server information.')

        logging.info(' ---> Search password and user ...')
        server_user = db_info_upd['server_user']
        server_password = db_info_upd['server_password']
        if (server_password is None) or (server_user is None):
            server_name = db_info_upd['server_name']

            server_user, server_password = get_db_credential(server_name)

            db_info_upd['server_user'] = server_user
            db_info_upd['server_password'] = server_password

            logging.info(' ---> Search password and user ... found in netrc file. OK')

        else:
            logging.info(' ---> Search password and user ... found in configuration file. OK')

        return db_info_upd
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
    def collect_file_list(self, folder_name_raw, file_name_raw):

        domain_name = self.domain_name

        file_name_obj = {}
        for variable_step in self.variable_list:
            variable_tag = self.variable_dict[variable_step]['tag']

            if variable_tag is not None:
                file_name_list = []
                for datetime_step in self.time_range:

                    template_values_step = {
                        'domain_name': domain_name,
                        'ancillary_var_name': variable_step,
                        'destination_var_name': variable_step,
                        'ancillary_datetime': datetime_step, 'ancillary_sub_path_time': datetime_step,
                        'destination_datetime': datetime_step, 'destination_sub_path_time': datetime_step}

                    folder_name_def = fill_tags2string(
                        folder_name_raw, self.template_dict, template_values_step)
                    file_name_def = fill_tags2string(
                        file_name_raw, self.template_dict, template_values_step)
                    file_path_def = os.path.join(folder_name_def, file_name_def)

                    file_name_list.append(file_path_def)

                file_name_obj[variable_step] = file_name_list

        return file_name_obj

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to download datasets
    def download_data(self):

        logging.info(' ----> Download datasets ... ')

        time_range = self.time_range
        file_path_anc_obj = self.file_path_anc_dset_obj
        file_path_dst_obj = self.file_path_dst_dset_obj
        var_dict = self.variable_dict

        flag_upd_anc = self.flag_updating_ancillary
        flag_upd_dst = self.flag_updating_destination

        for var_name, var_fields in var_dict.items():

            logging.info(' -----> Variable ' + var_name + ' ... ')

            var_tag = var_fields['tag']
            var_download = var_fields['download']

            if var_tag is not None:

                file_path_anc_list = file_path_anc_obj[var_name]
                file_path_dst_list = file_path_dst_obj[var_name]

                if var_download:

                    for time_step, file_path_anc_step, file_path_dst_step in zip(
                            time_range, file_path_anc_list, file_path_dst_list):

                        logging.info(' ------> Time Step ' + str(time_step) + ' ... ')

                        folder_name_anc_step, file_name_anc_step = os.path.split(file_path_anc_step)
                        make_folder(folder_name_anc_step)

                        if flag_upd_anc:
                            if os.path.exists(file_path_anc_step):
                                os.remove(file_path_anc_step)

                        if flag_upd_dst:
                            if os.path.exists(file_path_dst_step):
                                os.remove(file_path_dst_step)

                        if (not os.path.exists(file_path_anc_step)) and (not os.path.exists(file_path_dst_step)):

                            time_from, time_to = parse_query_time(time_step)
                            var_data = get_data_ws(var_tag, time_from, time_to, self.db_settings, flag_type='automatic')
                            write_obj(file_path_anc_step, var_data)

                            logging.info(' ------> Time Step ' + str(time_step) + ' ... DONE')

                        elif (os.path.exists(file_path_anc_step)) and (not os.path.exists(file_path_dst_step)):
                            logging.info(' ------> Time Step ' + str(time_step) +
                                         ' ... SKIPPED. Ancillary file always exists.')
                        elif (not os.path.exists(file_path_anc_step)) and (os.path.exists(file_path_dst_step)):
                            logging.info(' ------> Time Step ' + str(time_step) +
                                         ' ... SKIPPED. Destination file always exists.')
                        else:
                            logging.error(' ===> Bad file multiple condition')
                            raise NotImplemented("File multiple condition not implemented yet")

                    logging.info(' -----> Variable ' + var_name + ' ... DONE')

                else:

                    logging.info(' -----> Variable ' + var_name + ' ... SKIPPED. '
                                                                  'Variable downloading is not activated.')

            else:

                logging.info(' -----> Variable ' + var_name + ' ... SKIPPED. Variable tag is null.')

        logging.info(' ----> Download datasets ... DONE')

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to organize datasets
    def organize_data(self):

        logging.info(' ----> Organize datasets ... ')

        time_range = self.time_range
        file_path_anc_obj = self.file_path_anc_dset_obj
        file_path_dst_obj = self.file_path_dst_dset_obj

        var_dict = self.variable_dict
        var_fields_expected = self.file_fields_dst_dset

        flag_upd_dst = self.flag_updating_destination

        for var_name, var_fields in var_dict.items():

            logging.info(' -----> Variable ' + var_name + ' ... ')

            var_tag = var_fields['tag']
            var_type = var_fields['type']
            var_units = var_fields['units']
            var_valid_range = var_fields['valid_range']
            var_min_count = var_fields['min_count']
            var_scale_factor = var_fields['scale_factor']

            if var_tag is not None:

                file_path_anc_list = file_path_anc_obj[var_name]
                file_path_dst_list = file_path_dst_obj[var_name]

                for time_step, file_path_anc_step, file_path_dst_step in zip(
                        time_range, file_path_anc_list, file_path_dst_list):

                    logging.info(' ------> Time Step ' + str(time_step) + ' ... ')

                    if flag_upd_dst:
                        if os.path.exists(file_path_dst_step):
                            os.remove(file_path_dst_step)

                    if (os.path.exists(file_path_anc_step)) and (not os.path.exists(file_path_dst_step)):

                        var_data = read_obj(file_path_anc_step)

                        var_df = organize_data_ws(var_data, data_type=var_type,
                                                  data_scale_factor=var_scale_factor, data_min_count=var_min_count,
                                                  data_units=var_units, data_valid_range=var_valid_range)

                        var_df = order_data_ws(var_df, var_fields_expected)

                        folder_name_dst_dset, file_name_dst_dset = os.path.split(file_path_dst_step)
                        make_folder(folder_name_dst_dset)

                        write_file_csv(file_path_dst_step, var_df)

                        logging.info(' ------> Time Step ' + str(time_step) + ' ... DONE')

                    elif (not os.path.exists(file_path_anc_step)) and (os.path.exists(file_path_dst_step)):
                        logging.info(' ------> Time Step ' + str(time_step) +
                                     ' ... SKIPPED. Destination file always exists.')
                    elif (not os.path.exists(file_path_anc_step)) and (not os.path.exists(file_path_dst_step)):
                        logging.info(' ------> Time Step ' + str(time_step) +
                                     ' ... SKIPPED. Variable is not activated.')

                logging.info(' -----> Variable ' + var_name + ' ... DONE')

            else:

                logging.info(' -----> Variable ' + var_name + ' ... SKIPPED. Variable tag is null.')

        logging.info(' ----> Organize datasets ... DONE')

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to clean temporary information
    def clean_tmp(self):

        file_path_anc = self.file_path_anc_dset_obj
        clean_tmp = self.flag_cleaning_tmp
        folder_name_anc_main = self.folder_name_anc_main

        if clean_tmp:

            # Remove tmp file and folder(s)
            for var_name, var_file_path_list in file_path_anc.items():
                for var_file_path_step in var_file_path_list:
                    if os.path.exists(var_file_path_step):
                        os.remove(var_file_path_step)
                    var_folder_name_step, var_file_name_step = os.path.split(var_file_path_step)
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
