#!/usr/bin/python3

"""
HyDE Downloading Tool - NWP GFS 0.25 historical downloader

__date__ = '20210618'
__version__ = '1.0.0'
__author__ =
        'Andrea Libertino (andrea.libertino@cimafoundation.org',
        'Fabio Delogu (fabio.delogu@cimafoundation.org',
        'Alessandro Masoero (alessandro.masoero@cimafoundation.org',
__library__ = 'HyDE'

General command line:
python3 hyde_downloader_nwp_gfs_historical.py -settings_file configuration.json -time YYYY-MM-DD HH:MM

Version(s):
20210618 (1.0.0) --> Beta release
"""
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Complete library
import logging
from argparse import ArgumentParser
from datetime import timedelta, datetime
from siphon.catalog import TDSCatalog
from siphon.ncss import NCSS
from xarray.backends import NetCDF4DataStore
import xarray as xr
import pandas as pd
from copy import deepcopy
import os
import time
import json
import numpy as np
from siphon.http_util import session_manager
import netrc

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Algorithm information
alg_name = 'HYDE DOWNLOADING TOOL - NWP GFS HISTORICAL DOWNLOADER'
alg_version = '1.0.0'
alg_release = '2021-06-18'
# Algorithm parameter(s)
time_format = '%Y%m%d%H%M'
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Script Main
def main():

    # -------------------------------------------------------------------------------------
    # Get algorithm settings
    alg_settings, alg_time = get_args()

    # Set algorithm settings
    data_settings = read_file_json(alg_settings)

    # Initialize UCAR user/pwd
    if data_settings["data"]["credential_historical_ucar_archive"]["username"] is None or data_settings["data"]["credential_historical_ucar_archive"]["password"] is None:
        netrc_handle = netrc.netrc()
        UCARuser, _, UCARpwd = netrc_handle.authenticators('rda.ucar.edu')
    else:
        UCARuser = data_settings["data"]["credential_historical_ucar_archive"]["username"]
        UCARpwd = data_settings["data"]["credential_historical_ucar_archive"]["password"]

    # Set algorithm logging
    os.makedirs(data_settings['data']['log']['folder'], exist_ok=True)
    set_logging(logger_file=os.path.join(data_settings['data']['log']['folder'], data_settings['data']['log']['filename']))
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    # -------------------------------------------------------------------------------------
    # Info algorithm
    logging.info(' ============================================================================ ')
    logging.info(' ==> ' + alg_name + ' (Version: ' + alg_version + ' Release_Date: ' + alg_release + ')')
    logging.info(' ==> START ... ')
    logging.info(' ')

    # Time algorithm information
    start_time = time.time()
    # -------------------------------------------------------------------------------------

    timeRun = datetime.strptime(alg_time,'%Y-%m-%d %H:%M')
    timeEnd = timeRun + pd.Timedelta(str(data_settings["data"]["dynamic"]["time"]["time_forecast_period"]) + data_settings["data"]["dynamic"]["time"]["time_forecast_frequency"])

    outFolder = data_settings["data"]["dynamic"]["outcome"]["folder"]

    var_dic = deepcopy(data_settings["algorithm"]["template"])
    for keys in data_settings["algorithm"]["template"].keys():
        var_dic[keys] = timeRun.strftime(data_settings["algorithm"]["template"][keys])

    outFolder=outFolder.format(**var_dic)
    os.makedirs(outFolder, exist_ok=True)
    os.system("rm " + os.path.join(outFolder, data_settings["algorithm"]["ancillary"]["domain"] + "_gfs.t" + timeRun.strftime('%H') + "z.0p25." + timeRun.strftime('%Y%m%d') + "_*.nc") + " | True")

    # Starting info
    logging.info(' --> TIME RUN: ' + str(timeRun))
    logging.info(' --> TIME END: ' + str(timeEnd))

    variables = data_settings["data"]["dynamic"]["variables"]
    variables_name = [i for i in variables.keys()]

    # Extract keys info
    variables_info = {}
    for varHMC in variables_name:
        for varGFS in variables[varHMC].keys():
            variables_info[varGFS] = variables[varHMC][varGFS]

    logging.info(' ---> Connect to UCAR archive...')
    session_manager.set_session_options(auth=(UCARuser, UCARpwd))
    archiveFrc = TDSCatalog(
        'https://rda.ucar.edu/thredds/catalog/files/g/ds084.1/' + timeRun.strftime('%Y') + '/' + timeRun.strftime(
            '%Y%m%d') + '/catalog.xml')
    listFrc = [i for i in list(archiveFrc.datasets.values()) if timeRun.strftime('%Y%m%d%H') in i.name and  int(i.name[-9:-6])<=data_settings["data"]["dynamic"]["time"]["time_forecast_period"]]
    outVarName = [varGFS for varHMC in variables.keys() for varGFS in variables[varHMC]]

    frcStepTimes = [timeRun + pd.Timedelta(str(int(frcStepDS.name[-9:-6])) + 'H') for frcStepDS in listFrc[1:]]

    logging.info(' ---> Connect to UCAR archive... OK')

    # Query remote UCAR server for data
    for frcStepDS, time_frc in zip(listFrc[1:], frcStepTimes):
        ncss = NCSS(frcStepDS.access_urls['NetcdfSubset'])

        # Remove variables not contained in dataset
        variablesGFS = convert_historical_GFS_varnames(outVarName)
        presentVariables = ()

        for v in variablesGFS:
            if v in ncss.variables:
                presentVariables = presentVariables + (v,)

        if len(presentVariables) < len(outVarName):
            variablesGFS = [w.replace('6_Hour', '3_Hour') for w in variablesGFS]
            presentVariables = ()
            for v in variablesGFS:
                if v in ncss.variables:
                    presentVariables = presentVariables + (v,)

            if len(presentVariables) < len(variablesGFS):
                logging.warning("---> WARNING! Some variables are not present in the original dataset!")
        logging.info(' --> Forecast time ' + time_frc.strftime("%Y-%m-%d %H:%M"))
        logging.info(' --> Download forecast file ' + frcStepDS.name)
        query = ncss.query()
        query.lonlat_box(data_settings["data"]["static"]["bounding_box"]["lon_left"], data_settings["data"]["static"]["bounding_box"]["lon_right"], data_settings["data"]["static"]["bounding_box"]["lat_bottom"], data_settings["data"]["static"]["bounding_box"]["lat_top"])
        query.accept('netcdf4')
        query.variables(*presentVariables)

        query.all_times()
        data = ncss.get_data(query)
        data = xr.open_dataset(NetCDF4DataStore(data)).drop_dims("bounds_dim", errors='ignore')

        if frcStepDS.name == listFrc[1].name:
            frcDS = xr.Dataset(coords={'time':frcStepTimes, 'lat':data.latitude.values, 'lon':data.longitude.values})
            for variableGFS in outVarName:
                frcDS[variableGFS] = xr.DataArray(dims=['time','lat','lon'], coords={'time':pd.date_range(timeRun + pd.Timedelta('1H'), timeEnd, freq='1H'), 'lat':data.latitude.values, 'lon':data.longitude.values})

        for presentVariable, variableGFS in zip(presentVariables, outVarName):
            logging.info(' ---> Download variable ' + presentVariable)
            if len(data[presentVariable].dims) > 3:
                if 'height' in data[presentVariable].dims:
                    data_step = data.loc[{'height':variables_info[variableGFS]["height"]}][presentVariable].squeeze().rename({'longitude':'lon','latitude':'lat'})
                else:
                    height_dim = [i for i in data[presentVariable].dims if 'height' in i]
                    if len(height_dim) > 1:
                        logging.error(" --> ERROR! Cannot identify heigth dim name for variable " + presentVariable)
                        raise ValueError
                    else:
                        data_step = data.loc[{height_dim[0]: variables_info[variableGFS]["height"]}][presentVariable].squeeze().rename({'longitude':'lon','latitude':'lat'})
            else:
                data_step = data[presentVariable].squeeze().rename({'longitude':'lon','latitude':'lat'})

            frcDS[variableGFS].loc[{'time':time_frc}] = data_step

    logging.info(' ---> Download forecast file ... OK ')
    output_list = []

    # Merge and reformat downloaded file to be consistent with the outcomes of the NOMADS gfs download procedure
    logging.info(' ---> Compute output files ... ')
    timeRange = pd.date_range(timeRun + pd.Timedelta(variables[varHMC][varGFS]["freq"]), timeEnd,
                              freq=variables[varHMC][varGFS]["freq"])

    for varHMC in variables_name:
        logging.info(' ---> Elaborate ' + varHMC + ' file...')
        variables_GFS_in = [i for i in variables[varHMC].keys()]
        logging.info(' ---> Is expected to contain GFS variables:' + ','.join(variables_GFS_in))
        for varGFS in variables[varHMC].keys():
            varIn = frcDS[varGFS]
            varFilled = varIn.reindex({'time': timeRange}, method='nearest')

            if varGFS=="Precipitation_rate_surface_Mixed_intervals_Average":
                if not data_settings['data']['dynamic']['vars_standards']['convert2standard_continuum_format']:
                    temp = deepcopy(varFilled)*3600
                    varFilled = temp.cumsum(dim=temp.dims[0], keep_attrs=True)
                else:
                    varFilled = deepcopy(varFilled)*3600

            outName = data_settings["algorithm"]["ancillary"]["domain"] + "_gfs.t" + timeRun.strftime('%H') + "z.0p25." + timeRun.strftime('%Y%m%d') + "_" + variables[varHMC][varGFS]["out_group"] + ".nc"

            if not os.path.isfile(os.path.join(outFolder, outName)):
                varFilled.to_dataset(name=variables[varHMC][varGFS]["varName"]).to_netcdf(
                    path=os.path.join(outFolder, outName), mode='w')
            else:
                varFilled.to_dataset(name=variables[varHMC][varGFS]["varName"]).to_netcdf(
                    path=os.path.join(outFolder, outName), mode='a')

            output_list.append(outName)
            logging.info(' ----> Compute ' + varGFS + ' variable...OK')

    output_list = np.unique(output_list)

    if data_settings['data']['dynamic']['vars_standards']['convert2standard_continuum_format'] is True:
        logging.info(' ----> Elaborate output file for being Continuum complient...')
        for out_file_name in output_list:
            out_file = deepcopy(xr.open_dataset(os.path.join(outFolder, out_file_name)))
            os.remove(os.path.join(outFolder, out_file_name))
            if '2t' in out_file.variables.mapping.keys():
                if data_settings['data']['dynamic']['vars_standards']['source_temperature_mesurement_unit'] == 'C':
                    pass
                elif data_settings['data']['dynamic']['vars_standards']['source_temperature_mesurement_unit'] == 'K':
                    logging.info(' ------> Convert temperature to C ... ')
                    if os.path.isfile(os.path.join(outFolder, out_file_name)):
                        os.remove(os.path.join(outFolder, out_file_name))
                    out_file['2t_C'] = out_file['2t'] - 273.15
                    out_file['2t_C'].attrs['long_name'] = '2 metre temperature'
                    out_file['2t_C'].attrs['units'] = 'C'
                    out_file['2t_C'].attrs['standard_name'] = "air_temperature"
                    out_file = out_file.rename({'2t': '2t_K'})
                    logging.info(' ------> Convert temperature to C ... DONE')
                else:
                    raise NotImplementedError

            if '10u' in out_file.variables.mapping.keys() and data_settings['data']['dynamic']['vars_standards']['source_wind_separate_components'] is True:
                logging.info(' ------> Combine wind component ... ')
                if os.path.isfile(os.path.join(outFolder, out_file_name)):
                    os.remove(os.path.join(outFolder, out_file_name))
                out_file['10wind'] = np.sqrt(out_file['10u'] ** 2 + out_file['10v'] ** 2)
                out_file['10wind'].attrs['long_name'] = '10 m wind'
                out_file['10wind'].attrs['units'] = 'm s**-1'
                out_file['10wind'].attrs['standard_name'] = "wind"
                logging.info(' ------> Combine wind component ... DONE')

            logging.info(' -----> Shift longitude to be in the -180 +180 range')
            out_file = out_file.assign_coords({'lon': np.where(out_file['lon'].values > 180, out_file['lon'].values - 360, out_file['lon'].values)})
            out_file.to_netcdf(os.path.join(outFolder, out_file_name))

        logging.info(' ----> Elaborate output file for being Continuum complient...DONE')


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
    logging.root.setLevel(logging.DEBUG)

    # Open logging basic configuration
    logging.basicConfig(level=logging.DEBUG, format=logger_format, filename=logger_file, filemode='w')

    # Set logger handle
    logger_handle_1 = logging.FileHandler(logger_file, 'w')
    logger_handle_2 = logging.StreamHandler()
    # Set logger level
    logger_handle_1.setLevel(logging.DEBUG)
    logger_handle_2.setLevel(logging.DEBUG)
    # Set logger formatter
    logger_formatter = logging.Formatter(logger_format)
    logger_handle_1.setFormatter(logger_formatter)
    logger_handle_2.setFormatter(logger_formatter)

    # Add handle to logging
    logging.getLogger('').addHandler(logger_handle_1)
    logging.getLogger('').addHandler(logger_handle_2)

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
def convert_historical_GFS_varnames(varList):
    conversion_dict = {"Precipitation_rate_surface_Mixed_intervals_Average":"Precipitation_rate_surface_6_Hour_Average", "Downward_Short-Wave_Radiation_Flux_surface_Mixed_intervals_Average":"Downward_Short-Wave_Radiation_Flux_surface_6_Hour_Average", "Downward_Long-Wave_Radp_Flux_surface_Mixed_intervals_Average":"Downward_Long-Wave_Radp_Flux_surface_6_Hour_Average", "Albedo_surface_Mixed_intervals_Average":"Albedo_surface_6_Hour_Average"}
    outputVarList = [conversion_dict.get(x, x) for x in varList]
    return outputVarList

# ----------------------------------------------------------------------------
# Call script from external library
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------





