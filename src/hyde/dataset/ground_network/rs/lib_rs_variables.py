"""
Library Features:

Name:          lib_rs_variables
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20201210'
Version:       '2.0.0'
"""
# -------------------------------------------------------------------------------------
# Library
import logging
import numpy as np
import pandas as pd

# Debug
import matplotlib.pylab as plt
logging.getLogger('matplotlib').setLevel(logging.WARNING)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to convert values 2 points
def convert_values2points(data_collections, geo_collections,
                          tag_idx_section='id', tag_code_section='code', tag_tag_section='tag',
                          tag_name_data='discharge', tag_code_data='code', tag_time_data='time',
                          missing_data=-9998.0, no_data=-9999.0):

    idx_sections = geo_collections[tag_idx_section].values.tolist()
    code_sections = geo_collections[tag_code_section].values.tolist()
    tag_sections = geo_collections[tag_tag_section].values.tolist()

    time_data = list(set(data_collections.index.tolist()))

    if time_data.__len__() > 1:
        logging.warning(' ===> Time is not unique in data time. Get the first value to reference.')
        time_data = time_data[0]
    else:
        time_data = time_data[0]

    ts_collections = []
    for idx_section, code_section, tag_section in zip(idx_sections, code_sections, tag_sections):

        logging.info(' --------> Get data for point: ' + tag_section + ' ... ')

        row_geo = geo_collections[geo_collections[tag_idx_section].values == idx_section]

        if code_section in data_collections[tag_code_data].values.tolist():
            row_data = data_collections[data_collections[tag_code_data].values == code_section]

            if row_geo[tag_code_section].values == row_data[tag_code_data].values:
                ts_data = row_data[tag_name_data]
                logging.info(' --------> Get data for point: ' + tag_section + ' ... DONE')
            else:
                ts_data = pd.Series(data=missing_data, index=[time_data])
                logging.warning(' ===> Code of section and data is not equal. Init value with ' + str(missing_data))
                logging.info(' --------> Get data for point: ' + tag_section + ' ... DONE')
        else:
            logging.info(' --------> Get data for point: ' + tag_section + ' ... SKIPPED. Section is not in data values')
            ts_data = pd.Series(data=no_data, index=[time_data])

        ts_collections.append(ts_data)

    return ts_collections

# -------------------------------------------------------------------------------------
