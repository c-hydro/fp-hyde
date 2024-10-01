"""
Library Features:

Name:          lib_ecmwf_generic
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20200210'
Version:       '1.0.0'
"""
#################################################################################
# Library
import logging
from datetime import datetime
from src.hyde.algorithm.settings.nwp.ecmwf.lib_ecmwf_args import logger_name

# Logging
log_stream = logging.getLogger(logger_name)
#################################################################################


# -------------------------------------------------------------------------------------
#  Method to reduce dictionary in a flat dictionary
def flat_dictionary(variable_info):
    var_info_redux = {}
    var_info_keys = {}
    for var_key, var_info in variable_info.items():
        var_info_redux[var_key] = {}
        for info_key, info_data in var_info.items():

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

        for tag_key, tag_value in tags_format.items():
            tag_key = '{' + tag_key + '}'
            if tag_value is not None:
                string_filled = string_raw.replace(tag_key, tag_value)
                string_raw = string_filled

        for tag_format_name, tag_format_value in list(tags_format.items()):

            if tag_format_name in list(tags_filling.keys()):
                tag_filling_value = tags_filling[tag_format_name]
                if tag_filling_value is not None:

                    if isinstance(tag_filling_value, datetime):
                        tag_filling_value = tag_filling_value.strftime(tag_format_value)

                    string_filled = string_filled.replace(tag_format_value, tag_filling_value)

        string_filled = string_filled.replace('//', '/')
        return string_filled
    else:
        return string_raw
# -------------------------------------------------------------------------------------
