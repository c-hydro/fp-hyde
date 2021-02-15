# -------------------------------------------------------------------------------------
# Libraries
import logging
import tempfile
import os
import json
import pickle
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write dataframe in csv format
def write_file_csv(file_name, data_frame,
                   data_separetor=',', data_encoding='utf-8', data_index=False, data_header=True):

    var_name = list(data_frame.columns.values)

    data_frame.to_csv(file_name, sep=data_separetor, encoding=data_encoding,
                      index=data_index, index_label=False, header=data_header,
                      columns=var_name)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read json file
def read_file_json(file_name):
    with open(file_name, 'r', encoding="utf-8") as file_handle:
        file_data = json.load(file_handle)
    return file_data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create a tmp name
def create_filename_tmp(prefix='tmp_', suffix='.tiff', folder=None):

    if folder is None:
        folder = '/tmp'

    with tempfile.NamedTemporaryFile(dir=folder, prefix=prefix, suffix=suffix, delete=False) as tmp:
        temp_file_name = tmp.name
    return temp_file_name
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read settings file
def read_file_settings(file_name):
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
# Method to read data obj
def read_obj(filename):
    if os.path.exists(filename):
        data = pickle.load(open(filename, "rb"))
    else:
        data = None
    return data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write data obj
def write_obj(filename, data):
    if os.path.exists(filename):
        os.remove(filename)
    with open(filename, 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)
# -------------------------------------------------------------------------------------
