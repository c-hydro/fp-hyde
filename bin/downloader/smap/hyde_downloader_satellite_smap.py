#!/usr/bin/python3
"""
HyDE Downloading Tool - SATELLITE SMAP (modified and extended NSIDC Data Download Script)

__date__ = '20200511'
__version__ = '1.0.2'
__author__ =
        'Fabio Delogu (fabio.delogu@cimafoundation.org',
        'Andrea Libertino (andrea.libertino@cimafoundation.org',

__library__ = 'HyDE'

If you wish, you may store your Earthdata username/password in a .netrc
file in your $HOME directory and the script will automatically attempt to
read this file. The .netrc file should have the following format:
   machine urs.earthdata.nasa.gov login myusername password mypassword
where 'myusername' and 'mypassword' are your Earthdata credentials.

General command line:
python3 hyde_downloader_satellite_smap.py -settings_file configuration.json -time "YYYY-MM-DD HH:MM"

Version(s):
20200511 (1.0.2) --> Fix bugs 
20200510 (1.0.1) --> Add multiprocessing mode and cleaning procedure(s) for ancillary and source file(s)
20200504 (1.0.0) --> Beta release
"""

# -------------------------------------------------------------------------------------
# Complete library
import logging
import time
import base64
import itertools
import json
import netrc
import re
import os
import ssl
import sys

import pandas as pd
import numpy as np

from multiprocessing import Pool, cpu_count
from contextlib import contextmanager
from argparse import ArgumentParser
from copy import deepcopy
from datetime import datetime
from osgeo import gdal, gdalconst

from urllib.parse import urlparse
from urllib.request import urlopen, Request, build_opener, HTTPCookieProcessor
from urllib.error import HTTPError, URLError
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Algorithm information
alg_name = 'HYDE DOWNLOADING TOOL - SATELLITE SMAP'
alg_version = '1.0.2'
alg_release = '2020-05-11'
# Algorithm parameter(s)
time_format = '%Y%m%d%H%M'
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get credentials
def get_credentials(url, urs_url='https://urs.earthdata.nasa.gov'):

    credentials = None
    try:
        info = netrc.netrc()
        username, account, password = info.authenticators(urlparse(urs_url).hostname)
        errprefix = 'File netrc error: '
    except Exception as e:
        logging.error(' ===> File netrc error: {0}'.format(str(e)))
        raise RuntimeError('Credentials are not available on netrc file')

    while not credentials:
        credentials = '{0}:{1}'.format(username, password)
        credentials = base64.b64encode(credentials.encode('ascii')).decode('ascii')

        if url:
            try:
                req = Request(url)
                req.add_header('Authorization', 'Basic {0}'.format(credentials))
                opener = build_opener(HTTPCookieProcessor())
                opener.open(req)
            except HTTPError:
                logging.error(' ===> ' + errprefix + 'Incorrect username or password')
                raise RuntimeError('Credentials are not available on netrc file')

    return credentials
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to correct version string
def build_version_query_params(version):
    desired_pad_length = 3
    if len(version) > desired_pad_length:
        logging.error(' ===> Version string too long: "{0}"'.format(version))
        raise RuntimeError('String is not allowed in this format')

    version = str(int(version))  # Strip off any leading zeros
    query_params = ''

    while len(version) <= desired_pad_length:
        padded_version = version.zfill(desired_pad_length)
        query_params += '&version={0}'.format(padded_version)
        desired_pad_length -= 1
    return query_params
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to build query url
def build_cmr_query_url(short_name, version, time_start, time_end,
                        bounding_box=None, polygon=None,
                        filename_filter=None, cmr_file_url=None):
    params = '&short_name={0}'.format(short_name)
    params += build_version_query_params(version)
    params += '&temporal[]={0},{1}'.format(time_start, time_end)
    if polygon:
        params += '&polygon={0}'.format(polygon)
    elif bounding_box:
        params += '&bounding_box={0}'.format(bounding_box)
    if filename_filter:
        option = '&options[producer_granule_id][pattern]=true'
        params += '&producer_granule_id[]={0}{1}'.format(filename_filter, option)
    return cmr_file_url + params
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to execute url request
def cmr_request(data_list):

    src_data = data_list[0]
    dest_data = data_list[1]
    credentials = data_list[2]

    file_name = os.path.split(dest_data)[1]

    logging.info(' -----> Downloading ' + src_data + ' :: ' + file_name + ' ... ')

    if not os.path.exists(dest_data):
        try:
            req = Request(src_data)
            if credentials:
                req.add_header('Authorization', 'Basic {0}'.format(credentials))
            opener = build_opener(HTTPCookieProcessor())
            data = opener.open(req).read()
            open(dest_data, 'wb').write(data)

            logging.info(' -----> Downloading ' + src_data + ' :: ' + file_name + ' ... DONE')

        except HTTPError as e:
            logging.info(' -----> Downloading ' + src_data + ' :: ' + file_name + ' ... FAILED')
            logging.error(' ===> HTTP error {0}, {1}'.format(e.code, e.reason))

        except URLError as e:
            logging.info(' -----> Downloading ' + src_data + ' :: ' + file_name + ' ... FAILED')
            logging.error(' ===> URL error: {0}'.format(e.reason))
        except IOError:
            raise
        except KeyboardInterrupt:
            quit()
    else:
        logging.info(' -----> Downloading ' + src_data + ' :: ' + file_name + ' ... SKIPPED. PREVIOUSLY DONE')

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to download url(s) in multiprocessing mode
def cmr_download_mp(urls, dests, process_n=4, process_max=None):

    if not urls:
        return

    if process_max is None:
        process_max = cpu_count() - 1
    if process_n > process_max:
        logging.warning(' ===> Maximum of recommended processes must be less then ' + str(process_max))
        logging.warning(' ===> Set number of process from ' + str(process_n) + ' to ' + str(process_max))
        process_n = process_max

    url_count = len(urls)
    logging.info(' ----> Transferring {0} files in multiprocessing mode ... '.format(url_count))
    credentials = None

    dest_file_list = list(dests.values())

    logging.info(' -----> Preparing files ... ')
    request_list = []
    for index, (url, dest_file) in enumerate(zip(urls, dest_file_list), start=1):

        if isinstance(dest_file, list):
            dest_file = dest_file[0]
        path_name, file_name = os.path.split(dest_file)
        make_folder(path_name)

        if not credentials and urlparse(url).scheme == 'https':
            credentials = get_credentials(url)

        if not os.path.exists(dest_file):
            request_list.append([url, dest_file, credentials])

    logging.info(' -----> Preparing files ... DONE')

    logging.info(' -----> Pooling requests ... ')
    response_list = []
    if request_list:
        with Pool(processes=process_n, maxtasksperchild=1) as process_pool:
            src_response = process_pool.map(cmr_request, request_list, chunksize=1)
            process_pool.close()
            process_pool.join()
            response_list.append(src_response)
        logging.info(' -----> Pooling requests ... DONE')
    else:
        logging.info(' -----> Pooling requests ... SKIPPED. PREVIOUSLY DONE')

    logging.info(' ----> Transferring {0} files in multiprocessing mode ... DONE'.format(url_count))
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to download url(s) in sequential mode
def cmr_download_seq(urls, dests):

    if not urls:
        return

    url_count = len(urls)
    logging.info(' ----> Transferring {0} files in sequential mode ... '.format(url_count))
    credentials = None

    dest_file_list = dests.values()

    for index, (url, dest_file) in enumerate(zip(urls, dest_file_list), start=1):

        if isinstance(dest_file, list):
            dest_file = dest_file[0]

        path_name, file_name = os.path.split(dest_file)
        make_folder(path_name)

        logging.info(' -----> {0}/{1}: {2} ... '.format(str(index).zfill(len(str(url_count))), url_count, file_name))

        if not os.path.exists(dest_file):
            if not credentials and urlparse(url).scheme == 'https':
                credentials = get_credentials(url)
            cmr_request([url, dest_file, credentials])
        else:
            logging.info(
                ' -----> {0}/{1}: {2} ... SKIPPED. PREVIOUSLY DONE'.format(str(index).zfill(len(str(url_count))),
                                                                           url_count, file_name))

    logging.info(' ----> Transferring {0} files in sequential mode ... DONE'.format(url_count))
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to filter url(s)
def cmr_filter_urls(search_results):
    """Select only the desired data files from CMR response."""
    if 'feed' not in search_results or 'entry' not in search_results['feed']:
        return []

    entries = [e['links']
               for e in search_results['feed']['entry']
               if 'links' in e]
    # Flatten "entries" to a simple list of links
    links = list(itertools.chain(*entries))

    urls = []
    unique_filenames = set()
    for link in links:
        if 'href' not in link:
            # Exclude links with nothing to download
            continue
        if 'inherited' in link and link['inherited'] is True:
            # Why are we excluding these links?
            continue
        if 'rel' in link and 'data#' not in link['rel']:
            # Exclude links which are not classified by CMR as "data" or "metadata"
            continue

        if 'title' in link and 'opendap' in link['title'].lower():
            # Exclude OPeNDAP links--they are responsible for many duplicates
            # This is a hack; when the metadata is updated to properly identify
            # non-datapool links, we should be able to do this in a non-hack way
            continue

        filename = link['href'].split('/')[-1]
        if filename in unique_filenames:
            # Exclude links with duplicate filenames (they would overwrite)
            continue
        unique_filenames.add(filename)

        urls.append(link['href'])

    return urls
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to search url(s)
def cmr_search(short_name, version, time_start, time_end,
               bounding_box='', polygon='', filename_filter='',
               cmr_page_size=None, cmr_url=None, cmr_file_url=None):

    cmr_file_url = (cmr_file_url.format(cmr_url, cmr_page_size))

    """Perform a scrolling CMR query for files matching input criteria."""
    cmr_query_url = build_cmr_query_url(short_name=short_name, version=version,
                                        time_start=time_start, time_end=time_end,
                                        bounding_box=bounding_box,
                                        polygon=polygon, filename_filter=filename_filter,
                                        cmr_file_url=cmr_file_url)

    logging.info(' ----> Querying for data:\n\t{0}\n'.format(cmr_query_url))

    cmr_scroll_id = None
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        urls = []
        while True:
            req = Request(cmr_query_url)
            if cmr_scroll_id:
                req.add_header('cmr-scroll-id', cmr_scroll_id)
            response = urlopen(req, context=ctx)
            if not cmr_scroll_id:
                # Python 2 and 3 have different case for the http headers
                headers = {k.lower(): v for k, v in dict(response.info()).items()}
                cmr_scroll_id = headers['cmr-scroll-id']
                hits = int(headers['cmr-hits'])
                if hits > 0:
                    logging.info(' ----> Found {0} matches.'.format(hits))
                else:
                    logging.info(' ----> Found no matches.')
            search_page = response.read()
            search_page = json.loads(search_page.decode('utf-8'))
            url_scroll_results = cmr_filter_urls(search_page)
            if not url_scroll_results:
                break
            if hits > cmr_page_size:
                print('.', end='')
                sys.stdout.flush()
            urls += url_scroll_results

        if hits > cmr_page_size:
            print()
        return urls
    except KeyboardInterrupt:
        quit()
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
    set_logging(logger_file=os.path.join(data_settings['data']['log']['folder'],
                                         data_settings['data']['log']['filename']))
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
    # Get algorithm time range information
    time_run, time_run_range = set_run_time(alg_time, data_settings['time'])

    # Get algorithm geographical information
    geo_settings = data_settings['data']['static']['geo_file']
    geo_proj, geo_geotrans, geo_data, \
    geo_wide, geo_high, geo_min_x, geo_max_y, geo_max_x, geo_min_y, \
    geo_mask_idx = read_file_geo(os.path.join(geo_settings['folder'], geo_settings['filename']))

    # Starting info
    logging.info(' --> TIME RUN: ' + str(time_run))

    # Iterate over time steps
    for time_run_step in time_run_range[1:]:

        # Starting info
        logging.info(' ---> TIME STEP: ' + str(time_run_step) + ' ... ')

        # Get data time range
        time_range, time_start, time_end = set_data_time(time_run_step, data_settings['data']['dynamic']['time'])

        # Collect product information
        short_name_list, version_list, template_root_list, template_vars_data_list, template_group_data_list, \
            bounding_box, cmr_url_list, urs_url_list, cmr_page_size_list, \
            url_filename_search_list, cmr_file_url_list, \
            polygon_list, filename_filter_list = collect_product_info(
            info_product=data_settings['product'], info_bbox=data_settings['data']['static']['bounding_box'],
            info_url=data_settings['data']['dynamic']['url'])

        # Iterate over product(s) type
        for file_id, (short_name_step, version_step, cmr_url_step, urs_url_step, cmr_page_size_step,
                      url_filename_search_step, cmr_file_url_step,
                      polygon_step, filename_filter_step) in enumerate(zip(short_name_list, version_list, cmr_url_list,
                                                                           urs_url_list, cmr_page_size_list,
                                                                           url_filename_search_list, cmr_file_url_list,
                                                                           polygon_list, filename_filter_list)):
            # Retrieve url(s)
            if not url_filename_search_step:
                url_filename_search_step = cmr_search(
                    short_name_step, version_step, time_start, time_end,
                    bounding_box=bounding_box,
                    polygon=polygon_step, filename_filter=filename_filter_step,
                    cmr_page_size=cmr_page_size_step, cmr_url=cmr_url_step, cmr_file_url=cmr_file_url_step)

            # Prepare folder(s) and filename(s)
            time_stamp, filename_list_url, filename_obj_source, fileroot_obj_source = set_data_source(
                file_id, url_filename_search_step,
                file_obj=data_settings['data']['dynamic']['source'],
                variable_obj=template_vars_data_list,
                root_obj=template_root_list,
                ancillary_obj=data_settings['algorithm']['ancillary'],
                template_obj=data_settings['algorithm']['template'],
                flag_cleaning_source=data_settings['algorithm']['flags']['cleaning_dynamic_data_source'])

            # Prepare ancillary filename(s)
            filename_obj_ancillary_global, filename_obj_ancillary_domain = set_data_ancillary(
                time_stamp, file_id,
                file_obj=data_settings['data']['dynamic']['ancillary'],
                variable_obj=template_vars_data_list,
                ancillary_obj=data_settings['algorithm']['ancillary'],
                template_obj=data_settings['algorithm']['template'],
                flag_cleaning_ancillary_global=data_settings['algorithm']['flags']['cleaning_dynamic_data_ancillary_global'],
                flag_cleaning_ancillary_domain=data_settings['algorithm']['flags']['cleaning_dynamic_data_ancillary_domain'])

            # Prepare outcome filename(s)
            filename_obj_outcome = set_data_outcome(
                time_stamp, file_id,
                file_obj=data_settings['data']['dynamic']['outcome'],
                variable_obj=template_vars_data_list,
                group_obj=template_group_data_list,
                ancillary_obj=data_settings['algorithm']['ancillary'],
                template_obj=data_settings['algorithm']['template'],
                flag_cleaning_outcome=data_settings['algorithm']['flags']['cleaning_dynamic_data_ancillary_global'])

            # Download file(s)
            if data_settings['algorithm']['flags']['downloading_mp']:
                cmr_download_mp(filename_list_url, filename_obj_source,
                                process_n=data_settings['algorithm']['ancillary']['process_mp'])
            else:
                cmr_download_seq(filename_list_url, filename_obj_source)
            
            # Process file(s)
            process_cmr(filename_obj_source, fileroot_obj_source,
                        filename_obj_ancillary_global, filename_obj_ancillary_domain,
                        filename_obj_outcome,
                        geo_proj, geo_geotrans, geo_data,
                        geo_wide, geo_high, geo_min_x, geo_max_y, geo_max_x, geo_min_y,
                        geo_mask_idx, template_vars_data_list)

            # Clean files source and ancillary (if needed)
            clean_data_tmp(filename_obj_source, filename_obj_ancillary_global, filename_obj_ancillary_domain,
                           flag_cleaning_source=data_settings['algorithm']['flags']['cleaning_dynamic_data_source'],
                           flag_cleaning_tmp=data_settings['algorithm']['flags']['cleaning_dynamic_data_tmp'])

        # Ending info
        logging.info(' ---> TIME STEP: ' + str(time_run_step) + ' ... DONE')

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
# Method to clean tmp data such as ancillary or global (if domain is set)
def clean_data_tmp(filename_obj_source, filename_obj_ancillary_global, filename_obj_ancillary_domain,
                   flag_cleaning_source=False, flag_cleaning_tmp=False):
    if flag_cleaning_source:
        for data_key, data_value in filename_obj_source.items():
            if not isinstance(data_value, list):
                data_value = list(data_value)
            for data_step in data_value:
                if os.path.exists(data_step):
                    os.remove(data_step)
    if flag_cleaning_tmp:
        for data_key, data_value in filename_obj_ancillary_global.items():
            for data_step in data_value:
                if os.path.exists(data_step):
                    os.remove(data_step)
        for data_key, data_value in filename_obj_ancillary_domain.items():
            for data_step in data_value:
                if os.path.exists(data_step):
                    os.remove(data_step)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to process cmr
def process_cmr(filename_obj_source, fileroot_obj_source,
                filename_obj_ancillary_global, filename_obj_ancillary_domain,
                filename_obj_outcome,
                geo_proj, geo_geotrans, geo_data,
                geo_wide, geo_high, geo_min_x, geo_max_y, geo_max_x, geo_min_y,
                geo_mask_idx, template_vars_data_list):

    filename_n = filename_obj_source.__len__()
    template_vars_data_obj = template_vars_data_list * filename_n

    for (fn_source_time, fp_source), fr_source_list, fp_anc_global_list, fp_anc_domain_list, \
        fp_outcome_list, var_list in zip(
            filename_obj_source.items(), fileroot_obj_source.values(),
            filename_obj_ancillary_global.values(), filename_obj_ancillary_domain.values(),
            filename_obj_outcome.values(), template_vars_data_obj):

        if isinstance(fp_source, list):
            fp_source = fp_source[0]
        ff_source, fn_source = os.path.split(fp_source[0])
        logging.info(' ----> Process file: ' + fn_source + ' ... ')

        for fr_source_step, fp_anc_global_step, fp_anc_domain_step, fp_outcome_step, var_step in zip(
                fr_source_list, fp_anc_global_list, fp_anc_domain_list, fp_outcome_list, var_list):

            # Info
            logging.info(' -----> Process variable: ' + var_step + ' ... ')

            # Create folder(s) for ancillary and outcome file(s)
            ff_anc_global_step, fn_anc_global_step = os.path.split(fp_anc_global_step)
            make_folder(ff_anc_global_step)
            ff_anc_domain_step, fn_anc_domain_step = os.path.split(fp_anc_domain_step)
            make_folder(ff_anc_domain_step)
            ff_outcome_step, fn_outcome_step = os.path.split(fp_outcome_step)
            make_folder(ff_outcome_step)

            # Translate global data from hdf5 to tiff in epsg:6933 modified
            logging.info(' ------> Translating and reproiecting ... ')
            gdal.Translate(fp_anc_global_step, fr_source_step,
                           outputSRS="+proj=cea +lon_0=0 +lat_ts=30 +ellps=WGS84 +units=m",
                           format='GTiff', outputBounds=[-17367530.45, 7314540.76, 17367530.45, -7314540.76],
                           noData=-9999)
            # Reproject from global tiff file in epsg:6933 modified to domain tiff file in epsg:4326
            reproject_file_tiff(fp_anc_global_step, fp_anc_domain_step,
                                geo_wide, geo_high, geo_geotrans, geo_proj)
            logging.info(' ------> Translating and reproiecting ... DONE')

            # Read domain tiff file in epsg:4326
            logging.info(' ------> Masking over domain ... ')
            smap_domain_dset, smap_domain_proj, smap_domain_geotrans, smap_domain_data = read_file_tiff(fp_anc_domain_step)
            # Mask domain tiff file in epsg:4326
            smap_domain_dims = smap_domain_data.shape
            smap_domain_masked_1d = deepcopy(smap_domain_data.ravel())
            smap_domain_masked_1d[geo_mask_idx] = np.nan
            smap_domain_masked_2d = np.reshape(smap_domain_masked_1d, [smap_domain_dims[0], smap_domain_dims[1]])
            logging.info(' ------> Masking over domain ... DONE')

            # Write domain tiff file in epsg:4326
            logging.info(' ------> Saving ' + fp_outcome_step + ' ... ')
            write_file_tiff(fp_outcome_step, smap_domain_masked_2d, geo_wide, geo_high, geo_geotrans, geo_proj)
            logging.info(' ------> Saving ' + fp_outcome_step + ' ... DONE')

            # Info
            logging.info(' -----> Process variable: ' + var_step + ' ... DONE')

        logging.info(' ----> Process file: ' + fn_source + ' ... DONE')

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create data outcome list
def set_data_outcome(time_stamp_list, file_id, variable_obj=None, group_obj=None, file_obj=None,
                       ancillary_obj=None, template_obj=None, flag_cleaning_outcome=False):

    folder_raw = file_obj['folder'][file_id]
    filename_raw = file_obj['filename'][file_id]

    group_list = group_obj[file_id]
    variable_list = variable_obj[file_id]
    domain = ancillary_obj['domain']

    filename_list = {}
    for time_stamp in time_stamp_list:

        var_list = []
        for variable, group in zip(variable_list, group_list):

            time_step = time_stamp.to_pydatetime()
            template_values = {"domain": domain,
                               "var_name": variable,
                               "group_name": group,
                               "outcome_sub_path_time": time_step,
                               "outcome_datetime": time_step}

            folder_step = fill_tags2string(folder_raw, template_obj, template_values)
            filename_step = fill_tags2string(filename_raw, template_obj, template_values)
            path_step = os.path.join(folder_step, filename_step)

            if flag_cleaning_outcome:
                if os.path.exists(path_step):
                    os.remove(path_step)

            var_list.append(path_step)

        filename_list[time_stamp] = var_list

    return filename_list
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create data ancillary list
def set_data_ancillary(time_stamp_list, file_id, variable_obj=None, file_obj=None,
                       ancillary_obj=None, template_obj=None,
                       flag_cleaning_ancillary_global=False, flag_cleaning_ancillary_domain=False):

    folder_global_raw = file_obj['global']['folder'][file_id]
    filename_global_raw = file_obj['global']['filename'][file_id]
    folder_domain_raw = file_obj['domain']['folder'][file_id]
    filename_domain_raw = file_obj['domain']['filename'][file_id]

    variable_list = variable_obj[file_id]
    domain = ancillary_obj['domain']

    filename_global_list = {}
    filename_domain_list = {}
    for time_stamp in time_stamp_list:

        var_global_list = []
        var_domain_list = []
        for variable in variable_list:

            time_step = time_stamp.to_pydatetime()
            template_values = {"domain": domain,
                               "var_name": variable,
                               "ancillary_sub_path_time": time_step,
                               "ancillary_datetime": time_step}

            folder_global_step = fill_tags2string(folder_global_raw, template_obj, template_values)
            filename_global_step = fill_tags2string(filename_global_raw, template_obj, template_values)
            path_global_step = os.path.join(folder_global_step, filename_global_step)

            folder_domain_step = fill_tags2string(folder_domain_raw, template_obj, template_values)
            filename_domain_step = fill_tags2string(filename_domain_raw, template_obj, template_values)
            path_domain_step = os.path.join(folder_domain_step, filename_domain_step)

            if flag_cleaning_ancillary_global:
                if os.path.exists(path_global_step):
                    os.remove(path_global_step)
            if flag_cleaning_ancillary_domain:
                if os.path.exists(path_domain_step):
                    os.remove(path_domain_step)

            var_global_list.append(path_global_step)
            var_domain_list.append(path_domain_step)

        filename_global_list[time_stamp] = var_global_list
        filename_domain_list[time_stamp] = var_domain_list

    return filename_global_list, filename_domain_list
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create data source list
def set_data_source(file_id, filename_url,
                    file_obj=None, variable_obj=None, root_obj=None, ancillary_obj=None, template_obj=None,
                    filename_suffix='.h5', flag_cleaning_source=False):

    if not isinstance(filename_url, list):
        filename_url = [filename_url]

    folder_raw = file_obj['folder'][file_id]
    filename_raw = file_obj['filename'][file_id]
    domain = ancillary_obj['domain']

    variable_list = variable_obj[file_id]
    fileroot_raw = root_obj[file_id]

    time_stamp_list = []
    filename_list_url = []
    filename_obj_source = {}
    fileroot_obj_source = {}
    for filename_url_step in filename_url:

        if filename_url_step.endswith(filename_suffix):

            match_time = re.search(r'\d{4}\d{2}\d{2}\w\d{2}\d{2}\d{2}', filename_url_step)
            time_str = match_time.group()
            time_stamp = pd.Timestamp(time_str)

            time_step = time_stamp.to_pydatetime()
            template_values = {"domain": domain,
                               "source_sub_path_time": time_step,
                               "source_datetime": time_step}

            folder_step = fill_tags2string(folder_raw, template_obj, template_values)
            filename_step = fill_tags2string(filename_raw, template_obj, template_values)

            path_step = os.path.join(folder_step, filename_step)

            if flag_cleaning_source:
                if os.path.exists(path_step):
                    os.remove(path_step)

            time_stamp_list.append(time_stamp)
            filename_list_url.append(filename_url_step)

            if time_step not in list(filename_obj_source.keys()):
                filename_obj_source[time_step] = [path_step]
            else:
                logging.error(' ===> Time is always set in source obj')
                raise NotImplementedError('Merge filename(s) is not implemented yet')

            var_fileroot_list = []
            for variable in variable_list:
                template_values = {"domain": domain,
                                   "file_name": path_step,
                                   "var_name": variable,
                                   "source_sub_path_time": time_step,
                                   "source_datetime": time_step}

                fileroot_step = fill_tags2string(fileroot_raw, template_obj, template_values)
                var_fileroot_list.append(fileroot_step)
            fileroot_obj_source[time_stamp] = var_fileroot_list

    return time_stamp_list, filename_list_url, filename_obj_source, fileroot_obj_source

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

        # string_filled = string_filled.replace('//', '/')
        return string_filled
    else:
        return string_raw

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to collect product info
def collect_product_info(info_product=None, info_bbox=None, info_url=None):

    pr_short_name = info_product['short_name']
    pr_version = info_product['version']
    pr_template_root = info_product['template_root']
    pr_template_vars_data = info_product['template_vars_data']
    pr_template_group_data = info_product['template_group_data']

    pr_bbox_lon_right = info_bbox['lon_right']
    pr_bbox_lon_left = info_bbox['lon_left']
    pr_bbox_lat_top = info_bbox['lat_top']
    pr_bbox_lat_bottom = info_bbox['lat_bottom']

    pr_cmr_url = info_url['cmr_url']
    pr_urs_url = info_url['urs_url']
    pr_cmr_page_size = info_url['cmr_page_size']
    pr_url_list = info_url['url_list']
    pr_cmr_file_url = info_url['cmr_file_url']
    pr_polygon = info_url['polygon']
    pr_filename_filter = info_url['filename_filter']

    # bounding_box [min_lon min_lat max_lon max_lat]
    pr_bbox_tmp = [str(pr_bbox_lon_right), str(pr_bbox_lat_bottom), str(pr_bbox_lon_left), str(pr_bbox_lat_top)]
    pr_bbox_ref = ','.join(pr_bbox_tmp)

    return pr_short_name, pr_version, pr_template_root, pr_template_vars_data, pr_template_group_data, \
        pr_bbox_ref, \
        pr_cmr_url, pr_urs_url, pr_cmr_page_size, pr_url_list, pr_cmr_file_url, pr_polygon, pr_filename_filter

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to keep the working directory
@contextmanager
def working_directory(directory):
    owd = os.getcwd()
    try:
        os.chdir(directory)
        yield directory
    finally:
        os.chdir(owd)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define data time range
def set_data_time(time_step, time_settings):
    time_period_obs = time_settings['time_observed_period']
    time_period_for = time_settings['time_forecast_period']
    time_freq_obs = time_settings['time_observed_frequency']
    time_freq_for = time_settings['time_forecast_frequency']
    time_format = time_settings['time_format']

    time_step_obs = time_step

    if time_step.hour > 0:
        time_step_to = time_step_obs
        time_step_from = time_step.floor('D')
        time_range_obs = pd.date_range(start=time_step_from, end=time_step_to, freq=time_freq_obs)
    else:
        time_range_obs = pd.date_range(end=time_step_obs, periods=time_period_obs, freq=time_freq_obs)

    time_step_for = pd.date_range([time_step][0], periods=2, freq=time_freq_for)[-1]
    time_range_for = pd.date_range(start=time_step_for, periods=time_period_for, freq=time_freq_for)

    time_range_data = time_range_obs.union(time_range_for)

    time_range_start = time_range_data[0].strftime(time_format)
    time_range_end = time_range_data[-1].strftime(time_format)

    return time_range_data, time_range_start, time_range_end

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define run time range
def set_run_time(time_alg, time_settings, time_ascending=False):
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
    time_day_round = time_now_raw.floor('D')

    if time_now_round > time_day_round:
        time_last = pd.DatetimeIndex([time_now_round])
    else:
        time_last = None

    if time_period > 0:
        time_range = pd.date_range(end=time_day_round, periods=time_period, freq=time_freq)
    else:
        logging.warning(' ===> TimePeriod must be greater then 0. TimePeriod is set automatically to 1')
        time_range = pd.DatetimeIndex([time_day_round], freq=time_freq)

    if time_last is not None:
        time_period = time_range.union(time_last)
    else:
        time_period = time_range

    time_period = time_period.sort_values(ascending=time_ascending)

    return time_now_round, time_period
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to make folder
def make_folder(path_folder):
    if not os.path.exists(path_folder):
        os.makedirs(path_folder)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read tiff file
def reproject_file_tiff(file_name_in, file_name_out,
                        file_wide_out, file_high_out, file_geotrans_out, file_proj_out):
    dset_tiff_out = gdal.GetDriverByName('GTiff').Create(
        file_name_out, file_wide_out, file_high_out, 1, gdalconst.GDT_Float32)
    dset_tiff_out.SetGeoTransform(file_geotrans_out)
    dset_tiff_out.SetProjection(file_proj_out)

    dset_tiff_in = gdal.Open(file_name_in, gdalconst.GA_ReadOnly)
    dset_proj_in = dset_tiff_in.GetProjection()
    dset_geotrans_in = dset_tiff_in.GetGeoTransform()
    dset_data_in = dset_tiff_in.ReadAsArray()
    dset_band_in = dset_tiff_in.GetRasterBand(1)

    # Reproject from input file to output file set with out information
    gdal.ReprojectImage(dset_tiff_in, dset_tiff_out, dset_proj_in, file_proj_out,
                        gdalconst.GRA_NearestNeighbour)
    return dset_tiff_out
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write file tiff
def write_file_tiff(file_name, file_data, file_wide, file_high, file_geotrans, file_proj):
    smap_dset_mask = gdal.GetDriverByName('GTiff').Create(file_name, file_wide, file_high, 1,
                                                          gdalconst.GDT_Float32)
    smap_dset_mask.SetGeoTransform(file_geotrans)
    smap_dset_mask.SetProjection(file_proj)
    smap_dset_mask.GetRasterBand(1).WriteArray(file_data)
    del smap_dset_mask
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read tiff file
def read_file_tiff(file_name_tiff):
    if os.path.exists(file_name_tiff):
        dset_tiff = gdal.Open(file_name_tiff, gdalconst.GA_ReadOnly)
        dset_proj = dset_tiff.GetProjection()
        dset_geotrans = dset_tiff.GetGeoTransform()
        dset_data = dset_tiff.ReadAsArray()
        dset_band = dset_tiff.GetRasterBand(1)
    else:
        logging.error(' ===> Tiff file ' + file_name_tiff + ' not found')
        raise IOError('Tiff file location or name is wrong')

    return dset_tiff, dset_proj, dset_geotrans, dset_data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read geographical file
def read_file_geo(file_name_geo):

    if os.path.exists(file_name_geo):
        if file_name_geo.endswith('tif') or file_name_geo.endswith('.tiff'):
            dset_geo = gdal.Open(file_name_geo, gdalconst.GA_ReadOnly)
            geo_proj = dset_geo.GetProjection()
            geo_geotrans = dset_geo.GetGeoTransform()
            geo_data = dset_geo.ReadAsArray()
            geo_band = dset_geo.GetRasterBand(1)
            geo_wide = dset_geo.RasterXSize
            geo_high = dset_geo.RasterYSize
            geo_min_x = geo_geotrans[0]
            geo_max_y = geo_geotrans[3]
            geo_max_x = geo_min_x + geo_geotrans[1] * dset_geo.RasterXSize
            geo_min_y = geo_max_y + geo_geotrans[5] * dset_geo.RasterYSize
            geo_mask_grid = np.where(geo_data != 255, 1, 0)
            geo_mask_idx = np.where(geo_mask_grid.ravel() == 0)
        else:
            logging.error(' ===> Geographical file ' + file_name_geo + ' format unknown')
            raise NotImplementedError('File type reader not implemented yet')
    else:
        logging.error(' ===> Geographical file ' + file_name_geo + ' not found')
        raise IOError('Geographical file location or name is wrong')

    return geo_proj, geo_geotrans, geo_data, \
           geo_wide, geo_high, geo_min_x, geo_max_y, geo_max_x, geo_min_y, geo_mask_idx
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
if __name__ == '__main__':
    main()
# ----------------------------------------------------------------------------
