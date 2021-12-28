"""
HyDE Processing Tool - GRISO interpolator
__date__ = '20210602'
__version__ = '2.1.0'
__author__ =
        'Flavio Pignone (flavio.pignone@cimafoundation.org',
        'Andrea Libertino (andrea.libertino@cimafoundation.org',
        'Fabio Delogu (fabio.delogu@cimafoundation.org',
__library__ = 'hyde'
General command line:
### python op_conditional_merging_GRISO.py -time "YYYY-MM-DD HH:MM"
Version(s):
20210602 (2.1.0) --> Added support for not-standard point files. Add netrc support for drops2. Bug fixes.
20210425 (2.0.0) --> Added support to point rain files (for FloodProofs compatibility)
                     Script structure fully revised and bug fixes
20210312 (1.5.0) --> Geotiff output implementation, script structure updates, various bug fixes and improvements
20200326 (1.0.0) --> Beta release for FloodProofs Bolivia
"""
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Complete library
import os
import logging
from os.path import join
from datetime import datetime, timedelta
from argparse import ArgumentParser
import numpy as np
import xarray as xr
import pandas as pd
import json
import time
import netrc
from copy import deepcopy

from src.hyde.driver.model.griso.drv_model_griso_exec import GrisoCorrel, GrisoInterpola, GrisoPreproc
from src.hyde.driver.model.griso.drv_model_griso_io import importDropsData, importTimeSeries, check_and_write_dataarray, write_raster, read_point_data
# -------------------------------------------------------------------------------------
# Script Main
def main():
    # -------------------------------------------------------------------------------------
    # Version and algorithm information
    alg_name = 'HyDE Processing Tool - GRISO Interpolator '
    alg_version = '2.1.0'
    alg_release = '2021-06-02'
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get algorithm settings
    alg_settings, alg_time = get_args()

    # Set algorithm settings
    data_settings = read_file_json(alg_settings)

    # Set algorithm logging
    os.makedirs(data_settings['data']['log']['folder'], exist_ok=True)
    set_logging(logger_file=join(data_settings['data']['log']['folder'], data_settings['data']['log']['filename']))
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get algorithm settings
    settings_file, alg_time = get_args()
    dateRun = datetime.strptime(alg_time, "%Y-%m-%d %H:%M")

    startRun = dateRun - timedelta(hours=data_settings['data']['dynamic']['time']['time_observed_period']-1)
    endRun = dateRun + timedelta(hours=data_settings['data']['dynamic']['time']['time_forecast_period'])

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Info algorithm
    logging.info(' ============================================================================ ')
    logging.info(' ==> START ... ')
    logging.info(' ')

    # Time algorithm information
    start_time = time.time()

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Check computation setting
    logging.info(' --> Check computational settings')

    # Gauge data sources
    computation_settings = [data_settings['algorithm']['flags']["sources"]['use_timeseries'],
                            data_settings['algorithm']['flags']["sources"]['use_drops2'],
                            data_settings['algorithm']['flags']["sources"]['use_point_data']]
    if len([x for x in computation_settings if x]) > 1:
        logging.error(' ----> ERROR! Please choose if use local data or download stations trough drops2!')
        raise ValueError("Data sources flags are mutually exclusive!")

    # Import data for drops and time series setup
    if data_settings['algorithm']['flags']["sources"]['use_drops2']:
        logging.info(' --> Station data source: drops2 database')
        drops_settings = data_settings['data']['dynamic']['source_stations']['drops2']
        if not all([drops_settings['DropsUser'], drops_settings['DropsPwd']]):
            netrc_handle = netrc.netrc()
            try:
                drops_settings['DropsUser'], _, drops_settings['DropsPwd'] = netrc_handle.authenticators(drops_settings['DropsAddress'])
            except:
                logging.error(' --> Netrc authentication file not found in home directory! Generate it or provide user and password in the settings!')
                raise FileNotFoundError(
                    'Verify that your .netrc file exists in the home directory and that it includes proper credentials!')
        dfData, dfStations = importDropsData(
            drops_settings=data_settings['data']['dynamic']['source_stations']['drops2'], start_time=startRun,
            end_time=dateRun, time_frequency=data_settings['data']['dynamic']['time']['time_frequency'])
    elif data_settings['algorithm']['flags']["sources"]['use_timeseries']:
        logging.info(' --> Station data source: station time series')
        dfData, dfStations = importTimeSeries(
            timeseries_settings=data_settings['data']['dynamic']['source_stations']['time_series'],
            start_time=startRun, end_time=dateRun,
            time_frequency=data_settings['data']['dynamic']['time']['time_frequency'])
    else:
        logging.info(' --> Station data source: station point files')

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    corrFin = data_settings['algorithm']['settings']['radius_GRISO_km'] * 2
    logging.info(' --> Final correlation: ' + str(corrFin) + ' km')

    # Loop across time steps
    for timeNow in pd.date_range(start=startRun, end=endRun, freq=data_settings['data']['dynamic']['time']['time_frequency']):
        logging.info(' ---> Computing time step ' + timeNow.strftime("%Y-%m-%d %H:00:00"))

        # Compute time step file names
        file_out_time_step = os.path.join(data_settings['data']['outcome']['folder'], data_settings['data']['outcome']['filename'])
        point_in_time_step = os.path.join(data_settings['data']['dynamic']['source_stations']['point_files']['folder'], data_settings['data']['dynamic']['source_stations']['point_files']['filename'])

        for i in data_settings['algorithm']['template']:
            file_out_time_step = file_out_time_step.replace("{" + i + "}", timeNow.strftime(data_settings['algorithm']['template'][i]))
            point_in_time_step = point_in_time_step.replace("{" + i + "}", timeNow.strftime(data_settings['algorithm']['template'][i]))

        if os.path.isfile(file_out_time_step) or os.path.isfile(file_out_time_step + '.gz'):
            if data_settings['algorithm']['flags']['overwrite_existing']:
                pass
            else:
                logging.info(' ---> Time step ' + timeNow.strftime("%Y-%m-%d %H:00:00") + ' already exist, skipping...')
                continue

        # Make output dir
        os.makedirs(os.path.dirname(file_out_time_step), exist_ok=True)

        logging.info(' ---> Import grid data...')
        #import grid
        grid_in = xr.open_rasterio(os.path.join(data_settings['data']['static']['folder'],data_settings['data']['static']['filename']))
        grid_in = grid_in.rename({'x':'lon', 'y':'lat'})
        logging.info(' ---> Import grid data...DONE')

        # Import point gauge data for point_data setup
        try:
            if data_settings['algorithm']['flags']["sources"]['use_point_data']:
                logging.info(' ----> Load time step point data ...')
                if data_settings['algorithm']['flags']["sources"]['non_standard_tab_fields']:
                    fields_dict = data_settings['data']['dynamic']['source_stations']['point_files']['non_standard_tab_fields']
                    dfStations, data = read_point_data(point_in_time_step, st_code=fields_dict["station_code"], st_name=fields_dict["station_name"], st_lon=fields_dict["longitude"],
                                                       st_lat=fields_dict["latitude"], st_data=fields_dict["data"])
                else:
                    dfStations, data = read_point_data(point_in_time_step, st_code='code', st_name='name', st_lon='longitude', st_lat='latitude', st_data='data')
            else:
                data = dfData.loc[timeNow.strftime("%Y-%m-%d %H:00:00")].values
                if len(data) == 0:
                    raise ValueError
        except (FileNotFoundError, ValueError) as err:
        # If no time step available skip
            logging.warning(' ----> WARNING! No station data available for time step ' + timeNow.strftime("%Y-%m-%d %H:00:00"))
            logging.warning(' ----> Skip time step' + timeNow.strftime("%Y-%m-%d %H:00:00"))
            continue

        if not data_settings['algorithm']['flags']["sources"]['use_point_data']:
            # Check if station data with nan values are present and, in the case, remove station from Station dataframe
            # (only if not point data are used, in this case, no further cleaning is needed)
            logging.info(' ----> Check null values for time step ...')
            avail_time_step = len(dfData.columns[~np.isnan(data)])
            logging.info(' ----> Available data for the time step ...' + str(avail_time_step))
            dfStations_available = dfStations.loc[dfData.columns[~np.isnan(data)]]
            data = data[~np.isnan(data)]
        else:
            dfStations_available = deepcopy(dfStations)

        # Data preprocessing for GRISO
        logging.info(' ---> GRISO: Data preprocessing...')
        point_data, a2dPosizioni, grid_rain, grid, passoKm = GrisoPreproc(corrFin,dfStations_available.lon.astype(np.float),dfStations_available.lat.values.astype(np.float), data, Grid=grid_in)

        logging.info(' ---> GRISO: Data preprocessing... DONE')

        # Calculate GRISO correlation features
        logging.info(' ---> GRISO: Calculate correlation...')
        correl_features = GrisoCorrel(point_data["rPluvio"], point_data["cPluvio"], corrFin, grid_rain, passoKm,
                                      a2dPosizioni, point_data["gauge_value"], corr_type= 'fixed')

        logging.info(' ---> GRISO: Data preprocessing...DONE')

        # GRISO interpolation
        logging.info(' ---> GRISO: Observed data interpolation...')
        griso_obs = GrisoInterpola(point_data["rPluvio"], point_data["cPluvio"], point_data["gauge_value"],
                                   correl_features)
        logging.info(' ---> GRISO: Observed data interpolation...DONE')

        if data_settings['data']['outcome']['format'].lower() == 'netcdf' or data_settings['data']['outcome']['format'].lower() == 'nc':

            logging.info(' ---> Saving outfile in netcdf format ' + os.path.basename(file_out_time_step))
            griso_out = check_and_write_dataarray(griso_obs, grid_in, 'precip', lat_var_name='lat', lon_var_name='lon')
            griso_out.to_netcdf(file_out_time_step)

        elif data_settings['data']['outcome']['format'].lower() == 'tif' or data_settings['data']['outcome']['format'].lower() == 'tiff' or data_settings['data']['outcome']['format'].lower() == 'gtiff':
            logging.info(' ---> Saving outfile in GTiff format ' + os.path.basename(file_out_time_step))
            write_raster(griso_obs, grid_in, file_out_time_step, driver='GTiff')
        else:
            logging.error('ERROR! Unknown or unsupported output format! ')
            raise ValueError("Supported output formats are netcdf and GTiff")

        if data_settings['algorithm']['flags']['compress_output']:
            os.system('gzip ' + file_out_time_step)

    # -------------------------------------------------------------------------------------
    # Info algorithm
    time_elapsed = round(time.time() - start_time, 1)

    logging.info(' ')
    logging.info(' ==> ' + alg_name + ' (Version: ' + alg_version + ' Release_Date: ' + alg_release + ')')
    logging.info(' ==> TIME ELAPSED: ' + str(time_elapsed) + ' seconds')
    logging.info(' ==> ... END')
    logging.info(' ==> Bye, Bye')
    logging.info(' ============================================================================ ')
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to read file json
def read_file_json(file_name):

    env_ws = {}
    for env_item, env_value in os.environ.items():
        env_ws[env_item] = env_value

    with open(file_name, "r") as file_handle:
        json_block = []
        for file_row in file_handle:

            for env_key, env_value in env_ws.items():
                env_tag = '$' + env_key
                if env_tag in file_row:
                    env_value = env_value.strip("'\\'")
                    file_row = file_row.replace(env_tag, env_value)
                    file_row = file_row.replace('//', '/')

            # Add the line to our JSON block
            json_block.append(file_row)

            # Check whether we closed our JSON block
            if file_row.startswith('}'):
                # Do something with the JSON dictionary
                json_dict = json.loads(''.join(json_block))
                # Start a new block
                json_block = []

    return json_dict
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to get script argument(s)
def get_args():
    parser_handle = ArgumentParser()
    parser_handle.add_argument('-settings_file', action="store", dest="alg_settings")
    parser_handle.add_argument('-time', action="store", dest="alg_time")
    parser_values = parser_handle.parse_args()

    if parser_values.alg_settings:
        alg_settings = parser_values.alg_settings
    else:
        alg_settings = 'configuration.json'

    if parser_values.alg_time:
        alg_time = parser_values.alg_time
    else:
        alg_time = None

    return alg_settings, alg_time
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to set logging information
def set_logging(logger_file='log.txt', logger_format=None):
    if logger_format is None:
        logger_format = '%(asctime)s %(name)-12s %(levelname)-8s ' \
                        '%(filename)s:[%(lineno)-6s - %(funcName)20s()] %(message)s'

    # Remove old logging file
    if os.path.exists(logger_file):
        os.remove(logger_file)

    # Set level of root debugger
    logging.root.setLevel(logging.INFO)

    # Open logging basic configuration
    logging.basicConfig(level=logging.INFO, format=logger_format, filename=logger_file, filemode='w')

    # Set logger handle
    logger_handle_1 = logging.FileHandler(logger_file, 'w')
    logger_handle_2 = logging.StreamHandler()
    # Set logger level
    logger_handle_1.setLevel(logging.INFO)
    logger_handle_2.setLevel(logging.INFO)
    # Set logger formatter
    logger_formatter = logging.Formatter(logger_format)
    logger_handle_1.setFormatter(logger_formatter)
    logger_handle_2.setFormatter(logger_formatter)
    # Add handle to logging
    logging.getLogger('').addHandler(logger_handle_1)
    logging.getLogger('').addHandler(logger_handle_2)
# -------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Call script from external library
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------

