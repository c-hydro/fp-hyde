#!/usr/bin/python3

"""
HYDE PROCESSING TOOLS - File Transfer

__date__ = '20211215'
__version__ = '1.1.0'
__author__ = 'Fabio Delogu (fabio.delogu@cimafoundation.org'
__library__ = 'HyDE'

General command line:
python3 hyde_tools_transfer_datasets.py -settings_file configuration.json -time "YYYY-mm-dd HH:MM"
"""

# -------------------------------------------------------------------------------------
# Libraries
import logging
import time
import argparse
import os
import json
import glob
import subprocess

import pandas as pd

from copy import deepcopy

logger = logging.getLogger(__name__)
logger_format = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logger.setLevel(logging.DEBUG)

logging.basicConfig(
    level=logging.INFO,
    format=logger_format,
    handlers=[logging.FileHandler("hyde_tools_transfer_datasets.log"), logging.StreamHandler()]
)
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Script settings
tag_folder_name = 'folder_name'
tag_file_name = 'file_name'
tag_method = 'method'

time_format_algorithm = '%y-%m-%d %H:%M'
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Algorithm information
project_name = 'HyDE'
alg_name = 'File Transfer'
alg_type = 'Processing Tool'
alg_version = '1.1.0'
alg_release = '2021-12-15'
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to join file registry
def main():

    # -------------------------------------------------------------------------------------
    # Get and read algorithm settings
    file_configuration, time_run_args = get_args()
    settings_data = read_file_settings(file_configuration)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm
    logging.info(' ============================================================================ ')
    logging.info('[' + project_name + ' ' + alg_type + ' - ' + alg_name + ' (Version ' + alg_version +
                 ' - Release ' + alg_release + ')]')
    logging.info(' ==> START ... ')
    logging.info(' ')

    # Time algorithm information
    alg_time_start = time.time()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm start
    logging.info(' ---> Transfer file(s) by source to destination location(s) ... ')

    # Configure template information
    template_time_raw = settings_data['template']

    # Configure datasets information
    data_src_settings = settings_data['source']
    data_dst_settings = settings_data['destination']

    # Configure method(s)
    data_src_methods = settings_data['method']

    # Configure time information
    time_run_file = settings_data['time']['time_run']
    time_start = settings_data['time']['time_start']
    time_end = settings_data['time']['time_end']
    time_period = settings_data['time']['time_period']
    time_frequency = settings_data['time']['time_frequency']
    time_rounding = settings_data['time']['time_rounding']

    time_run, time_range = set_time(
        time_run_args=time_run_args, time_run_file=time_run_file,
        time_run_file_start=time_start, time_run_file_end=time_end,
        time_period=time_period, time_frequency=time_frequency, time_rounding=time_rounding)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Iterate over time period
    for time_step in time_range:

        # -------------------------------------------------------------------------------------
        # Info time start
        logging.info(' ----> Time "' + time_step.strftime(format=time_format_algorithm) + '" ... ')

        # Iterate over datasets
        for (dset_key, dset_fields_src), dset_fields_dst in zip(data_src_settings.items(), data_dst_settings.values()):

            # Info dataset start
            logging.info(' -----> Dataset "' + dset_key + '" ... ')

            template_time_filled = {}
            for time_key, time_format in template_time_raw.items():
                template_time_filled[time_key] = time_step.strftime(time_format)

            # Transfer method
            file_method_src = dset_fields_src[tag_method]

            if file_method_src in list(data_src_methods.keys()):
                method_mode = data_src_methods['mode']
                method_info = data_src_methods[file_method_src]['settings']
                method_command_ancillary = data_src_methods[file_method_src]['command_ancillary']
                method_command_exec = data_src_methods[file_method_src]['command_exec']
                method_command_line = data_src_methods[file_method_src]['command_line']
            else:
                logging.error(' ===> Method "' + file_method_src + ' is not defined in the settings file.')
                raise IOError('Check your settings file and insert the method and its fields')

            # File path source
            folder_name_src_tmp = dset_fields_src[tag_folder_name]
            file_name_src_tmp = dset_fields_src[tag_file_name]
            file_path_src_tmp = os.path.join(folder_name_src_tmp, file_name_src_tmp)
            file_path_src_def = file_path_src_tmp.format(**template_time_filled)

            if '*' in file_path_src_def:
                file_list_src_def = glob.glob(file_path_src_def)
            elif '*' not in file_path_src_def:
                if isinstance(file_path_src_def, str):
                    file_list_src_def = [file_path_src_def]
                elif isinstance(file_path_src_def, list):
                    file_list_src_def = deepcopy(file_path_src_def)
                else:
                    logging.error(' ===> File format source is not in supported format')
                    raise NotImplementedError('Case not implemented yet')
            else:
                file_list_src_def = deepcopy(file_path_src_def)

            # Check the list source file(s)
            if file_list_src_def:

                # File path destination
                folder_name_dst_tmp = dset_fields_dst[tag_folder_name]
                file_name_dst_tmp = dset_fields_dst[tag_file_name]

                if ('*' in file_name_src_tmp) and ('*' not in file_name_dst_tmp):
                    logging.warning(
                        ' ===> Symbol "*" defined in the source file(s), but not in the destination file(s).')
                    logging.warning(' ===> Destination file(s) are defined using the name of source file(s)')
                    file_name_dst_tmp = None

                if (file_name_dst_tmp is not None) and ('*' not in file_name_dst_tmp):

                    file_path_dst_tmp = os.path.join(folder_name_dst_tmp, file_name_dst_tmp)
                    file_path_dst_def = file_path_dst_tmp.format(**template_time_filled)

                elif (file_name_dst_tmp is None) and ('*' in file_path_src_def):

                    file_path_dst_def = []
                    for file_path_src_tmp in file_list_src_def:
                        folder_name_src_tmp, file_name_src_tmp = os.path.split(file_path_src_tmp)
                        file_path_dst_tmp = os.path.join(folder_name_dst_tmp, file_name_src_tmp)
                        file_path_dst_filled = file_path_dst_tmp.format(**template_time_filled)
                        file_path_dst_def.append(file_path_dst_filled)

                elif (file_name_dst_tmp is not None) and ('*' in file_name_dst_tmp):
                    file_path_dst_def = []
                    for file_path_src_tmp in file_list_src_def:
                        folder_name_src_tmp, file_name_src_tmp = os.path.split(file_path_src_tmp)
                        file_path_dst_tmp = os.path.join(folder_name_dst_tmp, file_name_src_tmp)
                        file_path_dst_filled = file_path_dst_tmp.format(**template_time_filled)
                        file_path_dst_def.append(file_path_dst_filled)

                else:
                    logging.error(' ===> File destination name is not defined')
                    raise NotImplementedError('Case not implemented yet')

                if isinstance(file_path_dst_def, str):
                    file_list_dst_def = [file_path_dst_def]
                elif isinstance(file_path_dst_def, list):
                    file_list_dst_def = deepcopy(file_path_dst_def)
                else:
                    logging.error(' ===> File format source is not in supported format')
                    raise NotImplementedError('Case not implemented yet')

                # Cycles over source and destination file(s)
                for file_path_src_step, file_path_dst_step in zip(file_list_src_def, file_list_dst_def):

                    # Define folder and file name(s)
                    folder_name_src_step, file_name_src_step = os.path.split(file_path_src_step)
                    folder_name_dst_step, file_name_dst_step = os.path.split(file_path_dst_step)

                    # Method settings
                    file_info = {
                        'folder_name_src': folder_name_src_step, 'file_name_src': file_name_src_step,
                        'folder_name_dst': folder_name_dst_step, 'file_name_dst': file_name_dst_step}

                    template_command_line = {**method_info, **file_info}

                    method_cmd_create_folder = None
                    if (method_mode == 'local2local') or (method_mode == 'remote2local'):
                        make_folder(folder_name_dst_step)
                    elif method_mode == 'local2remote':

                        method_cmd_create_folder = None
                        if 'create_folder' in list(method_command_ancillary.keys()):
                            method_cmd_create_folder = method_command_ancillary['create_folder']
                        if method_cmd_create_folder is None:
                            logging.warning(' ===> Transfer mode "' + method_mode + ' needs to create remote folder.')
                            logging.warning(' ===> Check if the command settings are able to create a remote folder.')
                        else:
                            method_cmd_create_folder = deepcopy(method_cmd_create_folder.format(**template_command_line))

                    else:
                        logging.error(' ===> Transfer mode "' + method_mode + '" is unknown')
                        raise NotImplementedError('Case not implemented yet')

                    method_cmd_transfer_exec = deepcopy(method_command_exec.format(**template_command_line))
                    method_cmd_transfer_command = method_command_line.format(**template_command_line)

                    if file_method_src == 'ftp':
                        method_cmd_transfer = method_cmd_transfer_exec + ' "' + method_cmd_transfer_command + '"'
                    elif file_method_src == 'rsync':
                        method_cmd_transfer = method_cmd_transfer_exec + ' ' + method_cmd_transfer_command
                    else:
                        method_cmd_transfer = method_cmd_transfer_exec + ' ' + method_cmd_transfer_command

                    # Transfer file from local to remote
                    logging.info(' ------> Transfer source file "' + file_name_src_step + '" to destination file "' +
                                 file_name_dst_step + '" ... ')

                    if os.path.exists(file_path_src_step):

                        if method_cmd_create_folder is not None:
                            execute_command(method_cmd_create_folder,
                                            command_type='Create remote folder')

                        execute_command(method_cmd_transfer,
                                        command_type='Transfer source file "' +
                                                     file_name_src_step + '" to destination file "' +
                                                     file_name_dst_step)

                    else:
                        logging.info(' ------> Transfer source file "' + file_name_src_step + '" to destination file "' +
                                     file_name_dst_step + '" ... SKIPPED. File source does not exists. ')

                # Info dataset end (done)
                logging.info(' -----> Dataset "' + dset_key + '" ... DONE')

            else:
                # Info dataset end (skipped)
                logging.info(' -----> Dataset "' + dset_key + '" ... SKIPPED. File(s) source not found')

        # Info time end
        logging.info(' ----> Time "' + time_step.strftime(format=time_format_algorithm) + '" ... DONE')
        # -------------------------------------------------------------------------------------

    # # Info algorithm end
    logging.info(' ---> Transfer file from source to destination location(s) ... DONE')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm
    alg_time_elapsed = round(time.time() - alg_time_start, 1)

    logging.info(' ')
    logging.info('[' + project_name + ' ' + alg_type + ' - ' + alg_name + ' (Version ' + alg_version +
                 ' - Release ' + alg_release + ')]')
    logging.info(' ==> TIME ELAPSED: ' + str(alg_time_elapsed) + ' seconds')
    logging.info(' ==> ... END')
    logging.info(' ==> Bye, Bye')
    logging.info(' ============================================================================ ')
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to execute command line
def execute_command(command_line, command_type='Execute command'):

    # Info start
    logging.info(' ---> ' + command_type + ' ... ')

    # call command line
    command_code = subprocess.call(
        command_line, shell=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # method_return_code = os.system(method_cmd) # old code
    if command_code == 0:
        logging.info(' ---> ' + command_type + ' ... DONE')
    else:
        logging.warning(' ===> Execution ended with fails in submitted command line.')
        logging.info(' ---> ' + command_type + ' ... FAILED. Error occurred in the command line execution')

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to make folder
def make_folder(path_folder):
    if not os.path.exists(path_folder):
        os.makedirs(path_folder)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read file settings
def read_file_settings(file_name):
    with open(file_name) as file_handle:
        file_data = json.load(file_handle)
    return file_data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set time run
def set_time(time_run_args=None, time_run_file=None, time_format='%Y-%m-%d %H:$M',
             time_run_file_start=None, time_run_file_end=None,
             time_period=1, time_frequency='H', time_rounding='H', time_reverse=True):

    logging.info(' ----> Set time period ... ')
    if (time_run_file_start is None) and (time_run_file_end is None):

        logging.info(' -----> Time info defined by "time_run" argument ... ')

        if time_run_args is not None:
            time_run = time_run_args
            logging.info(' ------> Time ' + time_run + ' set by argument')
        elif (time_run_args is None) and (time_run_file is not None):
            time_run = time_run_file
            logging.info(' ------> Time ' + time_run + ' set by user')
        elif (time_run_args is None) and (time_run_file is None):
            time_now = date.today()
            time_run = time_now.strftime(time_format)
            logging.info(' ------> Time ' + time_run + ' set by system')
        else:
            logging.info(' ----> Set time period ... FAILED')
            logging.error(' ===> Argument "time_run" is not correctly set')
            raise IOError('Time type or format is wrong')

        time_tmp = pd.Timestamp(time_run)
        time_run = time_tmp.floor(time_rounding)

        if time_period > 0:
            time_range = pd.date_range(end=time_run, periods=time_period, freq=time_frequency)
        else:
            log_stream.warning(' ===> TimePeriod must be greater then 0. TimePeriod is set automatically to 1')
            time_range = pd.DatetimeIndex([time_now], freq=time_frequency)

        logging.info(' -----> Time info defined by "time_run" argument ... DONE')

    elif (time_run_file_start is not None) and (time_run_file_end is not None):

        logging.info(' -----> Time info defined by "time_start" and "time_end" arguments ... ')

        time_run_file_start = pd.Timestamp(time_run_file_start)
        time_run_file_start = time_run_file_start.floor(time_rounding)
        time_run_file_end = pd.Timestamp(time_run_file_end)
        time_run_file_end = time_run_file_end.floor(time_rounding)

        time_now = date.today()
        time_run = time_now.strftime(time_format)
        time_run = pd.Timestamp(time_run)
        time_run = time_run.floor(time_rounding)
        time_range = pd.date_range(start=time_run_file_start, end=time_run_file_end, freq=time_frequency)

        logging.info(' -----> Time info defined by "time_start" and "time_end" arguments ... DONE')

    else:
        logging.info(' ----> Set time period ... FAILED')
        logging.error(' ===> Arguments "time_start" and/or "time_end" is/are not correctly set')
        raise IOError('Time type or format is wrong')

    if time_reverse:
        time_range = time_range[::-1]

    logging.info(' ----> Set time period ... DONE')

    return time_run, time_range

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get script argument(s)
def get_args():
    parser_handle = argparse.ArgumentParser()
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
# Call script from external library
if __name__ == "__main__":
    main()
# -------------------------------------------------------------------------------------
