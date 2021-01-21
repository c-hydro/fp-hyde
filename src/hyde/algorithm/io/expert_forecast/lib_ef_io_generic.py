"""
Library Features:

Name:          lib_ef_io_generic
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210104'
Version:       '1.0.0'
"""
#######################################################################################
# Libraries
import logging
import tempfile
import os
import json
import pickle
import re

import pandas as pd
import numpy as np

from copy import deepcopy
from scipy.io import loadmat

import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to save data info in json format
def save_file_json(file_name, file_data_dict, file_attrs=None, file_indent=4):

    file_workspace = {}
    for file_key, file_value in file_data_dict.items():

        if isinstance(file_value, dict):
            file_time_list = []
            file_data_list = []
            for file_time_step, file_data_step in file_value.items():

                file_time_list.append(file_time_step.strftime('%Y-%m-%d %H:%M'))
                file_data_list.append(file_data_step)

                if 'time' not in list(file_workspace.keys()):
                    file_workspace['time'] = file_time_list

                file_workspace[file_key] = file_data_list

        else:
            logging.error(' ===> Error in getting datasets')
            raise RuntimeError('Datasets case not implemented yet')

    if file_attrs is not None:
        for attr_key, attr_data in file_attrs.items():
            file_workspace[attr_key] = attr_data

    file_data = json.dumps(file_workspace, indent=file_indent, ensure_ascii=False, sort_keys=False)
    #file_data = re.sub(r'",\s+', '", ', file_data)

    with open(file_name, "w", encoding='utf-8') as file_handle:
        file_handle.write(file_data)

    pass

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Create default dataframe
def create_default_dframe(df_columns, df_shape, df_nodata=0.0):

    df_data = np.zeros(shape=df_shape)
    df_data[:, :] = df_nodata

    df_obj = pd.DataFrame(data=df_data, columns=df_columns)

    return df_obj
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read csv file
def read_file_csv(file_name, file_sep=';', file_skiprows=0, tag_time_dim='time'):

    file_dframe = pd.read_table(file_name, sep=file_sep, skiprows=file_skiprows)

    file_dframe.columns = file_dframe.columns.str.strip()
    file_dframe = file_dframe.loc[:, ~file_dframe.columns.str.contains('^Unnamed')]
    file_dframe = file_dframe.replace(to_replace=',', value='', regex=True)

    file_dframe = file_dframe.rename(columns={'data previsione': tag_time_dim})

    return file_dframe

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read mat file
def read_file_mat(file_name, var_name='vm'):

    file_data = loadmat(file_name)
    if var_name in list(file_data.keys()):
        var_data = file_data[var_name]
    else:
        logging.warning(' ===> Variable not found in mat file. Return none value')
        var_data = None
    return var_data

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
# Method to get file settings in json format
def read_file_settings(file_name_settings):
    if os.path.exists(file_name_settings):
        with open(file_name_settings) as file_handle:
            data_settings = json.load(file_handle)
    else:
        logging.error(' ===> Error in reading algorithm settings file')
        raise IOError('File not found')
    return data_settings
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
