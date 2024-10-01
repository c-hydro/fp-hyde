"""
Library Features:

Name:          lib_gfs_generic
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20200310'
Version:       '1.0.1'
"""
#################################################################################
# Library
import logging

from copy import deepcopy
from datetime import datetime

from src.hyde.algorithm.settings.nwp.gfs.lib_gfs_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
#################################################################################


# -------------------------------------------------------------------------------------
#  Method to reduce dictionary in a flat dictionary
def flat_dictionary(variable_info, comment_key='_comment'):
    var_info_redux = {}
    var_info_keys = {}
    for var_key, var_info in variable_info.items():
        var_info_redux[var_key] = {}
        for info_key, info_data in var_info.items():

            if not info_key == comment_key:
                info_keys = list(info_data.keys())
                if info_key not in var_info_keys:
                    var_info_keys[info_key] = info_keys
                else:
                    tmp_keys = var_info_keys[info_key]
                    set_tmp = set(tmp_keys)
                    set_info = set(info_keys)
                    list_intersection = list(set_tmp.intersection(set_info))
                    var_info_keys[info_key] = list_intersection

                for data_key, data_attr in info_data.items():
                    var_info_redux[var_key][data_key] = data_attr
    return var_info_redux, var_info_keys
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
