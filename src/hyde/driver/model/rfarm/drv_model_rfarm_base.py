"""
Library Features:

Name:          drv_model_rfarm_io_base
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190903'
Version:       '1.0.0'
"""
#################################################################################
# Library
import logging
import os
import re

import pandas as pd

from copy import deepcopy

from src.hyde.algorithm.utils.rfarm.lib_rfarm_generic import fill_tags2string
from src.hyde.algorithm.settings.model.rfarm.lib_rfarm_args import logger_name, time_units, time_format, time_calendar

from src.hyde.driver.model.rfarm.drv_model_rfarm_io import RFarmData, RFarmResult
from src.hyde.driver.model.rfarm.drv_model_rfarm_exec import RFarmModel

# Logging
log_stream = logging.getLogger(logger_name)

# Debug
# import matplotlib.pylab as plt
#################################################################################


# -------------------------------------------------------------------------------------
# Class data object
class DataObj(dict):
    pass
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class to compute time model
class ModelTime:

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, **kwargs):
        self.time_step = kwargs['time_step']
        self.time_run = kwargs['time_run']
        self.time_settings = kwargs['time_settings']
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to compute model time
    def computeModelTime(self, time_ascending=True, time_closed='right'):

        log_stream.info(' ---> Compute model time ... ')

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
            time_start = time_observed_range[0]
        else:
            time_start = time_step
        if not time_forecast_range.empty:
            time_end = time_forecast_range[-1]
        else:
            time_end = time_step

        time_range = pd.date_range(start=time_start, end=time_end, freq=time_observed_frequency, closed=time_closed)
        time_range = time_range.sort_values(return_indexer=False, ascending=time_ascending)

        time_obj = DataObj
        time_obj.time_run = time_run
        time_obj.time_step = time_step
        time_obj.time_range = time_range
        time_obj.time_from = time_range[0]
        time_obj.time_to = time_range[-1]
        time_obj.time_format = time_format
        time_obj.time_units = time_units
        time_obj.time_calendar = time_calendar

        log_stream.info(' ---> Compute model time ... DONE!')

        return time_obj

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class to driver model
class ModelRunner:

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, time_step, time_range,
                 variable_in, variable_out, data_geo, template, parameters,
                 file_ancillary_in=None, file_ancillary_out=None, file_in=None, file_out=None,
                 file_ancillary_in_updating=True, file_ancillary_out_updating=None,
                 file_out_updating=None, file_out_zipping=False, file_ext_zipping='.gz',
                 file_write_engine='netcdf4'):

        # Generic information
        self.time_step = time_step
        self.time_range = time_range
        self.var_info_in = variable_in
        self.var_info_out = variable_out
        self.data_geo = data_geo
        self.model_tags_template = template
        self.model_parameters = parameters

        # Data input file
        if file_in is not None:
            model_tags_in_values = {'datetime_input': self.time_step, 'sub_path_time': self.time_step}

            file_in_raw = fill_tags2string(file_in, self.model_tags_template, model_tags_in_values)
            self.folder_in_raw, self.filename_in_raw = os.path.split(file_in_raw)

            self.folder_in_list = []
            self.filename_in_list = []
            for time_iter in self.time_range:
                model_tags_list_values = {'datetime_input': time_iter, 'sub_path_time': self.time_step}
                file_in_list = fill_tags2string(file_in, self.model_tags_template, model_tags_list_values)
                folder_in_list, filename_in_list = os.path.split(file_in_list)
                self.folder_in_list.append(folder_in_list)
                self.filename_in_list.append(filename_in_list)

        else:
            raise TypeError

        if not os.path.exists(self.folder_in_raw):
            raise FileNotFoundError(' Path does not exist [' + self.folder_in_raw + ']')

        # Ancillary input file
        if file_ancillary_in is not None:
            model_tags_values = {'datetime_input': self.time_step, 'sub_path_time': self.time_step}
            file_ancillary_in = fill_tags2string(file_ancillary_in, self.model_tags_template, model_tags_values)
            self.folder_ancillary_in_raw, self.filename_ancillary_in_raw = os.path.split(file_ancillary_in)
        else:
            self.folder_ancillary_in_raw = None
            self.filename_ancillary_in_raw = None

        if self.folder_ancillary_in_raw is not None:
            folder_ancillary_in_root = re.split('[{}]', self.folder_ancillary_in_raw)[0]
            if not os.path.exists(folder_ancillary_in_root):
                os.makedirs(folder_ancillary_in_root)

        # Ancillary outcome file
        if file_ancillary_out is not None:
            model_tags_template = deepcopy(self.model_tags_template)
            model_tags_template.pop('ensemble', None)
            model_tags_values = {'datetime_outcome': self.time_step, 'sub_path_time': self.time_step}
            file_ancillary_out = fill_tags2string(file_ancillary_out, model_tags_template, model_tags_values)
            self.folder_ancillary_out_raw, self.filename_ancillary_out_raw = os.path.split(file_ancillary_out)
        else:
            self.folder_ancillary_out_raw = None
            self.filename_ancillary_out_raw = None

        if self.folder_ancillary_out_raw is not None:
            folder_ancillary_out_root = re.split('[{}]', self.folder_ancillary_out_raw)[0]
            if not os.path.exists(folder_ancillary_out_root):
                os.makedirs(folder_ancillary_out_root)

        # Result outcome file
        if file_out is not None:
            model_tags_template = deepcopy(self.model_tags_template)
            model_tags_template.pop('ensemble', None)
            model_tags_values = {'datetime_outcome': self.time_step, 'sub_path_time': self.time_step}
            file_out = fill_tags2string(file_out, model_tags_template, model_tags_values)
            self.folder_out_raw, self.filename_out_raw = os.path.split(file_out)
        else:
            raise TypeError

        folder_out_root = re.split('[{}]', self.folder_out_raw)[0]
        if not os.path.exists(folder_out_root):
            os.makedirs(folder_out_root)

        # Model driver for collecting RFarm data
        self.driver_rf_data = RFarmData(
            self.folder_in_raw, self.filename_in_raw,
            folder_data_list=self.folder_in_list, filename_data_list=self.filename_in_list,
            var_name=self.var_info_in['id']['var_name'],
            var_dims=self.var_info_in['id']['var_type'][0],
            var_type=self.var_info_in['id']['var_type'][1],
            var_units=self.var_info_in['attributes']['units'],
            file_format=self.var_info_in['id']['var_format'],
            file_source=self.var_info_in['id']['var_source'],
            folder_tmp=self.folder_ancillary_in_raw, filename_tmp=self.filename_ancillary_in_raw,
        )

        # Model driver for running RFarm model
        self.driver_rf_model = RFarmModel(
            ensemble_n=self.model_parameters['ensemble'],
            ensemble_format=self.model_tags_template['ensemble'],
            ratio_s=self.model_parameters['ratio_s'],
            ratio_t=self.model_parameters['ratio_t'],
            slope_s=self.model_parameters['slope_s'],
            slope_t=self.model_parameters['slope_t'],
            cs_sf=self.model_parameters['cs_sf'],
            ct_sf=self.model_parameters['ct_sf'],
            multi_core=self.model_parameters['multi_core'],
            domain_extension=self.model_parameters['domain_extension'],
            folder_tmp=self.folder_ancillary_out_raw,
            filename_tmp=self.filename_ancillary_out_raw,
            model_var=self.var_info_out['id']['var_name']
        )

        # Model driver of saving RFarm result(s)
        self.driver_rf_result = RFarmResult(
            self.driver_rf_model.ensemble_filename,
            ensemble_n=self.model_parameters['ensemble'],
            ensemble_format=self.model_tags_template['ensemble'],
            folder_out=self.folder_out_raw,
            filename_out=self.filename_out_raw,
            var_name=self.var_info_out['id']['var_name'],
            var_dims=self.var_info_in['id']['var_type'][0],
            var_attrs=self.var_info_out['attributes'],
            ensemble_zip=file_out_zipping,
            ext_zip_type=file_ext_zipping,
            write_engine=file_write_engine
        )

        self.file_ancillary_in_updating = file_ancillary_in_updating
        self.file_ancillary_out_updating = file_ancillary_out_updating
        self.file_out_updating = file_out_updating
        self.file_out_zipping = file_out_zipping
        self.file_write_engine = file_write_engine

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to clean temporary data
    def clean(self, cleaning_dynamic_tmp=False):

        if cleaning_dynamic_tmp:

            # Clean ensemble group tmp input file(s)
            file_group_in_tmp = self.driver_rf_data.file_tmp
            if isinstance(file_group_in_tmp, str):
                file_group_in_tmp = [file_group_in_tmp]
            for file in file_group_in_tmp:
                if os.path.exists(file):
                    os.remove(file)

            # Clean ensemble group tmp outcome file(s)
            file_group_out_tmp = self.driver_rf_result.ensemble_group_in
            if isinstance(file_group_out_tmp, str):
                file_group_out_tmp = [file_group_out_tmp]
            for file in file_group_out_tmp:
                if os.path.exists(file):
                    os.remove(file)

        if self.file_out_zipping:
            file_group_out_unzip = self.driver_rf_result.ensemble_group_out
            if isinstance(file_group_out_unzip, str):
                file_group_out_unzip = [file_group_out_unzip]
            # Clean ensemble group outcome file(s)
            for file in file_group_out_unzip:
                if os.path.exists(file):
                    os.remove(file)
        else:
            file_group_out_zip = self.driver_rf_result.zip_group_out
            if isinstance(file_group_out_zip, str):
                file_group_out_zip = [file_group_out_zip]
            # Clean ensemble group outcome file(s)
            for file in file_group_out_zip:
                if os.path.exists(file):
                    os.remove(file)

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to collect data
    def collect(self, var_time_obj):

        # -------------------------------------------------------------------------------------
        # Starting info
        log_stream.info(' ---> Collect data ... ')

        # Get time steps
        var_time_range = var_time_obj.time_range

        # Check data availability
        if self.driver_rf_data.found_data_first:

            # Configure updating flag about ancillary in file
            if os.path.exists(self.driver_rf_data.file_tmp):
                if self.file_ancillary_in_updating:
                    os.remove(self.driver_rf_data.file_tmp)
            else:
                self.file_ancillary_in_updating = True

            if self.file_ancillary_in_updating:
                data_obj = self.driver_rf_data.organize_data(var_time_range)
                # Ending info
                log_stream.info(' ---> Collect data ... DONE')
            else:
                data_obj = self.driver_rf_data.callback_data()
                # Ending info
                log_stream.info(' ---> Collect data ... PREVIOUSLY DONE!')

        else:
            # Ending info
            log_stream.info(' ---> Collect data ... SKIPPED! DATA INPUT NOT FOUND!')
            data_obj = None

        return data_obj

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to configure model
    def configure(self, data_obj):

        # -------------------------------------------------------------------------------------
        # Starting info
        log_stream.info(' ---> Model configuration ... ')

        # Check data availability
        if self.driver_rf_data.found_data_first:

            # Method to set ancillary out flag
            self.file_ancillary_out_updating = self.__set_ancillary_out_flag(self.file_ancillary_out_updating)

            # Check ancillary outcome flag
            if self.file_ancillary_out_updating:

                values_obj = data_obj.values
                lons_obj = data_obj['longitude'].values
                lats_obj = data_obj['latitude'].values

                time_obj = data_obj['time'].values

                lons_geo = self.data_geo['longitude']
                lats_geo = self.data_geo['latitude']
                res_lon_geo = self.data_geo['res_lon']
                res_lat_geo = self.data_geo['res_lat']

                # Configure model grid(s)
                self.driver_rf_model.configure_grid(lons_obj, lats_obj,
                                                    lons_geo, lats_geo, res_lon_geo, res_lat_geo,
                                                    self.driver_rf_model.domain_extension)
                # Configure model time(s)
                self.driver_rf_model.configure_time(time_obj)

                # Configure model data
                self.driver_rf_model.configure_data(values_obj)

                # Ending info
                log_stream.info(' ---> Model configuration ... DONE!')

            else:
                # Ending info
                log_stream.info(' ---> Model configuration ... SKIPPED! Results are saved during previously executions!')

        else:
            # Ending info
            log_stream.info(' ---> Model configuration ... SKIPPED! DATA INPUT NOT FOUND!')
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to execute model
    def exec(self):

        # -------------------------------------------------------------------------------------
        # Starting info
        log_stream.info(' ---> Model execution ... ')

        # Check data availability
        if self.driver_rf_data.found_data_first:

            # Check ancillary outcome flag
            if self.file_ancillary_out_updating:
                # Method to execute model run(s)
                ensemble_obj = self.driver_rf_model.execute_run()
                # Ending info
                log_stream.info(' ---> Model execution ... DONE!')
            else:
                # Method to collect model run(s)
                ensemble_obj = self.driver_rf_model.callback_run()
                # Ending info
                log_stream.info(' ---> Model execution ... SKIPPED! Results are collected using previously executions!')

        else:
            # Ending info
            log_stream.info(' ---> Model execution ... SKIPPED! DATA INPUT NOT FOUND!')
            ensemble_obj = None

        return ensemble_obj
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to save model
    def save(self, ensemble_obj):

        # -------------------------------------------------------------------------------------
        # Starting info
        log_stream.info(' ---> Save result(s) ... ')

        # Check data availability
        if self.driver_rf_data.found_data_first:

            # Geographical info
            values_geo = self.data_geo['values']
            lons_geo = self.data_geo['longitude']
            lats_geo = self.data_geo['latitude']

            # Method to set ancillary out flag
            self.file_out_updating = self.__set_ancillary_out_flag(self.file_out_updating)

            # Check ancillary outcome flag
            if self.file_out_updating:
                # Method to save model result(s)
                self.driver_rf_result.organize_result(ensemble_obj, values_geo, lons_geo, lats_geo)
                # Method to zip model result(s)
                self.driver_rf_result.zip_result()
                # Ending info
                log_stream.info(' ---> Save result(s) ... DONE!')
            else:
                # Ending info
                log_stream.info(' ---> Save result(s) ... SKIPPED! Results are collected using previously executions!')

        else:
            # Ending info
            log_stream.info(' ---> Save result(s) ... SKIPPED! DATA INPUT NOT FOUND!')

        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to set ancillary flag
    def __set_ancillary_out_flag(self, file_out_updating):

        if self.file_out_zipping:
            for ensemble_filename in self.driver_rf_result.ensemble_group_out:
                if os.path.exists(ensemble_filename):
                    os.remove(ensemble_filename)
            for ensemble_filename_zip in self.driver_rf_result.zip_group_out:
                if os.path.exists(ensemble_filename_zip):
                    if file_out_updating:
                        os.remove(ensemble_filename_zip)
                else:
                    file_out_updating = True
                    break
        else:
            for ensemble_filename_zip in self.driver_rf_result.zip_group_out:
                if os.path.exists(ensemble_filename_zip):
                    os.remove(ensemble_filename_zip)
            for ensemble_filename in self.driver_rf_result.ensemble_group_out:
                if os.path.exists(ensemble_filename):
                    if file_out_updating:
                        os.remove(ensemble_filename)
                else:
                    file_out_updating = True
                    break
        return file_out_updating
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
