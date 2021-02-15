# -------------------------------------------------------------------------------------
# Libraries
import logging
import os
import numpy as np
import pandas as pd
import xarray as xr

from src.hyde.algorithm.settings.model.rfarm.lib_rfarm_args import time_format, logger_name
log_stream = logging.getLogger(logger_name)

# Debug
import matplotlib.pylab as plt
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to convert expert forecast time period
def convert_time_expert_forecast(var_time_idx, var_time_freq='H', var_time_period=12):

    var_time_idx = pd.DatetimeIndex(var_time_idx)

    var_timestamp_base_start = pd.date_range(start=var_time_idx[0], periods=2, freq=var_time_freq)[1]
    var_timestamp_base_end = var_time_idx[-1]
    var_timestamp_base_period = pd.date_range(start=var_timestamp_base_start, end=var_timestamp_base_end,
                                              freq=var_time_freq)

    var_time_ext_start = pd.date_range(var_timestamp_base_period[-1], periods=2, freq=var_time_freq)[1]
    var_timestamp_ext_period = pd.date_range(start=var_time_ext_start, freq=var_time_freq, periods=var_time_period)

    var_time_period = var_timestamp_base_period.union(var_timestamp_ext_period)

    return var_time_period
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read expert forecast datasets
def read_data_expert_forecast(file_list, tag_var_time=None, tag_var_name_list=None, tag_var_reference=None):

    if tag_var_time is None:
        tag_var_time = ['time']

    if tag_var_reference is None:
        tag_var_reference = ['name']
    if tag_var_name_list is None:
        tag_var_name_list = ['rain_average', 'rain_peak', 'slope_x', 'slope_y', 'slope_t']

    tag_var_fields = tag_var_time + tag_var_reference + tag_var_name_list

    if not isinstance(tag_var_name_list, list):
        tag_var_name_list = [tag_var_name_list]
    if not isinstance(file_list, list):
        file_list = [file_list]

    file_reference = {}
    file_datasets = {}
    file_time = None
    for file_id, file_step in enumerate(file_list):
        file_reference[file_id] = {}
        file_datasets[file_id] = {}
        if os.path.exists(file_step):
            file_data = pd.read_json(file_step)
            for var_name in tag_var_fields:
                var_data = file_data[var_name].values
                if var_data.shape.__len__() == 1:
                    var_list_tmp = var_data.tolist()
                elif var_data.shape.__len__() > 1:
                    var_data = var_data.tolist()
                    if var_data.shape[1] == 1:
                        var_list_tmp = [var_value[0] for var_value in var_data]
                    else:
                        raise NotImplementedError('Dataset dimensions not allowed')
                else:
                    raise NotImplementedError('Variable dimensions not allowed')

                if var_name in tag_var_time:
                    if file_time is None:
                        file_time = var_list_tmp
                if var_name in tag_var_reference:
                    file_reference[file_id] = list(set(var_list_tmp))[0]
                if var_name in tag_var_name_list:
                    file_datasets[file_id][var_name] = var_list_tmp

    time_collections = file_time
    datasets_collections = {}
    for (file_ref_key, file_ref_name), file_datasets_fields in zip(file_reference.items(), file_datasets.values()):
        datasets_collections[file_ref_name] = file_datasets_fields

    return datasets_collections, time_collections

# -------------------------------------------------------------------------------------


