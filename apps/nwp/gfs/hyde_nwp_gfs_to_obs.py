"""
HyDE Processing Tool - NWP GFS to OBS

__date__ = '20250620'
__version__ = '1.2.0'
__author__ =
        'Andrea Libertino (andrea.libertino@cimafoundation.org',
        'Fabio Delogu (fabio.delogu@cimafoundation.org'
__library__ = 'hyde'

General command line:
python hyde_nwp_gfs_to_obs.py -settings_file configuration.json -time YYYY-MM-DD HH:MM

Version(s):
20250620 (1.2.0) --> Fixed flipped latitude values under certains conditions
20210311 (1.1.0) --> Updated input gfs format to be Continuum-compliant
20210302 (1.0.0) --> Beta release for hyde package
"""
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
import numpy as np
import logging, json, os, time, struct
from argparse import ArgumentParser
import pandas as pd
import xarray as xr
from copy import deepcopy
import datetime

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Algorithm information
alg_name = 'HyDE Processing Tool - nwp gfs to obs'
alg_version = '1.1.0'
alg_release = '2021-03-11'
# Algorithm parameter(s)
time_format = '%Y%m%d%H%M'
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Defined attributes look-up table
attributes_defined_lut = {
    'blocking_attrs': ['coordinates'],
    'encoding_attrs': {
        '_FillValue': ['_FillValue', 'fill_value'],
        'scale_factor': ['scale_factor', 'ScaleFactor']
    },
    'filtering_attrs': {
        'Valid_range': ['Valid_range', 'valid_range'],
        'Missing_value': ['Missing_value', 'missing_value']
    }
}

# -------------------------------------------------------------------------------------
def main():

    # -------------------------------------------------------------------------------------
    # Get algorithm settings
    alg_settings, alg_time = get_args()

    # Set algorithm settings
    data_settings = read_file_json(alg_settings)

    # Set algorithm logging
    os.makedirs(data_settings['log']['folder_name'], exist_ok=True)
    set_logging(logger_file=os.path.join(data_settings['log']['folder_name'], data_settings['log']['file_name']))

    # -------------------------------------------------------------------------------------
    # Info algorithm
    logging.info(' ============================================================================ ')
    logging.info(' ==> ' + alg_name + ' (Version: ' + alg_version + ' Release_Date: ' + alg_release + ')')
    logging.info(' ==> START ... ')
    logging.info(' ')

    # Time algorithm information
    start_time = time.time()
    # -------------------------------------------------------------------------------------

    timeEnd = datetime.datetime.strptime(alg_time,'%Y-%m-%d %H:%M')
    timeStart = timeEnd - pd.Timedelta(str(data_settings["data"]["dynamic"]["time"]["time_period"]) + data_settings["data"]["dynamic"]["time"]["period_unit"])
    timeRange = pd.date_range(timeStart,timeEnd, freq=data_settings["data"]["dynamic"]["time"]["time_frequency"])

    logging.info(' ---> Observed period : ' + timeStart.strftime('%Y-%m-%d %H:%M') + ' - ' + timeEnd.strftime('%Y-%m-%d %H:%M'))

    varIn = [i for i in data_settings['data']['dynamic']['source'] if data_settings['data']['dynamic']['source'][i]['compute']]

    logging.info(' ---> Compute variables : ' + ','.join(varIn))
    readed_grid = False

    for timeNow in timeRange:
        logging.info(' ----> Compute time step ' + timeNow.strftime("%Y-%m-%d %H:%M") + '...')
        inMaps = {}
        missing_input = False

        for var in varIn:
            logging.info(' ---> Extract variable: ' + var)

            template_time_step = fill_template_time_step(data_settings['algorithm']['template'], timeNow)
            file_time_step = os.path.join(data_settings['data']['dynamic']['source'][var]['folder_name'],
                                              data_settings['data']['dynamic']['source'][var]['file_name']).format(
                **template_time_step)

            if not os.path.isfile(file_time_step):
                # If the forecast related to the timeNow time step does not exist I search for timeNow in the precedent time step
                template_time_step = fill_template_time_step(data_settings['algorithm']['template'], timeNow - pd.Timedelta('1D'))
                file_time_step = os.path.join(data_settings['data']['dynamic']['source'][var]['folder_name'],
                                             data_settings['data']['dynamic']['source'][var]['file_name']).format(**template_time_step)
                if not os.path.isfile(file_time_step):
                    logging.warning(' --> WARNING! File for time step ' + timeNow.strftime(
                        "%Y-%m-%d %H") + ' not found... SKIPPED!"')
                    missing_input = True
                    break
                # And then re-generate the timeNow templates for the output templates
                template_time_step = fill_template_time_step(data_settings['algorithm']['template'], timeNow)

            file_open = xr.open_dataset(file_time_step).sel(time=timeNow, method='backfill')
            inMaps[var] = np.squeeze(file_open[data_settings['data']['dynamic']['source'][var]['var_name']])

            if not readed_grid:
                logging.info(" ---> Read geographic references")
                nrows = len(file_open.lat)
                ncols = len(file_open.lon)
                res = float(abs(file_open.lat[1]-file_open.lat[0]))
                xll = float(min(file_open.lon)) - res/2
                yll = float(min(file_open.lat)) - res/2

                attributes_dict = {'ncols': ncols,
                                   'nrows': nrows,
                                   'nodata_value': -9999.0,
                                   'xllcorner': xll,
                                   'yllcorner': yll,
                                   'cellsize': res}

                geo_x_values = np.sort(file_open.lon)
                # Check if lo is in the 0-360 format and shift to -180 180
                if any(geo_x_values>180):
                    geo_x_values = geo_x_values-360
                geo_y_values = np.sort(file_open.lat)
                geo_data_values = -9999

                readed_grid = True

        if not missing_input:
            logging.info(' ---> Create variables dataset...')
            dset_data = create_dset(inMaps, geo_data_values, geo_x_values, geo_y_values, timeNow,
                                global_attrs_dict=attributes_dict)

            file_out_time_step = os.path.join(data_settings['data']['dynamic']['destination']['folder_name'], data_settings['data']['dynamic']['destination']['file_name']).format(**template_time_step)

            logging.info(' ---> Write output...')
            os.makedirs(os.path.dirname(file_out_time_step), exist_ok=True)
            write_dset(file_out_time_step, dset_data, dset_mode='w', dset_engine='h5netcdf', dset_compression_level=0,
                       dset_format='NETCDF4',
                       dim_key_time='time', fill_value=-9999.0)

            if data_settings['data']['dynamic']['destination']['file_compression']:
                os.system('gzip -f ' + file_out_time_step)




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


# --------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to create datasets
# Method to create datasets
def create_dset(var_data_dict, geo_data_values, geo_x_values, geo_y_values, time_data_values,
                var_attrs_dict=None,
                geo_data_attrs_dict=None, geo_data_name='terrain',
                geo_x_attrs_dict=None, geo_x_name='longitude',
                geo_y_attrs_dict=None, geo_y_name='latitude',
                geo_data_1d=False,
                global_attrs_dict=None,
                coord_name_x='longitude', coord_name_y='latitude', coord_name_time='time',
                dim_name_x='west_east', dim_name_y='south_north', dim_name_time='time',
                dims_order_2d=None, dims_order_3d=None,
                missing_value_default=-9999.0, fill_value_default=-9999.0, meteogrid_dem_available=False, time_data=None):

    # Ensure latitudes are increasing (South to North)
    lat_descending = geo_y_values[0] > geo_y_values[-1]
    if lat_descending:
        geo_y_values = geo_y_values[::-1]
        for key in var_data_dict:
            var_data_dict[key] = np.flipud(var_data_dict[key])
        if isinstance(geo_data_values, np.ndarray) and geo_data_values.ndim == 2:
            geo_data_values = np.flipud(geo_data_values)

    geo_x_values_tmp = geo_x_values
    geo_y_values_tmp = geo_y_values
    if geo_data_1d:
        if (geo_x_values.shape.__len__() == 2) and (geo_y_values.shape.__len__() == 2):
            geo_x_values_tmp = geo_x_values[0, :]
            geo_y_values_tmp = geo_y_values[:, 0]
    else:
        if (geo_x_values.shape.__len__() == 1) and (geo_y_values.shape.__len__() == 1):
            geo_x_values_tmp, geo_y_values_tmp = np.meshgrid(geo_x_values, geo_y_values)

    if dims_order_2d is None:
        dims_order_2d = [dim_name_y, dim_name_x]
    if dims_order_3d is None:
        dims_order_3d = [dim_name_y, dim_name_x, dim_name_time]

    if not isinstance(time_data_values, list):
        time_data_values = [time_data_values]

    if var_attrs_dict is None:
        var_attrs_dict = {var_name_step: None for var_name_step in var_data_dict.keys()}

    var_dset = xr.Dataset(coords={coord_name_time: ([dim_name_time], time_data_values)})

    if global_attrs_dict is not None:
        for k, v in global_attrs_dict.items():
            var_dset.attrs[k] = v
        if 'nodata_value' not in global_attrs_dict:
            global_attrs_dict['nodata_value'] = -9999.0

    var_dset.coords[coord_name_time] = var_dset.coords[coord_name_time].astype('datetime64[ns]')

    if meteogrid_dem_available:
        var_da_terrain = xr.DataArray(geo_data_values, name=geo_data_name,
                                      dims=dims_order_2d,
                                      coords={coord_name_x: ([dim_name_y, dim_name_x], geo_x_values_tmp),
                                              coord_name_y: ([dim_name_y, dim_name_x], geo_y_values_tmp)})
        var_dset[geo_data_name] = var_da_terrain

    if geo_data_attrs_dict:
        geo_attrs_dict_info, geo_attrs_dict_encoded = select_attrs(geo_data_attrs_dict)
        if geo_attrs_dict_info:
            var_dset[geo_data_name].attrs = geo_attrs_dict_info
        if geo_attrs_dict_encoded:
            var_dset[geo_data_name].encoding = geo_attrs_dict_encoded

    if geo_x_name in var_dset.coords and geo_x_attrs_dict:
        geo_attrs_info, geo_attrs_encoded = select_attrs(geo_x_attrs_dict)
        if geo_attrs_info:
            var_dset[geo_x_name].attrs = geo_attrs_info
        if geo_attrs_encoded:
            var_dset[geo_x_name].encoding = geo_attrs_encoded

    if geo_y_name in var_dset.coords and geo_y_attrs_dict:
        geo_attrs_info, geo_attrs_encoded = select_attrs(geo_y_attrs_dict)
        if geo_attrs_info:
            var_dset[geo_y_name].attrs = geo_attrs_info
        if geo_attrs_encoded:
            var_dset[geo_y_name].encoding = geo_attrs_encoded

    for (var_name, var_data), var_attrs in zip(var_data_dict.items(), var_attrs_dict.values()):

        if var_data.ndim == 2:
            var_da = xr.DataArray(var_data, name=var_name,
                                  dims=dims_order_2d,
                                  coords={coord_name_x: ([dim_name_y, dim_name_x], geo_x_values_tmp),
                                          coord_name_y: ([dim_name_y, dim_name_x], geo_y_values_tmp)})
        elif var_data.ndim == 3:
            var_da = xr.DataArray(var_data, name=var_name,
                                  dims=dims_order_3d,
                                  coords={coord_name_time: ([dim_name_time], time_data),
                                          coord_name_x: ([dim_name_y, dim_name_x], geo_x_values_tmp),
                                          coord_name_y: ([dim_name_y, dim_name_x], geo_y_values_tmp)})
        else:
            raise NotImplementedError(f"Data with {var_data.ndim} dimensions not supported.")

        if var_attrs:
            missing_value = next((var_attrs.get(k) for k in attributes_defined_lut['filtering_attrs']['Missing_value']
                                  if k in var_attrs), missing_value_default)

            valid_range = next((var_attrs.get(k) for k in attributes_defined_lut['filtering_attrs']['Valid_range']
                                if k in var_attrs), None)
            if valid_range:
                var_da = clip_data(var_da, valid_range, missing_value=missing_value)

            fill_value = next((var_attrs.get(k) for k in attributes_defined_lut['encoding_attrs']['_FillValue']
                               if k in var_attrs), fill_value_default)

            if meteogrid_dem_available:
                var_da = var_da.where(var_da_terrain > global_attrs_dict['nodata_value'], other=fill_value)

        var_dset[var_name] = var_da

        if var_attrs:
            attr_info, attr_encoded = select_attrs(var_attrs)
            if attr_info:
                var_dset[var_name].attrs = attr_info
            if attr_encoded:
                var_dset[var_name].encoding = attr_encoded

    return var_dset
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to select attributes
def select_attrs(attrs_var_raw):

    if attrs_var_raw is not None:

        attrs_var_tmp = deepcopy(attrs_var_raw)
        for attrs_def_key, attrs_def_items in attributes_defined_lut.items():

            if isinstance(attrs_def_items, dict):
                for field_key, field_items in attrs_def_items.items():
                    if isinstance(field_items, list):
                        for field_name in field_items:
                            if field_name in attrs_var_tmp:
                                if field_name != field_key:
                                    field_value = attrs_var_tmp[field_name]
                                    attrs_var_tmp.pop(field_name, None)
                                    attrs_var_tmp[field_key] = field_value
                    else:
                        logging.error(' ===> Type variable not allowed')
                        raise NotImplemented('Attributes values type not implemented yet')

            elif isinstance(attrs_def_items, list):
                pass
            else:
                logging.error(' ===> Type variable not allowed')
                raise NotImplemented('Attributes values type not implemented yet')

        blocked_attrs = attributes_defined_lut['blocking_attrs']
        encoded_attrs = list(attributes_defined_lut['encoding_attrs'].keys())

        attrs_var_info = {}
        attrs_var_encoded = {}
        for attrs_var_key, attrs_var_value in attrs_var_tmp.items():

            if attrs_var_value is not None:
                if isinstance(attrs_var_value, list):
                    var_string = [str(value) for value in attrs_var_value]
                    attrs_var_value = ','.join(var_string)
                if isinstance(attrs_var_value, dict):
                    var_string = json.dumps(attrs_var_value)
                    attrs_var_value = var_string

                if attrs_var_key in encoded_attrs:
                    attrs_var_encoded[attrs_var_key] = attrs_var_value
                elif attrs_var_key in blocked_attrs:
                    pass
                else:
                    attrs_var_info[attrs_var_key] = attrs_var_value
    else:
        attrs_var_info = None
        attrs_var_encoded = None

    return attrs_var_info, attrs_var_encoded
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to clip data 2D/3D using a min/max threshold(s) and assign a missing value
def clip_data(map, valid_range=None, missing_value=None):

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
# Method to write dataset
def write_dset(file_name,
               dset_data, dset_mode='w', dset_engine='h5netcdf', dset_compression_level=0, dset_format='NETCDF4',
               dim_key_time='time', fill_value=-9999.0):

    dset_encoding = {}
    for var_name in dset_data.data_vars:

        if isinstance(var_name, bytes):
            var_name_upd = var_name.decode("utf-8")
            dset_data = var_name.rename({var_name: var_name_upd})
            var_name = var_name_upd

        var_attrs_encoding = dset_data[var_name].encoding

        if '_FillValue' not in list(var_attrs_encoding.keys()):
            var_attrs_encoding['_FillValue'] = fill_value
        if dset_compression_level > 0:
            if 'zlib' not in list(var_attrs_encoding.keys()):
                var_attrs_encoding['zlib'] = True
            if 'complevel' not in list(var_attrs_encoding.keys()):
                var_attrs_encoding['complevel'] = dset_compression_level

        dset_encoding[var_name] = var_attrs_encoding

    if dim_key_time in list(dset_data.coords):
        dset_encoding[dim_key_time] = {'calendar': 'gregorian'}

    dset_data.to_netcdf(path=file_name, format=dset_format, mode=dset_mode, engine=dset_engine,
                        encoding=dset_encoding)
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

# -------------------------------------------------------------------------------------
# Method to fill path names
def fill_template_time_step(template_dict, timeNow):
    template_compiled={}
    for i in template_dict.keys():
        if '%' in template_dict[i]:
            template_compiled[i] = timeNow.strftime(template_dict[i])
        else:
            template_compiled[i] = template_dict[i]

    return template_compiled
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Call script from external library

if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------
