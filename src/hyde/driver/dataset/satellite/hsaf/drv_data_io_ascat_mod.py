"""
Library Features:

Name:          drv_data_io_ascat_mod
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190729'
Version:       '1.0.0'
"""
#################################################################################
# Library
import logging
import pandas as pd

from os import remove, removedirs, listdir
from os.path import split, exists, join

from src.common.utils.lib_utils_op_dict import mergeDict

from src.hyde.algorithm.utils.satellite.hsaf.lib_ascat_generic import check_filename
from src.hyde.dataset.satellite.ascat.lib_ascat_organizer_mod_base import AscatOrganizerNRT, AscatOrganizerDataRecord
from src.hyde.algorithm.settings.satellite.hsaf.lib_ascat_args import logger_name, \
    time_format, time_units, time_calendar

# Logging
log_stream = logging.getLogger(logger_name)
#################################################################################


# -------------------------------------------------------------------------------------
# Class data object
class DataObj(dict):
    pass
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class to compute time product
class DataProductTime:

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, **kwargs):
        self.time_step = kwargs['time_step']
        self.time_run = kwargs['time_run']
        self.time_settings = kwargs['time_settings']
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute data time
    def computeDataTime(self, time_ascending=True):

        time_step = self.time_step
        time_run = self.time_run
        time_settings = self.time_settings

        if 'time_observed_period' in time_settings and 'time_observed_frequency' in time_settings:
            time_observed_period = time_settings['time_observed_period']
            time_observed_frequency = time_settings['time_observed_frequency']
        else:
            time_observed_period = 0
            time_observed_frequency = 'H'

        if 'time_forecast_period' in time_settings and 'time_forecast_frequency' in time_settings:
            time_forecast_period = time_settings['time_forecast_period']
            time_forecast_frequency = time_settings['time_forecast_frequency']
        else:
            time_forecast_period = 0
            time_forecast_frequency = 'H'

        if time_observed_frequency == 'A-OFFSET':
            time_observed_frequency = pd.DateOffset(years=1)

        time_observed_range = pd.date_range(end=time_step, periods=time_observed_period + 1,
                                            freq=time_observed_frequency)
        time_forecast_range = pd.date_range(start=time_step, periods=time_forecast_period + 1,
                                            freq=time_forecast_frequency)

        if not time_observed_range.empty:
            time_from = time_observed_range[0]
        else:
            time_from = time_step
        if not time_forecast_range.empty:
            time_to = time_forecast_range[-1]
        else:
            time_to = time_step

        time_range = pd.date_range(start=time_from, end=time_to, freq=time_observed_frequency)
        time_range = time_range.sort_values(return_indexer=False, ascending=time_ascending)

        time_obj = DataObj
        time_obj.time_run = time_run
        time_obj.time_step = time_step
        time_obj.time_range = time_range
        time_obj.time_from = time_from
        time_obj.time_to = time_to
        time_obj.time_format = time_format
        time_obj.time_units = time_units
        time_obj.time_calendar = time_calendar

        return time_obj

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class to analyze data product
class DataProductWrapper:

    # -------------------------------------------------------------------------------------
    # Class variable(s)
    ascat_organizer = None
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, **kwargs):

        self.settings = kwargs['settings']
        self.time = kwargs['time']
        self.flags = kwargs['flags']

        self.var_in = kwargs['var_in']
        self.var_out = kwargs['var_out']

        self.filepath_domain, self.filename_domain = split(kwargs['rzsm_domain'])
        self.filepath_grid_ref_global, self.filename_grid_ref_global = split(kwargs['rzsm_grid_ref_global'])
        self.filepath_grid_ref_domain, self.filename_grid_ref_domain = split(kwargs['rzsm_grid_ref_domain'])
        self.filepath_grid_ref_dr, self.filename_grid_ref_dr = split(kwargs['rzsm_grid_ref_dr'])

        self.filepath_data_in, self.filename_tmpl_in = split(kwargs['rzsm_data_in'])
        self.filepath_data_out, self.filename_tmpl_out = split(kwargs['rzsm_data_out'])
        self.filepath_data_analysis, self.filename_tmpl_analysis = split(kwargs['rzsm_data_analysis'])
        self.filepath_data_points, self.filename_tmpl_points = split(kwargs['rzsm_data_points'])
        self.filepath_data_maps, self.filename_tmpl_maps = split(kwargs['rzsm_data_maps'])
        self.filepath_data_dr, self.filename_tmpl_dr = split(kwargs['rzsm_data_dr'])
        self.filepath_data_dr_scaled, self.filename_tmpl_dr_scaled = split(kwargs['rzsm_data_dr_scaled'])

        self.rzsm_updating_out = kwargs['rzsm_updating_out']
        self.rzsm_updating_analysis = kwargs['rzsm_updating_analysis']

        if 'rzsm_updating_points' in kwargs:
            self.rzsm_updating_points = kwargs['rzsm_updating_points']
        else:
            self.rzsm_updating_points = None

        if 'rzsm_updating_maps' in kwargs:
            self.rzsm_updating_maps = kwargs['rzsm_updating_maps']
        else:
            self.rzsm_updating_maps = None

        if 'rzsm_updating_dr' in kwargs:
            self.rzsm_updating_dr = kwargs['rzsm_updating_dr']
        else:
            self.rzsm_updating_dr = None

        self.var_obj_in = self.__findDataVariable(self.var_in)
        self.var_obj_out = self.__findDataVariable(self.var_out)

        self.var_list_in = list(self.var_obj_in.keys())
        self.var_list_out = list(self.var_obj_out.keys())

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to find variable data
    @staticmethod
    def __findDataVariable(var_data, var_tag_id='id', var_tag_attributes='attributes'):

        var_data_id = var_data[var_tag_id]
        var_data_attrs = var_data[var_tag_attributes]

        var_name = var_data_id['var_name']
        var_n = var_name.__len__()

        var_obj = {}
        for id, name in enumerate(var_name):
            var_obj[name] = {}
            for var_attrs_key, var_attrs_value in var_data_attrs.items():
                var_obj[name][var_attrs_key] = {}

                if not isinstance(var_attrs_value, list):
                    var_attrs_value = [var_attrs_value] * var_n

                var_obj[name][var_attrs_key] = var_attrs_value[id]

        return var_obj

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to clean ancillary and not useful file(s) and folder(s)
    def cleanDataProduct(self, rzsm_cleaning_out=False, rzsm_cleaning_analysis=False, rzsm_cleaning_points=False):

        driver = self.ascat_organizer
        cells = self.ascat_organizer.dr_cells

        data_cleaning = {
            'out_data': [rzsm_cleaning_out, driver.ascat_path_out, driver.ascat_filename_tmpl_out],
            'analysis_data': [rzsm_cleaning_analysis, driver.ascat_path_analysis, driver.ascat_filename_tmpl_analysis],
            'points_data': [rzsm_cleaning_points, driver.ascat_path_points, driver.ascat_filename_tmpl_points],
            'out_ancillary': [rzsm_cleaning_out, driver.ascat_path_out, 'grid.nc']}

        for data_key, data_value in data_cleaning.items():
            if data_value[0]:
                for cell in cells:
                    file_cleaning = join(data_value[1], data_value[2] % cell)
                    if exists(file_cleaning):
                        remove(file_cleaning)
                if exists(data_value[1]):
                    if not listdir(data_value[1]):
                        removedirs(data_value[1])

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to execute data record
    def execDataRecord(self):

        self.ascat_organizer = AscatOrganizerDataRecord(
            self.time.time_run,
            self.filepath_data_in,
            self.filepath_data_out,
            self.filepath_data_dr_scaled,
            self.filepath_data_analysis,
            self.filepath_data_points,
            self.filepath_data_maps,
            self.filepath_grid_ref_domain,
            self.filepath_grid_ref_dr,
            self.filepath_grid_ref_global,
            self.filepath_domain,
            self.filename_tmpl_in,
            self.filename_tmpl_out,
            self.filename_tmpl_dr_scaled,
            self.filename_tmpl_analysis,
            self.filename_tmpl_points,
            self.filename_tmpl_maps,
            self.filename_grid_ref_domain,
            self.filename_grid_ref_dr,
            self.filename_grid_ref_global,
            self.filename_domain,
            parameters=self.var_list_in,
            parameters_scaled=self.var_list_out,
            time_start=self.time.time_from, time_end=self.time.time_to,
            ascat_updating_out=self.rzsm_updating_out,
            ascat_updating_analysis=self.rzsm_updating_analysis,
            ascat_updating_dr=self.rzsm_updating_dr,
        )

        # Starting info time
        log_stream.info(' ---> Time == Start: ' + self.time.time_from.strftime(time_format) +
                        ' - End: ' + self.time.time_to.strftime(time_format) + ' ... ')

        # Method to compose data in time-series format
        log_stream.info(' ----> Create dr indexed time-series data ... ')
        if not check_filename(self.ascat_organizer.ascat_path_out, self.filepath_grid_ref_global,
                              self.ascat_organizer.ascat_filename_tmpl_out, self.filename_grid_ref_global):
            self.ascat_organizer.reshuffler()
            log_stream.info(' ----> Create dr indexed time-series data ... DONE')
        else:
            log_stream.info(' ----> Create dr indexed time-series data ... PREVIOUSLY CREATED')

        # Method to analyze data saved in time-series format
        log_stream.info(' ----> Create dr analysis data ... ')
        if not check_filename(self.ascat_organizer.ascat_path_analysis, self.filepath_grid_ref_global,
                              self.ascat_organizer.ascat_filename_tmpl_analysis, self.filename_grid_ref_global):
            self.ascat_organizer.analyzer()
            log_stream.info(' ----> Create nrt analysis data ... DONE')
        else:
            log_stream.info(' ----> Create nrt analysis data ... PREVIOUSLY CREATED')

        # Method to save data saved in time-series contiguous format
        log_stream.info(' ----> Create dr contiguous time-series data ... ')
        if not check_filename(self.ascat_organizer.ascat_path_dr, self.filepath_grid_ref_global,
                              self.ascat_organizer.ascat_filename_tmpl_dr, self.filename_grid_ref_global):
            self.ascat_organizer.writer()
            log_stream.info(' ----> Create dr contiguous time-series data ... DONE')
        else:
            log_stream.info(' ----> Create dr contiguous time-series data ... PREVIOUSLY CREATED')

        # Ending info time
        log_stream.info(' ---> Time == Start: ' + self.time.time_from.strftime(time_format) +
                        ' - End: ' + self.time.time_to.strftime(time_format) + ' ... DONE')

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to execute data product
    def execDataProduct(self):

        # -------------------------------------------------------------------------------------
        # Set class to organize data
        self.ascat_organizer = AscatOrganizerNRT(
            self.time.time_step,
            self.filepath_data_in,
            self.filepath_data_out,
            self.filepath_data_dr_scaled,
            self.filepath_data_analysis,
            self.filepath_data_points,
            self.filepath_data_maps,
            self.filepath_grid_ref_domain,
            self.filepath_grid_ref_dr,
            self.filepath_grid_ref_global,
            self.filepath_domain,
            self.filename_tmpl_in,
            self.filename_tmpl_out,
            self.filename_tmpl_dr_scaled,
            self.filename_tmpl_analysis,
            self.filename_tmpl_points,
            self.filename_tmpl_maps,
            self.filename_grid_ref_domain,
            self.filename_grid_ref_dr,
            self.filename_grid_ref_global,
            self.filename_domain,
            parameters=self.var_list_in,
            parameters_scaled=self.var_list_out,
            time_start=self.time.time_from, time_end=self.time.time_to,
            ascat_updating_out=self.rzsm_updating_out,
            ascat_updating_analysis=self.rzsm_updating_analysis,
            ascat_updating_points=self.rzsm_updating_points,
            ascat_updating_maps=self.rzsm_updating_maps
        )

        # Starting info time
        log_stream.info(' ---> Time == Step: ' + self.time.time_step.strftime(time_format) + ' ... ')

        # Check data availability
        if self.ascat_organizer.cells_in is not None:

            # Method to compose data in time-series format
            log_stream.info(' ----> Create nrt time-series data ... ')
            if not check_filename(self.ascat_organizer.ascat_path_out, self.filepath_grid_ref_dr,
                                  self.ascat_organizer.ascat_filename_tmpl_out, self.filename_grid_ref_dr):
                self.ascat_organizer.composer()
                log_stream.info(' ----> Create nrt time-series data ... DONE')
            else:
                log_stream.info(' ----> Create nrt time-series data ... PREVIOUSLY CREATED')

            # Method to analyze data saved in time-series format
            log_stream.info(' ----> Create nrt analysis data ... ')
            if not check_filename(self.ascat_organizer.ascat_path_analysis, self.filepath_grid_ref_global,
                                  self.ascat_organizer.ascat_filename_tmpl_analysis, self.filename_grid_ref_global):
                self.ascat_organizer.analyzer()
                log_stream.info(' ----> Create nrt analysis data ... DONE')
            else:
                log_stream.info(' ----> Create nrt analysis data ... PREVIOUSLY CREATED')

            # Method to interpolate and save data in gridded format
            log_stream.info(' ----> Create nrt map data ... ')
            if not check_filename(self.ascat_organizer.ascat_path_maps, self.filepath_grid_ref_global,
                                  self.ascat_organizer.ascat_filename_tmpl_maps, self.filename_grid_ref_global):
                self.ascat_organizer.mapper(parameters_attrs=mergeDict(self.var_obj_in, self.var_obj_out))
                log_stream.info(' ----> Create nrt map data ... DONE')
            else:
                log_stream.info(' ----> Create nrt map data ... PREVIOUSLY CREATED')

            # Ending info time (done)
            log_stream.info(' ---> Time == Step: ' + self.time.time_step.strftime(time_format) + ' ... DONE')

        else:

            # Ending info time (skipped)
            log_stream.info(' ---> Time == Step: ' + self.time.time_step.strftime(time_format) +
                            ' ... SKIPPED! DATA NOT AVAILABLE!')

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
