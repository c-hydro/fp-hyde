"""
Library Features:

Name:          lib_utils_io_grib
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20230727'
Version:       '1.0.0'
"""

# ----------------------------------------------------------------------------------------------------------------------
# libraries
import logging
import os
import numpy as np
import pandas as pd
import xarray as xr

from copy import deepcopy

from lib_info_args import logger_name
from lib_utils_io import create_darray

import lib_fx_nwp_lami_2i as lib_fx_nwp

# set logger
alg_logger = logging.getLogger(logger_name)
logging.getLogger('cfgrib').setLevel(logging.WARNING)
logging.getLogger('gribapi').setLevel(logging.WARNING)

# debug
import matplotlib.pylab as plt

# default netcdf encoded attributes
attrs_encoded = ["_FillValue", "dtype", "scale_factor", "add_offset", "grid_mapping"]
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to organize grib file
def organize_file_grib(obj_data, obj_time=None, obj_geo_x=None, obj_geo_y=None,
                       obj_attrs=None, obj_method=None, obj_settings=None,
                       reference_time=None,
                       var_name_time='time', var_name_geo_x='longitude', var_name_geo_y='latitude',
                       coord_name_time='time', coord_name_x='longitude', coord_name_y='latitude',
                       dim_name_time='time', dim_name_x='longitude', dim_name_y='latitude'):

    # organize time information
    data_time = None
    if obj_time is not None:
        if isinstance(obj_time, str):
            data_time = pd.DatetimeIndex([pd.Timestamp(obj_time)])
        elif isinstance(obj_time, pd.DatetimeIndex):
            data_time = deepcopy(obj_time)
        elif isinstance(obj_time, pd.Timestamp):
            data_time = pd.DatetimeIndex([obj_time])
        elif isinstance(obj_time, np.ndarray):
            data_time = pd.DatetimeIndex(obj_time)
        else:
            alg_logger.error(' ===> Time obj format is not supported')
            raise NotImplemented('Case not implemented yet')

    # iterate over variable(s)
    collections_data_dset, collections_data_attrs = xr.Dataset(), {}
    for (data_name, data_values), (attrs_name, attrs_data) in zip(obj_data.items(), obj_attrs.items()):

        # check variable name and attributes name
        assert data_name == attrs_name, \
            ' ===> Data name and attributes name are different'

        # get settings data
        settings_data = None
        if data_name in list(obj_settings.keys()):
            settings_data = obj_settings[data_name]
        # get method data
        method_data = None
        if data_name in list(obj_method.keys()):
            method_data = obj_method[data_name]

        # check variable units (data and settings)
        if settings_data is not None:
            if 'units' in list(attrs_data.keys()) and 'units' in list(settings_data.keys()):
                assert attrs_data['units'].lower() == settings_data['units'].lower(), \
                    ' ===> Variable units and attributes units are different'

        # create variable attributes
        if settings_data is not None:
            data_attrs_tmp = {**attrs_data, **settings_data}
        else:
            data_attrs_tmp = attrs_data

        # create variable data array
        data_dframe_tmp = create_darray(
            data_values, obj_geo_x, obj_geo_y,
            geo_1d=False, time=data_time,
            coord_name_x=coord_name_x, coord_name_y=coord_name_y, coord_name_time=coord_name_time,
            dim_name_x=dim_name_x, dim_name_y=dim_name_y, dim_name_time=dim_name_time)

        # adjust data according to the variable mode
        if method_data is not None:

            # define mode attributes
            fx_name = method_data['fx']
            fx_type, fx_period = method_data['type'], method_data['period']

            # search fx method in the library
            if hasattr(lib_fx_nwp, fx_name):

                # define fx method
                fx_obj = getattr(lib_fx_nwp, fx_name)
                # define fx arguments
                fx_args = {'var_dframe': data_dframe_tmp,
                           'var_time_reference': reference_time,
                           'var_attrs': data_attrs_tmp,
                           'var_type': fx_type}
                # apply fx method and arguments
                data_dframe_def, data_attrs_def = fx_obj(**fx_args)

            else:
                alg_logger.error(' ===> Method fx "' + fx_name + '" is not available')
                raise NotImplementedError('Case not implemented yet')

        else:
            data_dframe_def = data_dframe_tmp
            data_attrs_def = data_attrs_tmp

        collections_data_dset[data_name] = data_dframe_def
        collections_data_attrs[data_name] = data_attrs_def

    return collections_data_dset, collections_data_attrs
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to read grib file
def read_file_grib(file_name, file_variables=None, file_time_reference=None,
                   var_name_geo_x='longitude', var_name_geo_y='latitude'):

    # check file availability
    if os.path.exists(file_name):

        # check file time reference format
        if not isinstance(file_time_reference, pd.Timestamp):
            file_time_reference = pd.Timestamp(file_time_reference)

        filter_vars = []
        for var_name_data in file_variables.values():
            if var_name_data not in [var_name_geo_x, var_name_geo_y]:
                filter_vars.append(var_name_data)

        # open file
        if not isinstance(filter_vars, list):
            filter_vars = [filter_vars]

        # iterate over filter variables
        file_dset = None
        for filter_var in filter_vars:
            tmp_dset = xr.open_dataset(
                file_name, engine='cfgrib',
                backend_kwargs={'filter_by_keys': {'cfVarName': filter_var}})

            if file_dset is None:
                file_dset = tmp_dset
            else:
                file_dset = file_dset.merge(tmp_dset)

        # check file empty or not
        if len(file_dset.dims) > 0:

            # organize time object
            time_range = file_dset['valid_time'].values
            time_steps = file_dset['step'].values
            time_reference = file_dset['time'].values
            time_start, time_end = time_range[0], time_range[-1]

            time_obj = {'reference': time_reference,
                        'time': time_range, 'steps': time_steps,
                        'start': time_start, 'end': time_end}

            # organize attrs obj
            file_attrs = file_dset.attrs

            # organize data and geo object(s)
            data_obj, geo_obj, attrs_obj = {}, {}, {}
            for var_name_out, var_name_in in file_variables.items():
                if var_name_out == var_name_geo_x:
                    geo_obj[var_name_out] = file_dset[var_name_in].values
                if var_name_out == var_name_geo_y:
                    geo_obj[var_name_out] = file_dset[var_name_in].values

                if var_name_in != var_name_geo_x or var_name_in != var_name_geo_y:
                    if var_name_in in list(file_dset.data_vars):

                        # get data values
                        tmp_values = file_dset[var_name_in].values
                        data_values = np.squeeze(tmp_values)
                        # get data attributes
                        tmp_attrs = file_dset[var_name_in].attrs
                        data_attrs = {**tmp_attrs, **file_attrs}

                        ''' debug
                        plt.figure()
                        plt.imshow(data_values)
                        plt.colorbar()
                        plt.show()
                        '''
                        # store data and attrs in a common object
                        data_obj[var_name_out] = data_values
                        attrs_obj[var_name_out] = data_attrs
                    else:
                        if var_name_in not in [var_name_geo_x, var_name_geo_y]:
                            alg_logger.warning(' ===> Variable "' + var_name_in + '" not found in the dataset')

        else:
            alg_logger.warning(' ===> Variable(s) are not found in the object but file is available and readable')
            data_obj, attrs_obj, geo_obj, time_obj = None, None, None, None

    else:
        alg_logger.warning(' ===> File name "' + file_name + '" not found')
        data_obj, attrs_obj, geo_obj, time_obj = None, None, None, None

    return data_obj, attrs_obj, geo_obj, time_obj

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to write nc file
def write_file_nc(file_name, dset_data,
                  dset_mode='w', dset_engine='netcdf4', dset_compression=9, dset_format='NETCDF4',
                  dim_key_time='time', no_data=-9999.0):

    dset_encoded = dict(zlib=True, complevel=dset_compression)

    dset_encoding = {}
    for var_name in dset_data.data_vars:

        if isinstance(var_name, bytes):
            tmp_name = var_name.decode("utf-8")
            dset_data.rename({var_name: tmp_name})
            var_name = deepcopy(tmp_name)

        var_data = dset_data[var_name]
        if len(var_data.dims) > 0:
            dset_encoding[var_name] = deepcopy(dset_encoded)

        var_attrs = dset_data[var_name].attrs
        if var_attrs:
            for attr_key, attr_value in var_attrs.items():
                if attr_key in attrs_encoded:

                    dset_encoding[var_name][attr_key] = {}

                    if isinstance(attr_value, list):
                        attr_string = [str(value) for value in attr_value]
                        attr_value = ','.join(attr_string)

                    dset_encoding[var_name][attr_key] = attr_value

        if '_FillValue' not in list(dset_encoding[var_name].keys()):
            dset_encoding[var_name]['_FillValue'] = no_data

    if dim_key_time in list(dset_data.coords):
        dset_encoding[dim_key_time] = {'calendar': 'gregorian'}

    dset_data.to_netcdf(path=file_name, format=dset_format, mode=dset_mode,
                        engine=dset_engine, encoding=dset_encoding)
# ----------------------------------------------------------------------------------------------------------------------
