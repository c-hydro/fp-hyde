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
                          missing_data=-9999.0, no_data=-9999.0,
                          tag_file_fields=None):

    if tag_file_fields is None:
        tag_file_fields = ['code', 'discharge', 'tag']

    idx_sections = geo_collections[tag_idx_section].values.tolist()
    code_sections = geo_collections[tag_code_section].values.tolist()
    tag_sections = geo_collections[tag_tag_section].values.tolist()

    time_data = list(set(data_collections.index.tolist()))

    if tag_code_data not in tag_file_fields:
        logging.error(' ===> Section code tag tag must be in the file fields list')
        raise IOError('Check your section code tag')
    if tag_name_data not in tag_file_fields:
        logging.error(' ===> Variable name tag must be in the file fields list')
        raise IOError('Check your variable name tag')

    if time_data.__len__() > 1:
        logging.warning(' ===> Time is not unique in data time. Get the first value to reference.')
        time_data = time_data[0]
    else:
        time_data = time_data[0]

    df_collections = []
    for idx_section, code_section, tag_section in zip(idx_sections, code_sections, tag_sections):

        logging.info(' --------> Get data for point: ' + tag_section + ' ... ')

        row_geo = geo_collections[geo_collections[tag_idx_section].values == idx_section]

        if code_section in data_collections[tag_code_data].values.tolist():
            row_data = data_collections[data_collections[tag_code_data].values == code_section]

            if row_geo[tag_code_section].values == row_data[tag_code_data].values:
                df_data = row_data[tag_file_fields]
                logging.info(' --------> Get data for point: ' + tag_section + ' ... DONE')
            else:
                logging.warning(' ===> Code of section and data is not equal. Init value with ' + str(missing_data))

                if tag_section in geo_collections[tag_tag_section].values.tolist():
                    row_geo = geo_collections[geo_collections[tag_tag_section].values == tag_section]
                    code_data = row_geo[tag_code_data].values[0]
                else:
                    code_data = missing_data

                value_dict = {}
                for tag_field in tag_file_fields:
                    if tag_field != tag_name_data:
                        if tag_field in list(row_geo.columns):
                            value_tmp = row_geo[tag_field].values[0]
                        else:
                            if tag_field == tag_name_data:
                                value_tmp = no_data
                            elif tag_field == tag_code_data:
                                value_tmp = code_data
                    else:
                        value_tmp = no_data
                    value_dict[tag_field] = value_tmp
                df_data = pd.DataFrame(data=value_dict, index=[time_data])

                logging.info(' --------> Get data for point: ' + tag_section + ' ... DONE')
        else:
            logging.info(' --------> Get data for point: ' + tag_section + ' ... SKIPPED. Section is not in data values')

            if tag_section in geo_collections[tag_tag_section].values.tolist():
                row_geo = geo_collections[geo_collections[tag_tag_section].values == tag_section]
                code_data = row_geo[tag_code_data].values[0]
            else:
                code_data = missing_data

            value_dict = {}
            for tag_field in tag_file_fields:
                if tag_field != tag_name_data:
                    if tag_field in list(row_geo.columns):
                        value_tmp = row_geo[tag_field].values[0]
                        if tag_field == tag_name_data:
                            value_tmp = no_data
                        elif tag_field == tag_code_data:
                            value_tmp = code_data
                else:
                    value_tmp = no_data
                value_dict[tag_field] = value_tmp
            df_data = pd.DataFrame(data=value_dict, index=[time_data])

        df_collections.append(df_data)

    return df_collections

# -------------------------------------------------------------------------------------
