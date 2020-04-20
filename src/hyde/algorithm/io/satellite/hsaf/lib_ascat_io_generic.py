# -------------------------------------------------------------------------------------
# Libraries
import os
import pickle

import numpy as np
import pandas as pd
import xarray as xr

from copy import deepcopy
from netCDF4 import Dataset, date2num

from src.hyde.algorithm.analysis.satellite.hsaf.lib_ascat_analysis import clip_map

# Definition(s)
time_units = 'days since 1858-11-17 00:00:00'
time_format = '%Y%m%d%H%M'

decoded_attrs = ['_FillValue', 'scale_factor']
valid_range_attr = 'Valid_range'
missing_value_attr = 'Missing_value'
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create dataset
def create_dset(time, data, terrain, geox, geoy, attrs=None):

    dset = xr.Dataset(coords={'time': (['time'], pd.DatetimeIndex([time]))})
    dset.coords['time'] = dset.coords['time'].astype('datetime64[ns]')

    da_terrain = xr.DataArray(np.flipud(terrain),
                              dims=['south_north', 'west_east'],
                              coords={'Longitude': (['south_north', 'west_east'], geox),
                                      'Latitude': (['south_north', 'west_east'], np.flipud(geoy))})

    dset['terrain'] = da_terrain

    for var_name, var_data in data.items():
        var_da = xr.DataArray(np.flipud(var_data),
                              dims=['south_north', 'west_east'],
                              coords={'Longitude': (['south_north', 'west_east'], geox),
                                      'Latitude': (['south_north', 'west_east'], np.flipud(geoy))})

        if var_name in list(attrs.keys()):
            if valid_range_attr in list(attrs[var_name].keys()):
                valid_range = attrs[var_name][valid_range_attr]
                var_da = clip_map(var_da, valid_range)

            if missing_value_attr in list(attrs[var_name].keys()):
                missing_value = attrs[var_name][missing_value_attr]
                var_da = var_da.where(da_terrain > 0, other=missing_value)

        dset[var_name] = var_da

        if attrs:
            if var_name in attrs:
                var_attrs = attrs[var_name]
                for key_attr, value_attr in var_attrs.items():
                    if value_attr is not None:
                        if key_attr not in decoded_attrs:

                            if isinstance(value_attr, list):
                                string_attr = [str(value) for value in value_attr]
                                value_attr = ','.join(string_attr)

                            dset[var_name].attrs[key_attr] = value_attr

    return dset

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write dataset
def write_dset(filename, dset, attrs=None, mode='w', engine='netcdf4', compression=0):

    data_encoded = dict(zlib=True, complevel=compression)

    data_encoding = {}
    for var_name in dset.data_vars:

        if isinstance(var_name, bytes):
            var_name_upd = var_name.decode("utf-8")
            dset = var_name.rename({var_name: var_name_upd})
            var_name = var_name_upd

        var_data = dset[var_name]
        if len(var_data.dims) > 0:
            data_encoding[var_name] = deepcopy(data_encoded)

        if attrs:
            if var_name in list(attrs.keys()):
                attrs_var = attrs[var_name]
                for attr_key, attr_value in attrs_var.items():

                    if attr_key in decoded_attrs:

                        data_encoding[var_name][attr_key] = {}

                        if isinstance(attr_value, list):
                            attr_string = [str(value) for value in attr_value]
                            attr_value = ','.join(attr_string)

                        data_encoding[var_name][attr_key] = attr_value

    if 'time' in list(dset.coords):
        data_encoding['time'] = {'calendar': 'gregorian'}

    dset.to_netcdf(path=filename, format='NETCDF4', mode=mode, engine=engine, encoding=data_encoding)

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read dataset
def read_dset(filename, engine='h5netcdf'):
    with xr.open_dataset(filename, engine=engine) as file:
        dset = file.load()
        file.close()
    return dset
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read analysis data
def read_points_data(filename):
    if os.path.exists(filename):
        data = pickle.load(open(filename, "rb"))
    else:
        data = None
    return data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write points data
def write_points_data(filename, data):

    if os.path.exists(filename):
        os.remove(filename)

    with open(filename, 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read analysis data
def read_analysis_data(filename):
    if os.path.exists(filename):
        data = pickle.load(open(filename, "rb"))
    else:
        data = None
    return data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write analysis data
def write_analysis_data(filename, data=None):

    if os.path.exists(filename):
        os.remove(filename)

    with open(filename, 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write data to netcdf file
def write_cell_data(filename, data, attrs_data, attrs_file=None,
                    time_var='time', loc_ids_var='location_id',
                    loc_dim_name='locations', time_dim_name='time'):

    # Open file
    dset = Dataset(filename, 'w')

    # Create variables dimension(s)
    loc_n = data[loc_ids_var].__len__()
    time_n = data[time_var].__len__()

    dset.createDimension(dimname=loc_dim_name, size=loc_n)
    dset.createDimension(dimname=time_dim_name, size=time_n)

    if attrs_file is not None:
        for attr_name in attrs_file:
            attrs_dict = attrs_file[attr_name]
            dset.setncattr(attr_name, attrs_dict)

    for var_name in data:

        var_data = data[var_name]

        if var_name == time_var:

            var_time = date2num(var_data, units=time_units, calendar='standard')
            var_obj = dset.createVariable(varname=var_name, dimensions=(time_dim_name,), datatype='float64')
            var_obj.units = time_units
            var_obj[:] = var_time

        else:

            var_dims = var_data.ndim

            if var_name in attrs_data:
                var_attrs = attrs_data[var_name]
            else:
                var_attrs = {}
            var_dtype = var_data.dtype

            if var_dims == 1:
                if var_data.__len__() == loc_n:
                    var_dims_tag = (loc_dim_name,)
                elif var_data.__len__() == time_n:
                    var_dims_tag = (time_dim_name,)
                else:
                    var_dims_tag = None
            elif var_dims == 2:
                var_dims_tag = (loc_dim_name, time_dim_name)
            else:
                var_dims_tag = None

            var_obj = dset.createVariable(var_name, var_dtype, dimensions=var_dims_tag, fill_value=None,
                                          zlib=None, complevel=None)

            for attr_name in var_attrs:
                var_obj.setncattr(attr_name, var_attrs[attr_name])

            if var_data is not None:
                if var_dims == 1:
                    var_obj[:] = var_data
                elif var_dims == 2:
                    var_obj[:, :] = var_data

    dset.close()
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read cell data
def read_cell_data(filename, parameters,
                   time_var='time', lon_var='lon', lat_var='lat', alt_var='alt',
                   loc_ids_var='location_id', loc_idx_var='locationIndex', loc_lut_var='row_size'):

    # List of dynamic variable(s)
    vars_ts = parameters

    # Open file in nc format
    dset = Dataset(filename, mode='r')
    vars = dset.variables

    # Get global attributes
    file_attrs = {}
    for attr_name in dset.ncattrs():
        file_attrs[attr_name] = getattr(dset, attr_name)

    # Get registry data
    lons_dset = dset.variables[lon_var][:]
    lats_dset = dset.variables[lat_var][:]
    alts_dset = dset.variables[alt_var][:]

    # gpis_nan = []
    # for i, gpi in enumerate(gpis_loc):
    #    if not gpi:
    #        gpis_nan.append(i)

    # gpis = np.delete(gpis_loc, np.asarray(gpis_nan))
    # lons = np.delete(lons_loc, np.asarray(gpis_nan))
    # lats = np.delete(lats_loc, np.asarray(gpis_nan))
    # alts = np.delete(alts_loc, np.asarray(gpis_nan))

    # Get indexed variable(s)
    var_idx_dset = dset.variables[loc_idx_var][:]
    var_time_dset = dset.variables[time_var][:]
    var_gpis_dset = dset.variables[loc_ids_var][:]
    # var_gpis_dset = grid.find_nearest_gpi(lons_dset.data, lats_dset.data)

    ws_data = {}
    ws_attrs = {}
    for var_name in vars:
        var_name = str(var_name)
        var_data_dset = dset.variables[var_name][:]

        if var_name in vars_ts:

            var_data_ts = np.array([])
            var_time_ts = np.array([])
            row_ts = np.array([])

            for i, var_gpi_dset in enumerate(var_gpis_dset):

                data_idx = np.where(var_idx_dset == i)

                var_data_idx = var_data_dset[data_idx]
                var_time_idx = var_time_dset[data_idx]

                sort_idx = np.argsort(var_time_idx)

                var_data_sort = var_data_idx[sort_idx]
                var_time_sort = var_time_idx[sort_idx]

                var_time_ts = np.concatenate([var_time_ts, var_time_sort])
                var_data_ts = np.concatenate([var_data_ts, var_data_sort])
                row_ts = np.concatenate([row_ts, np.asarray(var_data_sort.__len__() * np.ones(1))])

            ws_data[var_name] = var_data_ts

            if 'time' not in ws_data:
                ws_data['time'] = var_time_ts
                ws_attrs['time'] = \
                    {'standard_name': 'time',
                     'long_name': 'time of measurement',
                     'units': time_units}

            if loc_lut_var not in ws_data:
                ws_data[loc_lut_var] = np.asarray(row_ts, dtype=int)
                ws_attrs[loc_lut_var] = \
                    {'long_name': 'number of observations at this location',
                     'sample_dimension': var_idx_dset.__len__()}

            if loc_ids_var not in ws_data:
                ws_data[loc_ids_var] = var_gpis_dset
            if loc_idx_var not in ws_data:
                ws_data[loc_idx_var] = var_idx_dset

            if lon_var not in ws_data:
                ws_data[lon_var] = lons_dset
            if lat_var not in ws_data:
                ws_data[lat_var] = lats_dset
            if alt_var not in ws_data:
                ws_data[alt_var] = alts_dset

    dset.close()

    return ws_data, ws_attrs, file_attrs
# -------------------------------------------------------------------------------------
