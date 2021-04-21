"""
HyDE Processing Tool - Modified Conditional Merging with GRISO
__date__ = '20210425'
__version__ = '2.0.0'
__author__ =
        'Flavio Pignone (flavio.pignone@cimafoundation.org',
        'Andrea Libertino (andrea.libertino@cimafoundation.org',
        'Fabio Delogu (fabio.delogu@cimafoundation.org',
__library__ = 'hyde'
General command line:
### python op_conditional_merging_GRISO.py -time "YYYY-MM-DD HH:MM"
Version(s):
20210425 (2.0.0) --> Dynamic radius for GRISO implemented
                     Added support to point rain files (for FloodProofs compatibility)
                     Script structure fully revised and bug fixes
20210312 (1.5.0) --> Geotiff output implementation, script structure updates, various bug fixes and improvements
20201209 (1.2.0) --> Integrated with local station data configuration. Settings file implemented.
20200716 (1.1.0) --> Integrated with drops2 libraries. Updates and bug fixes.
20200326 (1.0.0) --> Beta release for FloodProofs Bolivia
"""
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Complete library
import os
import sys
import copy
import logging
from os.path import join
from datetime import datetime, timedelta
from argparse import ArgumentParser
import numpy as np
import xarray as xr
import pandas as pd
import json
import time
import matplotlib.pyplot as plt

from src.hyde.driver.model.griso.drv_model_griso_exec import GrisoCorrel, GrisoInterpola, GrisoPreproc
from src.hyde.driver.model.griso.drv_model_griso_io import importDropsData, importTimeSeries, check_and_write_dataarray, write_geotiff
# -------------------------------------------------------------------------------------
# Script Main
def main():

    # -------------------------------------------------------------------------------------
    # Version and algorithm information
    alg_name = 'HyDE Processing Tool - Modified Conditional Merging with GRISO '
    alg_version = '2.0.0'
    alg_release = '2021-04-25'
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

    # Griso correlation type
    computation_settings = [data_settings['algorithm']['flags']["mcm"]['fixed_correlation'], data_settings['algorithm']['flags']["mcm"]['dynamic_correlation']]
    if len([x for x in computation_settings if x]) > 1 or len([x for x in computation_settings if x]) == 0:
        logging.error(' ----> ERROR! Please choose if use fixed or dynamic correlation!')
        raise ValueError("Correlation type settings are mutually exclusive!")

    if data_settings['algorithm']['flags']["mcm"]['fixed_correlation']:
        corr_type = 'fixed'
    else:
        corr_type = 'dynamic'
    logging.info(' --> Griso correlation type: ' + corr_type)

    # Gauge data sources
    computation_settings = [data_settings['algorithm']['flags']["sources"]['use_timeseries'], data_settings['algorithm']['flags']["sources"]['use_drops2'], data_settings['algorithm']['flags']["sources"]['use_point_data']]
    if len([x for x in computation_settings if x]) > 1 or len([x for x in computation_settings if x]) == 0:
        logging.error(' ----> ERROR! Please choose if use local data or download stations trough drops2!')
        raise ValueError("Data sources flags are mutually exclusive!")

    # Import data for drops and time series setup
    if data_settings['algorithm']['flags']["sources"]['use_drops2']:
        logging.info(' --> Station data source: drops2 database')
        dfData, dfStations = importDropsData(drops_settings=data_settings['data']['dynamic']['source_stations']['drops2'], start_time=startRun, end_time=dateRun, time_frequency= data_settings['data']['dynamic']['time']['time_frequency'])
    elif data_settings['algorithm']['flags']["sources"]['use_timeseries']:
        logging.info(' --> Station data source: station time series')
        dfData, dfStations = importTimeSeries(timeseries_settings=data_settings['data']['dynamic']['source_stations']['time_series'], start_time=startRun, end_time=dateRun, time_frequency= data_settings['data']['dynamic']['time']['time_frequency'])
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
        ancillary_out_time_step = os.path.join(data_settings['data']['ancillary']['folder'], data_settings['data']['ancillary']['filename'])
        gridded_in_time_step = os.path.join(data_settings['data']['dynamic']['source_gridded']['folder'], data_settings['data']['dynamic']['source_gridded']['filename'])
        point_in_time_step = os.path.join(data_settings['data']['dynamic']['source_stations']['point_files']['folder'], data_settings['data']['dynamic']['source_stations']['point_files']['filename'])

        for i in data_settings['algorithm']['template']:
            file_out_time_step = file_out_time_step.replace("{" + i + "}", timeNow.strftime(data_settings['algorithm']['template'][i]))
            gridded_in_time_step = gridded_in_time_step.replace("{" + i + "}", timeNow.strftime(data_settings['algorithm']['template'][i]))
            ancillary_out_time_step = ancillary_out_time_step.replace("{" + i + "}", timeNow.strftime(data_settings['algorithm']['template'][i]))
            point_in_time_step = point_in_time_step.replace("{" + i + "}", timeNow.strftime(data_settings['algorithm']['template'][i]))

        if os.path.isfile(file_out_time_step) or os.path.isfile(file_out_time_step + '.gz'):
            if data_settings['algorithm']['flags']['overwrite_existing']:
                pass
            else:
                logging.info(' ---> Time step ' + timeNow.strftime("%Y-%m-%d %H:00:00") + ' already exist, skipping...')
                continue

        # Make output dir
        os.makedirs(os.path.dirname(file_out_time_step), exist_ok=True)

        # Import gridded source
        logging.info(' ----> Importing gridded source')
        try:
            if data_settings['algorithm']['flags']['compressed_gridded_input']:
                os.system('gunzip ' + gridded_in_time_step + '.gz')
            sat = xr.open_dataset(gridded_in_time_step, decode_times=False)
            if data_settings['algorithm']['flags']['compressed_gridded_input']:
                os.system('gzip ' + gridded_in_time_step)
        except:
            logging.error('----> ERROR! File ' + os.path.basename(gridded_in_time_step) + ' not found!')
            raise FileNotFoundError

        sat = sat.rename({data_settings['data']['dynamic']['source_gridded']['var_name']:'precip', data_settings['data']['dynamic']['source_gridded']['lon_name']:'lon', data_settings['data']['dynamic']['source_gridded']['lat_name']:'lat'})

        # Import point gauge data for point_data setup
        try:
            if data_settings['algorithm']['flags']["sources"]['use_point_data']:
                logging.info(' ----> Load time step point data ...')
                dfStations = pd.read_csv(point_in_time_step, usecols=['code','name','latitude','longitude'], index_col=['code']).rename(columns={'latitude':'lat','longitude':'lon'})
                data = pd.read_csv(point_in_time_step, usecols=['data']).squeeze()
            else:
                data = dfData.loc[timeNow.strftime("%Y-%m-%d %H:00:00")].values
                if len(data) == 0:
                    raise ValueError
        except:
        # If no data available for the actual time step just copy the input
            if not data_settings['algorithm']['flags']['raise_error_if_no_station_available']:
                logging.warning(' ----> WARNING! No station data available for time step ' + timeNow.strftime("%Y-%m-%d %H:00:00"))
                sat_out = copy.deepcopy(sat)
                sat_out.to_netcdf(file_out_time_step)
                continue
            else:
                logging.error(' ----> ERROR! No station data available for time step ' + timeNow.strftime("%Y-%m-%d %H:00:00"))
                raise FileNotFoundError

        # Extract gridded product values at point locations
        sat_gauge = np.array([sat['precip'].sel({'lon':Lon, 'lat':Lat}, method='nearest').values for Lon,Lat in zip(dfStations.lon.astype(np.float),dfStations.lat.astype(np.float))])

        ##  Save txt with station data - FOR DEBUGGING
        #os.makedirs(os.path.dirname(ancillary_out_time_step), exist_ok=True)
        #temp = np.vstack((dfStations.lon.astype(np.float),dfStations.lat.astype(np.float) , data)).T
        #np.savetxt(os.path.join(os.path.dirname(ancillary_out_time_step), 'rainfall_' + timeNow.strftime("%Y%m%d_%H%M" + '.txt')), temp)
        #temp2 = np.vstack((dfStations.lon.astype(np.float),dfStations.lat.astype(np.float) , np.squeeze(sat_gauge))).T
        #np.savetxt(os.path.join(os.path.dirname(ancillary_out_time_step), 'grid_value_' + timeNow.strftime("%Y%m%d_%H%M" + '.txt')), temp2)

        # Data preprocessing for GRISO
        logging.info(' ---> GRISO: Data preprocessing...')
        point_data, a2dPosizioni, grid_rain, grid, passoKm = GrisoPreproc(corrFin,dfStations.lon.astype(np.float),dfStations.lat.values.astype(np.float), data, sat_gauge, Grid=sat)
        logging.info(' ---> GRISO: Data preprocessing... DONE')

        # Calculate GRISO correlation features
        logging.info(' ---> GRISO: Calculate correlation...')
        correl_features = GrisoCorrel(point_data["rPluvio"], point_data["cPluvio"], corrFin, grid_rain, passoKm, a2dPosizioni, grid.shape[0], grid.shape[1], point_data["gauge_value"], corr_type= corr_type)
        logging.info(' ---> GRISO: Data preprocessing...DONE')

        # GRISO interpolator on observed data
        logging.info(' ---> GRISO: Observed data interpolation...')
        griso_obs = GrisoInterpola(point_data["rPluvio"], point_data["cPluvio"], point_data["gauge_value"], correl_features["CorrStimata"], corrFin, passoKm, correl_features["FinestraPosizioniExt"])

        griso_out = copy.deepcopy(sat)
        try:
            griso_out.precip.values = griso_obs
        except:
            griso_out.precip.values[0,:,:] = griso_obs

        # Save ancillary griso maps
        if data_settings['algorithm']['flags']['save_griso_ancillary_maps']:
            os.makedirs(os.path.dirname(ancillary_out_time_step), exist_ok=True)
            os.system('rm ' + ancillary_out_time_step)
            griso_out.to_netcdf(ancillary_out_time_step)
            if data_settings['algorithm']['flags']['compress_output']:
                os.system('gzip ' + ancillary_out_time_step)
        logging.info(' ---> GRISO: Data preprocessing...DONE')

        # GRISO interpolator on satellite data
        logging.info(' ---> GRISO: Gridded data interpolation...')
        griso_sat = GrisoInterpola(point_data["rPluvio"], point_data["cPluvio"], point_data["grid_value"], correl_features["CorrStimata"], corrFin, passoKm, correl_features["FinestraPosizioniExt"])
        logging.info(' ---> GRISO: Gridded data interpolation...DONE')

        ##  Save griso of gridded field - FOR DEBUGGING
        #os.makedirs(os.path.dirname(ancillary_out_time_step), exist_ok=True)
        #griso_sat_out = copy.deepcopy(sat)
        #griso_sat_out.precip.values[0, :, :] = griso_sat
        #griso_sat_out.to_netcdf(os.path.join(os.path.dirname(ancillary_out_time_step), 'griso_sat_' + timeNow.strftime("%Y%m%d_%H%M" + '.nc')))

        # Modified Conditional Merging
        logging.info(' ---> Perform Modified Conditional Merging...')
        error_sat = np.squeeze(grid_rain) - griso_sat

        conditioned_sat = griso_obs + error_sat
        conditioned_sat[conditioned_sat < 0] = 0
        mcm_out = check_and_write_dataarray(conditioned_sat, sat, var_name='precip', lat_var_name='lat',
                                  lon_var_name='lon')
        logging.info(' ---> Perform Modified Conditional Merging...DONE')

        # Plot output and save figure
        logging.info(' ---> Make and save figure...')
        if data_settings['algorithm']['flags']['save_figures']:
            os.makedirs(os.path.dirname(ancillary_out_time_step), exist_ok=True)

            fig, axs = plt.subplots(2,2)

            maxVal = np.max(np.concatenate((sat["precip"].values.flatten(),griso_out["precip"].values.flatten(), conditioned_sat.flatten(), data)))
            griso_out["precip"].plot(x="lon", y="lat", cmap='gray', ax=axs[0, 0], alpha=0.4, add_colorbar = False)
            OB = axs[0, 0].scatter(dfStations.lon.astype(np.float),dfStations.lat.astype(np.float) ,10, c=data, vmin=0, vmax=maxVal)
            axs[0, 0].set_title("OBS")
            fig.colorbar(OB, ax=axs[0, 0])

            SAT = sat["precip"].plot(x="lon", y="lat", ax=axs[0, 1], add_colorbar = False, vmin=0, vmax=maxVal)
            axs[0, 1].set_title("SAT")
            fig.colorbar(SAT, ax=axs[0, 1])

            GR = griso_out["precip"].plot(x="lon", y="lat", ax=axs[1, 0], add_colorbar = False, vmin=0, vmax=maxVal)
            axs[1, 0].set_title("GRISO")
            fig.colorbar(GR, ax=axs[1, 0])

            MCM = mcm_out.plot(x="lon", y="lat", ax=axs[1, 1], add_colorbar = False, vmin=0, vmax=maxVal)
            axs[1, 1].set_xlabel("longitude [degrees_east]")
            axs[1, 1].set_ylabel("latitude [degrees_north]")
            axs[1, 1].set_title("MCM")
            fig.colorbar(MCM, ax=axs[1, 1])

            plt.show(block=True)
            plt.suptitle(timeNow.strftime("%Y-%m-%d %H:%M"))

            plt.tight_layout()
            plt.savefig(os.path.join(os.path.dirname(ancillary_out_time_step), 'figure_mcm_' + timeNow.strftime("%Y%m%d_%H%M" + '.png')))
        logging.info(' ---> Make and save figure...DONE')

        # Save output
        logging.info(' ---> Save output map in ' + data_settings['data']['outcome'][
            'format'].lower() + ' format')

        if data_settings['data']['outcome']['format'].lower() == 'netcdf' or data_settings['data']['outcome'][
            'format'].lower() == 'nc':

            logging.info(' ---> Saving outfile in netcdf format ' + os.path.basename(file_out_time_step))
            mcm_out.to_netcdf(file_out_time_step)

        elif data_settings['data']['outcome']['format'].lower() == 'tif' or data_settings['data']['outcome'][
            'format'].lower() == 'tiff' or data_settings['data']['outcome']['format'].lower() == 'gtiff':
            logging.info(' ---> Saving outfile in GTiff format ' + os.path.basename(file_out_time_step))

            grid = xr.open_rasterio(gridded_in_time_step)
            write_geotiff(conditioned_sat, grid, file_out_time_step)

        else:
            logging.error('ERROR! Unknown or unsupported output format! ')
            raise ValueError("Supported output formats are netcdf and GTiff")

        if data_settings['algorithm']['flags']['compress_output']:
            os.system('gzip -f ' + file_out_time_step)

        logging.info(' ---> Saving outfile...DONE')

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

