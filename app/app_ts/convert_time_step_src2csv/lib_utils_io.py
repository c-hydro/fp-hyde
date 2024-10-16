"""
Library Features:

Name:          lib_utils_io
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20231121'
Version:       '1.0.0'
"""


# ----------------------------------------------------------------------------------------------------------------------
# libraries
import logging
import pandas as pd

from lib_info_args import logger_name

# logging
log_stream = logging.getLogger(logger_name)
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to merge point to table
def merge_points_to_table(file_dframe, file_var='vwc_10_cm'):

    if not isinstance(file_dframe, dict):
        log_stream.error(' ===> File dframe obj must be a dictionary')
        raise IOError('File data frame must be a dictionary')

    point_collections = None
    for point_name, point_dframe in file_dframe.items():
        if file_var in point_dframe:
            point_values = point_dframe[file_var].values
            point_index = point_dframe.index

            point_data = {point_name: point_values}
            if point_collections is None:
                point_collections = pd.DataFrame(index=point_index, data=point_data)
            else:
                point_collections[point_name] = point_values
        else:
            log_stream.warning(' ===> Variable "' + file_var + '" is not available in point "' + point_name + '"')

    if point_collections is not None:
        point_collections.index.name = 'time'

    return point_collections

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to select time table
def select_table_by_times(table_dframe_generic, time_range, time_reverse=True):

    time_range = sorted(time_range)

    time_start = time_range[0]
    time_end = time_range[-1]

    time_mask = (table_dframe_generic.index >= time_start) & (table_dframe_generic.index <= time_end)
    table_dframe_selected = table_dframe_generic.loc[time_mask]

    if time_reverse:
        table_dframe_selected = table_dframe_selected.iloc[::-1]

    return table_dframe_selected
# ----------------------------------------------------------------------------------------------------------------------
