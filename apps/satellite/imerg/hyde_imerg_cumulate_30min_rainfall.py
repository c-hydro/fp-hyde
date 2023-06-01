"""
HyDE Processing Tool - NWP GFS to OBS

__date__ = '20220601'
__version__ = '1.0.0'
__author__ =
        'Andrea Libertino (andrea.libertino@cimafoundation.org',
__library__ = 'hyde'

General command line:
python hyde_nwp_gfs_to_obs.py -settings_file configuration.json -time YYYY-MM-DD HH:MM

Version(s):
20220601 (1.0.0) --> Beta release for hyde package
"""
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
import logging, json, os, time
from argparse import ArgumentParser
import pandas as pd
import xarray as xr
import datetime
import rioxarray

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Algorithm information
alg_name = 'HyDE Processing Tool - nwp gfs to obs'
alg_version = '1.0.0'
alg_release = '2021-03-11'
# Algorithm parameter(s)
time_format = '%Y%m%d%H%M'
# -------------------------------------------------------------------------------------

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

    time_end = datetime.datetime.strptime(alg_time,'%Y-%m-%d %H:%M')
    time_start = time_end - pd.Timedelta(str(data_settings["data"]["dynamic"]["time"]["time_period"]) + data_settings["data"]["dynamic"]["time"]["period_unit"])
    timeRange = pd.date_range(time_start,time_end, freq=data_settings["data"]["dynamic"]["time"]["time_frequency"])

    logging.info(' ---> Observed period : ' + time_start.strftime('%Y-%m-%d %H:%M') + ' - ' + time_end.strftime('%Y-%m-%d %H:%M'))

    for time_now in timeRange:
        logging.info(' ----> Compute time step ' + time_now.strftime("%Y-%m-%d %H:%M") + '...')
        template_time_step = fill_template_time_step(data_settings['algorithm']['template'], time_now)
        template_prev_time_step = fill_template_time_step(data_settings['algorithm']['template'], time_now - pd.Timedelta("30min"))

        template_time_step["domain"] = data_settings["algorithm"]["info"]["domain"]
        template_prev_time_step["domain"] = data_settings["algorithm"]["info"]["domain"]

        for prod in data_settings['data']['dynamic']['products'].keys():
            logging.info(' ---> Compute product: ' + prod)

            file_in_time_step = os.path.join(data_settings['data']['dynamic']['products'][prod]['source_folder'],
                                              data_settings['data']['dynamic']['products'][prod]['source_filename']).format(**template_time_step)
            file_out_time_step = os.path.join(data_settings['data']['dynamic']['products'][prod]['destination_folder'],
                                              data_settings['data']['dynamic']['products'][prod][
                                                  'destination_filename']).format(**template_time_step)

            if os.path.isfile(file_out_time_step):
                if data_settings["algorithm"]["flags"]["recompute_existing"]:
                    logging.info(" ----> Output file exist! It will be overwritten!")
                else:
                    logging.info(" ----> Output file exist! Skip!")
                    continue

            if os.path.isfile(file_in_time_step):
                file_in_prev_time_step = os.path.join(data_settings['data']['dynamic']['products'][prod]['source_folder'],
                                                 data_settings['data']['dynamic']['products'][prod][
                                                     'source_filename']).format(**template_prev_time_step)
                if os.path.isfile(file_in_prev_time_step):
                    logging.info(' ----> All necessary file for the time step are available!')
                    rain_now_mm_h = xr.open_rasterio(file_in_time_step) + xr.open_rasterio(file_in_prev_time_step)
                else:
                    logging.warning(' ----> WARNING! Previous time step is not available!')
                    continue
            else:
                logging.warning(' ----> WARNING! No data available for considered time step!')
                continue

            os.makedirs(os.path.dirname(file_out_time_step), exist_ok=True)
            rain_now_mm_h.rio.to_raster(file_out_time_step, compress="DEFLATE")

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
