# -------------------------------------------------------------------------------------
# Libraries
import logging
import mysql.connector as pymysql
import datetime
import csv
import netrc

import numpy as np
import pandas as pd

from copy import deepcopy
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to order ground network data
def order_data(data_frame, data_fields_expected):

    data_fields_raw = list(data_frame.columns.values)

    columns_result = all(elem in data_fields_raw for elem in data_fields_expected)
    if columns_result:
        data_frame_ordered = data_frame[data_fields_expected]
    else:
        logging.warning(' ===> Dataframe ordering failed because all expected columns are not in original dataframe')
        data_frame_ordered = data_frame

    return data_frame_ordered

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to organize dams data into a dataframe
def organize_data_dams(
        time, data_collection, dams_df, data_type='istantaneous',
        data_units='m^3', data_valid_range=None,
        data_scale_factor=1, data_min_count=1, no_data=-9999.0,
        columns_list_data=None, columns_type_data=None, columns_id_data=None,
        column_join_data='name', column_join_dams='name',
        column_idx_data='id', column_value_data='data', column_time_data='time', column_name_data='name'):

    if columns_list_data is None:
        columns_list_data = ['id', 'name', 'time', 'data']
    if columns_type_data is None:
        columns_type_data = [np.int, str, datetime.datetime, np.float]
    if columns_id_data is None:
        columns_id_data = [0, 1, 2, 3]

    if data_valid_range is None:
        data_valid_range = [0, None]

    if column_idx_data not in columns_list_data:
        logging.error(' ===> Column data index tag is not in columns list names')
        raise ValueError('Bad definition of data column tag')
    if column_value_data not in columns_list_data:
        logging.error(' ===> Column values data tag is not in columns list names')
        raise ValueError('Bad definition of column tag')
    if column_time_data not in columns_list_data:
        logging.error(' ===> Column time data tag is not in columns list names')
        raise ValueError('Bad definition of column tag')
    if column_name_data not in columns_list_data:
        logging.error(' ===> Column name data tag is not in columns list names')
        raise ValueError('Bad definition of column tag')

    data_workspace = {}
    for data_array_row in data_collection:

        columns_list_select = [columns_list_data[i] for i in columns_id_data]
        columns_type_select = [columns_type_data[i] for i in columns_id_data]

        data_list_row = list(data_array_row)
        data_list_select = [data_list_row[i] for i in columns_id_data]

        for column_name, column_value in zip(columns_list_select, data_list_select):

            if column_name not in list(data_workspace.keys()):
                data_workspace[column_name] = [column_value]
            else:
                column_tmp = data_workspace[column_name]
                column_tmp.append(column_value)
                data_workspace[column_name] = column_tmp

    for column_name, column_type in zip(columns_list_select, columns_type_select):
        data_tmp = data_workspace[column_name]

        if np.int == column_type:
            data_tmp = np.asarray(data_tmp, dtype=np.int)
        elif np.float == column_type:
            data_tmp = np.asarray(data_tmp, dtype=np.float)
        elif pd.Timestamp == column_type:
            data_tmp = pd.to_datetime(data_tmp)
        elif bool == column_type:
            data_tmp = np.asarray(data_tmp, dtype=bool)

        if column_name == column_value_data:

            data_tmp = data_tmp / data_scale_factor

            data_valid_min = data_valid_range[0]
            data_valid_max = data_valid_range[1]

            if data_valid_min is not None:
                data_tmp[data_tmp < data_valid_min] = np.nan
            if data_valid_max is not None:
                data_tmp[data_tmp > data_valid_max] = np.nan

        data_workspace[column_name] = data_tmp

    data_df = pd.DataFrame(data_workspace, columns=columns_list_select)

    # Adapt names on database qith names in the shapefile
    data_df[column_join_data] = data_df[column_join_data].str.title()
    data_df[column_join_data] = data_df[column_join_data].str.replace('_','')

    data_df_merged = pd.merge(data_df, dams_df, left_on=column_join_data, right_on=column_join_dams)

    data_df_select = data_df_merged[(data_df_merged[column_time_data] == time)]
    data_df_filter = data_df_select.dropna(subset=[column_value_data])

    if data_df_filter is not None:
        if 'units' not in list(data_df_filter.columns):
            data_df_filter['units'] = data_units

        if data_df_filter.empty:
            data_df_filter = None
        else:
            data_df_filter[column_value_data] = data_df_filter[column_value_data].fillna(no_data)

    return data_df_filter

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get dams dataset
def get_data_dams(var_name, time_from, time_to, db_obj_settings):

    # Define DB query
    db_query_data = define_query_dams_data(var_name=var_name, time_from=time_from, time_to=time_to)

    # Open DB connection
    db_connection = pymysql.connect(**db_obj_settings)

    db_cursor = db_connection.cursor()
    db_cursor.execute("SELECT VERSION()")
    db_rows = db_cursor.fetchone()

    db_cursor.execute(db_query_data)
    db_dataset = db_cursor.fetchall()
    db_len = len(db_dataset)

    db_cursor.close()
    # Close DB connection
    db_connection.commit()

    return db_dataset

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define database settings
def get_db_credential(db_name="db_dighe"):
    try:
        info = netrc.netrc()
        db_info = info.authenticators(db_name)
        if db_info:
            username, account, password = db_info[0], db_info[1], db_info[2]
        else:
            username, password = None, None

    except Exception as e:
        logging.error(' ===> File netrc error: {0}'.format(str(e)))
        raise RuntimeError('Credentials are not available on netrc file')

    return username, password
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define database settings
def define_db_settings(db_info):

    logging.info(' ---> Define server configuration ... ')

    if 'server_mode' in list(db_info.keys()):
        server_mode = db_info['server_mode']
    else:
        server_mode = True
    if 'server_ip' in list(db_info.keys()):
        server_ip = db_info['server_ip']
    else:
        logging.error(' ===> Server ip is not defined')
        raise IOError('Parameter is not defined in the configuration file.')
    if 'server_name' in list(db_info.keys()):
        server_name = db_info['server_name']
    else:
        logging.error(' ===> Server name is not defined')
        raise IOError('Parameter is not defined in the configuration file.')
    if 'server_user' in list(db_info.keys()):
        server_user = db_info['server_user']
    else:
        logging.error(' ===> Server user is not defined')
        raise IOError('Parameter is not defined in the configuration file.')
    if 'server_password' in list(db_info.keys()):
        server_password = db_info['server_password']
    else:
        logging.warning(' ===> Server password is not defined')
        server_password = None

    # pymysql.connect(host='10.6.26.209', user='cima', db='db_dighe')
    if server_mode:
        logging.info(' ---> Define server configuration ... OK. Set active mode')
        if server_password:
            db_settings = {'host': server_ip, 'user': server_user,
                           'db': server_name, 'password': server_password}
        else:
            db_settings = {'host': server_ip, 'user': server_user, 'db': server_name}
    else:
        logging.info(' ---> Define server configuration ... SKIPPED. Set inactive mode.')
        db_settings = None

    return db_settings
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to parse the query time
def parse_query_time(time_step, time_frequency='H', time_format="%Y-%m-%dT%H:%M:%S.%f",
                     time_mode='accumulated'):

    if time_mode == 'accumulated':
        time_to = time_step.strftime(time_format)[:-3]
        time_from = pd.date_range(end=time_step, freq=time_frequency, periods=2)[0].strftime(time_format)[:-3]
    elif time_mode == 'instantaneous':
        time_to = time_step.strftime(time_format)[:-3]
        time_from = time_step.strftime(time_format)[:-3]
    else:
        logging.error(' ===> Time query definition failed')
        raise IOError('The time mode is not correctly defined')

    return time_from, time_to

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define river station query data
def define_query_dams_data(var_name='volume', time_from=None, time_to=None):

    if (time_from is not None) and (time_to is not None):

        db_query = "SELECT dighe.id_diga, livelli.nome_diga, livelli.data_livello, livelli." + var_name + " "
        db_query += "FROM livelli INNER JOIN dighe ON livelli.nome_diga=dighe.nome_diga "
        db_query += "WHERE livelli.data_livello BETWEEN  '" + time_from + "' AND '" + time_to + "' "
        db_query += "ORDER BY dighe.id_diga "

    else:
        logging.error(' ===> Data query definition failed')
        raise IOError('Some arguments are not correctly defined')

    return db_query
# -------------------------------------------------------------------------------------
