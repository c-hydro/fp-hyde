"""
Library Features:

Name:          lib_data_io_csv
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20240301'
Version:       '1.0.0'
"""

# ----------------------------------------------------------------------------------------------------------------------
# libraries
import logging
import warnings
import numpy as np
import pandas as pd

from lib_utils_obj import invert_dict
from lib_info_args import logger_name

# logging
warnings.simplefilter(action='ignore', category=FutureWarning)
log_stream = logging.getLogger(logger_name)
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to read file csv
def read_file_csv(file_name, dframe_fields=None,
                  dframe_index='name', dframe_date_format='%Y-%m-%d %H:%M',
                  dframe_sep=',', dframe_decimal='.', dframe_float_precision='legacy'):
    # check fields
    if dframe_fields is None:
        dframe_fields = {}

    # read file csv
    file_dframe = pd.read_csv(file_name, sep=dframe_sep, decimal=dframe_decimal)

    # apply fields name
    tmp_fields = invert_dict(dframe_fields)
    file_dframe = file_dframe.rename(columns=tmp_fields)
    # remove columns not in the fields list
    for columns_tmp in list(file_dframe.columns):
        if columns_tmp not in list(dframe_fields.keys()):
            file_dframe = file_dframe.drop(columns_tmp, axis=1)

    if dframe_index not in list(file_dframe.columns):
        if 'time_end' in list(file_dframe.columns):
            tmp_index = 'time_start'
        elif 'time_start' in list(file_dframe.columns):
            tmp_index = 'time'
        else:
            log_stream.error(' ===> Index column "' + dframe_index +
                             '"  must be available in the source dataframe. Check the source file')
            raise RuntimeError('Including the index column in the source file for skipping this error.')
    else:
        tmp_index = dframe_index

    try:
        file_dframe[dframe_index] = pd.DatetimeIndex(file_dframe[tmp_index].values).strftime(dframe_date_format)
        file_dframe[dframe_index] = pd.DatetimeIndex(file_dframe[tmp_index])
    except Exception as exc:
        log_stream.warning(' ===> Dataframe index not in time format')
        file_dframe = file_dframe.set_index(dframe_index)

    file_dframe = file_dframe.reset_index()

    for columns_tmp in ['index']:
        if columns_tmp in list(file_dframe.columns):
            if columns_tmp != dframe_index:
                file_dframe = file_dframe.drop(columns_tmp, axis=1)
    file_dframe = file_dframe.set_index(dframe_index)
    file_dframe.sort_index(inplace=True)

    return file_dframe

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to write file csv
def write_file_csv(file_name, file_dframe,
                   dframe_sep=',', dframe_decimal='.', dframe_float_format='%.2f',
                   dframe_index=False, dframe_header=True,
                   dframe_index_label='time', dframe_index_format='%Y-%m-%d %H:%M',
                   dframe_no_data=-9999):

    if np.isfinite(dframe_no_data):
        file_dframe.fillna(dframe_no_data, inplace=True)

    if dframe_index_format is not None:
        file_dframe.index = file_dframe.index.strftime(dframe_index_format)

    file_dframe.to_csv(
        file_name, mode='w',
        index=dframe_index, sep=dframe_sep, decimal=dframe_decimal,
        index_label=dframe_index_label,
        header=dframe_header, float_format=dframe_float_format,  quotechar='"')

# ----------------------------------------------------------------------------------------------------------------------
