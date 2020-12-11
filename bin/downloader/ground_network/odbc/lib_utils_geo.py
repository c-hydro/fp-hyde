# -------------------------------------------------------------------------------------
# Libraries
import logging
import numpy as np
import geopandas as gpd
import pandas as pd
import rasterio

logging.getLogger('rasterio').setLevel(logging.WARNING)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read shapefile section(s)
def read_data_shapefile_section(file_name, columns_name_expected=None, columns_name_type=None, columns_name_tag=None):

    if columns_name_expected is None:
        columns_name_expected = ['HMC_X', 'HMC_Y', 'BASIN', 'SEC_NAME', 'SEC_RS', 'AREA', 'Q_THR1', 'Q_THR2']
    if columns_name_type is None:
        columns_name_type = [np.int, np.int, str, str, str, np.float, np.float, np.float]
    if columns_name_tag is None:
        columns_name_tag = columns_name_expected

    file_dframe_raw = gpd.read_file(file_name)
    file_rows = file_dframe_raw.shape[0]

    file_obj = {}
    for column_name, column_type, column_tag in zip(columns_name_expected, columns_name_type, columns_name_tag):
        if column_name in file_dframe_raw.columns:
            column_data_tmp = file_dframe_raw[column_name].values.tolist()

            if column_type == np.int:
                column_data = [np.int(item) for item in column_data_tmp]
            elif column_type == str:
                column_data = [str(item) for item in column_data_tmp]
            elif column_type == np.float:
                column_data = [np.float(item) for item in column_data_tmp]
            else:
                logging.error(' ===> Datatype for undefined columns in the section shapefile is not allowed')
                raise NotImplementedError('Datatype not implemented yet')
        else:

            logging.warning(' ===> Column ' + column_name +
                            ' not available in shapefile. Initialized with undefined values according with datatype')
            if column_type == np.int:
                column_data = [-9999] * file_rows
            elif column_type == str:
                column_data = [''] * file_rows
            elif column_type == np.float:
                column_data = [-9999.0] * file_rows
            else:
                logging.error(' ===> Datatype for undefined columns in the section shapefile is not allowed')
                raise NotImplementedError('Datatype not implemented yet')

        file_obj[column_tag] = column_data

    section_df = pd.DataFrame(file_obj, columns=columns_name_tag)

    return section_df
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read ascii data raster
def read_data_raster_land(file_name):

    dset = rasterio.open(file_name)
    bounds = dset.bounds
    res = dset.res
    transform = dset.transform
    data = dset.read()
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

    file_obj = {'values': values, 'longitude': lons, 'latitude': lats,
                'transform': transform,
                'bb_left': bounds.left, 'bb_right': bounds.right,
                'bb_top': bounds.top, 'bb_bottom': bounds.bottom,
                'res_lon': res[0], 'res_lat': res[1]}

    return file_obj
# -------------------------------------------------------------------------------------
