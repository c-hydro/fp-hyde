"""
Library Features:

Name:          drv_model_griso_generic
Author(s):     Andrea Libertino (andrea.libertino@cimafoundation.org)
Date:          '20210311'
Version:       '1.0.0'
"""
# -------------------------------------------------------------------------------------
import logging
import pandas as pd
import numpy as np
import sys
import os
import xarray as xr
import rasterio as rio

# -------------------------------------------------------------------------------------
# download data from drops2
def importDropsData(drops_settings, start_time, end_time, time_frequency):
    from drops2 import sensors
    from drops2.utils import DropsCredentials

    # Initialize drops
    logging.info(' ---> Drops2 mode selected: connecting to the server...')
    DropsCredentials.set(drops_settings['DropsAddress'], drops_settings['DropsUser'], drops_settings['DropsPwd'])

    # download_OBS_DROPS2
    logging.info(' ---> Getting stations list from server')
    sensors_list_P = sensors.get_sensor_list(drops_settings['DropsSensor'], geo_win=(
    drops_settings['lon_left'], drops_settings['lon_right'], drops_settings['lat_bottom'], drops_settings['lat_top']),
                                             group=drops_settings['DropsGroup'])
    dfStations = pd.DataFrame(np.array([(p.name, p.lat, p.lng) for p in sensors_list_P]),
                              index=np.array([(p.id) for p in sensors_list_P]), columns=['name', 'lat', 'lon'])
    logging.info(' ---> Found ' + str(len(dfStations.index)) + ' stations')

    logging.info(' ---> Getting stations data from server')
    dfData = sensors.get_sensor_data(drops_settings['DropsSensor'], sensors_list_P, start_time.strftime("%Y%m%d%H%M"),
                                     (end_time + pd.Timedelta('1H')).strftime("%Y%m%d%H%M"), as_pandas=True)

    #columnNames = [dfStations.loc[cd]['name'] for cd in dfData.columns]
    dfData.columns = dfData.columns #[columnNames]

    # Shift data back of 1 time step for referring it to the beginning of the time step
    dfData = dfData.shift(-1)

    logging.info(' ---> Checking for empty or not-valid series')
    # Check empty stations
    dfData.values[dfData.values < 0] = np.nan
    dfData = dfData.dropna(axis='columns', how='all')
    logging.info(' ---> Removed ' + str(len(dfStations.index) - len(dfData.columns)) + ' for only non-valid data')

    logging.info(' ---> Removing listed offline stations')
    # Check provided broken stations
    dfData = dfData.drop(drops_settings['codes_not_valid'], axis='columns', errors='ignore')
    logging.info(' ---> Removed ' + str(len(drops_settings['codes_not_valid'])) + ' offline stations')

    dfStations = dfStations.loc[dfStations.index.isin(dfData.columns.values)]

    logging.info(' ---> Resampling at hourly scale')
    dfData = dfData.resample(time_frequency).sum()

    dfData = dfData.dropna(axis='rows', how='all')

    return dfData, dfStations

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# import timeseries data
def importTimeSeries(timeseries_settings, start_time, end_time, time_frequency):
    logging.info(' ---> Local data mode selected: loading data...')

    dfStations = pd.read_csv(os.path.join(timeseries_settings['coordinates_file']['folder'],timeseries_settings['coordinates_file']['filename']), delimiter=timeseries_settings['coordinates_file']['delimiter'], header=None, usecols=[timeseries_settings['coordinates_file']['station_name_col'],timeseries_settings['coordinates_file']['lat_col'],timeseries_settings['coordinates_file']['lon_col']], names=['name', 'lat', 'lon'])
    dfData = pd.DataFrame(
        index=pd.date_range(start_time, end_time, freq=time_frequency),
        columns=dfStations['name'])

    for station_name in dfStations['name']:
        try:
            data_name = os.path.join(timeseries_settings['data_files']['folder'],
                                     timeseries_settings['data_files']['filename'].format(station_name=station_name))
            dfData[station_name] = pd.read_csv(data_name, delimiter=timeseries_settings['data_files']['delimiter'], header=None, usecols=[timeseries_settings['data_files']['datetime_col'],timeseries_settings['data_files']['data_col']], parse_dates=True,
                                               index_col=timeseries_settings['data_files']['datetime_col']).resample(
                time_frequency).sum()
        except:
            logging.warning(' ---> WARINING! Station ' + station_name + ' not found!')
            continue

    logging.info(' ---> Checking for empty or not-valid series')
    # Check empty stations
    dfData.values[dfData.values < 0] = np.nan
    dfData = dfData.dropna(axis='columns', how='all')
    logging.info(' ---> Removed ' + str(len(dfStations.index) - len(dfData.columns)) + ' for only non-valid data')

    dfStations = dfStations.loc[dfStations['name'].isin([stat for stat in dfData.columns.values])]

    if len(dfStations['name']) == 0:
        logging.warning('----> WARNING! There are not enough data for merging')

    return dfData, dfStations

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
def check_and_write_netcdf(variable, grid, file_out, var_name='precip', lat_var_name='lat', lon_var_name='lon'):
    Lat = grid[lat_var_name]
    Lon = grid[lon_var_name]

    if float(Lat[-1]) < float(Lat[0]):
        Lat = np.sort(Lat)
        variable = np.flipud(variable)

    var_out = xr.DataArray(data=variable, dims=["south_north", "east_weast"],
                           coords=dict(lat=("south_north", Lat), lon=("east_weast", Lon)), name=var_name)

    var_out.to_netcdf(file_out)

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------

def write_geotiff(variable, grid, file_out):
    with rio.open(file_out, 'w', driver='GTiff',
                  height=variable.shape[0], width=variable.shape[1], count=1, dtype=variable.dtype,
                  crs='+proj=latlong', transform=grid.transform) as dst:
        dst.write(variable, 1)