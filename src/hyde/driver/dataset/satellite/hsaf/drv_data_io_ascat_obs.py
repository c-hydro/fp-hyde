"""
Library Features:

Name:          drv_data_io_ascat_obs
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190805'
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
from src.hyde.dataset.satellite.ascat.lib_ascat_resampler_base import AscatResamplerConfigure
from src.hyde.dataset.satellite.ascat.lib_ascat_organizer_obs_base import AscatOrganizerNRT, AscatOrganizerDataRecord
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

        self.filepath_domain, self.filename_domain = split(kwargs['sm_domain'])
        self.filepath_grid_ref_global, self.filename_grid_ref_global = split(kwargs['sm_grid_ref_global'])
        self.filepath_grid_ref_domain, self.filename_grid_ref_domain = split(kwargs['sm_grid_ref_domain'])
        self.filepath_grid_mod, self.filename_grid_mod = split(kwargs['rzsm_grid'])

        self.filepath_data_in_ref, self.filename_tmpl_in_ref = self.__splitList(kwargs['sm_data_in_ref'])
        self.filepath_data_out_ref, self.filename_tmpl_out_ref = self.__splitList(kwargs['sm_data_out_ref'])

        self.filepath_data_out, self.filename_tmpl_out = split(kwargs['sm_data_out'])
        self.filepath_data_analysis, self.filename_tmpl_analysis = split(kwargs['sm_data_analysis'])
        self.filepath_data_points, self.filename_tmpl_points = split(kwargs['sm_data_points'])
        self.filepath_data_maps, self.filename_tmpl_maps = split(kwargs['sm_data_maps'])
        self.filepath_data_dr_sm_global, self.filename_tmpl_dr_sm_global = split(kwargs['sm_data_dr_global'])
        self.filepath_data_dr_sm_domain, self.filename_tmpl_dr_sm_domain = split(kwargs['sm_data_dr_domain'])
        self.filepath_data_dr_rzsm, self.filename_tmpl_dr_rzsm = split(kwargs['rzsm_data_dr'])

        self.sm_updating_out_idx = kwargs['sm_updating_out_idx']
        self.sm_updating_out_contiguous = kwargs['sm_updating_out_contiguous']

        if 'sm_updating_analysis' in kwargs:
            self.sm_updating_analysis = kwargs['sm_updating_analysis']
        else:
            self.sm_updating_analysis = None

        if 'sm_updating_points' in kwargs:
            self.sm_updating_points = kwargs['sm_updating_points']
        else:
            self.sm_updating_points = None

        if 'sm_updating_maps' in kwargs:
            self.sm_updating_maps = kwargs['sm_updating_maps']
        else:
            self.sm_updating_maps = None

        self.var_product = ['h16', 'h101']

        self.var_obj_in = self.__findDataVariable(self.var_in)
        self.var_obj_out = self.__findDataVariable(self.var_out)

        self.var_list_in = list(self.var_obj_in.keys())
        self.var_list_out = list(self.var_obj_out.keys())

        # Define filtered and scaled variable(s)
        var_ctime = self.var_out['id']['var_parameters']['var_ctime']
        var_list_mod = self.var_out['id']['var_parameters']['var_mod']

        self.var_idx_out_filtered = [i for i, x in enumerate(var_ctime) if x is not None]
        self.var_idx_out_scaled = [i for i, x in enumerate(var_list_mod) if x is not None]

        self.var_ctime = [var_ctime[idx] for idx in self.var_idx_out_filtered]
        self.var_list_mod = [var_list_mod[idx] for idx in self.var_idx_out_scaled]

        self.var_list_out_filtered = [self.var_list_out[idx] for idx in self.var_idx_out_filtered]
        self.var_list_out_scaled = [self.var_list_out[idx] for idx in self.var_idx_out_scaled]

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to split list of filepath(s) and filename(s)
    @staticmethod
    def __splitList(list_in):
        filepath_out = []
        filename_out = []
        for list_step in list_in:
            filepath_step, filename_step = split(list_step)
            filepath_out.append(filepath_step)
            filename_out.append(filename_step)
        return filepath_out, filename_out
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
    def cleanDataProduct(self, sm_cleaning_out=False, sm_cleaning_analysis=False, sm_cleaning_points=False):

        driver = self.ascat_organizer
        cells = self.ascat_organizer.dr_cells_obs_domain

        data_cleaning = {
            'out_data': [sm_cleaning_out, driver.ascat_path_out, driver.ascat_filename_tmpl_out],
            'analysis_data': [sm_cleaning_analysis, driver.ascat_path_analysis, driver.ascat_filename_tmpl_analysis],
            'points_data': [sm_cleaning_points, driver.ascat_path_points, driver.ascat_filename_tmpl_points],
            'out_ancillary': [sm_cleaning_out, driver.ascat_path_out, 'grid.nc']}

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

        # -------------------------------------------------------------------------------------
        # Set class to organize data
        self.ascat_organizer = AscatOrganizerDataRecord(
            self.time.time_run,
            self.filepath_data_out_ref,
            self.filepath_data_out,
            self.filepath_grid_ref_domain,
            self.filepath_domain,
            self.filename_tmpl_out_ref,
            self.filename_tmpl_out,
            self.filename_grid_ref_domain,
            self.filename_domain,
            parameters=self.var_list_in,
            time_start=self.time.time_from, time_end=self.time.time_to,
            ascat_updating_out=self.sm_updating_out_contiguous,
        )

        # Starting info time
        log_stream.info(' ---> Time == Start: ' + self.time.time_from.strftime(time_format) +
                        ' - End: ' + self.time.time_to.strftime(time_format) + ' ... ')

        # Method to compose data in organic ssm time-series
        log_stream.info(' ----> Create data record time-series data ... ')
        if not check_filename(self.ascat_organizer.ascat_path_out, self.filepath_grid_ref_domain,
                              self.ascat_organizer.ascat_filename_tmpl_out, self.filename_grid_ref_domain):
            self.ascat_organizer.composer()
            log_stream.info(' ----> Create data record time-series data ... DONE')
        else:
            log_stream.info(' ----> Create data record time-series data ... PREVIOUSLY CREATED')

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
            self.time.time_run,
            self.filepath_data_out_ref,
            self.filepath_data_out,
            self.filepath_data_analysis,
            self.filepath_data_points,
            self.filepath_data_maps,
            self.filepath_data_dr_sm_global,
            self.filepath_data_dr_sm_domain,
            self.filepath_data_dr_rzsm,
            self.filepath_grid_ref_domain,
            self.filepath_grid_ref_domain,
            self.filepath_grid_mod,
            self.filepath_domain,
            self.filename_tmpl_out_ref,
            self.filename_tmpl_out,
            self.filename_tmpl_analysis,
            self.filename_tmpl_points,
            self.filename_tmpl_maps,
            self.filename_tmpl_dr_sm_global,
            self.filename_tmpl_dr_sm_domain,
            self.filename_tmpl_dr_rzsm,
            self.filename_grid_ref_domain,
            self.filename_grid_ref_domain,
            self.filename_grid_mod,
            self.filename_domain,
            parameters=self.var_list_in,
            parameters_tmpl_filtered=self.var_list_out_filtered,
            parameters_tmpl_scaled=self.var_list_out_scaled,
            parameters_tmpl_mod=self.var_list_mod,
            ascat_updating_out=self.sm_updating_out_contiguous,
            ascat_updating_analysis=self.sm_updating_analysis,
            ascat_updating_points=self.sm_updating_points,
            ascat_updating_maps=self.sm_updating_maps
        )

        # Starting info time
        log_stream.info(' ---> Time == Step: ' + self.time.time_run.strftime(time_format) + ' ... ')

        # Method to compose data in organic ssm time-series
        log_stream.info(' ----> Create nrt time-series data ... ')
        if not check_filename(self.ascat_organizer.ascat_path_out, self.filepath_grid_ref_domain,
                              self.ascat_organizer.ascat_filename_tmpl_out, self.filename_grid_ref_domain):
            self.ascat_organizer.composer()
            log_stream.info(' ----> Create nrt time-series data ... DONE')
        else:
            log_stream.info(' ----> Create nrt time-series data ... PREVIOUSLY CREATED')

        # Method to analyze data for computing filtered and scaled variable(s)
        log_stream.info(' ----> Create nrt analysis data ... ')
        if not check_filename(self.ascat_organizer.ascat_path_analysis, self.filepath_grid_ref_domain,
                              self.ascat_organizer.ascat_filename_tmpl_analysis, self.filename_grid_ref_domain):
            self.ascat_organizer.analyzer(var_swi_ctime=self.var_ctime, var_scaling_method='mean_std')
            log_stream.info(' ----> Create nrt analysis data ... DONE')
        else:
            log_stream.info(' ----> Create nrt analysis data ... PREVIOUSLY CREATED')

        # Method to interpolate and save data in gridded format
        log_stream.info(' ----> Create nrt map data ... ')
        if not check_filename(self.ascat_organizer.ascat_path_maps, self.filepath_grid_ref_domain,
                              self.ascat_organizer.ascat_filename_tmpl_maps, self.filename_grid_ref_domain):
            self.ascat_organizer.mapper(parameters_attrs=mergeDict(self.var_obj_in, self.var_obj_out))
            log_stream.info(' ----> Create nrt map data ... DONE')
        else:
            log_stream.info(' ----> Create nrt map data ... PREVIOUSLY CREATED')

        # Ending info time (done)
        log_stream.info(' ---> Time == Step: ' + self.time.time_run.strftime(time_format) + ' ... DONE')
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to resample data from swath to time-series indexed format
    def resampleDataProduct(self, dr=False, write_n_resampled=None):

        # Define tags according with analysis mode (data record or nrt mode)
        if dr:
            # Starting info time
            log_stream.info(' ---> Time == Start: ' + self.time.time_from.strftime(time_format) +
                            ' - End: ' + self.time.time_to.strftime(time_format) + ' ... ')

            tmpl_tags = {'datetime': '%Y%m%d%H%M', 'sub_path_time': '%Y/%m/%d', 'cell': '%04d',
                         'time_start': 'from_%Y%m%d', 'time_end': 'to_%Y%m%d'}
            tmpl_values = {'datetime':  None, 'sub_path_time': None, 'cell': None,
                           'time_start': self.time.time_from, 'time_end': self.time.time_to}

            # Dump data if n equal or greater then this
            if write_n_resampled is None:
                write_n_resampled = 2000

        else:
            # Starting info time
            log_stream.info(' ---> Time == Step: ' + self.time.time_run.strftime(time_format) + ' ... ')

            tmpl_tags = None
            tmpl_values = None

            # Dump data if n equal or greater then this
            if write_n_resampled is None:
                write_n_resampled = 2000

        # Iterate over dataset(s)
        for ascat_product, ascat_pathname_in, ascat_pathname_out, ascat_filename_out in zip(
                self.var_product, self.filepath_data_in_ref,
                self.filepath_data_out_ref, self.filename_tmpl_out_ref):

            # Info product
            log_stream.info(' ----> Resample data for product ' + ascat_product + ' ... ')

            # Initialize class for resampling data
            ascat_resampler_configure = AscatResamplerConfigure(
                self.time.time_run,
                ascat_product,
                ascat_pathname_in,
                ascat_pathname_out,
                ascat_filename_ts=ascat_filename_out,
                grid_path=self.filepath_grid_ref_domain,
                grid_filename=self.filename_grid_ref_domain,
                mask=False,
                tmpl_tags=tmpl_tags,
                tmpl_values=tmpl_values,
                time_start=self.time.time_from, time_end=self.time.time_to,
                ascat_updating_ts=self.sm_updating_out_idx)

            if not check_filename(ascat_resampler_configure.ascat_path_ts, self.filepath_grid_ref_domain,
                                  ascat_resampler_configure.ascat_filename_ts, self.filename_grid_ref_domain):
                ascat_resampler_configure.resampler(write_n_resampled=write_n_resampled, write_orbit_buffer=True)
                log_stream.info(' ----> Resample data for product ' + ascat_product + ' ... DONE')
            else:
                log_stream.info(' ----> Resample data for product ' + ascat_product + ' ... PREVIOUSLY CREATED')

        # Ending info time
        if dr:
            log_stream.info(' ---> Time == Start: ' + self.time.time_from.strftime(time_format) +
                            ' - End: ' + self.time.time_to.strftime(time_format) + ' ... DONE')
        else:
            log_stream.info(' ---> Time == Step: ' + self.time.time_run.strftime(time_format) + ' ... DONE')

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
