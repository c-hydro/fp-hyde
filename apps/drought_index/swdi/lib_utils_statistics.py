import logging
import pandas as pd
import numpy as np
from scipy.signal import lfilter

from lib_utils_system import convert_list2dict
from lib_utils_io import write_obj

import matplotlib.pylab as plt


def compute_norm_data(ws_filter, ws_moments, geo_mask=None):
    ws_norm = {}
    for ref_key, ref_filter in ws_filter.items():

        ws_norm[ref_key] = {}
        for ref_time, ref_values in ref_filter.items():
            ref_month = pd.Timestamp(ref_time).month

            ref_moment_mean = ws_moments[ref_key]['mean'][ref_month]
            ref_moment_std = ws_moments[ref_key]['std'][ref_month]

            ref_values = np.asarray(ref_values)
            ref_norm = (ref_values - ref_moment_mean) / ref_moment_std

            if geo_mask is not None:
                ref_norm = ref_norm * geo_mask

            ws_norm[ref_key][ref_month] = ref_norm

    return ws_norm


def compute_moments_data_first_order(filter_data, tag_mean='mean', tag_stdev='std'):

    ws_moment = {}
    for filter_order, filter_dictionary in filter_data.items():
        month_list = list(pd.DatetimeIndex(list(filter_dictionary.keys())).month)

        month_unique = list(set(month_list))
        ws_moment[filter_order] = {}

        var_list_mean = []
        var_list_std = []
        for month_step in month_unique:
            month_idx = [i for i, x in enumerate(month_list) if x == month_step]

            var_data_list = []
            for idx_step in month_idx:
                var_data_tmp = list(filter_dictionary.values())[idx_step]
                var_data_list.append(var_data_tmp)
            var_data_array = np.array(var_data_list, dtype=float)

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                var_data_mean = np.nanmean(var_data_array, axis=0, dtype=np.float32)
                var_data_std = np.std(var_data_array, axis=0, dtype=np.float32)

            var_list_mean.append(var_data_mean)
            var_list_std.append(var_data_std)

        var_dict_mean = convert_list2dict(month_unique, var_list_mean)
        var_dict_std = convert_list2dict(month_unique, var_list_std)

        ws_moment[filter_order][tag_mean] = var_dict_mean
        ws_moment[filter_order][tag_stdev] = var_dict_std

    return ws_moment


def filter_data(ws_data, field_capacity=None, wilting_point=None, index_name='sspi'):

    var_time_list = list(ws_data.keys())
    var_data_3d = np.array(list(ws_data.values()), dtype=float)

    ws_filter = {}

    filter_order1_3d = var_data_3d

    if index_name == 'swdi':
        if (field_capacity is not None) and (wilting_point is not None):
            filter_order1_3d = (filter_order1_3d - field_capacity) / (field_capacity - wilting_point)
        else:
            logging.error(' ===> Geographical data are null!')
            raise IOError('Some mandatory field are not defined')
    elif index_name == 'sspi':
        filter_order1_3d = var_data_3d
    else:
        logging.error(' ===> Filter index type is not available')
        raise NotImplemented('Filter type not implemented yet')

    filter_order1_list = filter_order1_3d.tolist()

    filter_order1_dict = convert_list2dict(var_time_list, filter_order1_list)
    ws_filter['month_1'] = filter_order1_dict

    filter_order2_3d = lfilter([1 / 2] * 2, 1, filter_order1_3d, axis=0)
    filter_order2_3d[0, :, :] = np.nan
    filter_order2_list = filter_order2_3d.tolist()
    filter_order2_dict = convert_list2dict(var_time_list, filter_order2_list)
    ws_filter['month_2'] = filter_order2_dict

    filter_order3_3d = lfilter([1 / 3] * 3, 1, filter_order1_3d, axis=0)
    filter_order3_3d[0:2, :, :] = np.nan
    filter_order3_list = filter_order3_3d.tolist()
    filter_order3_dict = convert_list2dict(var_time_list, filter_order3_list)
    ws_filter['month_3'] = filter_order3_dict

    filter_order6_3d = lfilter([1 / 6] * 6, 1, filter_order1_3d, axis=0)
    filter_order6_3d[0:5, :, :] = np.nan
    filter_order6_list = filter_order6_3d.tolist()
    filter_order6_dict = convert_list2dict(var_time_list, filter_order6_list)
    ws_filter['month_6'] = filter_order6_dict

    return ws_filter