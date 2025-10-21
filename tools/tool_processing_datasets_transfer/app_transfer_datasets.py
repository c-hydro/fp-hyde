#!/usr/bin/python3

"""
HYDE PROCESSING TOOLS - File Transfer

__date__ = '20241031'
__version__ = '1.4.0'
__author__ = 'Fabio Delogu (fabio.delogu@cimafoundation.org'
__library__ = 'HyDE'

General command line:
python3 app_transfer_datasets.py -settings_file configuration.json -time "YYYY-mm-dd HH:MM"
"""

# -------------------------------------------------------------------------------------
# Libraries
import logging
import time
import argparse
import os
import re
import json
import glob
import subprocess

import dateutil.parser as dparser
import pandas as pd

from datetime import datetime
from copy import deepcopy

# Logging
log_stream = logging.getLogger(__name__)
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
alg_name = 'Datasets Transfer'
alg_type = 'Processing Tool'
alg_version = '1.4.0'
alg_release = '2024-10-31'
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to join file registry
def main():

    # -------------------------------------------------------------------------------------
    # Get and read algorithm settings
    file_configuration, time_run_args = get_args()
    settings_data = read_file_settings(file_configuration)

    # Configure log information
    if 'log' in list(settings_data.keys()):
        folder_name_log, file_name_log = settings_data['log'][tag_folder_name], settings_data['log'][tag_file_name]
        make_folder(folder_name_log)
        set_log(logger_file_name=os.path.join(folder_name_log, file_name_log))
    else:
        set_log()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm
    log_stream.info(' ============================================================================ ')
    log_stream.info('[' + project_name + ' ' + alg_type + ' - ' + alg_name + ' (Version ' + alg_version +
                    ' - Release ' + alg_release + ')]')
    log_stream.info(' ==> START ... ')
    log_stream.info(' ')

    # Time algorithm information
    alg_time_start = time.time()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm start
    log_stream.info(' ---> Transfer datasets from source to destination location(s) ... ')

    # Configure ancillary information
    if 'ancillary' in list(settings_data.keys()):
        ancillary_raw = settings_data['ancillary']
    else:
        ancillary_raw = {'ancillary': {}}
        ancillary_raw['ancillary']['tag_name_list'] = ['datasets']

    # Configure template information
    template_time_raw = settings_data['template_time']
    template_string_raw = settings_data['template_string']

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

    # update time start and time end (based on time bounds left and right)
    time_start, time_end = set_time_bounds(
        time_run_args, time_run_file, time_period, time_frequency=time_frequency, time_rounding=time_rounding)
    # set time period
    time_run, time_range = set_time_period(
        time_run_args=time_run_args, time_run_file=time_run_file,
        time_run_file_start=time_start, time_run_file_end=time_end,
        time_period=time_period, time_frequency=time_frequency, time_rounding=time_rounding)
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Iterate over time period
    for time_step in time_range:

        # -------------------------------------------------------------------------------------
        # Info time start
        log_stream.info(' ----> Time "' + time_step.strftime(format=time_format_algorithm) + '" ... ')

        # Iterate over datasets
        for (dset_key, dset_fields_src), dset_fields_dst in zip(data_src_settings.items(), data_dst_settings.values()):

            # Iterate over name list
            for tag_value in ancillary_raw['tag_name_list']:

                # Fill template for time variable(s)
                template_time_filled = {}
                for time_key, time_format in template_time_raw.items():
                    template_time_filled[time_key] = time_step.strftime(time_format)
                # Fill template for other variable(s)
                template_var_filled = {'tag_name': tag_value}

                # define generic template
                template_generic_filled = {**template_time_filled, **template_var_filled}

                # Filled the structure with
                dset_key_step = fill_object(data_structure_raw=dset_key, data_template=template_generic_filled)
                                                     #tag_name='tag_name', tag_value=tag_value)

                dset_fields_src_step = fill_object(data_structure_raw=dset_fields_src, data_template=template_generic_filled)
                                                    # tag_name='tag_name', tag_value=tag_value)
                dset_fields_dst_step = fill_object(data_structure_raw=dset_fields_dst , data_template=template_generic_filled)
                                                    # tag_name='tag_name', tag_value=tag_value)

                # Get datasets root path
                folder_name_src_root = get_path_root(dset_fields_src)
                folder_name_dst_root = get_path_root(dset_fields_dst)

                # Info dataset start
                log_stream.info(' -----> Dataset "' + dset_key_step + '" ... ')

                # Transfer method
                file_method_src = dset_fields_src_step[tag_method]

                if file_method_src in list(data_src_methods.keys()):
                    method_mode = data_src_methods['mode']
                    method_info = data_src_methods[file_method_src]['settings']
                    method_command_ancillary = data_src_methods[file_method_src]['command_ancillary']
                    method_command_exec = data_src_methods[file_method_src]['command_exec']
                    method_command_line = data_src_methods[file_method_src]['command_line']
                else:
                    log_stream.error(' ===> Method "' + file_method_src + ' is not defined in the settings file.')
                    raise IOError('Check your settings file and insert the method and its fields')

                # File path source
                folder_name_src_tmp = dset_fields_src_step[tag_folder_name]
                file_name_src_tmp = dset_fields_src_step[tag_file_name]
                file_path_src_tmp = os.path.join(folder_name_src_tmp, file_name_src_tmp)
                file_path_src_def = file_path_src_tmp.format(**template_time_filled)

                if '*' in file_path_src_def:
                    if method_mode == 'remote2local':
                        file_list_src_def = [file_path_src_def]
                    else:
                        file_list_src_def = glob.glob(file_path_src_def)
                        file_list_src_def = sorted(file_list_src_def)
                elif '*' not in file_path_src_def:
                    if isinstance(file_path_src_def, str):
                        file_list_src_def = [file_path_src_def]
                    elif isinstance(file_path_src_def, list):
                        file_list_src_def = deepcopy(file_path_src_def)
                    else:
                        log_stream.error(' ===> File format source is not in supported format')
                        raise NotImplementedError('Case not implemented yet')
                else:
                    file_list_src_def = deepcopy(file_path_src_def)

                # Check the list source file(s)
                if file_list_src_def:

                    # File path destination
                    folder_name_dst_tmp = dset_fields_dst_step[tag_folder_name]
                    file_name_dst_tmp = dset_fields_dst_step[tag_file_name]

                    if ('*' in file_name_src_tmp) and ('*' not in file_name_dst_tmp):

                        if method_mode != 'remote2local':
                            log_stream.warning(
                                ' ===> Symbol "*" defined in the source file(s), but not in the destination file(s).')
                            log_stream.warning(' ===> Destination file(s) are defined using only the folder location')
                        else:
                            log_stream.warning(
                                ' ===> Symbol "*" defined in the source file(s), but not in the destination file(s).')
                            log_stream.warning(' ===> Destination file(s) are defined using the name of source file(s)')
                        file_name_dst_tmp = None

                    if (file_name_dst_tmp is not None) and ('*' not in file_name_dst_tmp):

                        file_path_dst_tmp = os.path.join(folder_name_dst_tmp, file_name_dst_tmp)
                        file_path_dst_def = file_path_dst_tmp.format(**template_time_filled)

                    elif (file_name_dst_tmp is None) and ('*' in file_path_src_def):

                        if method_mode == 'remote2local':
                            file_path_dst_def = [folder_name_dst_tmp]
                        else:
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

                            try:
                                time_parsed = dparser.parse(file_name_src_tmp, fuzzy=True)
                                format_parsed = template_time_raw['dset_datetime_dst']
                                time_parsed = time_parsed.strftime(format_parsed)
                            except BaseException as parser_error:
                                log_stream.warning(' ===> Extract time from string failed. "' + str(parser_error) +
                                                   '" Check the string format. Set the time to NoneType')
                                time_parsed = None

                            if time_parsed is None:
                                file_path_dst_tmp = os.path.join(folder_name_dst_tmp, file_name_src_tmp)
                            else:
                                file_name_dst_filled = file_name_dst_tmp.replace('*', time_parsed)
                                file_path_dst_tmp = os.path.join(folder_name_dst_tmp, file_name_dst_filled)

                            file_path_dst_filled = file_path_dst_tmp.format(**template_time_filled)
                            file_path_dst_def.append(file_path_dst_filled)

                    else:
                        log_stream.error(' ===> File destination name is not defined')
                        raise NotImplementedError('Case not implemented yet')

                    if isinstance(file_path_dst_def, str):
                        file_list_dst_def = [file_path_dst_def]
                    elif isinstance(file_path_dst_def, list):
                        file_list_dst_def = deepcopy(file_path_dst_def)
                    else:
                        log_stream.error(' ===> File format source is not in supported format')
                        raise NotImplementedError('Case not implemented yet')

                    # Cycles over source and destination file(s)
                    for file_path_src_step, file_path_dst_step in zip(file_list_src_def, file_list_dst_def):

                        # Define folder and file name(s)
                        folder_name_src_step, file_name_src_step = os.path.split(file_path_src_step); print(file_path_src_step)
                        folder_name_dst_step, file_name_dst_step = os.path.split(file_path_dst_step); print(file_path_dst_step)

                        # Method settings
                        file_info = {
                            'folder_name_src': folder_name_src_step, 'file_name_src': file_name_src_step,
                            'folder_name_dst': folder_name_dst_step, 'file_name_dst': file_name_dst_step,
                            'folder_root_src': folder_name_src_root, 'folder_root_dst': folder_name_dst_root}

                        template_command_line = {**method_info, **file_info}

                        method_cmd_create_folder, method_cmd_uncompress_file = None, None
                        method_cmd_find_file, method_cmd_remove_file = None, None
                        if (method_mode == 'local2local') or (method_mode == 'remote2local'):
                            make_folder(folder_name_dst_step)
                        elif method_mode == 'local2remote':

                            if 'create_folder' in list(method_command_ancillary.keys()):
                                method_cmd_create_folder = method_command_ancillary['create_folder']
                            if method_cmd_create_folder is None:
                                log_stream.warning(' ===> Transfer mode "' + method_mode + ' needs to create remote folder.')
                                log_stream.warning(' ===> Check if the command settings are able to create a remote folder.')
                            else:
                                method_cmd_create_folder = deepcopy(method_cmd_create_folder.format(**template_command_line))

                            if 'uncompress_file' in list(method_command_ancillary.keys()):
                                method_cmd_uncompress_file = method_command_ancillary['uncompress_file']
                            if method_cmd_uncompress_file is None:
                                log_stream.warning(' ===> Transfer mode "' + method_mode + ' will not uncompress file.')
                                log_stream.warning(' ===> Check if the file must be compressed or not.')
                            else:
                                method_cmd_uncompress_file = deepcopy(method_cmd_uncompress_file.format(**template_command_line))

                            if 'find_file' in list(method_command_ancillary.keys()):
                                method_cmd_find_file = method_command_ancillary['find_file']
                            if method_cmd_find_file is None:
                                log_stream.warning(' ===> Transfer mode "' + method_mode + ' will not uncompress file.')
                                log_stream.warning(' ===> Check if the file must be compressed or not.')
                            else:
                                method_cmd_find_file = deepcopy(method_cmd_find_file.format(**template_command_line))

                            if 'remove_file' in list(method_command_ancillary.keys()):
                                method_cmd_remove_file = method_command_ancillary['remove_file']
                            if method_cmd_remove_file is None:
                                log_stream.warning(' ===> Transfer mode "' + method_mode + ' will not uncompress file.')
                                log_stream.warning(' ===> Check if the file must be compressed or not.')
                            else:
                                method_cmd_remove_file = deepcopy(method_cmd_remove_file.format(**template_command_line))

                        else:
                            log_stream.error(' ===> Transfer mode "' + method_mode + '" is unknown')
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
                        log_stream.info(
                            adjust_comment(' ------> Transfer source datasets "' + file_name_src_step +
                                           '" to destination datasets "' + file_name_dst_step + '" ... '))

                        # Check datasets source
                        if (method_mode == 'local2local') or (method_mode == 'local2remote'):
                            if os.path.exists(file_path_src_step):
                                check_dataset_source = True
                            else:
                                check_dataset_source = False
                        elif method_mode == 'remote2local':
                            check_dataset_source = True
                        else:
                            log_stream.error(' ===> Transfer mode "' + method_mode + '" is unknown')
                            raise NotImplementedError('Case not implemented yet')

                        # Condition to transfer datasets
                        if check_dataset_source:

                            # Execute command to create remote folder
                            if method_cmd_create_folder is not None:
                                execute_command(
                                    method_cmd_create_folder, command_prefix=' -------> ',
                                    command_type='Create remote folder')

                            # Execute command to transfer datasets
                            execute_command(
                                method_cmd_transfer, command_prefix=' -------> ',
                                command_type='Transfer source datasets "' +
                                             file_name_src_step + '" to destination datasets "' +
                                             file_name_dst_step + '"')

                            # remove empty path(s)
                            remove_path_empty(file_info['folder_root_dst'], file_info['folder_name_dst'])

                            # Execute command to uncompress datasets
                            if method_cmd_uncompress_file is not None:
                                execute_command(
                                    method_cmd_uncompress_file, command_prefix=' -------> ',
                                    command_type='Extract compressed destination datasets "' + file_name_dst_step + '"')

                            # Execute command to remove datasets
                            if method_cmd_remove_file is not None:

                                command_find_file_code = execute_command(
                                    method_cmd_find_file, command_prefix=' -------> ',
                                    command_type='Find compressed destination datasets "' + file_name_dst_step + '"')

                                if command_find_file_code:
                                    execute_command(
                                        method_cmd_remove_file, command_prefix=' -------> ',
                                        command_type='Remove compressed destination datasets "' + file_name_dst_step + '"')

                            # Transfer datasets from local to remote
                            log_stream.info(
                                adjust_comment(' ------> Transfer source datasets "' + file_name_src_step +
                                               '" to destination datasets "' + file_name_dst_step + '" ... DONE'))

                        else:
                            log_stream.info(
                                adjust_comment(' ------> Transfer source datasets "' + file_name_src_step +
                                            '" to destination datasets "' + file_name_dst_step + '" ... SKIPPED. '
                                            'File source does not exists.'))

                    # Info dataset end (done)
                    log_stream.info(' -----> Dataset "' + dset_key_step + '" ... DONE')

                else:
                    # Info dataset end (skipped)
                    log_stream.info(' -----> Dataset "' + dset_key_step + '" ... SKIPPED. File(s) source not found')

        # Info time end
        log_stream.info(' ----> Time "' + time_step.strftime(format=time_format_algorithm) + '" ... DONE')
        # -------------------------------------------------------------------------------------

    # # Info algorithm end
    log_stream.info(' ---> Transfer datasets from source to destination location(s) ... DONE')
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm
    alg_time_elapsed = round(time.time() - alg_time_start, 1)

    log_stream.info(' ')
    log_stream.info('[' + project_name + ' ' + alg_type + ' - ' + alg_name + ' (Version ' + alg_version +
                    ' - Release ' + alg_release + ')]')
    log_stream.info(' ==> TIME ELAPSED: ' + str(alg_time_elapsed) + ' seconds')
    log_stream.info(' ==> ... END')
    log_stream.info(' ==> Bye, Bye')
    log_stream.info(' ============================================================================ ')
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to execute command line
def execute_command(command_line, command_prefix=' ---> ', command_type='Execute command',
                    command_st_out=subprocess.DEVNULL, command_st_err=subprocess.DEVNULL):

    # Info start
    log_stream.info(command_prefix + adjust_comment(command_type) + ' ... ')

    # call command line
    log_stream.info(command_prefix + 'Execute: "' + command_line + '"')
    command_code = subprocess.call(
        command_line, shell=True,
        stdout=command_st_out, stderr=command_st_err)

    # method_return_code = os.system(method_cmd) # old code
    if command_code == 0:
        log_stream.info(command_prefix + adjust_comment(command_type) + ' ... DONE')
        return True
    else:
        log_stream.warning(' ===> Execution return with non-zero code for the submitted command line.')
        log_stream.info(command_prefix + adjust_comment(command_type) + ' ... SKIPPED. ')
        return False

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to remove path empty
def remove_path_empty(folder_root, folder_name=None):

    folder_walk_generator = os.walk(folder_name) #, topdown=False)
    for folder_name_step, folder_dirs_step, folder_files_step in folder_walk_generator:
        with os.scandir(folder_name_step) as it:
            if any(it):
                pass
            else:
                if folder_name != folder_root:
                    folder_name_up = os.path.dirname(folder_name_step)
                    os.rmdir(folder_name_step)
                    remove_path_empty(folder_root, folder_name_up)
                else:
                    break

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to get path root
def get_path_root(data_structure, folder_tag='folder_name', folder_symbol='{'):

    folder_name, folder_root = None, None
    if folder_tag in list(data_structure.keys()):
        folder_name = data_structure[folder_tag]

    if folder_name is not None:
        if folder_symbol in folder_name:
            folder_root = folder_name.split(folder_symbol)[0]
        else:
            folder_root = deepcopy(folder_name)

    return folder_root
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to fill object
def fill_object(data_structure_raw, data_template=None): #tag_name='tag_name', tag_value='datasets'):

    #tag_dict = {tag_name: tag_value}
    tag_dict = deepcopy(data_template)

    if isinstance(data_structure_raw, str):
        data_structure_filled = deepcopy(data_structure_raw.format(**tag_dict))
    elif isinstance(data_structure_raw, dict):
        data_structure_filled = {}
        for data_key_raw, data_value_raw in data_structure_raw.items():

            if data_key_raw is not None:
                data_key_brackets = re.sub(r'[^(){}[\]]', '', data_key_raw)
                if data_key_brackets:
                    data_key_filled = data_key_raw.format(**tag_dict)
                else:
                    data_key_filled = deepcopy(data_key_raw)
            else:
                log_stream.error(' ===> Object key is defined by NoneType')
                raise RuntimeError('Key must be defined by a defined string')

            if data_value_raw is not None:
                data_value_brackets = re.sub(r'[^(){}[\]]', '', data_value_raw)
                if data_value_brackets:
                    data_value_filled = data_value_raw.format(**tag_dict)
                else:
                    data_value_filled = deepcopy(data_value_raw)
            else:
                data_value_raw = None
            data_structure_filled[data_key_filled] = data_value_filled
    else:
        log_stream.error(' ===> Object is not supported by the filling method')
        raise NotImplementedError('Case not implemented yet')

    return data_structure_filled
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
# Method to adjust string comment
def adjust_comment(string_comment):
    string_comment = string_comment.replace('""','')
    string_comment = re.sub("\s\s+", " ", string_comment)
    return string_comment
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set log file
def set_log(logger_name='hyde_tools_transfer_datasets', logger_file_name="hyde_tools_transfer_datasets.log",
            logger_formatter='%(asctime)s %(name)-12s ' +
                             '%(levelname)-8s %(message)-80s %(filename)s:[%(lineno)-6s - %(funcName)-20s()] '):

    # Open logger
    logging.getLogger(logger_name)
    logging.root.setLevel(logging.DEBUG)

    # Log handler(s)
    logger_handle_1 = logging.FileHandler(logger_file_name, 'w')
    logger_handle_2 = logging.StreamHandler()

    # Set logger level
    logger_handle_1.setLevel(logging.DEBUG)
    logger_handle_2.setLevel(logging.DEBUG)
    # Set logger formatter
    logger_handle_1.setFormatter(logging.Formatter(logger_formatter))
    logger_handle_2.setFormatter(logging.Formatter(logger_formatter))

    # Add handler(s) to logging module
    logging.getLogger('').addHandler(logger_handle_1)
    logging.getLogger('').addHandler(logger_handle_2)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# method to define period based on left and right bounds
def set_time_bounds(time_run_args, time_run_file, time_period,
                    time_format='%Y-%m-%d %H:%M', time_rounding='H', time_frequency='H'):

    log_stream.info(' ----> Set time bounds ... ')

    if time_run_args is not None:
        time_run = time_run_args
        log_stream.info(' ------> Time ' + time_run + ' set by argument')
    elif (time_run_args is None) and (time_run_file is not None):
        time_run = time_run_file
        log_stream.info(' ------> Time ' + time_run + ' set by user')
    elif (time_run_args is None) and (time_run_file is None):
        time_now = datetime.now()
        time_run = time_now.strftime(time_format)
        log_stream.info(' ------> Time ' + time_run + ' set by system')
    else:
        log_stream.info(' ----> Set time period ... FAILED')
        log_stream.error(' ===> Argument "time_run" is not correctly set')
        raise IOError('Time type or format is wrong')

    time_run = pd.Timestamp(time_run)
    time_run = time_run.floor(time_rounding)

    time_start, time_end = None, None
    if isinstance(time_period, (int, float)):
        pass
    elif isinstance(time_period, dict):

        # get time period bounds
        time_period_left = time_period['left']
        time_period_right = time_period['right']

        # set time start
        time_start = pd.date_range(end=time_run, periods=time_period_left, freq=time_frequency)[0]

        # set time end
        time_tmp = pd.date_range(start=time_run, periods=2, freq=time_frequency)[-1]
        time_end = pd.date_range(start=time_tmp, periods=time_period_right, freq=time_frequency)[-1]

    else:
        log_stream.error(' ===> Argument "time_period" format is not expected')
        raise NotImplemented('Case not implemented yet')

    log_stream.info(' ----> Set time bounds ... DONE')

    return time_start, time_end
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set time run
def set_time_period(time_run_args=None, time_run_file=None, time_format='%Y-%m-%d %H:%M',
             time_run_file_start=None, time_run_file_end=None,
             time_period=1, time_frequency='H', time_rounding='H', time_reverse=True):

    log_stream.info(' ----> Set time period ... ')
    if (time_run_file_start is None) and (time_run_file_end is None):

        log_stream.info(' -----> Time info defined by "time_run" argument ... ')

        if time_run_args is not None:
            time_run = time_run_args
        elif (time_run_args is None) and (time_run_file is not None):
            time_run = time_run_file
        elif (time_run_args is None) and (time_run_file is None):
            time_now = datetime.now()
            time_run = time_now.strftime(time_format)
        else:
            log_stream.error(' ===> Argument "time_run" is not correctly set')
            raise IOError('Time type or format is wrong')

        time_tmp = pd.Timestamp(time_run)
        time_run = time_tmp.floor(time_rounding)

        if time_period > 0:
            time_range = pd.date_range(end=time_run, periods=time_period, freq=time_frequency)
        else:
            log_stream.warning(' ===> TimePeriod must be greater then 0. TimePeriod is set automatically to 1')
            time_range = pd.DatetimeIndex([time_run], freq=time_frequency)

        log_stream.info(' -----> Time info defined by "time_run" argument ... DONE')

    elif (time_run_file_start is not None) and (time_run_file_end is not None):

        log_stream.info(' -----> Time info defined by "time_start" and "time_end" arguments ... ')

        time_run_file_start = pd.Timestamp(time_run_file_start)
        time_run_file_start = time_run_file_start.floor(time_rounding)
        time_run_file_end = pd.Timestamp(time_run_file_end)
        time_run_file_end = time_run_file_end.floor(time_rounding)

        time_now = pd.Timestamp.now()
        time_run = time_now.strftime(time_format)
        time_run = pd.Timestamp(time_run)
        time_run = time_run.floor(time_rounding)
        time_range = pd.date_range(start=time_run_file_start, end=time_run_file_end, freq=time_frequency)

        log_stream.info(' -----> Time info defined by "time_start" and "time_end" arguments ... DONE')

    else:
        log_stream.info(' ----> Set time period ... FAILED')
        log_stream.error(' ===> Arguments "time_start" and/or "time_end" is/are not correctly set')
        raise IOError('Time type or format is wrong')

    if time_reverse:
        time_range = time_range[::-1]

    log_stream.info(' ----> Set time period ... DONE')

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
