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
                               time_start_expected, time_end_expected, point_data_name='values',
                               time_frequency_expected='D', time_reverse=True):
    # create time range expected
    if (time_start_expected is not None) or (time_end_expected is not None):
        time_range_expected = pd.date_range(start=time_start_expected, end=time_end_expected, freq=time_frequency_expected)
    else:
        time_range_expected = None

    # iterate over variable(s)
    point_data_collections_dst = {}
    if point_data_collections_src is not None:
        for point_id, (point_label, point_data_raw) in enumerate(point_data_collections_src.items()):

            if point_data_raw is not None:
                # create null data
                null_data = np.zeros(shape=(time_range_expected.shape[0], 1))
                null_data[:] = np.nan
                # create null dataframe
                point_data_expected = pd.DataFrame(data=null_data, index=time_range_expected)

                # update expected data with raw data
                point_data_expected.update(point_data_raw)
                # time reverse flag
                if time_reverse:
                    point_data_expected = point_data_expected.sort_index(ascending=False)
                # set column name
                point_data_expected.columns = [point_data_name]
            else:
                # define not defined data using NoneType
                point_data_expected = None

            # store data in a common obj
            point_data_collections_dst[point_label] = point_data_expected

    else:
        log_stream.warning(' ===> No data available to combine over the expected time range')
        point_data_collections_dst = None

    return point_data_collections_dst

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to range data point
def range_data_point(point_collection,
                     time_start_reference, time_end_reference,
                     time_run_reference=None):

    if time_run_reference is not None:
        if isinstance(time_run_reference, str):
            time_run_reference = pd.Timestamp(time_run_reference)
        elif isinstance(time_run_reference, pd.Timestamp):
            pass
        else:
            log_stream.error(' ===> Time run reference is not correctly defined. Check your settings file.')
            raise RuntimeError('Time run reference is not correctly defined')

    if isinstance(time_start_reference, str):
        time_start_reference = pd.Timestamp(time_start_reference)
    elif isinstance(time_start_reference, pd.Timestamp):
        pass
    if isinstance(time_end_reference, str):
        time_end_reference = pd.Timestamp(time_end_reference)
    elif isinstance(time_end_reference, pd.Timestamp):
        pass

    time_start_collection, time_end_collection, frequency_collection, seconds_collections = [], [], [], []
    for point_name, point_data in point_collection.items():

        if point_data is not None:

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
        else:
            log_stream.warning(' ===> Point data are not available for "' + point_name + '"')

    # check seconds object to define times variable(s)
    if len(seconds_collections) > 0:
        idx_min = np.argmin(np.array(seconds_collections))

        time_frequency = frequency_collection[idx_min]
        time_start = pd.DatetimeIndex(time_start_collection).min()
        time_end = pd.DatetimeIndex(time_end_collection).max()
    else:
        time_frequency, time_start, time_end = None, None, None

    return time_frequency, time_start, time_end
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to join data point
def join_data_point(point_data, point_collection, point_time=None,
                    name_index='time', ascending_index=False, sort_index=True):

    # join point collections
    if point_collection is None:
        # iterate over variable(s)
        if point_data is not None:
            point_collection = {}
            for var_name, var_value in point_data.items():

                # get data based on selected time or all time(s)
                if point_time is not None:
                    # create dataframe collection
                    var_df = pd.DataFrame(data=var_value, index=[point_time])
                else:
                    # create dataframe collection
                    var_df = pd.DataFrame(data=var_value)
                # set index name
                var_df.index.name = name_index
                # store dataframe in a common obj
                point_collection[var_name] = var_df
        else:
            log_stream.warning(' ===> No data available to join')
    else:

        # iterate over variable(s)
        if point_data is not None:
            for var_name, var_value in point_data.items():
                # get tmp collection
                collection_df = point_collection[var_name]
                # create dataframe collection
                # get data based on selected time or all time(s)
                if point_time is not None:
                    tmp_df = pd.DataFrame(data=var_value, index=[point_time])
                else:
                    tmp_df = pd.DataFrame(data=var_value)

                # set index name
                tmp_df.index.name = name_index
                # append new line to dataframe collection
                collection_df = pd.concat([collection_df, tmp_df])

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
