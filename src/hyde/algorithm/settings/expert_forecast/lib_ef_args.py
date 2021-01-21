"""
Library Features:

Name:          lib_ef_args
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20201202'
Version:       '1.0.0'
"""

# -------------------------------------------------------------------------------------
# Data formats
time_type = 'GMT'  # 'GMT', 'local'
time_format = "%Y%m%d%H%M"  # '%Y%m%d%H%M'
time_units = 'days since 1858-11-17 00:00:00'
time_calendar = 'gregorian'

# Logging information
logger_name = 'logger_ef_rain'
logger_file = 'log.txt'
logger_handle = 'file'  # 'file' or 'stream'
logger_formatter = '%(asctime)s %(name)-12s %(levelname)-8s %(filename)s:[%(lineno)-6s - %(funcName)20s()] %(message)s'
# -------------------------------------------------------------------------------------
