# -------------------------------------------------------------------------------------
# Library
import rasterio
import os

import numpy as np

from netCDF4 import Dataset
from pygeogrids.grids import BasicGrid

from os.path import join

try:
    os.environ["PROJ_LIB"] = "/home/fabio/Documents/Work_Area/Code_Development/Library/proj-5.2.0/share/proj/"
    from mpl_toolkits.basemap import Basemap
except ImportWarning:
    os.environ["PROJ_LIB"] = ""

import matplotlib.pylab as plt
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to load a reference domain
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

    obj = {'values': values, 'lons': lons, 'lats': lats, 'transform': transform}

    grid = BasicGrid(lons.flatten(), lats.flatten()).to_cell_grid(cellsize=5.)

    return grid, obj
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to load the rzsm grid
def load_grid_rzsm(path_grid, filename_grid='grid.nc'):

    data_grid = Dataset(join(path_grid, filename_grid))

    lon_1d = data_grid['lon'][:]
    lat_1d = data_grid['lat'][:]

    lon_2d, lat_2d = np.meshgrid(lon_1d, lat_1d)
    grid = BasicGrid(lon_2d.flatten(), lat_2d.flatten()).to_cell_grid(cellsize=5.)

    return grid
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to select a grid using a reference
def select_grid(filename_grid_in, filename_grid_out, filename_reference,
                var_lon='lon', var_lat='lat', var_gpi='gpi',
                var_cell='cell', var_carea='committed_area', var_lflag='land_flag',
                var_dim='locations'):

    vars_grid = [var_lon] + [var_lat] + [var_gpi] + [var_cell] + [var_carea] + [var_lflag]

    dset_ref = rasterio.open(filename_reference)
    bounds_ref = dset_ref.bounds

    ws_grid_in = {}
    dset_grid_in = Dataset(filename_grid_in, 'r')
    for var_grid in vars_grid:
        data_grid_in = dset_grid_in.variables[var_grid][:]
        dtype_grid_in = data_grid_in.dtype

        attrs_grid_in = {}
        for attr_name in dset_grid_in.variables[var_grid].ncattrs():
            attrs_grid_in[attr_name] = dset_grid_in.variables[var_grid].getncattr(attr_name)

        ws_grid_in[var_grid] = {}
        ws_grid_in[var_grid]['values'] = data_grid_in
        ws_grid_in[var_grid]['dtype'] = dtype_grid_in
        ws_grid_in[var_grid]['attributes'] = attrs_grid_in

    if var_lon in list(ws_grid_in.keys()) and var_lat in list(ws_grid_in.keys()):
        idx_ref = np.where(
            ((ws_grid_in[var_lon]['values'].data >= bounds_ref.left) &
             (ws_grid_in[var_lon]['values'].data <= bounds_ref.right)) &
            ((ws_grid_in[var_lat]['values'].data >= bounds_ref.bottom) &
             (ws_grid_in[var_lat]['values'].data <= bounds_ref.top)))[0]
    else:
        idx_ref = None

    ws_grid_out = {}
    for var_grid in vars_grid:
        data_ref = ws_grid_in[var_grid]['values'][idx_ref]
        dtype_ref = ws_grid_in[var_grid]['dtype']
        attrs_ref = ws_grid_in[var_grid]['attributes']

        ws_grid_out[var_grid] = {}
        ws_grid_out[var_grid]['values'] = data_ref
        ws_grid_out[var_grid]['dtype'] = dtype_ref
        ws_grid_out[var_grid]['attributes'] = attrs_ref

    loc_n = ws_grid_out[var_gpi]['values'].data.shape[0]

    dset_grid_out = Dataset(filename_grid_out, 'w')
    dset_grid_out.createDimension(var_dim, loc_n)
    for var_grid in vars_grid:
        data_grid_out = ws_grid_out[var_grid]['values']
        dtype_grid_out = ws_grid_out[var_grid]['dtype']
        attrs_grid_out = ws_grid_out[var_grid]['attributes']

        var_obj_out = dset_grid_out.createVariable(var_grid, dtype_grid_out, dimensions=var_dim,
                                                   fill_value=None, zlib=None, complevel=None)
        for attr_name in attrs_grid_out:
            var_obj_out.setncattr(attr_name, attrs_grid_out[attr_name])

        var_obj_out[:] = data_grid_out

    dset_grid_out.close()

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to map data in geographical mode
def data_2_map(data_values, data_geox, data_geoy, resolution='l', vmin=None, vmax=None):

    plt.figure(figsize=(8, 8))
    m = Basemap(llcrnrlat=np.min(data_geoy), urcrnrlat=np.max(data_geoy),
                llcrnrlon=np.min(data_geox), urcrnrlon=np.max(data_geox),
                resolution=resolution)
    m.drawcoastlines(color='gray')
    m.drawcountries(color='gray')
    plt.pcolormesh(data_geox, data_geoy, data_values)
    if (vmin is not None) and (vmax is not None):
        plt.clim(vmin, vmax)
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
