"""
Library Features:

Name:          lib_ef_generic
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20201202'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging
import os
import re

import numpy as np

from shutil import rmtree
from random import randint
from copy import deepcopy
from datetime import datetime
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to search root path
def get_root_path(generic_path):

    string_patterns = re.findall(r"\{([A-Za-z0-9_]+)\}", generic_path)

    dict_patterns = {}
    for string_pattern in string_patterns:
        dict_patterns[string_pattern] = ''

    root_path = generic_path.format(**dict_patterns)

    return root_path
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to list sub-folders
def list_folder(main_path, reverse=True):
    path_generator = os.walk(main_path)

    path_list = []
    for path_obj in path_generator:
        path_string = path_obj[0]
        path_list.append(path_string)

    if reverse:
        path_list.reverse()

    return path_list
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create a random string
def random_string(string_root='temporary', string_separetor='_', rand_min=0, rand_max=1000):

    # Rand number
    rand_n = str(randint(rand_min, rand_max))
    # Rand time
    rand_time = datetime.now().strftime('%Y%m%d-%H%M%S_%f')
    # Rand string
    rand_string = string_separetor.join([string_root, rand_time, rand_n])

    return rand_string
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to delete folder (and check if folder exists)
def delete_folder(path_folder):
    # Check folder status
    if os.path.exists(path_folder):
        # Remove folder (file only-read too)
        rmtree(path_folder, ignore_errors=True)

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to make folder
def make_folder(path_folder):
    if not os.path.exists(path_folder):
        os.makedirs(path_folder)
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
# Method to get dictionary values using a key
def get_dict_values(d, key, value=[]):

    for k, v in iter(d.items()):

        if isinstance(v, dict):
            if k == key:

                for kk, vv in iter(v.items()):
                    temp = [kk, vv]
                    value.append(temp)

            else:
                vf = get_dict_values(v, key, value)

                if isinstance(vf, list):
                    if vf:
                        vf_end = vf[0]
                    else:
                        vf_end = None

                elif isinstance(vf, np.ndarray):
                    vf_end = vf.tolist()
                else:
                    vf_end = vf

                if vf_end not in value:
                    if vf_end:

                        if isinstance(value, list):
                            value.append(vf_end)
                        elif isinstance(value, str):
                            value = [value, vf_end]

                    else:
                        pass
                else:
                    pass

        else:
            if k == key:

                if isinstance(v, np.ndarray):
                    value = v
                else:
                    value = v
    return value
# -------------------------------------------------------------------------------------
