# -------------------------------------------------------------------------------------
# Library
import rasterio
import numpy as np

import matplotlib.pylab as plt
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to load a reference domain file
def load_domain(filename_reference):

    dset = rasterio.open(filename_reference)
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

    obj = {'values': values, 'longitude': lons, 'latitude': lats,
           'transform': transform,
           'bb_left': bounds.left, 'bb_right': bounds.right,
           'bb_top': bounds.top, 'bb_bottom': bounds.bottom,
           'res_lon': res[0], 'res_lat': res[1]}

    return obj
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to clip data 2D/3D using a min/max threshold(s) and assign a missing value
def clip_map(map, valid_range=None, missing_value=None):

    # Set variable valid range
    if valid_range is None:
        valid_range = [None, None]

    if valid_range is not None:
        if valid_range[0] is not None:
            valid_range_min = float(valid_range[0])
        else:
            valid_range_min = None
        if valid_range[1] is not None:
            valid_range_max = float(valid_range[1])
        else:
            valid_range_max = None
        # Set variable missing value
        if missing_value is None:
            missing_value_min = valid_range_min
            missing_value_max = valid_range_max
        else:
            missing_value_min = missing_value
            missing_value_max = missing_value

        # Apply min and max condition(s)
        if valid_range_min is not None:
            map = map.where(map >= valid_range_min, missing_value_min)
        if valid_range_max is not None:
            map = map.where(map <= valid_range_max, missing_value_max)

        return map
    else:
        return map

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to map data in geographical mode
def data_2_map(data_values, data_geox, data_geoy, resolution='l'):

    plt.figure(figsize=(8, 8))
    m = Basemap(llcrnrlat=np.min(data_geoy), urcrnrlat=np.max(data_geoy),
                llcrnrlon=np.min(data_geox), urcrnrlon=np.max(data_geox),
                resolution=resolution)
    m.drawcoastlines(color='gray')
    m.drawcountries(color='gray')
    plt.pcolormesh(data_geox, data_geoy, data_values)
    plt.show()
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to show data in array mode
def data_2_show(data):

    plt.figure()
    plt.imshow(data)
    plt.colorbar()
    plt.show()
# -------------------------------------------------------------------------------------
