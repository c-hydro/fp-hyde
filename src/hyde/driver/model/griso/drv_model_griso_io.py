"""
Library Features:

Name:          drv_model_griso_generic
Author(s):     Andrea Libertino (andrea.libertino@cimafoundation.org)
               Flavio Pignone (flavio.pignone@cimafoundation.org)
Date:          '20211026'
Version:       '2.0.0'
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
    sensors_list_P = sensors.get_sensor_list(drops_settings['DropsSensor'], geo_win=(drops_settings['lon_left'], drops_settings['lat_bottom'], drops_settings['lon_right'], drops_settings['lat_top']) ,group=drops_settings['DropsGroup']) #drops_settings['lon_left'], drops_settings['lat_bottom'], drops_settings['lon_right'], drops_settings['lat_top'])
    dfStations = pd.DataFrame(np.array([(p.name, p.lat, p.lng) for p in sensors_list_P]),
                              index=np.array([(p.id) for p in sensors_list_P]), columns=['name', 'lat', 'lon'])
    logging.info(' ---> Found ' + str(len(dfStations.index)) + ' stations')

    logging.info(' ---> Getting stations data from server')
    dfData = sensors.get_sensor_data(drops_settings['DropsSensor'], sensors_list_P, start_time.strftime("%Y%m%d%H%M"),
                                     (end_time + pd.Timedelta('1H')).strftime("%Y%m%d%H%M"), aggr_time=3600, as_pandas=True)

    # columnNames = [dfStations.loc[cd]['name'] for cd in dfData.columns]
    # dfData.columns = dfData.columns[columnNames]

    # Shift data back of 1 milliseconds for cumulating the hourly value to the previous time step at the hourly scale
    # e.g. the rain of the 4:00 time step need to be cumulated as it was 3:59:59 and afrer I should
    # assign the label to the right side of the interval (4:00)
    ######## dfData = dfData.set_index(dfData.index-pd.Timedelta(milliseconds=1))

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
    ######## dfData = dfData.resample(time_frequency, label='right').sum()

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
# Check dataarray orientation and eventually flip it

def check_and_write_dataarray(variable, grid, var_name='precip', lat_var_name='lat', lon_var_name='lon'):
    Lat = grid[lat_var_name]
    Lon = grid[lon_var_name]

    if float(Lat[-1]) < float(Lat[0]):
        Lat = np.sort(Lat)
        variable = np.flipud(variable)

    var_out = xr.DataArray(data=variable, dims=["south_north", "east_weast"],
                           coords=dict(lat=("south_north", Lat), lon=("east_weast", Lon.values)) , name=var_name)

    return var_out

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Write raster format

def write_raster(variable, grid, file_out, driver='GTiff'):
    variable = variable.astype(np.float32)
    with rio.open(file_out, 'w', driver=driver,
                  height=variable.shape[0], width=variable.shape[1], count=1, dtype=variable.dtype,
                  crs='+proj=latlong', transform=grid.transform, compress='DEFLATE') as dst:
        dst.write(variable, 1)

# --------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to create a data array
def create_darray_3d(data, time, geo_x, geo_y, geo_1d=True,
                     coord_name_x='west_east', coord_name_y='south_north', coord_name_time='time',
                     dim_name_x='west_east', dim_name_y='south_north', dim_name_time='time',
                     dims_order=None):

    if dims_order is None:
        dims_order = [dim_name_y, dim_name_x, dim_name_time]

    if geo_1d:
        if geo_x.shape.__len__() == 2:
            geo_x = geo_x[0, :]
        if geo_y.shape.__len__() == 2:
            geo_y = geo_y[:, 0]

        data_da = xr.DataArray(data,
                               dims=dims_order,
                               coords={coord_name_time: (dim_name_time, time),
                                       coord_name_x: (dim_name_x, geo_x),
                                       coord_name_y: (dim_name_y, geo_y)})
    else:
        logging.error(' ===> Longitude and Latitude must be 1d')
        raise IOError('Variable shape is not valid')

    return data_da
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to read tiff file
def read_file_tiff(file_name, var_name='variable', var_nodata=-9999.0, time=None,
                   coord_name_x='west_east', coord_name_y='south_north',
                   dim_name_x='west_east', dim_name_y='south_north'):

    with rio.open(file_name) as dset_in:
        meta = dset_in.profile
        bounds = dset_in.bounds
        res = dset_in.res
        transform = dset_in.transform
        nodata = dset_in.nodata
        dtype = dset_in.dtypes
        data = dset_in.read()
        values = data[0, :, :]

    decimal_round = 7

    center_right = bounds.right - (res[0] / 2)
    center_left = bounds.left + (res[0] / 2)
    center_top = bounds.top - (res[1] / 2)
    center_bottom = bounds.bottom + (res[1] / 2)

    lon = np.arange(center_left, center_right + np.abs(res[0] / 2), np.abs(res[0]), float)
    lat = np.arange(center_bottom, center_top + np.abs(res[0] / 2), np.abs(res[1]), float)
    lons, lats = np.meshgrid(lon, lat)

    min_lon_round = round(np.min(lons), decimal_round)
    max_lon_round = round(np.max(lons), decimal_round)
    min_lat_round = round(np.min(lats), decimal_round)
    max_lat_round = round(np.max(lats), decimal_round)

    center_right_round = round(center_right, decimal_round)
    center_left_round = round(center_left, decimal_round)
    center_bottom_round = round(center_bottom, decimal_round)
    center_top_round = round(center_top, decimal_round)

    assert min_lon_round == center_left_round
    assert max_lon_round == center_right_round
    assert min_lat_round == center_bottom_round
    assert max_lat_round == center_top_round

    lats = np.flipud(lats)

    dims = values.shape
    high = dims[0]  # nrows
    wide = dims[1]  # cols

    if nodata is None:
        nodata = var_nodata

    bounding_box = [min_lon_round, max_lat_round, max_lon_round, min_lat_round]

    da_out = create_darray_3d(data, time, lons, lats, geo_1d=True,
                     coord_name_x=coord_name_x, coord_name_y=coord_name_y, coord_name_time='time',
                     dim_name_x=dim_name_x, dim_name_y=dim_name_y , dim_name_time='time', dims_order=['time','lat','lon'])

    #attrs_out = {'bounding_box': bounding_box, 'high': high, 'wide': wide, 'meta': meta,
    #             'no_data': nodata, 'transform': transform, 'dtype': dtype}
    #da_out.attrs = attrs_out

    dset_out = da_out.to_dataset(name=var_name)

    return dset_out
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------

def read_point_data(point_in_time_step, st_code='code', st_name='name', st_lon='longitude', st_lat='latitude', st_data='data', sep=',', header=True):
    if st_data is None or st_lon is None or st_lat is None:
        logging.error(" ERROR! Data, longitude and latitudes are required inputs for point files")
        raise IOError

    var_names = [st_code, st_name, st_lon, st_lat, st_data]
    var_in = [i for i in var_names if i is not None]

    if sep is None:
        sep = ','

    if header is False:
        dfStations = pd.read_csv(point_in_time_step, sep=sep, usecols=var_in, header=None)
        data = pd.read_csv(point_in_time_step, sep=sep, usecols=[st_data], header=None).squeeze()
    else:
        dfStations = pd.read_csv(point_in_time_step, sep=sep, usecols=var_in)
        data = pd.read_csv(point_in_time_step, sep=sep, usecols=[st_data]).squeeze()

    if st_code is None:
        station_codes = np.arange(1,len(data)+1,1)
        dfStations['code'] = station_codes
    if st_name is None:
        station_names = ["p_" + str(i) for i in station_codes]
        dfStations['name'] = station_names

    dfStations.set_index('code')
    dfStations = dfStations.rename(columns={st_lat: 'lat', st_lon: 'lon', st_data: 'data'})


    return dfStations, data
