#!/usr/bin/python3

"""
HyDE Downloading Tool - SATELLITE GSMAP

__date__ = '20200427'
__version__ = '1.0.1'
__author__ =
        'Andrea Libertino (andrea.libertino@cimafoundation.org',
        'Fabio Delogu (fabio.delogu@cimafoundation.org',
        'Alessandro Masoero (alessandro.masoero@cimafoundation.org',
        'Laura Poletti (laura.poletti@cimafoundation.org',
__library__ = 'HyDE'

General command line:
python3 hyde_downloader_satellite_gsmap_nowcasting.py -settings_file configuration.json -time "YYYY-MM-DD HH:MM"

Version(s):
20200427 (1.0.1) --> Add list of remote files using folder name to avoid bad request of un-existing files
20200313 (1.0.0) --> Beta release
"""
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Complete library
import logging
import os
import time
import json
import tempfile
import netrc
import gzip

import numpy as np
import pandas as pd

import ftputil
from ftplib import FTP
from copy import deepcopy
from cdo import Cdo
from multiprocessing import Pool, cpu_count
from datetime import datetime
from os import makedirs
from os.path import join, exists, split
from argparse import ArgumentParser
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Algorithm information
alg_name = 'HYDE DOWNLOADING TOOL - SATELLITE GSMAP'
alg_version = '1.0.0'
alg_release = '2020-03-13'
# Algorithm parameter(s)
time_format = '%Y%m%d%H%M'
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class ftp gateway
class FTPDriver:

    def __init__(self, ftp_host="hokusai.eorc.jaxa.jp"):

        # Define which host in the .netrc file and in the ftp to use
        self.ftp_host = ftp_host

        # Read from the .netrc file in your home directory
        netrc_handle = netrc.netrc()
        username, _, password = netrc_handle.authenticators(self.ftp_host)

        self.ftp_handle = FTP(self.ftp_host)
        self.ftp_handle.login(username, password)

        self.ftp_utils = ftputil.host.FTPHost(self.ftp_host, username, password)

        self.ftp_file_downloaded = []
        self.ftp_file_error = []

        self.ftp_file_available = []
        self.ftp_folder_check = []

    def download_file(self, data_list):

        ftp_folder = data_list[0]
        ftp_file = data_list[1]
        dst_file = data_list[2]

        if ftp_folder not in self.ftp_folder_check:
            self.ftp_file_available = self.ftp_utils.listdir(ftp_folder)
            self.ftp_folder_check.append(ftp_folder)

        logging.info(' :: FTP request for downloading: ' + ftp_file + ' ... ')

        if ftp_file in self.ftp_file_available:
            logging.info(' :: Outcome data will be dumped in: ' + split(dst_file)[1] + ' ... ')
            try:
                self.ftp_handle.cwd(ftp_folder)  # got to ftp dataset dir
                self.ftp_handle.retrbinary("RETR " + ftp_file, open(dst_file, 'wb').write)

                os.popen("chmod g+rxX " + dst_file).readline()

                self.ftp_file_downloaded.append([ftp_folder, ftp_file])

                logging.info(' :: FTP request for downloading: ' + ftp_file + ' ... DONE')
                logging.info(' :: Outcome data will be dumped in: ' + split(dst_file)[1] + ' ... DONE')

            except ConnectionError:
                self.ftp_file_error.append([ftp_folder, ftp_file])

                logging.warning(' :: FTP request for downloading: ' + ftp_file + ' ... FAILED')
                logging.warning(' :: Outcome data will be dumped in: ' + split(dst_file)[1] + ' ... FAILED')

        else:
            logging.info(' :: FTP request for downloading: ' + ftp_file +
                         ' ... SKIPPED. File not available in folder ' + ftp_folder)

    def close(self):
        self.ftp_handle.quit()
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Script Main
def main():

    # -------------------------------------------------------------------------------------
    # Get algorithm settings
    alg_settings, alg_time = get_args()

    # Set algorithm settings
    data_settings = read_file_json(alg_settings)

    # Set algorithm logging
    make_folder(data_settings['data']['log']['folder'])
    set_logging(logger_file=join(data_settings['data']['log']['folder'], data_settings['data']['log']['filename']))
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm
    logging.info(' ============================================================================ ')
    logging.info(' ==> ' + alg_name + ' (Version: ' + alg_version + ' Release_Date: ' + alg_release + ')')
    logging.info(' ==> START ... ')
    logging.info(' ')

    # Time algorithm information
    start_time = time.time()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get algorithm time range
    time_run, time_run_range = set_run_time(alg_time, data_settings['time'])

    # Starting info
    logging.info(' --> TIME RUN: ' + str(time_run))

    # Iterate over time steps
    for time_run_step in time_run_range:

        # Starting info
        logging.info(' ---> NWP RUN: ' + str(time_run_step) + ' ... ')

        # Get data time range
        time_data_range = set_data_time(time_run_step, data_settings['data']['dynamic']['time'])

        # Set data sources
        data_ftp, root_ftp, folder_ftp, file_ftp = set_data_ftp(
            time_run_step, time_data_range,
            data_settings['data']['dynamic']['ftp'],
            data_settings['data']['static']['bounding_box'],
            data_settings['algorithm']['ancillary'],
            data_settings['algorithm']['template'],
            type_data=data_settings['algorithm']['ancillary']['type'])

        # Set data source
        data_source = set_data_source(time_run_step, time_data_range,
                                      data_settings['data']['dynamic']['source'],
                                      data_settings['data']['static']['bounding_box'],
                                      data_settings['algorithm']['ancillary'],
                                      data_settings['algorithm']['template'],
                                      type_data=data_settings['algorithm']['ancillary']['type'])

        # Set data ancillary global
        data_ancillary_global = set_data_ancillary_global(
            time_run_step, time_data_range,
            data_settings['data']['dynamic']['ancillary']['global'],
            data_settings['data']['static']['bounding_box'],
            data_settings['algorithm']['ancillary'],
            data_settings['algorithm']['template'],
            type_data=data_settings['algorithm']['ancillary']['type'])

        # Set data ancillary ctl
        data_ancillary_ctl = set_data_ancillary_ctl(
            time_run_step, time_data_range,
            data_settings['data']['dynamic']['ancillary']['ctl'],
            data_settings['data']['static']['bounding_box'],
            data_settings['algorithm']['ancillary'],
            data_settings['algorithm']['template'],
            type_data=data_settings['algorithm']['ancillary']['type'],
            flag_updating=data_settings['algorithm']['flags']['cleaning_dynamic_data_ctl'])

        # Set data outcome global
        data_outcome_global = set_data_outcome(
            time_run_step, time_data_range,
            data_settings['data']['dynamic']['outcome']['global'],
            data_settings['data']['static']['bounding_box'],
            data_settings['algorithm']['ancillary'],
            data_settings['algorithm']['template'],
            type_data=data_settings['algorithm']['ancillary']['type'],
            flag_updating=data_settings['algorithm']['flags']['cleaning_dynamic_data_global'])
        # Set data outcome domain
        data_outcome_domain = set_data_outcome(
            time_run_step, time_data_range,
            data_settings['data']['dynamic']['outcome']['domain'],
            data_settings['data']['static']['bounding_box'],
            data_settings['algorithm']['ancillary'],
            data_settings['algorithm']['template'],
            type_data=data_settings['algorithm']['ancillary']['type'],
            flag_updating=data_settings['algorithm']['flags']['cleaning_dynamic_data_domain'])

        # Retrieve and save data (in sequential or multiprocessing mode)
        if data_settings['algorithm']['flags']['downloading_mp']:
            retrieve_data_source_mp(
                data_ftp, root_ftp, folder_ftp, file_ftp, data_source,
                flag_updating=data_settings['algorithm']['flags']['cleaning_dynamic_data_source'],
                process_n=data_settings['algorithm']['ancillary']['process_mp'],
            )
        else:
            retrieve_data_source_seq(
                data_ftp, root_ftp, folder_ftp, file_ftp, data_source,
                flag_updating=data_settings['algorithm']['flags']['cleaning_dynamic_data_source'])

        # Merge and mask data ancillary to data outcome
        arrange_data_outcome(time_data_range,
                             data_source, data_outcome_global, data_outcome_domain, data_ancillary_ctl,
                             tags_template=data_settings['algorithm']['template'],
                             data_bbox=data_settings['data']['static']['bounding_box'],
                             cdo_exec=data_settings['algorithm']['ancillary']['cdo_exec'],
                             cdo_deps=data_settings['algorithm']['ancillary']['cdo_deps'])

        # Clean data tmp (such as ancillary and outcome global)
        clean_data_tmp(
            data_ancillary_ctl, data_outcome_global,
            flag_cleaning_tmp=data_settings['algorithm']['flags']['cleaning_dynamic_data_tmp'])

        # Ending info
        logging.info(' ---> NWP RUN: ' + str(time_run_step) + ' ... DONE')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm
    time_elapsed = round(time.time() - start_time, 1)

    logging.info(' ')
    logging.info(' ==> ' + alg_name + ' (Version: ' + alg_version + ' Release_Date: ' + alg_release + ')')
    logging.info(' ==> TIME ELAPSED: ' + str(time_elapsed) + ' seconds')
    logging.info(' ==> ... END')
    logging.info(' ==> Bye, Bye')
    logging.info(' ============================================================================ ')
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to fill data ancillary ctl
def fill_data_ancillary_ctl(time_step, file_source, ctl_template, tags_template, tag_dset='dset', tag_tdef='tdef'):

    folder_source, filename_source = os.path.split(file_source)

    hour_step = time_step.strftime('%H:00')
    day_step = time_step.strftime('%-d')
    year_step = time_step.strftime('%Y')
    month_step = time_step.strftime('%b').lower()

    tdef_ctl_step = hour_step + 'Z' + day_step + month_step + year_step
    dset_ctl_step = file_source
    tags_ctl_step = {tag_dset: dset_ctl_step, tag_tdef: tdef_ctl_step}

    ctl_template_filled = {}
    for template_ctl_key, template_ctl_content_raw in ctl_template.items():
        template_ctl_content_fill = template_ctl_content_raw.format(**tags_ctl_step)
        ctl_template_filled[template_ctl_key] = template_ctl_content_fill

    return ctl_template_filled
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write ancillary ctl file
def write_data_ancillary_ctl(filename_ctl, template_ctl):
    ctl_handle = open(filename_ctl, "w")
    for line_key, line_content in template_ctl.items():
        ctl_handle.write(line_content)
        ctl_handle.write("\n")
    ctl_handle.close()
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to clean tmp data such as ancillary or global (if domain is set)
def clean_data_tmp(data_ancillary, data_outcome_global,
                   flag_cleaning_tmp=False):

    if flag_cleaning_tmp:
        for data_key, data_value in data_ancillary.items():
            for data_step in data_value:
                if os.path.exists(data_step):
                    os.remove(data_step)
        for data_key, data_value in data_outcome_global.items():
            for data_step in data_value:
                if os.path.exists(data_step):
                    os.remove(data_step)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to unzip data source file
def unzip_data_source(filename_zip, filename_unzip):

    if os.path.exists(filename_zip):
        input = gzip.GzipFile(filename_zip, 'rb')
        data = input.read()
        input.close()
        output = open(filename_unzip, 'wb')
        output.write(data)
        output.close()
    else:
        logging.warning(' ===> Zip file does not exist. Checy your datasets.')
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to arrange outcome dataset(s)
def arrange_data_outcome(time_range, src_data, dst_data_global, dst_data_domain, ctl_data_ancillary,
                         tags_template=None,
                         data_bbox=None, cdo_exec=None, cdo_deps=None):

    logging.info(' ----> Dumping data ... ')

    if data_bbox is not None:
        bbox_lon_right = str(data_bbox['lon_right'])
        bbox_lon_left = str(data_bbox['lon_left'])
        bbox_lat_top = str(data_bbox['lat_top'])
        bbox_lat_bottom = str(data_bbox['lat_bottom'])

        bbox_points = [bbox_lon_right, bbox_lon_left, bbox_lat_bottom, bbox_lat_top]
        bbox_cdo = ','.join(bbox_points)
    else:
        bbox_cdo = None

    if cdo_exec is None:
        logging.error(' ===> CDO executable is not set!')
        raise RuntimeError(' CDO executable is not set!')

    for cdo_dep in cdo_deps:
        os.environ['LD_LIBRARY_PATH'] = 'LD_LIBRARY_PATH:' + cdo_dep
    cdo = Cdo()
    cdo.setCdo(cdo_exec)

    for (src_key_step, src_file_list), \
        (dst_key_global_step, dst_file_global_list), \
        (dst_key_domain_step, dst_file_domain_list),\
        (ctl_key_step, ctl_data_list) in zip(src_data.items(),
                                             dst_data_global.items(),
                                             dst_data_domain.items(),
                                             ctl_data_ancillary.items()):

        logging.info(' -----> Type ' + src_key_step + ' ... ')

        ctl_file_list = ctl_data_list[0]
        ctl_template_raw = ctl_data_list[1]

        src_file_list.sort()
        dst_file_global_list.sort()
        dst_file_domain_list.sort()
        ctl_file_list.sort()

        for time_step, src_file_step_zip, \
            dst_file_global_step, dst_file_domain_step, \
            ctl_file_step in zip(time_range, src_file_list,
                                 dst_file_global_list, dst_file_domain_list,
                                 ctl_file_list):

            logging.info(' ------> TimeStep ' + str(time_step) + ' ... ')

            logging.info(' ------> Convert and project global data ... ')
            if not os.path.exists(dst_file_global_step):

                folder_global_step, filename_global_step = os.path.split(dst_file_global_step)
                tmp_file_global_step = create_filename_tmp(folder=folder_global_step, suffix='.nc')

                src_file_step_unzip = os.path.splitext(src_file_step_zip)[0]
                ctl_template_step = fill_data_ancillary_ctl(time_step, src_file_step_unzip,
                                                        ctl_template_raw, tags_template)

                unzip_data_source(src_file_step_zip, src_file_step_unzip)

                write_data_ancillary_ctl(ctl_file_step, ctl_template_step)

                cdo.import_binary(input=ctl_file_step, output=tmp_file_global_step, options='-f nc')
                cdo.sellonlatbox('-180,180,-90,90', input=tmp_file_global_step, output=dst_file_global_step)

                if os.path.exists(src_file_step_unzip):
                    os.remove(src_file_step_unzip)
                if os.path.exists(tmp_file_global_step):
                    os.remove(tmp_file_global_step)

                logging.info(' ------> Convert and project global data ... DONE')
            else:
                logging.info(' ------> Convert and project global data ... SKIPPED. Data already available')

            logging.info(' ------> Mask global data over defined domain ...  ')
            if not os.path.exists(dst_file_domain_step):
                if bbox_cdo is not None:
                    cdo.sellonlatbox(bbox_cdo, input=dst_file_global_step, output=dst_file_domain_step)
                    logging.info(' ------> Mask global data over defined domain ...  DONE')
                else:
                    logging.info(' ------> Mask global data over defined domain ...  SKIPPED. '
                                 'Domain bounding box not defined.')
            else:
                logging.info(' ------> Mask global data over defined domain ...  SKIPPED. Data already masked.')

            logging.info(' ------> TimeStep ' + str(time_step) + ' ... DONE')

        logging.info(' -----> Type ' + src_key_step + ' ... DONE')

    logging.info(' ----> Dumping data ... DONE')
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to drop data
def select_time_steps(info_file, id_start=2, id_end=None, id_period=2):

    if id_end is None:
        id_end = int(info_file[-1].split()[0])

    list_vars = []
    for info_row in info_file:
        info_list = info_row.split()

        info_id = int(info_list[0])
        info_var = info_list[12]

        if info_id >= 0:
            list_vars.append(info_var)

    var_box = list(set(list_vars))

    ids_info = [str(id_start), str(id_end), str(id_period)]
    ids_box = '/'.join(ids_info)

    return var_box, ids_box
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create a tmp name
def create_filename_tmp(prefix='gfs_tmp_', suffix='.grib2', folder=None):

    if folder is None:
        folder = '/tmp'

    with tempfile.NamedTemporaryFile(dir=folder, prefix=prefix, suffix=suffix, delete=False) as tmp:
        temp_file_name = tmp.name
    return temp_file_name
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to retrieve and store data (multiprocess)
def retrieve_data_source_mp(src_data, src_root, src_folder, src_file,
                            dst_data,
                            flag_updating=False, process_n=20, process_max=None):

    logging.info(' ----> Downloading data in multiprocessing mode ... ')

    if process_max is None:
        process_max = cpu_count() - 1
    if process_n > process_max:
        logging.warning(' ----> Maximum of recommended processes must be less then ' + str(process_max))
        logging.warning(' ----> Set number of process from ' + str(process_n) + ' to ' + str(process_max))
        process_n = process_max

    data_list = []
    data_check = []
    for (src_data_key, src_data_list), \
        (src_root_key, src_root_list), (src_folder_key, src_folder_list), (src_file_key, src_file_list), \
        (dst_data_key, dst_data_list) in zip(
        src_data.items(),
        src_root.items(), src_folder.items(), src_file.items(),
        dst_data.items()):

        logging.info(' -----> DataType: ' + src_data_key + ' ... ')

        for src_step_ftp, \
            src_step_root, src_step_folder, src_step_file, dst_step_path in zip(
            src_data_list, src_root_list, src_folder_list, src_file_list, dst_data_list):

            dst_step_root, dst_step_file = split(dst_step_path)
            make_folder(dst_step_root)

            if exists(dst_step_path) and flag_updating:
                flag_updating = True
            elif (not exists(dst_step_path)) and flag_updating:
                flag_updating = True
            elif (not exists(dst_step_path)) and (not flag_updating):
                flag_updating = True
            if flag_updating:
                data_list.append([src_step_folder, src_step_file, dst_step_path])

            data_check.append([src_step_folder, src_step_file, dst_step_path])

        logging.info(' -----> DataType: ' + src_data_key + ' ... SET-UP')

    with Pool(processes=process_n, maxtasksperchild=1) as process_pool:
        _ = process_pool.map(wrap_download_file, data_list, chunksize=1)
        process_pool.close()
        process_pool.join()

    find_data_corrupted(data_check)

    logging.info(' ----> Downloading data in multiprocessing mode ... DONE')
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to wrap file downloader for mp process
def wrap_download_file(data_list):
    ftp_drv = FTPDriver()
    ftp_drv.download_file(data_list)
# -------------------------------------------------------------------------------------


# ------------------------------------------------------------------------------------
# Method to find outliers and to retry for downloading data again
def find_data_corrupted(data_list, data_perc_min=5, data_size_min=100000):

    logging.info(' -----> Checking for corrupted or unavailable data  ... ')

    data_size = []
    idx_nodata = []
    for dst_id, dst_step_path in enumerate(data_list):
        if os.path.exists(dst_step_path[1]):
            dst_step_size = os.path.getsize(dst_step_path[1])
        else:
            dst_step_size = 0
            idx_nodata.append(dst_id)
        data_size.append(dst_step_size)
    data_size = np.asarray(data_size)

    data_p_min = np.percentile(data_size, data_perc_min)

    idx_false = np.where(data_size < min([data_size_min, data_p_min]))[0]
    idx_nodata = np.asarray(idx_nodata, int)
    idx_retry = np.unique(np.concatenate((idx_false, idx_nodata), axis=0))

    ftp_drv = None
    for idx_step in idx_retry:

        # Set the ftp driver
        if ftp_drv is None:
            ftp_drv = FTPDriver()

        data_false = data_list[idx_step]

        if os.path.exists(data_false[1]):
            os.remove(data_false[1])

        logging.info(' ------> Downloading data ' + split(data_false[1])[1] + ' ... ')
        ftp_drv.download_file(data_false)
        logging.info(' ------> Downloading data ' + split(data_false[1])[1] + ' ... DONE')

    logging.info(' -----> Checking for corrupted or unavailable data  ... DONE')
# ------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to retrieve and store data (sequential)
def retrieve_data_source_seq(src_data, src_root, src_folder, src_file,
                             dst_data, flag_updating=False):

    logging.info(' ----> Downloading data in sequential mode ... ')

    # Set the ftp driver
    ftp_drv = FTPDriver()

    data_list = []
    data_check = []
    for (src_data_key, src_data_list), \
        (src_root_key, src_root_list), (src_folder_key, src_folder_list), (src_file_key, src_file_list), \
        (dst_data_key, dst_data_list) in zip(
            src_data.items(),
            src_root.items(), src_folder.items(), src_file.items(),
            dst_data.items()):

        logging.info(' -----> DataType: ' + src_data_key + ' ... ')

        for src_step_ftp, \
            src_step_root, src_step_folder, src_step_file, dst_step_path in zip(
            src_data_list, src_root_list, src_folder_list, src_file_list, dst_data_list):

            dst_step_root, dst_step_file = split(dst_step_path)
            make_folder(dst_step_root)

            logging.info(' ------> Save data in file: ' + str(dst_step_file) + ' ... ')
            if exists(dst_step_path) and flag_updating:
                flag_updating = True
            elif (not exists(dst_step_path)) and flag_updating:
                flag_updating = True
            elif (not exists(dst_step_path)) and (not flag_updating):
                flag_updating = True

            if flag_updating:

                ftp_drv.download_file([src_step_folder, src_step_file, dst_step_path])

                data_list.append([src_step_folder, src_step_file, dst_step_path])
                logging.info(' ------> Save data in file: ' + str(dst_step_file) + ' ... DONE')
            else:
                logging.info(' ------> Save data in file: ' + str(dst_step_file) +
                             ' ... SKIPPED. File saved previously')

            data_check.append([src_step_folder, src_step_file, dst_step_path])

        logging.info(' -----> DataType: ' + src_data_key + ' ... DONE')

    find_data_corrupted(data_check)

    logging.info(' ----> Downloading data in sequential mode ... DONE')
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create data outcome list
def set_data_outcome(time_run, time_range, data_def, geo_def, ancillary_def, tags_template,
                     type_data=None, flag_updating=True):

    if type_data is None:
        type_data = ["surface"]

    folder_list = data_def['folder']
    filename_list = data_def['filename']

    lon_right = geo_def['lon_right']
    lon_left = geo_def['lon_left']
    lat_top = geo_def['lat_top']
    lat_bottom = geo_def['lat_bottom']

    domain = ancillary_def['domain']

    hour_run = time_run.hour
    datetime_run = time_run.to_pydatetime()
    file_ws = {}
    for folder_raw, filename_raw, type_step in zip(folder_list, filename_list, type_data):
        file_list = []
        for time_id, time_step in enumerate(time_range):

            datetime_step = time_step.to_pydatetime()
            tags_values_step = {"domain": domain,
                                "outcome_sub_path_time": datetime_step, "outcome_datetime": datetime_step,
                                "run_hour": hour_run, "run_step": 0,
                                "run_datetime": datetime_run,
                                "run_lon_right": str(lon_right),
                                "run_lon_left": str(lon_left),
                                "run_lat_bottom": str(lat_bottom),
                                "run_lat_top": str(lat_top)}

            folder_step = fill_tags2string(folder_raw, tags_template, tags_values_step)
            filename_step = fill_tags2string(filename_raw, tags_template, tags_values_step)

            path_step = join(folder_step, filename_step)

            if flag_updating:
                if os.path.exists(path_step):
                    os.remove(path_step)

            if not os.path.exists(folder_step):
                make_folder(folder_step)

            file_list.append(path_step)

        file_ws[type_step] = file_list

    return file_ws

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create data ancillary ctl list
def set_data_ancillary_ctl(time_run, time_range, data_def, geo_def, ancillary_def, tags_template,
                           type_data=None, flag_updating=True):

    if type_data is None:
        type_data = ["surface"]

    folder_list = data_def['folder']
    filename_list = data_def['filename']
    template_list = data_def['template']

    lon_right = geo_def['lon_right']
    lon_left = geo_def['lon_left']
    lat_top = geo_def['lat_top']
    lat_bottom = geo_def['lat_bottom']

    domain = ancillary_def['domain']

    hour_run = time_run.hour
    datetime_run = time_run.to_pydatetime()
    file_ws = {}
    for folder_raw, filename_raw, template_raw, type_step in zip(folder_list, filename_list, template_list, type_data):
        file_list = []
        for time_id, time_step in enumerate(time_range):
            datetime_step = time_step.to_pydatetime()
            tags_values_step = {"domain": domain,
                                "ancillary_sub_path_time": datetime_step, "ancillary_datetime": datetime_step,
                                "run_hour": hour_run, "run_step": time_id,
                                "run_datetime": datetime_run,
                                "run_lon_right": str(lon_right),
                                "run_lon_left": str(lon_left),
                                "run_lat_bottom": str(lat_bottom),
                                "run_lat_top": str(lat_top)}

            folder_step = fill_tags2string(folder_raw, tags_template, tags_values_step)
            filename_step = fill_tags2string(filename_raw, tags_template, tags_values_step)

            path_step = join(folder_step, filename_step)

            if flag_updating:
                if os.path.exists(path_step):
                    os.remove(path_step)

            if not os.path.exists(folder_step):
                make_folder(folder_step)

            file_list.append(path_step)

        file_ws[type_step] = [file_list, template_raw]

    return file_ws

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create data ancillary global list
def set_data_ancillary_global(time_run, time_range, data_def, geo_def, ancillary_def, tags_template,
                              type_data=None):

    if type_data is None:
        type_data = ["surface"]

    folder_list = data_def['folder']
    filename_list = data_def['filename']

    lon_right = geo_def['lon_right']
    lon_left = geo_def['lon_left']
    lat_top = geo_def['lat_top']
    lat_bottom = geo_def['lat_bottom']

    domain = ancillary_def['domain']

    hour_run = time_run.hour
    datetime_run = time_run.to_pydatetime()
    file_ws = {}
    for folder_raw, filename_raw, type_step in zip(folder_list, filename_list, type_data):
        file_list = []
        for time_id, time_step in enumerate(time_range):

            datetime_step = time_step.to_pydatetime()
            tags_values_step = {"domain": domain,
                                "ancillary_sub_path_time": datetime_run, "ancillary_datetime": datetime_step,
                                "run_hour": hour_run, "run_step": time_id,
                                "run_datetime": datetime_run,
                                "run_lon_right": str(lon_right),
                                "run_lon_left": str(lon_left),
                                "run_lat_bottom": str(lat_bottom),
                                "run_lat_top": str(lat_top)}

            folder_step = fill_tags2string(folder_raw, tags_template, tags_values_step)
            filename_step = fill_tags2string(filename_raw, tags_template, tags_values_step)

            path_step = join(folder_step, filename_step)

            file_list.append(path_step)

        file_ws[type_step] = file_list

    return file_ws

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create data source list
def set_data_source(time_run, time_range, data_def, geo_def, ancillary_def, tags_template,
                    type_data=None):

    if type_data is None:
        type_data = ["surface"]

    folder_list = data_def['folder']
    filename_list = data_def['filename']

    lon_right = geo_def['lon_right']
    lon_left = geo_def['lon_left']
    lat_top = geo_def['lat_top']
    lat_bottom = geo_def['lat_bottom']

    domain = ancillary_def['domain']

    datetime_run = time_run.to_pydatetime()
    file_ws = {}
    for folder_raw, filename_raw, type_step in zip(folder_list, filename_list, type_data):
        file_list = []
        for time_id, time_step in enumerate(time_range):

            datetime_step = time_step.to_pydatetime()
            tags_values_step = {"domain": domain,
                                "source_sub_path_time_gauge_now": datetime_run,
                                "source_datetime_gauge_now": datetime_step,
                                "source_sub_path_time_rnc": datetime_run,
                                "source_datetime_rnc": datetime_step,
                                "run_datetime": datetime_run,
                                "run_lon_right": str(lon_right),
                                "run_lon_left": str(lon_left),
                                "run_lat_bottom": str(lat_bottom),
                                "run_lat_top": str(lat_top)}

            folder_step = fill_tags2string(folder_raw, tags_template, tags_values_step)
            filename_step = fill_tags2string(filename_raw, tags_template, tags_values_step)

            path_step = join(folder_step, filename_step)

            file_list.append(path_step)

        file_ws[type_step] = file_list

    return file_ws

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create data ftp list
def set_data_ftp(time_run, time_range, data_def, geo_def, ancillary_def, tags_template,
                    type_data=None):

    if type_data is None:
        type_data = ["surface"]

    ftp_root_list = data_def['ftp_root']
    ftp_folder_list = data_def['ftp_folder']
    ftp_file_list = data_def['ftp_file']

    lon_right = geo_def['lon_right']
    lon_left = geo_def['lon_left']
    lat_top = geo_def['lat_top']
    lat_bottom = geo_def['lat_bottom']

    domain = ancillary_def['domain']

    datetime_run = time_run.to_pydatetime()
    ftp_list_ws = {}
    ftp_root_ws = {}
    ftp_folder_ws = {}
    ftp_file_ws = {}
    for ftp_root_raw, ftp_folder_raw, ftp_file_raw, type_step in zip(
            ftp_root_list, ftp_folder_list, ftp_file_list, type_data):

        ftp_list_type = []
        ftp_root_type = []
        ftp_folder_type = []
        ftp_file_type = []
        for time_id, time_step in enumerate(time_range):

            datetime_step = time_step.to_pydatetime()
            tags_values_step = {"domain": domain,
                                "ftp_sub_path_time_gauge_now": datetime_run,
                                "ftp_datetime_gauge_now": datetime_step,
                                "ftp_sub_path_time_rnc": datetime_run,
                                "ftp_datetime_rnc": datetime_step,
                                "run_datetime": datetime_run,
                                "run_lon_right": str(lon_right),
                                "run_lon_left": str(lon_left),
                                "run_lat_bottom": str(lat_bottom),
                                "run_lat_top": str(lat_top)}

            ftp_root_step = fill_tags2string(ftp_root_raw, tags_template, tags_values_step)
            ftp_folder_step = fill_tags2string(ftp_folder_raw, tags_template, tags_values_step)
            ftp_file_step = fill_tags2string(ftp_file_raw, tags_template, tags_values_step)

            ftp_step = ftp_root_step + ftp_folder_step + ftp_file_step

            ftp_list_type.append(ftp_step)
            ftp_root_type.append(ftp_root_step)
            ftp_folder_type.append(ftp_folder_step)
            ftp_file_type.append(ftp_file_step)

        ftp_list_ws[type_step] = ftp_list_type
        ftp_root_ws[type_step] = ftp_root_type
        ftp_folder_ws[type_step] = ftp_folder_type
        ftp_file_ws[type_step] = ftp_file_type

    return ftp_list_ws, ftp_root_ws, ftp_folder_ws, ftp_file_ws
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to add time in a unfilled string (path or filename)
def fill_tags2string(string_raw, tags_format=None, tags_filling=None):

    apply_tags = False
    if string_raw is not None:
        for tag in list(tags_format.keys()):
            if tag in string_raw:
                apply_tags = True
                break

    if apply_tags:

        tags_format_tmp = deepcopy(tags_format)
        for tag_key, tag_value in tags_format.items():
            tag_key_tmp = '{' + tag_key + '}'
            if tag_value is not None:
                if tag_key_tmp in string_raw:
                    string_filled = string_raw.replace(tag_key_tmp, tag_value)
                    string_raw = string_filled
                else:
                    tags_format_tmp.pop(tag_key, None)

        for tag_format_name, tag_format_value in list(tags_format_tmp.items()):

            if tag_format_name in list(tags_filling.keys()):
                tag_filling_value = tags_filling[tag_format_name]
                if tag_filling_value is not None:

                    if isinstance(tag_filling_value, datetime):
                        tag_filling_value = tag_filling_value.strftime(tag_format_value)

                    if isinstance(tag_filling_value, (float, int)):
                        tag_filling_value = tag_format_value.format(tag_filling_value)

                    string_filled = string_filled.replace(tag_format_value, tag_filling_value)

        string_filled = string_filled.replace('//', '/')
        return string_filled
    else:
        return string_raw
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define data time range
def set_data_time(time_step, time_settings):

    time_period_obs = time_settings['time_observed_period']
    time_period_for = time_settings['time_forecast_period']
    time_freq_obs = time_settings['time_observed_frequency']
    time_freq_for = time_settings['time_forecast_frequency']

    time_step_obs = time_step
    time_range_obs = pd.date_range(end=time_step_obs, periods=time_period_obs, freq=time_freq_obs)

    time_step_for = pd.date_range([time_step][0], periods=2, freq=time_freq_for)[-1]
    time_range_for = pd.date_range(start=time_step_for, periods=time_period_for, freq=time_freq_for)

    time_range_data = time_range_obs.union(time_range_for)

    return time_range_data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to check time validity
def check_time_limit(time_alg, time_name='time_step', time_limit_period='2D'):
    time_day = pd.Timestamp.today()
    time_limit_upper = time_day.floor('H')
    time_limit_lower = pd.date_range(end=time_limit_upper, periods=2, freq=time_limit_period)[0]

    if time_alg < time_limit_lower:
        logging.error(' ===> ' + time_name + ' is not available on source database! It is less then DB time_from')
        raise IOError(time_name + ' is not correctly defined! Check your settings or algorithm args!')
    elif time_alg > time_limit_upper:
        logging.error(' ===> ' + time_name + ' is not available on source database! It is greater then DB time_to')
        raise IOError(time_name + ' is not correctly defined! Check your settings or algorithm args!')
    else:
        pass
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define run time range
def set_run_time(time_alg, time_settings):

    time_set = time_settings['time_now']
    time_freq = time_settings['time_frequency']
    time_round = time_settings['time_rounding']
    time_period = time_settings['time_period']

    if time_alg and time_set:
        time_now = time_alg
    elif time_alg is None and time_set:
        time_now = time_set
    elif time_alg and time_set is None:
        time_now = time_alg
    else:
        logging.error(' ===> TimeNow is not correctly set!')
        raise IOError('TimeNow is undefined! Check your settings or algorithm args!')

    time_now_raw = pd.Timestamp(time_now)
    time_now_round = time_now_raw.floor(time_round)

    if time_period > 0:
        time_range = pd.date_range(end=time_now_round, periods=time_period, freq=time_freq)
    else:
        logging.warning(' ===> TimePeriod must be greater then 0. TimePeriod is set automatically to 1')
        time_range = pd.DatetimeIndex([time_now_round], freq=time_freq)

    check_time_limit(time_now_round, time_name='time_now')
    check_time_limit(time_range[0], time_name='time_run_from')
    if time_range.__len__() == 1:
        check_time_limit(time_range[0], time_name='time_run_to')
    else:
        check_time_limit(time_range[1], time_name='time_run_to')
    return time_now_round, time_range

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to make folder
def make_folder(path_folder):
    if not exists(path_folder):
        makedirs(path_folder)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read file json
def read_file_json(file_name):

    env_ws = {}
    for env_item, env_value in os.environ.items():
        env_ws[env_item] = env_value

    with open(file_name, "r") as file_handle:
        json_block = []
        for file_row in file_handle:

            for env_key, env_value in env_ws.items():
                env_tag = '$' + env_key
                if env_tag in file_row:
                    env_value = env_value.strip("'\\'")
                    file_row = file_row.replace(env_tag, env_value)
                    file_row = file_row.replace('//', '/')

            # Add the line to our JSON block
            json_block.append(file_row)

            # Check whether we closed our JSON block
            if file_row.startswith('}'):
                # Do something with the JSON dictionary
                json_dict = json.loads(''.join(json_block))
                # Start a new block
                json_block = []

    return json_dict
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get script argument(s)
def get_args():
    parser_handle = ArgumentParser()
    parser_handle.add_argument('-settings_file', action="store", dest="alg_settings")
    parser_handle.add_argument('-time', action="store", dest="alg_time")
    parser_values = parser_handle.parse_args()

    if parser_values.alg_settings:
        alg_settings = parser_values.alg_settings
    else:
        alg_settings = 'configuration.json'

    if parser_values.alg_time:
        alg_time = parser_values.alg_time
    else:
        alg_time = None

    return alg_settings, alg_time
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set logging information
def set_logging(logger_file='log.txt', logger_format=None):

    if logger_format is None:
        logger_format = '%(asctime)s %(name)-12s %(levelname)-8s ' \
                        '%(filename)s:[%(lineno)-6s - %(funcName)20s()] %(message)s'

    # Remove old logging file
    if os.path.exists(logger_file):
        os.remove(logger_file)

    # Set level of root debugger
    logging.root.setLevel(logging.DEBUG)

    # Open logging basic configuration
    logging.basicConfig(level=logging.DEBUG, format=logger_format, filename=logger_file, filemode='w')

    # Set logger handle
    logger_handle_1 = logging.FileHandler(logger_file, 'w')
    logger_handle_2 = logging.StreamHandler()
    # Set logger level
    logger_handle_1.setLevel(logging.DEBUG)
    logger_handle_2.setLevel(logging.DEBUG)
    # Set logger formatter
    logger_formatter = logging.Formatter(logger_format)
    logger_handle_1.setFormatter(logger_formatter)
    logger_handle_2.setFormatter(logger_formatter)

    # Add handle to logging
    logging.getLogger('').addHandler(logger_handle_1)
    logging.getLogger('').addHandler(logger_handle_2)

# -------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------
# Call script from external library
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------
