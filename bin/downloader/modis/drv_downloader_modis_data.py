# -------------------------------------------------------------------------------------
# Libraries
import logging
import os
import glob

import pandas as pd

from copy import deepcopy

from bin.downloader.modis.lib_utils_system import fill_tags2string, make_folder, get_root_path, list_folder, remove_url
from bin.downloader.modis.lib_utils_process import make_bash_exec, run_bash_exec
from bin.downloader.modis.lib_utils_zip import zip_filename

from bin.downloader.modis.lib_utils_machine import get_machine_credential, define_machine_script_downloader
from bin.downloader.modis.lib_utils_mrt import define_mrt_mosaic_file, define_mrt_mosaic_cmd
from bin.downloader.modis.lib_utils_mrt import define_mrt_resample_file, define_mrt_resample_cmd
from bin.downloader.modis.lib_utils_mrt import execute_mrt_cmd
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class driver dynamic data
class DriverData:

    def __init__(self, time_step, machine_dict=None, src_dict=None, ancillary_dict=None, dst_dict=None,
                 time_dict=None, info_dict=None, product_dict=None, template_dict=None, library_dict=None,
                 flag_updating_source=True, flag_updating_ancillary=True, flag_updating_destination=True):

        self.time_step = time_step

        self.machine_dict = machine_dict
        self.src_dict = src_dict
        self.ancillary_dict = ancillary_dict
        self.dst_dict = dst_dict
        self.time_dict = time_dict
        self.info_dict = info_dict
        self.product_dict = product_dict
        self.template_dict = template_dict
        self.library_dict = library_dict

        self.tag_folder_name = 'folder_name'
        self.tag_file_name = 'file_name'
        self.tag_http_address = 'http_address'

        self.tag_file_name_download_tiles = "file_name_download_tiles"
        self.tag_file_name_mosaic_tiles = "file_name_mosaic_tiles"
        self.tag_file_name_mosaic_data = "file_name_mosaic_data"
        self.tag_file_name_resample_parameters = "file_name_resample_parameters"
        self.tag_file_name_resample_data = "file_name_resample_data"

        self.domain = self.info_dict['domain_name']
        self.compression_extension = self.info_dict['compression_extension']

        self.product_name = self.product_dict['name']
        self.product_version = self.product_dict['version']
        self.product_tiles = self.product_dict['tiles']

        self.library_folder = self.library_dict['folder']
        self.library_app_mosaic = self.library_dict['app_mosaic']
        self.library_app_resample = self.library_dict['app_resample']

        self.time_range = self.collect_file_time()

        self.machine_info = self.collect_machine_settings(self.machine_dict)
        self.machine_name = self.machine_info['name']
        self.machine_user = self.machine_info['user']
        self.machine_password = self.machine_info['password']
        self.machine_data_root = self.machine_info['data_root']
        self.machine_data_folder = self.machine_info['data_folder']

        self.tile_name_list, self.tile_name_composite = self.collect_tile_name()

        self.folder_name_src_raw = self.src_dict[self.tag_folder_name]
        self.file_name_src_raw = self.src_dict[self.tag_file_name]
        self.file_path_src_obj = self.define_file_name(self.folder_name_src_raw, self.file_name_src_raw)
        self.http_address_src_raw = self.src_dict[self.tag_http_address]
        self.address_name_src_obj = self.define_address_name(self.http_address_src_raw)

        self.folder_name_anc_raw = self.ancillary_dict[self.tag_folder_name]
        self.file_name_anc_download_tiles_raw = self.ancillary_dict[self.tag_file_name_download_tiles]
        self.file_name_anc_mosaic_tiles_raw = self.ancillary_dict[self.tag_file_name_mosaic_tiles]
        self.file_name_anc_mosaic_data_raw = self.ancillary_dict[self.tag_file_name_mosaic_data]
        self.file_name_anc_resample_parameters_raw = self.ancillary_dict[self.tag_file_name_resample_parameters]
        self.file_name_anc_resample_data_raw = self.ancillary_dict[self.tag_file_name_resample_data]

        self.file_path_anc_download_tiles_obj = self.define_file_name(self.folder_name_anc_raw,
                                                                      self.file_name_anc_download_tiles_raw)
        self.file_path_anc_mosaic_tiles_obj = self.define_file_name(self.folder_name_anc_raw,
                                                                    self.file_name_anc_mosaic_tiles_raw)
        self.file_path_anc_mosaic_data_obj = self.define_file_name(self.folder_name_anc_raw,
                                                                   self.file_name_anc_mosaic_data_raw)
        self.file_path_anc_resample_parameters_obj = self.define_file_name(self.folder_name_anc_raw,
                                                                           self.file_name_anc_resample_parameters_raw)
        self.file_path_anc_resample_data_obj = self.define_file_name(self.folder_name_anc_raw,
                                                                     self.file_name_anc_resample_data_raw)

        self.folder_name_dst_raw = self.dst_dict[self.tag_folder_name]
        self.file_name_dst_raw = self.dst_dict[self.tag_file_name]
        self.file_path_dst_obj = self.define_file_name(self.folder_name_dst_raw, self.file_name_dst_raw)

        if 'file_compression' in list(self.dst_dict.keys()):
            self.file_compression_dst = self.dst_dict['file_compression']
        else:
            self.file_compression_dst = False

        self.flag_updating_source = flag_updating_source
        self.flag_updating_ancillary = flag_updating_ancillary
        self.flag_updating_destination = flag_updating_destination

        self.folder_name_anc_main = get_root_path(self.folder_name_anc_raw)

        self.hidden_file_list = ['.netrc', '.urs_cookies']

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to collect machine information
    @staticmethod
    def collect_machine_settings(machine_info):

        machine_info_upd = deepcopy(machine_info)

        if 'name' not in list(machine_info_upd.keys()):
            logging.error(' ===> Machine name field not defined')
            raise IOError('Check your machine information.')

        if 'proxy' not in list(machine_info_upd.keys()):
            logging.error(' ===> Machine proxy field not defined')
            raise IOError('Check your machine information.')

        if 'user' not in list(machine_info_upd.keys()):
            logging.error(' ===> Machine user field not defined')
            raise IOError('Check your machine information.')

        if 'password' not in list(machine_info_upd.keys()):
            logging.error(' ===> Machine password field not defined')
            raise IOError('Check your machine information.')

        if 'data_root' not in list(machine_info_upd.keys()):
            logging.error(' ===> Machine datasets root field not defined')
            raise IOError('Check your machine information.')

        if 'data_folder' not in list(machine_info_upd.keys()):
            logging.error(' ===> Machine datasets folder field not defined')
            raise IOError('Check your machine information.')

        logging.info(' ---> Search password and user ...')
        machine_user = machine_info_upd['user']
        machine_password = machine_info_upd['password']
        if (machine_password is None) or (machine_user is None):
            server_name = machine_info_upd['name']

            if server_name is not None:

                machine_user, machine_password = get_machine_credential(server_name)
                machine_info_upd['user'] = machine_user
                machine_info_upd['password'] = machine_password

                logging.info(' ---> Search password and user ... found in netrc file. OK')

            else:

                logging.info(' ---> Search password and user ... FAILED')
                logging.error(' ===> Machine name must be defined in your settings file')
                raise IOError('Check your machine information.')

        else:
            logging.info(' ---> Search password and user ... found in configuration file. OK')

        return machine_info_upd
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
    # Method to collect tile names
    def collect_tile_name(self, tile_horz_string='h', tile_vert_string='v'):

        product_tiles = self.product_tiles

        tile_idx_list = []
        for tile_key, tile_info in product_tiles.items():
            tile_idx_h = tile_horz_string + str(tile_info[tile_horz_string]).zfill(2)
            tile_idx_v = tile_vert_string + str(tile_info[tile_vert_string]).zfill(2)
            tile_idx_map = tile_idx_h + tile_idx_v

            tile_idx_list.append(tile_idx_map)

        tile_idx_name = '_'.join(tile_idx_list)

        return tile_idx_list, tile_idx_name

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define address name
    def define_address_name(self, http_address_raw):

        address_name_obj = {}

        domain = self.domain
        product_name = self.product_name
        product_version = self.product_version

        machine_data_root = self.machine_data_root
        machine_data_folder = self.machine_data_folder

        for datetime_step in self.time_range:

            template_values_step = {
                'domain_name': domain,
                'machine_data_root': machine_data_root, 'machine_data_folder': machine_data_folder,
                'machine_datetime': datetime_step,
                'product_name': product_name, 'product_version': product_version,
                'source_datetime': datetime_step, 'source_sub_path_time': datetime_step,
                'ancillary_datetime': datetime_step, 'ancillary_sub_path_time': datetime_step,
                'destination_datetime': datetime_step, 'destination_sub_path_time': datetime_step}

            http_address_def = fill_tags2string(http_address_raw, self.template_dict, template_values_step)
            address_name_obj[datetime_step] = http_address_def

        return address_name_obj

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to define file name
    def define_file_name(self, folder_name_raw, file_name_raw):

        file_name_obj = {}

        domain = self.domain
        product_name = self.product_name
        product_version = self.product_version

        machine_data_root = self.machine_data_root
        machine_data_folder = self.machine_data_folder

        for datetime_step in self.time_range:

            template_values_step = {
                'domain_name': domain,
                'machine_data_root': machine_data_root, 'machine_data_folder': machine_data_folder,
                'machine_datetime': datetime_step,
                'product_name': product_name, 'product_version': product_version,
                'source_datetime': datetime_step, 'source_sub_path_time': datetime_step,
                'ancillary_datetime': datetime_step, 'ancillary_sub_path_time': datetime_step,
                'destination_datetime': datetime_step, 'destination_sub_path_time': datetime_step}

            folder_name_def = fill_tags2string(folder_name_raw, self.template_dict, template_values_step)
            file_name_def = fill_tags2string(file_name_raw, self.template_dict, template_values_step)
            file_path_def = os.path.join(folder_name_def, file_name_def)

            file_name_obj[datetime_step] = file_path_def

        return file_name_obj

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to search file using a template
    @staticmethod
    def search_file_name(file_name_tmpl):

        file_name_list = glob.glob(file_name_tmpl)
        if file_name_list:
            file_name_found = file_name_list[0]
        else:
            file_name_found = None
        return file_name_found
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to resample datasets
    def resample_data(self, file_composite_collections):

        logging.info(' ----> Resample datasets ... ')

        time_range = self.time_range
        tile_list = self.tile_name_list
        tile_name_composite = self.tile_name_composite

        flag_upd_dst = self.flag_updating_destination

        file_path_resample_parameters_obj = self.file_path_anc_resample_parameters_obj
        file_path_resample_data_obj = self.file_path_anc_resample_data_obj
        file_path_dst_obj = self.file_path_dst_obj

        library_folder = self.library_folder
        library_app_mosaic_mode = self.library_app_mosaic['activation']
        library_app_resample_exec = self.library_app_resample['executable']
        library_app_resample_mode = self.library_app_resample['activation']
        library_app_resample_spacial_subset_type = self.library_app_resample['spatial_subset_type']
        library_app_resample_resampling_method = self.library_app_resample['resampling_method']
        library_app_resample_proj = self.library_app_resample['proj']
        library_app_resample_datum = self.library_app_resample['datum']

        # Iterate over time-steps and filename(s)
        for time_step in time_range:

            logging.info(' -----> Time Step ' + str(time_step) + ' ... ')

            file_path_resample_params = file_path_resample_parameters_obj[time_step]
            file_path_resample_data = file_path_resample_data_obj[time_step]

            file_composite_list = file_composite_collections[time_step]
            file_path_dst = file_path_dst_obj[time_step]

            logging.info(' ------> Execute resampling ... ')
            if file_composite_list is not None:

                if not library_app_mosaic_mode:
                    file_resample_list = []
                    file_destination_list = []
                    file_parameters_list = []
                    for tile_name in tile_list:
                        template_values = {'tile_composite': tile_name}
                        file_path_res_tmp = fill_tags2string(file_path_resample_data, self.template_dict, template_values)
                        file_resample_list.append(file_path_res_tmp)
                        file_path_dst_tmp = fill_tags2string(file_path_dst, self.template_dict, template_values)
                        file_destination_list.append(file_path_dst_tmp)
                        file_path_params_tmp = fill_tags2string(file_path_resample_params, self.template_dict,
                                                                template_values)
                        file_parameters_list.append(file_path_params_tmp)
                else:
                    template_values = {'tile_composite': tile_name_composite}
                    file_path_res_tmp = fill_tags2string(file_path_resample_data, self.template_dict, template_values)
                    file_resample_list = [file_path_res_tmp]
                    file_path_dst_tmp = fill_tags2string(file_path_dst, self.template_dict, template_values)
                    file_destination_list = [file_path_dst_tmp]
                    file_path_params_tmp = fill_tags2string(file_path_resample_params, self.template_dict, template_values)
                    file_parameters_list = [file_path_params_tmp]

                file_composite_collections[time_step] = {}

                for file_path_composite, file_path_parameters, file_path_resample, file_path_destination in zip(
                        file_composite_list, file_parameters_list, file_resample_list, file_destination_list):

                    folder_name_composite, file_name_composite = os.path.split(file_path_composite)
                    folder_name_resample, file_name_resample = os.path.split(file_path_resample)
                    make_folder(folder_name_resample)
                    folder_name_parameters, file_name_parameters = os.path.split(file_path_parameters)
                    make_folder(folder_name_parameters)
                    folder_name_destination, file_name_destination = os.path.split(file_path_destination)
                    make_folder(folder_name_destination)
                    file_path_zip = file_path_destination + self.compression_extension

                    logging.info(' -------> Compute from ' + file_name_composite + ' to '
                                 + file_name_resample + ' ... ')

                    if flag_upd_dst:
                        if os.path.exists(file_path_destination):
                            os.remove(file_path_destination)
                        if os.path.exists(file_path_zip):
                            os.remove(file_path_zip)
                    if self.file_compression_dst:
                        file_check = file_path_zip
                    else:
                        file_check = file_path_destination

                    if library_app_resample_mode:

                        if not os.path.exists(file_check):

                            define_mrt_resample_file(file_path_composite, file_path_parameters, file_path_resample,
                                                     spatial_subset_type=library_app_resample_spacial_subset_type,
                                                     resampling_type=library_app_resample_resampling_method,
                                                     proj=library_app_resample_proj,
                                                     datum=library_app_resample_datum)

                            cmd_resample = define_mrt_resample_cmd(file_path_parameters,
                                                                   mrt_folder=library_folder,
                                                                   mrt_executable=library_app_resample_exec)
                            execute_mrt_cmd(cmd_resample)

                            logging.info(' -------> Compute from ' + file_name_composite + ' to '
                                         + file_name_resample + ' ... DONE')

                            logging.info(' -------> Move from ' + file_name_resample + ' to '
                                         + file_name_destination + ' ... ')

                            if os.path.exists(file_path_resample):
                                os.rename(file_path_resample, file_path_destination)
                                logging.info(' -------> Move from ' + file_name_resample + ' to '
                                             + file_name_destination + ' ... DONE')

                            else:
                                logging.info(' -------> Move from ' + file_name_resample + ' to '
                                             + file_name_destination + ' ... FAILED. Resampled file not available')

                            logging.info(' -------> Zip ' + file_name_destination + ' ... ')
                            if self.file_compression_dst:
                                zip_filename(file_path_destination, file_path_zip)
                                if os.path.exists(file_path_destination):
                                    os.remove(file_path_destination)
                                logging.info(' -------> Zip ' + file_name_destination + ' ... DONE')
                            else:
                                logging.info(' -------> Zip ' + file_name_destination +
                                             ' ... SKIPPED. Compression not activated')

                            if os.path.exists(file_path_composite):
                                os.remove(file_path_composite)
                            if os.path.exists(file_path_parameters):
                                os.remove(file_path_parameters)
                            if os.path.exists(file_path_resample):
                                os.remove(file_path_resample)
                            if os.path.exists(file_path_destination):
                                os.remove(file_path_destination)

                        else:
                            logging.info(' -------> Resample from ' + file_name_composite + ' to '
                                         + file_name_resample + ' ... SKIPPED. Resampled datasets previously computed')
                    else:
                        logging.info(' -------> Resample from ' + file_name_composite + ' to '
                                     + file_name_resample + ' ... NOT ACTIVATED')

                logging.info(' ------> Execute resampling ... DONE')
                logging.info(' -----> Time Step ' + str(time_step) + ' ... DONE')

            else:
                logging.info(' ------> Execute resampling ... SKIPPED. Datasets not available')
                logging.info(' -----> Time Step ' + str(time_step) + ' ... DONE')

        logging.info(' ----> Resample datasets ... DONE')

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to mosaic datasets
    def mosaic_data(self, file_tile_collections):

        logging.info(' ----> Mosaic datasets ... ')

        time_range = self.time_range
        tile_list = self.tile_name_list

        flag_upd_src = self.flag_updating_source
        flag_upd_anc = self.flag_updating_ancillary
        flag_upd_dst = self.flag_updating_destination

        file_path_src_obj = self.file_path_src_obj
        file_path_mosaic_tiles_obj = self.file_path_anc_mosaic_tiles_obj
        file_path_mosaic_data_obj = self.file_path_anc_mosaic_data_obj
        file_path_resample_parameters_obj = self.file_path_anc_resample_parameters_obj
        file_path_resample_data_obj = self.file_path_anc_resample_data_obj

        library_folder = self.library_folder
        library_app_mosaic_exec = self.library_app_mosaic['executable']
        library_app_mosaic_mode = self.library_app_mosaic['activation']

        # Iterate over time-steps and filename(s)
        file_composite_collections = {}
        for time_step in time_range:

            logging.info(' -----> Time Step ' + str(time_step) + ' ... ')

            file_path_mosaic_tiles = file_path_mosaic_tiles_obj[time_step]
            file_path_mosaic_data = file_path_mosaic_data_obj[time_step]

            file_tile_list = file_tile_collections[time_step]

            logging.info(' ------> Execute mosaic ... ')
            file_composite_collections[time_step] = {}
            if file_tile_list:

                if library_app_mosaic_mode:

                    template_values = {'tile_composite': self.tile_name_composite}
                    file_path_mosaic_data = fill_tags2string(file_path_mosaic_data, self.template_dict, template_values)

                    if flag_upd_anc:
                        if os.path.exists(file_path_mosaic_data):
                            os.remove(file_path_mosaic_data)

                    if not os.path.exists(file_path_mosaic_data):
                        file_folder_mosaic_data, file_name_mosaic_data = os.path.split(file_path_mosaic_data)
                        make_folder(file_folder_mosaic_data)

                        file_status = define_mrt_mosaic_file(file_path_mosaic_tiles, file_tile_list)

                        if file_status:
                            cmd_mosaic = define_mrt_mosaic_cmd(file_path_mosaic_tiles, file_path_mosaic_data,
                                                               mrt_folder=library_folder,
                                                               mrt_executable=library_app_mosaic_exec)

                            execute_mrt_cmd(cmd_mosaic)

                            file_composite_collections[time_step] = [file_path_mosaic_data]

                            if os.path.exists(file_path_mosaic_tiles):
                                os.remove(file_path_mosaic_tiles)
                            logging.info(' ------> Execute mosaic ... DONE. Datasets are stored in mosaic format')
                        else:
                            logging.info(' ------> Execute mosaic ... FAILED. All tiles are not available')
                            file_composite_collections[time_step] = None

                    else:
                        logging.info(' ------> Execute mosaic ... SKIPPED. Mosaic previously computed')
                        file_composite_collections[time_step] = [file_path_mosaic_data]

                else:
                    logging.info(' ------> Execute mosaic ... NOT ACTIVATED. Datasets are stored in tile format')
                    file_composite_collections[time_step] = file_tile_list

            else:
                logging.info(' ------> Execute mosaic ... SKIPPED. Datasets not available')
                file_composite_collections[time_step] = None

            logging.info(' -----> Time Step ' + str(time_step) + ' ... DONE')

        logging.info(' ----> Mosaic datasets ... DONE')

        return file_composite_collections

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to download datasets
    def download_data(self):

        logging.info(' ----> Download datasets ... ')

        time_range = self.time_range
        tile_list = self.tile_name_list

        flag_upd_src = self.flag_updating_source

        file_path_src_obj = self.file_path_src_obj
        file_path_download_tiles_obj = self.file_path_anc_download_tiles_obj

        address_name_src_obj = self.address_name_src_obj

        # Iterate over time-steps and filename(s)
        file_tile_collections = {}
        for time_step in time_range:

            logging.info(' -----> Time Step ' + str(time_step) + ' ... ')

            file_path_src = file_path_src_obj[time_step]
            file_path_download_tiles = file_path_download_tiles_obj[time_step]

            address_name_src = address_name_src_obj[time_step]

            file_path_tile_list = []
            for tile_name in tile_list:

                logging.info(' ------> Get datasets tile ' + tile_name + ' ... ')

                template_values_step = {'tile_name': tile_name}

                file_path_src_step = fill_tags2string(file_path_src, self.template_dict, template_values_step)
                address_name_src_step = fill_tags2string(address_name_src, self.template_dict, template_values_step)
                file_path_download_tiles_step = fill_tags2string(file_path_download_tiles,
                                                                 self.template_dict, template_values_step)

                file_path_found_step = self.search_file_name(file_path_src_step)
                if flag_upd_src:
                    if os.path.exists(file_path_found_step):
                        os.remove(file_path_found_step)
                    file_path_found_step = None

                if file_path_found_step is None:

                    folder_name_src_step, file_name_src_step = os.path.split(file_path_src_step)
                    make_folder(folder_name_src_step)
                    os.chdir(folder_name_src_step)

                    folder_name_download_tiles_step, file_name_download_tiles_step = os.path.split(
                        file_path_download_tiles_step)
                    make_folder(folder_name_download_tiles_step)

                    address_folder_src_step = remove_url(address_name_src_step)
                    address_path_src_step = os.path.join(folder_name_src_step, address_folder_src_step)

                    define_machine_script_downloader(folder_name_download_tiles_step, file_name_download_tiles_step,
                                                     folder_name_src_step, file_name_src_step, address_name_src_step,
                                                     self.machine_name, self.machine_user, self.machine_password)

                    make_bash_exec(file_path_download_tiles_step)

                    run_bash_exec(file_path_download_tiles_step)

                    file_path_tile_tmp = self.search_file_name(file_path_src_step)
                    file_path_tile_list.append(file_path_tile_tmp)

                    if os.path.exists(address_path_src_step):
                        os.chdir(folder_name_src_step)
                        os.removedirs(address_folder_src_step)
                    if os.path.exists(file_path_download_tiles_step):
                        os.remove(file_path_download_tiles_step)

                    for file_hidden in self.hidden_file_list:
                        if os.path.exists(os.path.join(folder_name_src_step, file_hidden)):
                            os.remove(os.path.join(folder_name_src_step, file_hidden))

                    logging.info(' ------> Get datasets tile ' + tile_name + ' ... DONE')

                else:
                    file_path_tile_tmp = self.search_file_name(file_path_src_step)
                    file_path_tile_list.append(file_path_tile_tmp)

                    logging.info(' ------> Get datasets tile ' + tile_name +
                                 ' ... SKIPPED. Datasets previously downloaded.')

            file_tile_collections[time_step] = file_path_tile_list

            logging.info(' -----> Time Step ' + str(time_step) + ' ... DONE')

        logging.info(' ----> Download datasets ... DONE')

        return file_tile_collections

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to clean temporary information
    def clean_tmp(self):

        print('ciao')

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
