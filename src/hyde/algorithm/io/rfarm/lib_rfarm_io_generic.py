# -------------------------------------------------------------------------------------
# Libraries
import os
import pickle
import json
import xarray as xr

from copy import deepcopy

from src.hyde.algorithm.geo.rfarm.lib_rfarm_geo import clip_map
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Attr(s) decoded
reserved_attrs = ['coordinates']
decoded_attrs = ['_FillValue', 'scale_factor']
valid_range_attr = 'Valid_range'
missing_value_attr = 'Missing_value'
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create a data array
def create_darray_2d(data, geox, geoy):

    darray = xr.DataArray(data,
                          dims=['south_north', 'west_east'],
                          coords={'longitude': (['south_north', 'west_east'], geox),
                                  'latitude': (['south_north', 'west_east'], geoy)})

    return darray
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create a data array
def create_darray_3d(data, time, geox, geoy):

    darray = xr.DataArray(data,
                          dims=['south_north', 'west_east', 'time'],
                          coords={'time': (['time'], time),
                                  'longitude': (['south_north', 'west_east'], geox),
                                  'latitude': (['south_north', 'west_east'], geoy)})

    return darray
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create dataset
def create_dset(time,
                data, terrain, geox, geoy,
                var_name='Rain', terrain_name='Terrain',
                var_attrs=None, terrain_attrs=None,
                dim_x_name='west_east', dim_y_name='south_north', dim_t_name='time'):

    dset = xr.Dataset(coords={'time': ([dim_t_name], time)})
    dset.coords['time'] = dset.coords['time'].astype('datetime64[ns]')

    da_terrain = xr.DataArray(terrain,  name=terrain_name,
                              dims=[dim_y_name, dim_x_name],
                              coords={'longitude': ([dim_y_name, dim_x_name], geox),
                                      'latitude': ([dim_y_name, dim_x_name], geoy)})
    dset[terrain_name] = da_terrain

    if terrain_attrs:
        for key_attr, value_attr in terrain_attrs.items():
            if value_attr is not None:
                if key_attr not in decoded_attrs:

                    if isinstance(value_attr, list):
                        string_attr = [str(value) for value in value_attr]
                        value_attr = ','.join(string_attr)
                    if isinstance(value_attr, dict):
                        string_attr = json.dumps(value_attr)
                        value_attr = string_attr

                    if key_attr in reserved_attrs:
                        value_attr = None

                    if value_attr is not None:
                        dset[terrain_name].attrs[key_attr] = value_attr

    da_var = xr.DataArray(data, name=var_name,
                          dims=[dim_t_name, dim_y_name, dim_x_name],
                          coords={'time': ([dim_t_name], time),
                                  'longitude': ([dim_y_name, dim_x_name], geox),
                                  'latitude': ([dim_y_name, dim_x_name], geoy)})

    if valid_range_attr in list(var_attrs.keys()):
        valid_range = var_attrs[valid_range_attr]
        da_var = clip_map(da_var, valid_range)

    if missing_value_attr in list(var_attrs.keys()):
        missing_value = var_attrs[missing_value_attr]
        da_var = da_var.where(da_terrain > 0, other=missing_value)

    dset[var_name] = da_var

    if var_attrs:
        for key_attr, value_attr in var_attrs.items():
            if value_attr is not None:
                if key_attr not in decoded_attrs:

                    if isinstance(value_attr, list):
                        string_attr = [str(value) for value in value_attr]
                        value_attr = ','.join(string_attr)

                    if isinstance(value_attr, dict):
                        string_attr = json.dumps(value_attr)
                        value_attr = string_attr

                    if key_attr in reserved_attrs:
                        value_attr = None

                    if value_attr is not None:
                        dset[var_name].attrs[key_attr] = value_attr

    return dset

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write dataset
def write_dset(filename, dset, attrs=None, mode='w', engine='h5netcdf', compression=0):

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
# Method to read data obj
def read_obj(filename):
    if os.path.exists(filename):
        data = pickle.load(open(filename, "rb"))
    else:
        data = None
    return data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to write data obj
def write_obj(filename, data):

    if os.path.exists(filename):
        os.remove(filename)

    with open(filename, 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)
# -------------------------------------------------------------------------------------



