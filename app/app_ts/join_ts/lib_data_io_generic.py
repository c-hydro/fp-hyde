"""
Library Features:

Name:          lib_data_io_generic
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20220320'
Version:       '1.0.0'
"""

# ----------------------------------------------------------------------------------------------------------------------
# libraries
import logging
import numpy as np
import pandas as pd

from copy import deepcopy

from lib_info_args import logger_name
from lib_utils_time import define_time_frequency

# logging
log_stream = logging.getLogger(logger_name)
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to combine data over the expected time range
def combine_data_point_by_time(point_data_collections_src, point_geo,
                               time_start_expected, time_end_expected,
                               time_frequency_expected='D', time_reverse=True):
    # create time range expected
    time_range_expected = pd.date_range(start=time_start_expected, end=time_end_expected, freq=time_frequency_expected)

    # iterate over variable(s)
    point_data_collections_dst = {}
    if point_data_collections_src is not None:
        for point_var, point_data_raw in point_data_collections_src.items():

            # create null data
            null_data = np.zeros(shape=(time_range_expected.shape[0], point_geo.shape[0]))
            null_data[:, :] = np.nan
            null_dict = {}
            for point_id, point_label in enumerate(point_data_raw.columns):
                null_dict[point_label] = null_data[:, point_id]
            point_data_expected = pd.DataFrame(data=null_dict, index=time_range_expected)

            # update expected data with raw data
            point_data_expected.update(point_data_raw)
            # time reverse flag
            if time_reverse:
                point_data_expected = point_data_expected.sort_index(ascending=False)

            # store data in a common obj
            point_data_collections_dst[point_var] = point_data_expected

    else:
        log_stream.warning(' ===> No data available to combine over the expected time range')
        point_data_collections_dst = None

    return point_data_collections_dst

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to range data point
def range_data_point(point_collection,
                     time_run_reference=None, time_start_reference=None, time_end_reference=None):

    time_start_collection, time_end_collection, frequency_collection, seconds_collections = [], [], [], []
    for point_name, point_data in point_collection.items():
        time_index_step = point_data.index
        time_start_step, time_end_step = time_index_step[0], time_index_step[-1]
        time_frequency_step = define_time_frequency(time_index_step)

        if time_frequency_step[0].isalpha():
            tmp_frequency_step = ''.join(['1', time_frequency_step])
        else:
            tmp_frequency_step = deepcopy(time_frequency_step)

        seconds_step = pd.to_timedelta(tmp_frequency_step).total_seconds()

        seconds_collections.append(seconds_step)
        frequency_collection.append(time_frequency_step)

        if time_start_reference is not None:
            if time_start_reference < time_start_step:
                time_start_step = deepcopy(time_start_reference)
        if time_end_reference is not None:
            if time_end_reference > time_end_step:
                time_end_step = deepcopy(time_end_reference)
            if time_run_reference > time_end_step:
                time_end_step = deepcopy(time_run_reference)

        time_start_collection.append(time_start_step)
        time_end_collection.append(time_end_step)

    idx_min = np.argmin(np.array(seconds_collections))

    time_frequency = frequency_collection[idx_min]
    time_start = pd.DatetimeIndex(time_start_collection).min()
    time_end = pd.DatetimeIndex(time_end_collection).max()

    return time_frequency, time_start, time_end
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to organize data point
def organize_data_point(point_dframe, ref_time=None, ref_registry=None):

    # get time refernce
    time_list = list(point_dframe['time'].values)
    time_list = list(set(time_list))
    if time_list.__len__() > 1:

        point_time = None
        for time_step in time_list:
            time_step = pd.Timestamp(time_step)
            if time_step != ref_time:
                time_mask = (pd.DatetimeIndex(point_dframe['time'].values) != time_step)
                point_dframe['data'][~time_mask] = np.nan
            elif time_step == ref_time:
                point_time = time_step

        if point_time is None:
            log_stream.error(' ===> Time reference not selected in the dataframe')
            raise RuntimeError('Check the dataframe time reference')

    else:
        point_time = time_list[0]

    if ref_registry is not None:
        ref_name = list(ref_registry['name'].values)
        ref_tag = list(ref_registry['tag'].values)

    # iterate over variable(s)
    point_collections = {}
    for point_key, point_data in point_dframe.items():

        if point_key != 'time':
            # get data and index
            tmp_index = point_data.index
            tmp_data = point_data.values
            # create object
            tmp_obj = {point_time: tmp_data}
            # create dataframe

            point_dframe = pd.DataFrame(data=tmp_obj, index=tmp_index)

            # update expected dataframe with raw data
            if ref_registry is not None:
                expected_dframe = pd.DataFrame(index=ref_name)
                point_dframe = expected_dframe.join(point_dframe)

            if ref_registry is not None:
                point_tags = [''] * ref_name.__len__()
                for i, (step_name, step_tag) in enumerate(zip(ref_name, ref_tag)):
                    step_idx = np.argwhere(point_dframe.index == step_name)[0][0]
                    step_tag = ref_tag[step_idx]

                    point_tags[step_idx] = step_tag

                point_dframe = point_dframe.reset_index()
                point_dframe['tag'] = point_tags
                point_dframe = point_dframe.set_index('tag')
                point_dframe = point_dframe.sort_index()
                point_dframe = point_dframe.drop(columns='index')

            # store in the collection
            point_collections[point_key] = point_dframe

    return point_collections, point_time
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to join data point
def join_data_point(point_data, point_collection, point_time=None,
                    name_index='time', ascending_index=False, sort_index=True):

    # join point collections
    if point_collection is None:
        # iterate over variable(s)
        if point_data is not None:
            point_collection = deepcopy(point_data)
        else:
            log_stream.warning(' ===> No data available to join')
    else:

        # iterate over variable(s)
        if point_data is not None:
            for var_name, tmp_df in point_data.items():

                # get collections and tmp dataframes
                collection_df = point_collection[var_name]

                # append new columns to the collection
                collection_df = collection_df.join(tmp_df)

                # sort index
                if sort_index:
                    if ascending_index:
                        collection_df = collection_df.sort_index(ascending=True)
                    else:
                        collection_df = collection_df.sort_index(ascending=False)

                # store in the collection
                point_collection[var_name] = collection_df

        else:
            log_stream.warning(' ===> No data available to join')

    return point_collection
# ----------------------------------------------------------------------------------------------------------------------
