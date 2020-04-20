"""
Class Features

Name:          drv_data_ecmwf_geo
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20200210'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging

from os import makedirs, remove
from os.path import join, split, exists

from src.hyde.algorithm.settings.nwp.ecmwf.lib_ecmwf_args import logger_name
from src.hyde.algorithm.geo.nwp.ecmwf.lib_ecmwf_geo import load_domain
from src.hyde.algorithm.io.nwp.ecmwf.lib_ecmwf_io_generic import read_obj, write_obj

# Log
log_stream = logging.getLogger(logger_name)
#######################################################################################


# -------------------------------------------------------------------------------------
# Class to compute geographical data
class DataGeo:

    # -------------------------------------------------------------------------------------
    # Method class initialization
    def __init__(self, file_domain, file_grid, file_updating=False):

        # -------------------------------------------------------------------------------------
        # Get path(s) and filename(s)
        filepath_domain, filename_domain = split(file_domain)
        filepath_grid, filename_grid = split(file_grid)

        # Store information in global workspace
        self.filepath_domain = filepath_domain
        self.filename_domain = filename_domain
        self.filepath_grid = filepath_grid
        self.filename_grid = filename_grid

        if not exists(self.filepath_grid):
            makedirs(self.filepath_grid)

        if file_updating:
            if exists(join(self.filepath_grid, self.filename_grid)):
                remove(join(self.filepath_grid, self.filename_grid))
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to get geographical data
    def getDataGeo(self):

        log_stream.info(' ---> Reference grid ... ')
        if not exists(join(self.filepath_grid, self.filename_grid)):

            if exists(join(self.filepath_domain, self.filename_domain)):

                domain_obj = load_domain(join(self.filepath_domain, self.filename_domain))
                write_obj(join(self.filepath_grid, self.filename_grid), domain_obj)

                log_stream.info(' ---> Reference grid ... DONE')

            else:
                log_stream.error(' ---> Reference grid ... FAILED!')
                raise FileNotFoundError(
                    'File not found! [' + join(self.filepath_domain, self.filename_domain + '] '))

        else:
            log_stream.info(' ---> Reference grid ... PREVIOUSLY CREATED')
            domain_obj = read_obj(join(self.filepath_grid, self.filename_grid))

        return domain_obj

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
