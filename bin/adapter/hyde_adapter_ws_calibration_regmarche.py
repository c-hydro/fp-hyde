#!/usr/bin/python3

"""
HYDE Converting Tool - Calibration RegMarche Weather Stations

__date__ = '20191210'
__version__ = '1.0.0'
__author__ = 'Fabio Delogu (fabio.delogu@cimafoundation.org'
__library__ = 'HyDE'

General command line:
python3 hyde_adapter_ws_calibration_regmarche.py -settings_file configuration.json
"""

# -------------------------------------------------------------------------------------
# Complete library
import os
import re
import json
import logging
import time
import datetime
import pandas as pd

from argparse import ArgumentParser

import matplotlib.pylab as plt
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Algorithm information
alg_name = 'HYDE CONVERTING TOOL - CALIBRATION REG_MARCHE WEATHER STATIONS'
alg_version = '1.0.0'
alg_release = '2019-12-10'
# Algorithm parameter(s)
time_format = '%Y%m%d%H%M'
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Script Main
def main():

    # -------------------------------------------------------------------------------------
    # Get algorithm settings
    with open(getSettings(), "r") as file_handle:
        file_settings = json.load(file_handle)

    # Set algorithm logging
    makeFolder(file_settings['log']['folder'])
    setLogging(
        sLoggerFile=os.path.join(file_settings['log']['folder'], file_settings['log']['file']),
        sLoggerMsgFmt=file_settings['log']['format'])
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm
    logging.info(' ============================================================================ ')
    logging.info(' ==> ' + alg_name + ' (Version: ' + alg_version + ' Release_Date: ' + alg_release + ')')
    logging.info(' ==> START ... ')
    logging.info(' ')

    # Time algorithm information
    start_time = time.time()
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get variable information
    var_data = file_settings['variables']
    tags_format = file_settings['tags']

    # Iterate over variable(s)
    for var_name, var_info in var_data.items():

        # var_name = 'rain
        # var_name = 'air_temperature'
        # var_name = 'relative_humidity'
        # var_name = 'incoming_radiation'
        # var_name = 'wind_speed'
        var_name = 'river_discharge'
        var_info = var_data[var_name]

        logging.info(' ===> Variable: ' + var_name + ' ... ')

        var_static_info = var_info['data_static']
        var_dynamic_in_info = var_info['data_dynamic_input']
        var_dynamic_out_info = var_info['data_dynamic_output']
        var_units = var_info['data_units']
        var_type = var_info['data_type']
        var_updating = var_info["data_updating"]
        var_format = var_info["data_format"]

        var_registry = parserRegistry(os.path.join(var_static_info['folder'][0], var_static_info['file'][0]),
                                      columns_name=var_static_info['fields_name'],
                                      columns_drop=var_static_info['fields_drop'])

        var_dynamic_in_folder = var_dynamic_in_info['folder']
        var_dynamic_in_file = var_dynamic_in_info['file']

        if var_dynamic_in_folder.__len__() < var_dynamic_in_file.__len__():
            var_dynamic_in_folder = var_dynamic_in_folder * var_dynamic_in_file.__len__()

        for var_step_folder, var_step_file in zip(var_dynamic_in_folder, var_dynamic_in_file):

            var_freq_in = var_dynamic_in_info['frequency']
            var_freq_out = var_dynamic_out_info['frequency']

            logging.info(' ====> File ' + var_step_file + ' ... ')

            if var_type == 'accumulated':
                var_step_df = parserData_Accumulated(os.path.join(var_step_folder, var_step_file), var_units=var_units)
            elif var_type == 'istantaneous':
                var_step_df = parserData_Istantaneous(os.path.join(var_step_folder, var_step_file), var_units=var_units)
            elif var_type == 'streamflow':
                var_step_df = parserData_StreamFlow(os.path.join(var_step_folder, var_step_file), var_units=var_units,
                                                    column_index='code')
            else:
                raise NotImplementedError

            if var_format == 'point':

                date_start = var_step_df.index.min()
                date_end = var_step_df.index.max()

                date_range = pd.date_range(start=date_start, end=date_end, freq=var_freq_in)
                date_range = date_range.round(freq=var_freq_out)
                date_range = date_range.unique()

                # Iterate over date step(s)
                for date_step in date_range:

                    #date_step = pd.Timestamp('2015-03-29 02:00:00')

                    logging.info(' =====> TimeStep: ' + str(date_step) + ' ... ')

                    try:

                        tags_filling = {'date_time': date_step.to_pydatetime(), 'date_sub_path': date_step.to_pydatetime()}

                        file_save_fields = var_dynamic_out_info['fields_name']
                        file_save_raw = os.path.join(var_dynamic_out_info['folder'][0], var_dynamic_out_info['file'][0])
                        file_save_def = fill_tags2string(file_save_raw, tags_format, tags_filling)

                        if not os.path.exists(file_save_def) or var_updating is True:

                            var_step_df_sub = var_step_df.loc[date_step]

                            if isinstance(var_step_df_sub, pd.Series):
                                var_step_df_merge = pd.merge(var_registry, pd.DataFrame(
                                    data=[var_step_df_sub.values],
                                    columns=var_step_df_sub.index), on='code')
                            elif isinstance(var_step_df_sub, pd.DataFrame):
                                var_step_df_merge = pd.merge(var_registry, var_step_df_sub, on='code')
                            else:
                                raise NotImplementedError

                            makeFolder(os.path.split(file_save_def)[0])

                            var_step_df_sel = var_step_df_merge.reindex(columns=file_save_fields)

                            var_step_df_sel.to_csv(file_save_def, sep=',', index=False, date_format='%Y-%m-%d %H:%M:%S')

                            logging.info(' =====> TimeStep: ' + str(date_step) + ' ... DONE!')

                        else:

                            logging.info(' =====> TimeStep: ' + str(date_step) +
                                         ' ... SKIPPED! Data previously computed!')

                    except Exception as exp:

                        logging.info(' =====> TimeStep: ' + str(date_step) + ' ... FAILED!')
                        logging.warning(' Exception arisen in ' + str(exp))

            else:

                for index_registry, row_registry in var_registry.reset_index().iterrows():

                    registry_name = row_registry['name']
                    registry_code = row_registry['code']

                    logging.info(' =====> Section: ' + registry_name + ' ... ')

                    var_step_df_sub = var_step_df.loc[registry_code]

                    date_start = var_step_df_sub.index.min()
                    date_end = var_step_df_sub.index.max()

                    date_range = pd.date_range(start=date_start, end=date_end, freq=var_freq_in)
                    date_range = date_range.round(freq=var_freq_out)
                    date_range = date_range.unique()

                    tags_filling = {'section_name': registry_name}

                    file_save_fields = var_dynamic_out_info['fields_name']
                    file_save_raw = os.path.join(var_dynamic_out_info['folder'][0], var_dynamic_out_info['file'][0])
                    file_save_def = fill_tags2string(file_save_raw, tags_format, tags_filling)

                    if not os.path.exists(file_save_def) or var_updating is True:

                        makeFolder(os.path.split(file_save_def)[0])

                        var_step_df_sel = var_step_df_sub.reindex(columns=file_save_fields)

                        var_step_df_sel.reset_index(inplace=True)
                        var_step_df_sel.set_index('time_end', inplace=True)
                        var_step_df_sel.index.name = 'time_end'

                        var_step_df_sel.to_csv(file_save_def, sep=',', index=False)

                        # debug - plot figure
                        fig = plt.figure()
                        var_step_df_sel['data'].plot(label='discharge', color='#0000FF', lw=1, linestyle='--') #, marker='o', ms=0.5)
                        plt.legend()
                        plt.ylabel("observed discharge [m^3/s]")
                        plt.xlabel("time [hour]")
                        plt.ylim(0, 15)
                        plt.grid()
                        plt.title('section: ' + registry_name)
                        filename = os.path.join(os.path.split(file_save_def)[0], "discharge_" + registry_name + ".tiff")
                        fig.savefig(filename, dpi=120)
                        plt.show()

                        logging.info(' =====> Section: ' + registry_name + ' ... DONE')

                    else:

                        logging.info(' =====> Section: ' + registry_name +
                                     ' ... SKIPPED! Data previously computed!')

            logging.info(' ====> File ' + var_step_file + ' ... DONE')

        logging.info(' ===> Variable: ' + var_name + ' ... DONE')

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm
    elapsed_time = round(time.time() - start_time, 1)

    logging.info(' ')
    logging.info(' ==> ' + alg_name + ' (Version: ' + alg_version + ' Release_Date: ' + alg_release + ')')
    logging.info(' ==> TIME ELAPSED: ' + str(elapsed_time) + ' seconds')
    logging.info(' ==> ... END')
    logging.info(' ==> Bye, Bye')
    logging.info(' ============================================================================ ')
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to parser file registry
def parserRegistry(file_registry, column_index='code', column_section_name='name',
                   columns_name=None, columns_drop=None, column_sep=',', skip_rows=1):

    if columns_name is None:
        columns_name = ['code', 'type', 'gaussboaga_east', 'gaussboaga_nord',
                        'lon_sexagesimal', 'lat_sexagesimal',
                        'longitude', 'latitude', 'altitude', 'name', 'loc_type_1', 'loc_type_2', 'loc_type_3',
                        'reference']

    if columns_drop is None:
        columns_drop = ['gaussboaga_east', 'gaussboaga_nord', 'lon_sexagesimal', 'lat_sexagesimal',
                        'loc_type_1', 'loc_type_2', 'loc_type_3', 'reference']

    file_data = pd.read_csv(file_registry, encoding='unicode_escape', skiprows=skip_rows, sep=column_sep,
                            names=columns_name)

    file_data.reset_index(inplace=True)
    file_data.set_index(column_index, inplace=True)
    file_data.index.name = column_index

    file_data = file_data.drop(columns_drop, axis=1)

    file_data[column_section_name] = file_data[column_section_name].apply(
        lambda x: re.sub('\W+', '', x.strip().lower()))

    return file_data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to parse data in accumulated format
def parserData_Accumulated(var_file, var_units=None, column_index='time',
               column_time_start='time_start', column_time_end='time_end',
               columns_name=None, columns_drop=None,
               columns_time_start=None, columns_time_end=None, column_sep=',', skip_rows=2):

    if var_units is None:
        var_units = ''

    if columns_name is None:
        columns_name = ['code',
                        'year_start', 'month_start', 'day_start', 'hour_start', 'minute_start',
                        'year_end', 'month_end', 'day_end', 'hour_end', 'minute_end',
                        'data', 'n', 'quality', 'snow_flag', 'type']

    if columns_drop is None:
        columns_drop = ['year_start', 'month_start', 'day_start', 'hour_start', 'minute_start',
                        'year_end', 'month_end', 'day_end', 'hour_end', 'minute_end',
                        'n', 'type']

    if columns_time_start is None:
        columns_time_start = ['year_start', 'month_start', 'day_start', 'hour_start', 'minute_start']

    if columns_time_end is None:
        columns_time_end = ['year_end', 'month_end', 'day_end', 'hour_end', 'minute_end']

    var_data = pd.read_csv(var_file, sep=column_sep,  skiprows=skip_rows, names=columns_name)

    var_data[column_time_end] = pd.to_datetime(
        dict(year=var_data[columns_time_end[0]],
             month=var_data[columns_time_end[1]], day=var_data[columns_time_end[2]],
             hour=var_data[columns_time_end[3]], minute=var_data[columns_time_end[4]]))

    var_data[column_time_start] = pd.to_datetime(
        dict(year=var_data[columns_time_start[0]],
             month=var_data[columns_time_start[1]], day=var_data[columns_time_start[2]],
             hour=var_data[columns_time_start[3]], minute=var_data[columns_time_start[4]]))

    var_data[column_index] = pd.to_datetime(
        dict(year=var_data[columns_time_end[0]],
             month=var_data[columns_time_end[1]], day=var_data[columns_time_end[2]],
             hour=var_data[columns_time_end[3]], minute=var_data[columns_time_end[4]]))

    var_data.reset_index(inplace=True)
    var_data.set_index(column_index, inplace=True)
    var_data.index.name = column_index

    var_data = var_data.drop(columns_drop, axis=1)

    var_data['units'] = var_units

    return var_data

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to parse data in instantaneous format
def parserData_Istantaneous(var_file, var_units=None, column_index='time',
               column_time_start='time_start', column_time_end='time_end',
               columns_name=None, columns_drop=None,
               columns_time_start=None, columns_time_end=None, column_sep=' ', skip_rows=2):

    if var_units is None:
        var_units = ''

    if columns_name is None:
        columns_name = ['code', 'time_yyyymmdd', 'time_hhmmss', 'data']

    if columns_drop is None:
        columns_drop = ['time_yyyymmdd', 'time_hhmmss']

    if columns_time_start is None:
        columns_time_start = ['time_yyyymmdd', 'time_hhmmss']

    if columns_time_end is None:
        columns_time_end = ['time_yyyymmdd', 'time_hhmmss']

    var_data = pd.read_csv(var_file, sep=column_sep,  skiprows=skip_rows, names=columns_name)
    var_data.reset_index(inplace=True)
    var_data = var_data.dropna(axis=1, how='all')
    var_data.columns = columns_name

    var_data[column_time_end] = pd.to_datetime(
        var_data[columns_time_end[0]] + var_data[columns_time_end[1]], format='%Y-%m-%d%H:%M:%S.000')

    var_data[column_time_start] = pd.to_datetime(
        var_data[columns_time_start[0]] + var_data[columns_time_start[1]], format='%Y-%m-%d%H:%M:%S.000')

    var_data[column_index] = pd.to_datetime(
        var_data[columns_time_end[0]] + var_data[columns_time_end[1]], format='%Y-%m-%d%H:%M:%S.000')

    var_data.set_index(column_index, inplace=True)
    var_data.index.name = column_index

    var_data = var_data.drop(columns_drop, axis=1)

    var_data['units'] = var_units

    return var_data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to parser file data
def parserData_StreamFlow(var_file, var_units=None, column_index='time',
               column_time_start='time_start', column_time_end='time_end',
               columns_name=None, columns_drop=None,
               columns_time_start=None, columns_time_end=None, column_sep=',', skip_rows=2):

    if var_units is None:
        var_units = ''

    if column_index == 'time':
        if columns_name is None:
            columns_name = ['code',
                            'year', 'month', 'day', 'hour', 'minute',
                            'water_level_raw', 'data', 'water_level_interp', 'type']
    elif column_index == 'code':
        if columns_name is None:
            columns_name = ['id',
                            'year', 'month', 'day', 'hour', 'minute',
                            'water_level_raw', 'data', 'water_level_interp', 'type']
    else:
        raise NotImplementedError

    if columns_drop is None:
        columns_drop = ['year', 'month', 'day', 'hour', 'minute', 'type', 'water_level_raw', 'water_level_interp']

    if columns_time_start is None:
        columns_time_start = ['year', 'month', 'day', 'hour', 'minute']

    if columns_time_end is None:
        columns_time_end = ['year', 'month', 'day', 'hour', 'minute']

    var_data = pd.read_csv(var_file, sep=column_sep,  skiprows=skip_rows, names=columns_name)

    var_data[column_time_end] = pd.to_datetime(
        dict(year=var_data[columns_time_end[0]],
             month=var_data[columns_time_end[1]], day=var_data[columns_time_end[2]],
             hour=var_data[columns_time_end[3]], minute=var_data[columns_time_end[4]]))

    var_data[column_time_start] = pd.to_datetime(
        dict(year=var_data[columns_time_start[0]],
             month=var_data[columns_time_start[1]], day=var_data[columns_time_start[2]],
             hour=var_data[columns_time_start[3]], minute=var_data[columns_time_start[4]]))

    if column_index == 'time':
        var_data[column_index] = pd.to_datetime(
            dict(year=var_data[columns_time_end[0]],
                 month=var_data[columns_time_end[1]], day=var_data[columns_time_end[2]],
                 hour=var_data[columns_time_end[3]], minute=var_data[columns_time_end[4]]))
    elif column_index == 'code':
        var_data[column_index] = var_data['id']
    else:
        raise NotImplementedError

    var_data.reset_index(inplace=True)
    var_data.set_index(column_index, inplace=True)
    var_data.index.name = column_index

    var_data = var_data.drop(columns_drop, axis=1)

    var_data['units'] = var_units

    return var_data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to add time in a unfilled string (path or filename)
def fill_tags2string(string_raw, tags_format=None, tags_filling=None):

    apply_tags = False
    if string_raw is not None:
        for tag in list(tags_format.keys()):
            if tag in string_raw:
                apply_tags = True
                break

    if apply_tags:
        string_filled = string_raw.format(**tags_format)

        for tag_format_name, tag_format_value in list(tags_format.items()):

            if tag_format_name in list(tags_filling.keys()):
                tag_filling_value = tags_filling[tag_format_name]
                if tag_filling_value is not None:

                    if isinstance(tag_filling_value, datetime.datetime):
                        tag_filling_value = tag_filling_value.strftime(tag_format_value)

                    string_filled = string_filled.replace(tag_format_value, tag_filling_value)

        string_filled = string_filled.replace('//', '/')
        return string_filled
    else:
        return string_raw
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to make folder
def makeFolder(sPathFolder):
    if not os.path.exists(sPathFolder):
        os.makedirs(sPathFolder)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get script argument(s)
def getSettings():
    oParser = ArgumentParser()
    oParser.add_argument('-settings_file', action="store", dest="sFileSettings")
    oParserValue = oParser.parse_args()

    if oParserValue.sFileSettings:
        sFileSettings = oParserValue.sFileSettings
    else:
        sFileSettings = 'configuration.json'

    return sFileSettings
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to set logging information
def setLogging(sLoggerFile='log.txt',
               sLoggerMsgFmt=None):

    if sLoggerMsgFmt is None:
        sLoggerMsgFmt = '%(asctime)s %(name)-12s %(levelname)-8s ' \
                        '%(filename)s:[%(lineno)-6s - %(funcName)20s()] %(message)s'

    # Remove old logging file
    if os.path.exists(sLoggerFile):
        os.remove(sLoggerFile)

    # Open logging basic configuration
    logging.basicConfig(level=logging.INFO,
                        format=sLoggerMsgFmt,
                        filename=sLoggerFile,
                        filemode='w')

    # Set logger handle
    oLogHandle_1 = logging.FileHandler(sLoggerFile, 'w')
    oLogHandle_2 = logging.StreamHandler()
    # Set logger level
    oLogHandle_1.setLevel(logging.DEBUG)
    oLogHandle_2.setLevel(logging.DEBUG)
    # Set logger formatter
    oLogFormatter = logging.Formatter(sLoggerMsgFmt)
    oLogHandle_1.setFormatter(oLogFormatter)
    oLogHandle_2.setFormatter(oLogFormatter)
    # Add handle to logging
    logging.getLogger('').addHandler(oLogHandle_1)
    logging.getLogger('').addHandler(oLogHandle_2)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Call script from external library
if __name__ == "__main__":
    main()
# -------------------------------------------------------------------------------------
