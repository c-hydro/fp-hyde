"""
Library Features:

Name:          lib_astrorad_args
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20200215'
Version:       '1.1.0'
"""

# -------------------------------------------------------------------------------------
# Data formats
time_type = 'GMT'  # 'GMT', 'local'
time_format = "%Y%m%d%H%M"  # '%Y%m%d%H%M'
time_units = 'days since 1858-11-17 00:00:00'
time_calendar = 'gregorian'

# Logging information
logger_name = 'logger_astrorad'
logger_file = 'log.txt'
logger_handle = 'file'  # 'file' or 'stream'
logger_formatter = '%(asctime)s %(name)-12s %(levelname)-8s %(filename)s:[%(lineno)-6s - %(funcName)20s()] %(message)s'

# Default lookup table for cloud factor against rain values
lookup_table_cf_default = {
    'CF_L1': {'Rain': [0, 1],       'CloudFactor': [0.95]},
    'CF_L2': {'Rain': [1, 3],   	'CloudFactor': [0.75]},
    'CF_L3': {'Rain': [3, 5],   	'CloudFactor': [0.65]},
    'CF_L4': {'Rain': [5, 10],   	'CloudFactor': [0.50]},
    'CF_L5': {'Rain': [10, None],   'CloudFactor': [0.15]}
}
# Datasets name accepted to use the configuration data method of the astrorad model
var_list_default = ['rain', 'cloud_factor']
# -------------------------------------------------------------------------------------
