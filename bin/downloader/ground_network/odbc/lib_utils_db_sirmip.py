# -------------------------------------------------------------------------------------
# Libraries
import logging
import pyodbc
import datetime
import csv
import netrc

import numpy as np
import pandas as pd
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get weather station dataset
def get_data_ws(var_name, time_from, time_to, db_line_settings, flag_type='automatic'):

    # Define DB query
    db_query = define_query_ws(var_name, time_from, time_to, flag_type)

    # Open DB connection
    db_connection = pyodbc.connect(db_line_settings)
    db_cursor = db_connection.cursor()

    # Execute DB query
    db_cursor.execute(db_query)
    # Get all data
    db_dataset = db_cursor.fetchall()
    # Close DB connection
    db_connection.commit()

    return db_dataset
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
# Method to organize river stations data into a dataframe
def organize_data_rs(time, data_collection, sections_df, data_type='istantaneous',
                     data_units='m^3/s', data_valid_range=None,
                     data_scale_factor=1, data_min_count=1,
                     columns_list_data=None, columns_type_data=None, columns_id_data=None,
                     column_idx_data='code', column_wl_data='water_level',
                     column_discharge_data='discharge', column_time_data='time',
                     column_idx_sections='code'):

    if columns_list_data is None:
        columns_list_data = ['id', 'code', 'time_datatime', 'time', 'time_parts', 'water_level', 'discharge',
                             'undefined_1', 'undefined_2', 'name', 'check']
    if columns_type_data is None:
        columns_type_data = [np.int, np.int, datetime.datetime, pd.Timestamp, str, np.float, np.float,
                             str, str, str, bool]
    if columns_id_data is None:
        columns_id_data = [0, 1, 3, 5, 6, 10]

    if data_valid_range is None:
        data_valid_range = [0, None]

    if column_idx_data not in columns_list_data:
        logging.error(' ===> Column data index tag is not in columns list names')
        raise ValueError('Bad definition of data column tag')
    if column_discharge_data not in columns_list_data:
        logging.error(' ===> Column discharge data tag is not in columns list names')
        raise ValueError('Bad definition of column tag')
    if column_wl_data not in columns_list_data:
        logging.error(' ===> Column water level data tag is not in columns list names')
        raise ValueError('Bad definition of column tag')
    if column_time_data not in columns_list_data:
        logging.error(' ===> Column time data tag is not in columns list names')
        raise ValueError('Bad definition of column tag')
    if column_idx_sections != column_idx_data:
        logging.error(' ===> Column index of sections and data tags must have the same name')
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

        if column_name == column_discharge_data:

            data_tmp = data_tmp / data_scale_factor

            data_valid_min = data_valid_range[0]
            data_valid_max = data_valid_range[1]

            if data_valid_min is not None:
                data_tmp[data_tmp < data_valid_min] = np.nan
            if data_valid_max is not None:
                data_tmp[data_tmp > data_valid_max] = np.nan

        data_workspace[column_name] = data_tmp

    data_df = pd.DataFrame(data_workspace, columns=columns_list_select)
    data_df_merged = pd.merge(data_df, sections_df, left_on=column_idx_data, right_on=column_idx_sections)
    data_df_select = data_df_merged[(data_df_merged[column_time_data] == time)]

    if 'units' not in list(data_df_select.columns):
        data_df_select['units'] = data_units

    return data_df_select

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to organize weather stations data into a dataframe
def organize_data_ws(data_collection, data_type='accumulated', data_units='', data_valid_range=None,
                     data_scale_factor=1, data_min_count=1,
                     columns_list=None, columns_type=None, columns_id=None,
                     column_idx='code', column_data='data', column_time_start='time_start', column_time_end='time_end'):

    if columns_list is None:
        columns_list = ['code', 'id', 'name', 'data', 'longitude', 'latitude', 'altitude',
                        'boundary_limit_01', 'boundary_limit_02', 'boundary_limit_03',
                        'catchment', 'time_start', 'time_end']
    if columns_type is None:
        columns_type = [np.int, np.int, str, np.float, np.float, np.float, np.float,
                        str, str, str,
                        str, pd.Timestamp, pd.Timestamp]
    if columns_id is None:
        columns_id = [0, 2, 3, 4, 5, 6, 10, 11, 12]

    if data_valid_range is None:
        data_valid_range = [0, None]

    if column_idx not in columns_list:
        logging.error(' ===> Column index tag is not in columns list names')
        raise ValueError('Bad definition of column tag')
    if column_data not in columns_list:
        logging.error(' ===> Column data tag is not in columns list names')
        raise ValueError('Bad definition of column tag')
    if column_time_start not in columns_list:
        logging.error(' ===> Column time start tag is not in columns list names')
        raise ValueError('Bad definition of column tag')
    if column_time_end not in columns_list:
        logging.error(' ===> Column time end tag is not in columns list names')
        raise ValueError('Bad definition of column tag')

    data_workspace = {}
    for data_array_row in data_collection:

        columns_list_select = [columns_list[i] for i in columns_id]
        columns_type_select = [columns_type[i] for i in columns_id]

        data_list_row = list(data_array_row)
        data_list_select = [data_list_row[i] for i in columns_id]

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

        if column_name == column_data:

            data_tmp = data_tmp / data_scale_factor

            data_valid_min = data_valid_range[0]
            data_valid_max = data_valid_range[1]

            if data_valid_min is not None:
                data_tmp[data_tmp < data_valid_min] = np.nan
            if data_valid_max is not None:
                data_tmp[data_tmp > data_valid_max] = np.nan

        data_workspace[column_name] = data_tmp

    data_df = pd.DataFrame(data_workspace, columns=columns_list_select)
    data_df = data_df.reset_index()
    data_df = data_df.set_index([column_idx])

    if data_type == 'accumulated':

        data_df_value = data_df.groupby(column_idx)[column_data].sum(min_count=data_min_count)
        data_df_time_start = data_df.groupby(column_idx)[column_time_start].min()
        data_df_time_end = data_df.groupby(column_idx)[column_time_end].max()

    elif data_type == 'instantaneous':

        if data_min_count == 1:
            data_df_value = data_df.groupby(column_idx)[column_data].last()
        else:
            data_df_value = data_df.groupby(column_idx)[column_data].mean()
        data_df_time_start = data_df.groupby(column_idx)[column_time_start].last()
        data_df_time_end = data_df.groupby(column_idx)[column_time_end].last()

    else:
        logging.error(' ===> Wrong definition of dataset type')
        raise NotImplemented('Dataset type not implemented yet')

    data_dict_dynamic = {column_idx: data_df_value.index, column_data: data_df_value.values,
                         column_time_start: data_df_time_start.values, column_time_end: data_df_time_end.values}

    data_df_dynamic = pd.DataFrame(data_dict_dynamic)
    data_df_dynamic = data_df_dynamic.reset_index()
    data_df_dynamic = data_df_dynamic.set_index(column_idx)

    data_df_static = data_df.drop(
        columns=[column_data, column_time_start, column_time_end]).groupby(column_idx).first()

    data_df_merged = pd.merge(data_df_static, data_df_dynamic, left_index=True, right_index=True)
    idx_df_merged = data_df_merged.index.values

    data_df_merged = data_df_merged.reset_index(drop=True)
    data_df_merged.insert(0, column_idx, idx_df_merged)
    data_df_merged = data_df_merged.drop(columns=['index_x', 'index_y'])

    if 'units' not in list(data_df_merged.columns):
        data_df_merged['units'] = data_units

    return data_df_merged
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get river station dataset
def get_data_rs(var_name, time_from, time_to, db_line_settings):

    # Define DB query
    db_query_registry = define_query_rs_registry(var_name)
    db_query_data = define_query_rs_data()

    # Open DB connection
    db_connection = pyodbc.connect(db_line_settings)
    db_cursor = db_connection.cursor()

    # Execute DB query
    db_cursor.execute(db_query_registry)
    # Get all registry
    db_registry = db_cursor.fetchall()

    # Execute DB query to data
    db_dataset = []
    for db_registry_id, db_registry_field in enumerate(db_registry):

        db_registry_code = np.int(db_registry_field[0])
        db_query_parameters = (time_from, time_to, db_registry_code)

        db_cursor.execute(db_query_data, db_query_parameters)
        db_point = db_cursor.fetchall()

        for db_point_step in db_point:
            if db_point_step:
                db_dataset.append(db_point_step)

    # Close DB connection
    db_connection.commit()

    return db_dataset

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define database settings
def get_db_credential(db_name="SIRMIP"):
    try:
        info = netrc.netrc()
        username, account, password = info.authenticators(db_name)
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
        logging.error(' ===> Server password is not defined')
        raise IOError('Parameter is not defined in the configuration file.')

    if server_mode:
        logging.info(' ---> Define server configuration ... OK. Set active mode')
        db_settings = 'DSN=Sirmip;DATABASE=' + server_name + ';PWD=' + server_password + ';UID=' + server_user
    else:
        logging.info(' ---> Define server configuration ... SKIPPED. Set inactive mode.')
        db_settings = None

    return db_settings
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to parse the query time
def parse_query_time(time_step, time_frequency='H', time_format="%Y-%m-%dT%H:%M:%S.%f"):

    time_to = time_step.strftime(time_format)[:-3]
    time_from = pd.date_range(end=time_step, freq=time_frequency, periods=2)[0].strftime(time_format)[:-3]

    return time_from, time_to

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define weather station query
def define_query_ws(var_name, time_from, time_end, flag_type='automatic'):

    if flag_type == 'automatic':

        db_query_data = "SELECT s.CodiceUnico AS CodiceSensore, st.CodiceUnico AS CodiceStazione, st.NomeAnnale AS NomeStazione, ds.DatoOrigine AS Pioggia_mm, "
        db_query_data += "geo.LongCentesimale AS Lon, geo.LatCentesimale AS Lat, geo.Quota AS Zm, sito.Regione, sito.Provincia, sito.Comune, s.BacinoAnnale, "
        db_query_data += "CONVERT(CHAR(19), ds.Data, 126 ) AS DataInizio, "
        db_query_data += "CONVERT(CHAR(19), ds.Data,   126 ) AS DataFine "
        db_query_data += "FROM DatoSensore AS ds INNER JOIN Sensore AS s ON ds.Sensore = s.CodiceUnico "
        db_query_data += "    INNER JOIN Stazione AS st ON s.Stazione = st.CodiceUnico "
        db_query_data += "    INNER JOIN Georeferenza AS geo ON st.Posizione = geo.IDGeo "
        db_query_data += "    INNER JOIN Sito ON st.SitoCollocazione = sito.IDSito "
        db_query_data += "WHERE "
        db_query_data += "    ( ( ds.Data BETWEEN '" + time_from + "' AND '" + time_end + "' ) AND NOT( ds.Data='" + time_from + "' ) ) "
        db_query_data += "    AND (s.TipoSensore='" + var_name + "' ) "
        db_query_data += "    AND NOT( ds.DatoOrigine IS NULL ) "
        db_query_data += "    AND NOT( geo.GaussBoagaEst IS NULL ) "
        db_query_data += "    AND NOT( geo.GaussBoagaNord IS NULL ) "
        db_query_data += "    AND NOT( geo.Quota IS NULL ) "
        db_query_data += "ORDER BY st.CodiceUnico, ds.Data ASC; "

    elif flag_type == 'mechanic':

        db_query_data = "SELECT s.CodiceUnico AS CodiceSensore, st.CodiceUnico AS CodiceStazione, st.NomeAnnale AS NomeStazione, ds.DatoOrigine AS Pioggia_mm, "
        db_query_data += "geo.LongCentesimale AS Lon, geo.LatCentesimale AS Lat, geo.Quota AS Zm, sito.Regione, sito.Provincia, sito.Comune, s.BacinoAnnale, "
        db_query_data += "CONVERT(CHAR(19), ds.Data, 126 ) AS DataInizio, "
        db_query_data += "CONVERT(CHAR(19), ds.Data,   126 ) AS DataFine "
        db_query_data += "FROM DatoSensore AS ds INNER JOIN Sensore AS s ON ds.Sensore = s.CodiceUnico "
        db_query_data += "    INNER JOIN Stazione AS st ON s.Stazione = st.CodiceUnico "
        db_query_data += "    INNER JOIN Georeferenza AS geo ON st.Posizione = geo.IDGeo "
        db_query_data += "    INNER JOIN Sito ON st.SitoCollocazione = sito.IDSito "
        db_query_data += "WHERE "
        db_query_data += "    ( ( ds.Data BETWEEN '" + time_from + "' AND '" + time_end + "' ) AND NOT( ds.Data='" + time_from + "' ) ) "
        db_query_data += "    AND (s.TipoSensore='" + var_name + "' ) "
        db_query_data += "    AND NOT( ds.DatoOrigine IS NULL ) "
        db_query_data += "    AND NOT( geo.GaussBoagaEst IS NULL ) "
        db_query_data += "    AND NOT( geo.GaussBoagaNord IS NULL ) "
        db_query_data += "    AND NOT( geo.Quota IS NULL ) "
        db_query_data += "ORDER BY st.CodiceUnico, ds.Data ASC; "

    else:
        logging.error(' ===> Weather station query definition failed')
        raise IOError('Flag is not allowed.')

    return db_query_data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define river station query data
def define_query_rs_data():

    # db_query_data =  "DECLARE @data1 datetime, @data2 datetime "
    # db_query_data += "set @data1='" + time_from + "' "
    # db_query_data += "set @data2='" + time_end + "' "
    # db_query_data += "EXECUTE Liv2QperiodoSensore @data1, @data2, "+str(iDBRegistry_AUT)+", 'o', 10000, 0;"
    db_query_data = "{CALL Liv2QperiodoSensore (?, ?, ?, 'o', 10000, 0)};"

    # NOTE:
    # 'o' = raw data; 'v' = validated data [v<o] --> USE 'o';
    # 10000 = max number of items;
    # 0 = not validated rating curve ; 1 = validated rating curve --> USE 0;

    return db_query_data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define river station query registry
def define_query_rs_registry(var_name):
    db_query_registry = "SELECT CodiceUnico from Sensore where TipoSensore='" + var_name + "';"
    return db_query_registry
# -------------------------------------------------------------------------------------
