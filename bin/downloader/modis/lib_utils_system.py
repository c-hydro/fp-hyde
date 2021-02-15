# -------------------------------------------------------------------------------------
# Libraries
import os
import re

from copy import deepcopy
from datetime import datetime
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
# Method to make folder
def make_folder(path_folder):
    if not os.path.exists(path_folder):
        os.makedirs(path_folder)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to detect url(s)
def detect_url(string):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, string)
    return [x[0] for x in url]
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to remove url
def remove_url(url):
    url_tmpl = re.compile(r"https?://(www\.)?")
    string = url_tmpl.sub('', url).strip().strip('/')
    return string
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
        for tag_key_name, tag_value in tags_format.items():
            tag_key_format = '{' + tag_key_name + '}'
            if tag_value is not None:
                if tag_key_name in list(tags_filling.keys()):
                    if tag_key_format in string_raw:
                        string_filled = string_raw.replace(tag_key_format, tag_value)
                        string_raw = string_filled
                    else:
                        tags_format_tmp.pop(tag_key_name, None)

        dim_max = 1
        for tags_filling_values_tmp in tags_filling.values():
            if isinstance(tags_filling_values_tmp, list):
                dim_tmp = tags_filling_values_tmp.__len__()
                if dim_tmp > dim_max:
                    dim_max = dim_tmp

        string_filled_list = [string_filled] * dim_max

        string_filled_def = []
        for string_id, string_filled_step in enumerate(string_filled_list):
            for tag_format_name, tag_format_value in list(tags_format_tmp.items()):

                if tag_format_name in list(tags_filling.keys()):
                    tag_filling_value = tags_filling[tag_format_name]

                    if isinstance(tag_filling_value, list):
                        tag_filling_step = tag_filling_value[string_id]
                    else:
                        tag_filling_step = tag_filling_value

                    if tag_filling_step is not None:

                        if isinstance(tag_filling_step, datetime):
                            tag_filling_step = tag_filling_step.strftime(tag_format_value)

                        if isinstance(tag_filling_step, (float, int)):
                            tag_filling_step = tag_format_value.format(tag_filling_step)

                        string_filled_step = string_filled_step.replace(tag_format_value, tag_filling_step)

            string_filled_def.append(string_filled_step)

        if dim_max == 1:
            string_url = detect_url(string_filled_def[0])
            if string_url.__len__() == 0:
                string_filled_out = string_filled_def[0].replace('//', '/')
            else:
                string_filled_out = string_filled_def[0]
        else:
            string_filled_out = []
            for string_filled_tmp in string_filled_def:
                string_url = detect_url(string_filled_tmp)
                if string_url.__len__() == 0:
                    string_filled_out.append(string_filled_tmp.replace('//', '/'))
                else:
                    string_filled_out.append(string_filled_tmp)

        return string_filled_out
    else:
        return string_raw
# -------------------------------------------------------------------------------------
