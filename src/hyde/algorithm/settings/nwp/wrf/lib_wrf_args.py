"""
Library Features:

Name:          lib_wrf_args
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210522'
Version:       '1.2.0'
"""

# -------------------------------------------------------------------------------------
# Data formats
time_type = 'GMT'  # 'GMT', 'local'
time_format = "%Y%m%d%H%M"  # '%Y%m%d%H%M'
time_units = 'days since 1858-11-17 00:00:00'
time_calendar = 'gregorian'

# Logging information
logger_name = 'logger_wrf'
logger_file = 'log.txt'
logger_handle = 'file'  # 'file' or 'stream'
logger_formatter = '%(asctime)s %(name)-12s %(levelname)-8s %(filename)s:[%(lineno)-6s - %(funcName)20s()] %(message)s'
# -------------------------------------------------------------------------------------
