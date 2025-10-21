"""
Library Features:

Name:          lib_utils_obj
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20231010'
Version:       '1.0.0'
"""


# ----------------------------------------------------------------------------------------------------------------------
# libraries
import logging
import unicodedata
import re
from copy import deepcopy

from lib_info_args import logger_name

# logging
log_stream = logging.getLogger(logger_name)
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to sanitize string
def sanitize_string(string_name):

    string_name = string_name.lower()
    string_name = re.sub(r"['.,-]", "", string_name)
    string_name = string_name.replace(' ', '')
    string_name = unicodedata.normalize('NFD', string_name).encode('ascii', 'ignore')
    string_name = string_name.decode("utf-8")

    return string_name
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to map variable(s) in a dataframe object
def map_vars_dframe(var_dframe_in, var_map=None, inverse_map=False):

    if var_map is not None:
        if inverse_map:
            var_map_def = {v: k for k, v in var_map.items()}
        else:
            var_map_def = deepcopy(var_map)
    else:
        var_map_def = None

    if var_map_def is not None:
        var_rename, var_name_excluded = {}, None
        for var_name_out, var_name_in in var_map_def.items():
            var_list_in = list(var_dframe_in.columns)
            if var_name_in not in var_list_in:
                if var_name_excluded is None:
                    var_name_excluded = []
                var_name_excluded.append(var_name_out)
                log_stream.warning(' ===> Variable "' + var_name_in +
                                   '" not included in the dataframe obj. It could be included by default values or'
                                   'excluded due to not implemented case')
            else:
                var_rename[var_name_in] = var_name_out

        if var_name_excluded is not None:
            for var_name_tmp in var_name_excluded:
                if var_name_tmp in list(var_map.keys()):
                    var_map.pop(var_name_tmp)

        var_column_list = list(var_dframe_in.columns)
        if inverse_map:
            var_map_list = list(var_map.keys())
        else:
            var_map_list = list(var_map.values())

        for var_column_name in var_column_list:
            if var_column_name not in var_map_list:
                var_dframe_in.drop(var_column_name, axis=1, inplace=True)
                log_stream.warning(' ===> Variable "' + var_column_name +
                                   '" not included in the mapping obj. It will be removed from the dataframe obj')

        var_dframe_out = var_dframe_in.rename(columns=var_rename)

    else:
        var_dframe_out = deepcopy(var_dframe_in)

    return var_dframe_out
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to map variable(s) in a dictionary object
def map_vars_dict(var_data_in, var_map=None):

    if var_map is not None:
        var_data_out = {}
        for var_name_out, var_name_in in var_map.items():
            if var_name_in in list(var_data_in.keys()):
                values_tmp = var_data_in[var_name_in]
                var_data_out[var_name_out] = values_tmp
            else:
                log_stream.warning(' ===> Variable "' + var_name_in + '" is not included in the source obj')
    else:
        var_data_out = deepcopy(var_data_in)

    return var_data_out
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to fill template time tags
def fill_tags_time(template_time_tags,
                   time_reference=None, time_start=None, time_end=None):
    template_time_values = {}
    for template_key, template_value in template_time_tags.items():
        if 'start' in template_key:
            if time_start is not None:
                time_string = time_start.to_pydatetime()
                template_time_values[template_key] = time_string
        elif 'end' in template_key:
            if time_end is not None:
                time_string = time_end.to_pydatetime()
                template_time_values[template_key] = time_string
        else:
            if time_reference is not None:
                time_string = time_reference.to_pydatetime()
                template_time_values[template_key] = time_string
    return template_time_values
# ----------------------------------------------------------------------------------------------------------------------
