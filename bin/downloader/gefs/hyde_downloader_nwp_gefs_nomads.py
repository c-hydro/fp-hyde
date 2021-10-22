#!/usr/bin/python3

"""
HyDE Downloading Tool - NWP GEFS 0.25

__date__ = '20210914'
__version__ = '1.0.0'
__author__ =
        'Andrea Libertino (andrea.libertino@cimafoundation.org',
        'Fabio Delogu (fabio.delogu@cimafoundation.org',
__library__ = 'HyDE'

General command line:
python3 hyde_downloader_nwp_gefs_nomads.py -settings_file configuration.json -time YYYY-MM-DD HH:MM

Version(s):
20200227 (1.0.0) --> Beta release
"""
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Complete library
import logging
import os
import time
import json
import urllib.request
import tempfile
import xarray as xr

import numpy as np
import pandas as pd

from urllib.request import Request, urlopen
from urllib.error import URLError

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
alg_name = 'HYDE DOWNLOADING TOOL - NWP GEFS'
alg_version = '1.0.0'
alg_release = '2021-09-14'
# Algorithm parameter(s)
time_format = '%Y%m%d%H%M'
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
    ens_members = np.arange(1,data_settings["algorithm"]["ancillary"]["ens_members"]+1)

    # Starting info
    logging.info(' --> TIME RUN: ' + str(time_run))


    # Iterate over time steps
    for time_run_step in time_run_range:

        # Starting info
        logging.info(' ---> NWP RUN: ' + str(time_run_step) + ' ... ')

        # Iterate over ensemble members
        for ens_member in ens_members:

            # Starting info
            logging.info(' ---> ENSEMBLE MEMBER: ' + str(ens_member).zfill(2) + ' ... ')

            # Get data time range
            time_data_range = set_data_time(time_run_step, data_settings['data']['dynamic']['time'])
            time_data_full = pd.date_range(time_run + pd.Timedelta('1H'), time_data_range[-1], freq='1H')

            # Set data sources
            data_source = set_data_source(time_run_step, time_data_range, ens_member,
                                          data_settings['data']['dynamic']['source'],
                                          data_settings['data']['static']['bounding_box'],
                                          data_settings['algorithm']['ancillary'],
                                          data_settings['algorithm']['template'],
                                          type_data=data_settings['algorithm']['ancillary']['type'],)
            # Set data ancillary
            data_ancillary = set_data_ancillary(time_run_step, time_data_range, ens_member,
                                                data_settings['data']['dynamic']['ancillary'],
                                                data_settings['data']['static']['bounding_box'],
                                                data_settings['algorithm']['ancillary'],
                                                data_settings['algorithm']['template'],
                                                type_data=data_settings['algorithm']['ancillary']['type'],)

            # Set data outcome global
            data_outcome_global = set_data_outcome(
                time_run_step, ens_member,
                data_settings['data']['dynamic']['outcome']['global'],
                data_settings['data']['static']['bounding_box'],
                data_settings['algorithm']['ancillary'],
                data_settings['algorithm']['template'],
                type_data=data_settings['algorithm']['ancillary']['type'],
                flag_updating=data_settings['algorithm']['flags']['cleaning_dynamic_data_global'])

            # Set data outcome domain
            data_outcome_domain = set_data_outcome(
                time_run_step, ens_member,
                data_settings['data']['dynamic']['outcome']['domain'],
                data_settings['data']['static']['bounding_box'],
                data_settings['algorithm']['ancillary'],
                data_settings['algorithm']['template'],
                type_data=data_settings['algorithm']['ancillary']['type'],
                flag_updating=data_settings['algorithm']['flags']['cleaning_dynamic_data_domain'])

            if data_settings['algorithm']['flags']['downloading_mp']:
                retrieve_data_source_mp(
                    data_source, data_ancillary,
                    flag_updating=data_settings['algorithm']['flags']['cleaning_dynamic_data_ancillary'],
                    process_n=data_settings['algorithm']['ancillary']['process_mp'], limit=data_settings['algorithm']['ancillary']['remote_server_hit_per_min'])
            else:
                retrieve_data_source_seq(
                    data_source, data_ancillary,
                    flag_updating=data_settings['algorithm']['flags']['cleaning_dynamic_data_ancillary'], limit=data_settings['algorithm']['ancillary']['remote_server_hit_per_min'])

            # Merge and mask data ancillary to data outcome
            arrange_data_outcome(data_ancillary, data_outcome_global, data_outcome_domain,
                                 data_bbox=data_settings['data']['static']['bounding_box'],
                                 cdo_exec=data_settings['algorithm']['ancillary']['cdo_exec'],
                                 cdo_deps=data_settings['algorithm']['ancillary']['cdo_deps'],
                                 source_standards=data_settings['data']['dynamic']['source']['vars_standards'],
                                 date_range=time_data_full)

            # Clean data tmp (such as ancillary and outcome global)
            clean_data_tmp(
                data_ancillary, data_outcome_global,
                flag_cleaning_tmp=data_settings['algorithm']['flags']['cleaning_dynamic_data_tmp'])

            logging.info(' ---> ENSEMBLE MEMBER: ' + str(ens_member).zfill(2) + ' ... DONE')

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
# Method to check source url(s)
def check_url_source(src_data, src_code_exist=200, process_n=20, process_max=None):

    logging.info(' ----> Checking source url(s) ... ')

    if process_max is None:
        process_max = cpu_count() - 1
    if process_n > process_max:
        logging.warning(' ----> Maximum of recommended processes must be less then ' + str(process_max))
        logging.warning(' ----> Set number of process from ' + str(process_n) + ' to ' + str(process_max))
        process_n = process_max

    src_response_list = []
    src_key_list = []
    for src_data_key, src_data_list in src_data.items():

        logging.info(' -----> Source ' + src_data_key + ' ... ')

        with Pool(processes=process_n, maxtasksperchild=1) as process_pool:
            src_response = process_pool.map(request_url, src_data_list, chunksize=1)
            process_pool.close()
            process_pool.join()
            src_response_list.append(src_response)

        src_key_list.append(src_data_key)
        logging.info(' -----> Source ' + src_data_key + ' ... DONE')

    for src_key_step, src_response_step in zip(src_key_list, src_response_list):
        if not all(src_code_el == src_code_exist for src_code_el in src_response_step):
            logging.warning(' ===> Some url(s) for source ' + src_key_step + ' are not available!')
            logging.info(' ----> Checking source url(s) ... FAILED')
            return False

    logging.info(' ----> Checking source url(s) ... DONE')
    return True

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to request url
def request_url(src_url):
    logging.getLogger('requests').setLevel(logging.CRITICAL)
    src_request = Request(src_url)
    try:
        src_response = urlopen(src_request)
        return src_response.code
    except URLError as e:
        if hasattr(e, 'reason'):
            logging.warning(' ===> URL is unreachable from server.')
            logging.warning(' ===> URL: ', src_url[0])
            return False
        elif hasattr(e, 'code'):
            logging.warning(' ===> The server couldn\'t fulfill the request.')
            logging.warning(' ===> URL: ', src_url[0])
            return False
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
# Method to merge and mask outcome dataset(s)
def arrange_data_outcome(src_data, dst_data_global, dst_data_domain,
                         data_bbox=None, cdo_exec=None, cdo_deps=None, source_standards=None, date_range=None):

    logging.info(' ----> Dumping data ... ')

    if data_bbox is not None:
        bbox_lon_right = str(data_bbox['lon_right'])
        bbox_lon_left = str(data_bbox['lon_left'])
        bbox_lat_top = str(data_bbox['lat_top'])
        bbox_lat_bottom = str(data_bbox['lat_bottom'])

        bbox_points = [bbox_lon_left, bbox_lon_right, bbox_lat_bottom, bbox_lat_top]
        bbox_cdo = ','.join(bbox_points)
    else:
        bbox_cdo = None

    if cdo_exec is None:
        logging.error(' ===> CDO executable is not set!')
        raise RuntimeError(' CDO executable is not set!')

    for cdo_dep in cdo_deps:
        os.environ['LD_LIBRARY_PATH'] = 'LD_LIBRARY_PATH:' + cdo_dep
    #temp for local debug
    os.environ['PATH'] = os.environ['PATH'] + ':/home/andrea/FP_libs/fp_libs_cdo/cdo-1.9.8_nc-4.6.0_hdf-1.8.17_eccodes-2.17.0/bin/'

    cdo = Cdo()
    cdo.setCdo(cdo_exec)

    for (src_key_step, src_data_step), \
        (dst_key_global_step, dst_data_global_step), (dst_key_domain_step, dst_data_domain_step) in \
            zip(src_data.items(), dst_data_global.items(), dst_data_domain.items()):

        logging.info(' -----> Type ' + src_key_step + ' ... ')

        src_data_step.sort()
        if isinstance(dst_data_global_step, list):
            dst_data_global_step = dst_data_global_step[0]
        if isinstance(dst_data_domain_step, list):
            dst_data_domain_step = dst_data_domain_step[0]

        folder_data_global_step, filename_data_global_step = os.path.split(dst_data_global_step)
        tmp_data_global_step_cat = create_filename_tmp(folder=folder_data_global_step, suffix='.grib2')
        tmp_data_global_step_seltimestep = create_filename_tmp(folder=folder_data_global_step, suffix='.grib2')
        tmp_data_global_step_convert = create_filename_tmp(folder=folder_data_global_step, suffix='.nc')

        logging.info(' ------> Merge, convert and project data ...  ')
        if not os.path.exists(dst_data_global_step):

            cdo.cat(input=src_data_step, output=tmp_data_global_step_cat, options='-r')
            info_file = cdo.infov(input=tmp_data_global_step_cat)

            # Explore available variable in the grib file, skiping rows with headers and footers
            var_in_all = [i.split(':')[-1].replace(' ','') for i in cdo.infov(input=tmp_data_global_step_cat) if i.split(':')[0].replace(' ','').isnumeric()]
            var_in = np.unique(var_in_all)
            logging.info(' ------> Var(s) found in file: ' + ','.join(var_in))

            step_expected = int(src_data_step.__len__()*len(var_in))
            step_get = len(var_in_all)

            if step_get > step_expected:
                step_ratio = int(step_get / step_expected)
                var_select_cdo, timestep_select_cdo = select_time_steps(
                    info_file, id_start=step_ratio, id_end=step_get, id_period=step_ratio)
                cdo.seltimestep(timestep_select_cdo, input=tmp_data_global_step_cat, output=tmp_data_global_step_seltimestep)
            else:
                if os.path.exists(tmp_data_global_step_seltimestep):
                    os.remove(tmp_data_global_step_seltimestep)
                tmp_data_global_step_seltimestep = tmp_data_global_step_cat

            cdo.copy(input=tmp_data_global_step_seltimestep, output=tmp_data_global_step_convert, options="-f nc4")
            cdo.sellonlatbox('-180,180,-90,90', input=tmp_data_global_step_convert, output=dst_data_global_step)

            if not source_standards == None:

                if source_standards['convert2standard_continuum_format']:
                    out_file = deepcopy(xr.open_dataset(dst_data_global_step))
                    time_range_full = pd.date_range(min(out_file["time"].values),max(out_file["time"].values),freq='H')
                    os.remove(dst_data_global_step)

                    if '2t' in var_in.tolist():
                        if source_standards['source_temperature_mesurement_unit'] == 'C':
                            pass
                        elif source_standards['source_temperature_mesurement_unit'] == 'K':
                            logging.info(' ------> Convert temperature to C ... ')
                            #out_file = deepcopy(xr.open_dataset(dst_data_global_step))
                            out_file['2t_C'] = out_file['2t'] - 273.15
                            out_file['2t_C'].attrs['long_name'] = '2 metre temperature'
                            out_file['2t_C'].attrs['units'] = 'C'
                            out_file['2t_C'].attrs['standard_name'] = "air_temperature"
                            out_file = out_file.rename({'2t': '2t_K'})
                            #out_file.to_netcdf(dst_data_global_step)
                            logging.info(' ------> Convert temperature to C ... DONE')
                        else:
                            raise NotImplementedError

                    if 'tp' in var_in.tolist() and source_standards['source_precipitation_is_cumulated'] is True:
                        logging.info(' ------> Decumulate precipitation ... ')
                        #out_file = deepcopy(xr.open_dataset(dst_data_global_step))
                        #os.remove(dst_data_global_step)
                        temp = np.diff(out_file['tp'].values, n=1, axis=0, prepend=0)
                        out_file['tp'][np.arange(2,out_file['tp'].values.shape[0],2),:,:].values = temp[np.arange(2,out_file['tp'].values.shape[0],2),:,:]
                        out_file['tp'].values = out_file['tp'].values/3
                        out_file['tp'].attrs['long_name'] = 'hourly precipitation depth'
                        out_file['tp'].attrs['units'] = 'mm'
                        out_file['tp'].attrs['standard_name'] = "precipitation"
                        #out_file.to_netcdf(dst_data_global_step)
                        logging.info(' ------> Decumulate precipitation ... DONE')

                    if '10u' in var_in.tolist() and source_standards['source_wind_separate_components'] is True:
                        logging.info(' ------> Combine wind component ... ')
                        #out_file = deepcopy(xr.open_dataset(dst_data_global_step))
                        #os.remove(dst_data_global_step)
                        out_file['10wind'] = np.sqrt(out_file['10u']**2 + out_file['10v']**2)
                        out_file['10wind'].attrs['long_name'] = '10 m wind'
                        out_file['10wind'].attrs['units'] = 'm s**-1'
                        out_file['10wind'].attrs['standard_name'] = "wind"
                        #out_file.to_netcdf(dst_data_global_step)
                        logging.info(' ------> Combine wind component ... DONE')

                    # out_file = deepcopy(xr.open_dataset(dst_data_global_step))
                    # os.remove(dst_data_global_step)

                    # Check if file has "heigth" dimension and remove it
                    try:
                        out_file = out_file.squeeze(dim="height", drop=True)
                        out_file = out_file.squeeze(dim="height_2", drop=True)
                        logging.info(' ------> Remove height dimensions ... ')
                    except:
                        pass

                    # Reindex time axis by padding last available map over the time range
                    out_file=out_file.reindex(time=date_range, method='nearest')
                    out_file.to_netcdf(dst_data_global_step)

            if os.path.exists(tmp_data_global_step_cat):
                os.remove(tmp_data_global_step_cat)
            if os.path.exists(tmp_data_global_step_seltimestep):
                os.remove(tmp_data_global_step_seltimestep)
            if os.path.exists(tmp_data_global_step_convert):
                os.remove(tmp_data_global_step_convert)

            logging.info(' ------> Merge, convert and project data ...  DONE')
        else:
            logging.info(' ------> Merge, convert and project data ...  SKIPPED. Data already merged.')

        logging.info(' ------> Mask data over domain ...  ')
        if not os.path.exists(dst_data_domain_step):
            if bbox_cdo is not None:
                cdo.sellonlatbox(bbox_cdo, input=dst_data_global_step, output=dst_data_domain_step)
                logging.info(' ------> Mask data over domain ...  DONE')
            else:
                logging.info(' ------> Mask data over domain ...  SKIPPED. Domain bounding box not defined.')
        else:
            logging.info(' ------> Mask data over domain ...  SKIPPED. Data already masked.')

        logging.info(' -----> Type ' + src_key_step + ' ... DONE')

    logging.info(' ----> Dumping data ... DONE')
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to drop data
def select_time_steps(info_file, id_start=2, id_end=None, id_period=2):

    if id_end is None:
        id_end = int(info_file[-1].split()[0])

    list_vars = []
    for info_row in info_file[:-1]:
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
def retrieve_data_source_mp(src_data, dst_data, flag_updating=False, process_n=20, process_max=None, limit=9999):

    logging.info(' ----> Downloading data in multiprocessing mode ... ')

    if process_max is None:
        process_max = cpu_count() - 1
    if process_n > process_max:
        logging.warning(' ----> Maximum of recommended processes must be less then ' + str(process_max))
        logging.warning(' ----> Set number of process from ' + str(process_n) + ' to ' + str(process_max))
        process_n = process_max

    data_list = []
    data_check = []
    for (src_data_key, src_data_list), (dst_data_key, dst_data_list) in zip(src_data.items(), dst_data.items()):
        for src_step_url, dst_step_path in zip(src_data_list, dst_data_list):
            dst_step_root, dst_step_file = split(dst_step_path)
            make_folder(dst_step_root)

            if exists(dst_step_path) and flag_updating:
                flag_updating = True
            elif (not exists(dst_step_path)) and flag_updating:
                flag_updating = True
            elif (not exists(dst_step_path)) and (not flag_updating):
                flag_updating = True
            if flag_updating:
                data_list.append([src_step_url, dst_step_path])

            data_check.append([src_step_url, dst_step_path])

    if len(data_list)>limit:
        for i in range(0,len(data_list),limit):
            max_available = min(i + limit, len(data_list))
            chunk = data_list[i:i + limit]

            with Pool(processes=process_n, maxtasksperchild=1) as process_pool:
                _ = process_pool.map(request_data_source, chunk, chunksize=1)
                process_pool.close()
                process_pool.join()

            logging.info(' ----> Wait 60 seconds for next requests ...')
            time.sleep(60)
            if max_available<len(data_list):
                logging.info(' ----> '  + str(int(100*max_available/len(data_list))) + ' % complete...')
                logging.info(' ----> Continue with next chunk of requests...')
    else:
        with Pool(processes=process_n, maxtasksperchild=1) as process_pool:
            _ = process_pool.map(request_data_source, data_list, chunksize=1)
            process_pool.close()
            process_pool.join()

    find_data_corrupted(data_check)

    logging.info(' ----> Downloading data in multiprocessing mode ... DONE')
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

    for idx_step in idx_retry:
        data_false = data_list[idx_step]

        if os.path.exists(data_false[1]):
            os.remove(data_false[1])

        logging.info(' ------> Downloading data ' + split(data_false[1])[1] + ' ... ')
        request_data_source(data_false)
        logging.info(' ------> Downloading data ' + split(data_false[1])[1] + ' ... DONE')

    logging.info(' -----> Checking for corrupted or unavailable data  ... DONE')
# ------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to request data using a source url and a destination filename
def request_data_source(data_list):
    logging.info(' :: Http request for downloading: ' + data_list[0] + ' ... ')
    logging.info(' :: Outcome data will be dumped in: ' + split(data_list[1])[1] + ' ... ')

    try:
        urllib.request.urlretrieve(data_list[0], filename=data_list[1])
        logging.info(' :: Outcome data will be dumped in: ' + split(data_list[1])[1] + ' ... DONE')
        logging.info(' :: Http request for downloading: ' + data_list[0] + ' ... DONE')
        return True
    except IOError:
        logging.warning(' :: Outcome data will be dumped in: ' + split(data_list[1])[1] + ' ... FAILED')
        logging.error(' :: Http request for downloading: ' + data_list[0] + ' ... FAILED. IO error.')
        raise IOError(' :: Http request for downloading: ' + data_list[0] + ' ... FAILED. Data Not available on the server.')
    except ConnectionResetError:
        logging.warning(' :: Outcome data will be dumped in: ' + split(data_list[1])[1] + ' ... FAILED')
        logging.error(' :: Http request for downloading: ' + data_list[0] + ' ... FAILED. Connection Reset error')
        raise ConnectionResetError(' :: Http request for downloading: ' + data_list[0] + ' ... FAILED. Connection Reset error')
    except ConnectionAbortedError:
        logging.warning(' :: Outcome data will be dumped in: ' + split(data_list[1])[1] + ' ... FAILED')
        logging.error(' :: Http request for downloading: ' + data_list[0] + ' ... FAILED. Connetction Aborted error.')
        raise ConnectionAbortedError(' :: Http request for downloading: ' + data_list[0] + ' ... FAILED. Connetction Aborted error.')
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to retrieve and store data (sequential)
def retrieve_data_source_seq(src_data, dst_data, flag_updating=False, limit=9999):

    logging.info(' ----> Downloading data in sequential mode ... ')

    data_list = []
    data_check = []
    hit_count = 0
    for (src_data_key, src_data_list), (dst_data_key, dst_data_list) in zip(src_data.items(), dst_data.items()):

        logging.info(' -----> DataType: ' + src_data_key + ' ... ')

        for src_step_url, dst_step_path in zip(src_data_list, dst_data_list):

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
                request_data_source([src_step_url, dst_step_path])
                hit_count += 1
                data_list.append([src_step_url, dst_step_path])
                logging.info(' -------> Save data in file: ' + str(dst_step_file) + ' ... DONE')
                if hit_count == limit:
                    logging.info(' ----> Wait 60 seconds for next requests ...')
                    time.sleep(60)
                    hit_count = 0
                    logging.info(' ----> Continue with next chunk of requests...')
            else:
                logging.info(' ------> Save data in file: ' + str(dst_step_file) +
                             ' ... SKIPPED. File saved previously')

            data_check.append([src_step_url, dst_step_path])

        logging.info(' -----> DataType: ' + src_data_key + ' ... DONE')

    find_data_corrupted(data_check)

    logging.info(' ----> Downloading data in sequential mode ... DONE')
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create data outcome list
def set_data_outcome(time_run, ens_member_num, data_def, geo_def, ancillary_def, tags_template,
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
    ens_member = str(ens_member_num).zfill(2)

    hour_run = time_run.hour
    datetime_run = time_run.to_pydatetime()
    file_ws = {}
    for folder_raw, filename_raw, type_step in zip(folder_list, filename_list, type_data):
        file_list = []

        tags_values_step = {"domain": domain,
                            "outcome_sub_path_time": datetime_run, "outcome_datetime": datetime_run,
                            "run_hour": hour_run, "run_step": 0,
                            "run_datetime": datetime_run,
                            "run_lon_right": str(lon_right),
                            "run_lon_left": str(lon_left),
                            "run_lat_bottom": str(lat_bottom),
                            "run_lat_top": str(lat_top),
                            "ens_member" : ens_member}

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
# Method to create data ancillary list
def set_data_ancillary(time_run, time_range, ens_member_num, data_def, geo_def, ancillary_def, tags_template,
                       type_data=None, anl_include=False):

    if type_data is None:
        type_data = ["surface"]

    folder_list = data_def['folder']
    filename_list = data_def['filename']

    lon_right = geo_def['lon_right']
    lon_left = geo_def['lon_left']
    lat_top = geo_def['lat_top']
    lat_bottom = geo_def['lat_bottom']

    domain = ancillary_def['domain']
    ens_member = str(ens_member_num).zfill(2)

    hour_run = time_run.hour
    datetime_run = time_run.to_pydatetime()
    file_ws = {}
    for folder_raw, filename_raw, type_step in zip(folder_list, filename_list, type_data):
        file_list = []
        for time_id, time_step in enumerate(time_range):

            if not anl_include:
                time_id = time_id + 1

            datetime_step = time_step.to_pydatetime()
            tags_values_step = {"domain": domain,
                                "ancillary_sub_path_time": datetime_run, "ancillary_datetime": datetime_step,
                                "run_hour": hour_run, "run_step": time_id,
                                "run_datetime": datetime_run,
                                "run_lon_right": str(lon_right),
                                "run_lon_left": str(lon_left),
                                "run_lat_bottom": str(lat_bottom),
                                "run_lat_top": str(lat_top),
                                "ens_member": ens_member}

            folder_step = fill_tags2string(folder_raw, tags_template, tags_values_step)
            filename_step = fill_tags2string(filename_raw, tags_template, tags_values_step)

            path_step = join(folder_step, filename_step)

            file_list.append(path_step)

        file_ws[type_step] = file_list

    return file_ws

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create data source list
def set_data_source(time_run, time_range, ens_member_num, data_def, geo_def, ancillary_def, tags_template,
                    type_data=None, anl_include=False):

    if type_data is None:
        type_data = ["surface"]

    url_root_list = data_def['url_root']
    url_file_list = data_def['url_file']
    url_lev_list = data_def['url_lev']
    url_vars_list = data_def['url_vars']
    url_bbox_list = data_def['url_bbox']
    url_loc_list = data_def['url_loc']

    lon_right = geo_def['lon_right']
    lon_left = geo_def['lon_left']
    lat_top = geo_def['lat_top']
    lat_bottom = geo_def['lat_bottom']

    domain = ancillary_def['domain']
    ens_member = str(ens_member_num).zfill(2)

    frc_steps = (time_range - time_run).total_seconds()/3600

    hour_run = time_run.hour
    datetime_run = time_run.to_pydatetime()
    url_ws = {}
    for url_root_raw, url_file_raw, url_lev_raw, url_vars_raw, url_bbox_raw, url_loc_raw, type_step in zip(
            url_root_list, url_file_list, url_lev_list, url_vars_list, url_bbox_list, url_loc_list, type_data):

        if url_bbox_raw is None:
            url_bbox_raw = ''

        url_list = []
        for time_id, time_step in zip(frc_steps, time_range):

            datetime_step = time_step.to_pydatetime()
            tags_values_step = {"domain": domain,
                                "outcome_sub_path_time": datetime_run, "outcome_datetime": datetime_step,
                                "run_hour": hour_run, "run_step": int(time_id),
                                "run_datetime": datetime_run,
                                "run_lon_right": str(lon_right),
                                "run_lon_left": str(lon_left),
                                "run_lat_bottom": str(lat_bottom),
                                "run_lat_top": str(lat_top),
                                "ens_member": ens_member}

            url_root_step = fill_tags2string(url_root_raw, tags_template, tags_values_step)
            url_file_step = fill_tags2string(url_file_raw, tags_template, tags_values_step)
            url_lev_step = fill_tags2string(url_lev_raw, tags_template, tags_values_step)
            url_vars_step = fill_tags2string(url_vars_raw, tags_template, tags_values_step)
            url_bbox_step = fill_tags2string(url_bbox_raw, tags_template, tags_values_step)
            url_loc_step = fill_tags2string(url_loc_raw, tags_template, tags_values_step)

            url_step = url_root_step + url_file_step + url_lev_step + url_vars_step + url_bbox_step + url_loc_step

            url_list.append(url_step)

        url_ws[type_step] = url_list

    return url_ws
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
def check_time_limit(time_alg, time_name='time_step', time_limit_period='9D', time_round='D'):
    time_day = pd.Timestamp.today()
    time_limit_upper = time_day.floor(time_round)
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

    if time_period < 1:
        time_period = 1
        logging.warning(' ===> TimePeriod must be greater then zero! TimePeriod set to 1.')

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

    check_time_limit(time_now_round, time_name='time_now', time_round=time_round)
    check_time_limit(time_range[0], time_name='time_run_from', time_round='H')
    if time_period > 1:
        check_time_limit(time_range[1], time_name='time_run_to', time_round='H')
    else:
        check_time_limit(time_range[0], time_name='time_run_to', time_round='H')
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
