import logging
import warnings
import pandas as pd
import numpy as np
from scipy.signal import lfilter

from lib_utils_system import convert_list2dict


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


def compute_moments_data_gamma_distribution(filter_data, count_all, count_filtered,
                                            tag_gamma_k='k', tag_gamma_theta='theta',
                                            tag_gamma_count_ratio='count_ratio'):

    ws_moment = {}
    for filter_order, filter_dictionary, in filter_data.items():

        month_list = list(pd.DatetimeIndex(list(filter_dictionary.keys())).month)

        month_unique = list(set(month_list))
        ws_moment[filter_order] = {}

        var_list_k = []
        var_list_theta = []
        var_list_count_ratio = []
        for month_step in month_unique:
            month_idx = [i for i, x in enumerate(month_list) if x == month_step]

            var_data_list = []
            var_count_all_list = []
            var_count_filtered_list = []
            for idx_step in month_idx:
                var_data_tmp = list(filter_dictionary.values())[idx_step]
                var_count_all_tmp = list(count_all.values())[idx_step]
                var_count_filtered_tmp = list(count_filtered.values())[idx_step]
                var_data_list.append(var_data_tmp)
                var_count_all_list.append(var_count_all_tmp)
                var_count_filtered_list.append(var_count_filtered_tmp)

            var_data_array = np.array(var_data_list, dtype=float)
            var_count_all_array = np.array(var_count_all_list, dtype=float)
            var_count_filtered_array = np.array(var_count_filtered_list, dtype=float)

            var_data_mean = np.nanmean(var_data_array, axis=0, dtype=np.float32)
            var_data_variance = np.nanvar(var_data_array, axis=0, dtype=np.float32)
            var_count_all = np.nansum(var_count_all_array, axis=0, dtype=np.float32)
            var_count_filtered = np.nansum(var_count_filtered_array, axis=0, dtype=np.float32)

            var_count_ratio = var_count_filtered / var_count_all

            var_idx_selected = np.where(var_count_filtered < 0.2 * var_count_all)

            var_data_mean[var_idx_selected[0], var_idx_selected[1]] = np.nan
            var_data_variance[var_idx_selected[0], var_idx_selected[1]] = np.nan
            var_count_ratio[var_idx_selected[0], var_idx_selected[1]] = np.nan

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                var_data_k = (var_data_mean ** 2) / var_data_variance
                var_data_theta = var_data_variance / var_data_mean

            var_list_k.append(var_data_k)
            var_list_theta.append(var_data_theta)
            var_list_count_ratio.append(var_count_ratio)

        var_dict_k = convert_list2dict(month_unique, var_list_k)
        var_dict_theta = convert_list2dict(month_unique, var_list_theta)
        var_dict_count_ratio = convert_list2dict(month_unique, var_list_count_ratio)

        ws_moment[filter_order][tag_gamma_k] = var_dict_k
        ws_moment[filter_order][tag_gamma_theta] = var_dict_theta
        ws_moment[filter_order][tag_gamma_count_ratio] = var_dict_count_ratio

    return ws_moment


def filter_data(ws_data, field_capacity=None, wilting_point=None, index_name='sspi'):

    var_time_list = list(ws_data.keys())
    var_data_3d = np.array(list(ws_data.values()), dtype=float)

    ws_filter = {}

    if index_name == 'swdi':
        filter_order1_3d = var_data_3d
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