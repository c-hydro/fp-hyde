"""
Library Features:

Name:          drv_model_wrf_base
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20200302'
Version:       '1.0.0'
"""
#################################################################################
# Library
import logging
import os
import re

import numpy as np
import pandas as pd

from itertools import compress
from copy import deepcopy

from src.common.utils.lib_utils_op_system import removeEmptyFolders

from src.hyde.algorithm.utils.nwp.wrf.lib_wrf_generic import fill_tags2string, flat_dictionary
from src.hyde.algorithm.settings.nwp.wrf.lib_wrf_args import logger_name, time_units, time_format, time_calendar
from src.hyde.driver.dataset.nwp.wrf.drv_data_wrf_io import DataReader, DataWriter
from src.hyde.driver.dataset.nwp.wrf.drv_data_wrf_exec import DataComposer

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

        time_step_obs = time_step
        time_step_for = pd.Timestamp(pd.date_range(start=time_step_obs, periods=2, freq=time_forecast_frequency)[-1])

        time_observed_range = pd.date_range(end=time_step_obs, periods=time_observed_period + 1,
                                            freq=time_observed_frequency)

        time_forecast_range = pd.date_range(start=time_step_for, periods=time_forecast_period,
                                            freq=time_forecast_frequency)

        if time_observed_period > 0:
            if not time_observed_range.empty:
                time_from = time_observed_range[0]
            else:
                time_from = time_step
        else:
            time_from = time_forecast_range[0]

        if time_forecast_period > 0:
            if not time_forecast_range.empty:
                time_to = time_forecast_range[-1]
            else:
                time_to = time_step
        else:
            time_to = time_observed_range[-1]

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
# Class to driver model
class DataProductBuilder:

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, time_run, time_range,
                 variable_info_in, variable_info_out, data_domain, data_geo, template, parameters,
                 file_ancillary_in=None,
                 file_ancillary_processing=None, file_ancillary_analyzing=None, file_ancillary_out=None,
                 file_data=None,
                 file_ancillary_in_updating=True,
                 file_ancillary_processing_updating=True,
                 file_ancillary_out_updating=True,
                 file_ancillary_tmp_cleaning=False,
                 file_out_updating=None, file_out_mode_zipping=False, file_out_ext_zipping='.gz',
                 file_out_write_engine='netcdf4', coord_time='XTIME'):

        # Info
        log_stream.info(' ---> TimeStep: ' + str(time_run))

        # Generic information
        self.time_run = time_run
        self.time_range = time_range
        self.time_period = int(self.time_range.shape[0])

        self.file_data = file_data

        self.file_availability = True

        self.data_domain = data_domain
        self.data_geo = data_geo
        self.data_tags_template = template
        self.data_parameters = parameters

        self.var_tag_geo_terrain = 'terrain'
        self.var_tag_geo_x = 'geo_x'
        self.var_tag_geo_y = 'geo_y'
        self.var_tag_time = 'time'

        self.file_tag_coord_geo_x = 'XLONG'
        self.file_tag_coord_geo_y = 'XLAT'
        self.file_tag_coord_time = coord_time

        self.file_tag_dim_geo_x = 'west_east'
        self.file_tag_dim_geo_y = 'south_north'
        self.file_tag_dim_time = 'Time'

        var_info_in = []
        var_pvt_in = []
        for variable_pvt_in, variable_data_in in variable_info_in.items():
            var_pvt_in.append(variable_pvt_in)
            var_info_in.append(variable_data_in)

        var_info_out = []
        var_pvt_out = []
        for variable_pvt_out, variable_data_out in variable_info_out.items():
            var_pvt_out.append(variable_pvt_out)
            var_info_out.append(variable_data_out)

        self.var_pvt_in = var_pvt_in
        self.var_info_in = var_info_in
        self.var_pvt_out = var_pvt_out
        self.var_info_out = var_info_out

        vars_file_in = {}
        for var_pvt_step, var_info_step in zip(self.var_pvt_in, var_info_in):
            var_file_in = var_info_step['id']['var_file']
            vars_file_in[var_pvt_step] = var_file_in
        vars_file_out = {}
        for var_pvt_step, var_info_step in zip(self.var_pvt_out, var_info_out):
            var_file_out = var_info_step['id']['var_file']
            vars_file_out[var_pvt_step] = var_file_out

        file_data_in = {}
        for var_key_in, var_ref_in in vars_file_in.items():
            file_data_list = []
            for var_ref_step in var_ref_in:
                if var_ref_step in list(self.file_data.keys()):
                    file_data_step = self.file_data[var_ref_step]
                    file_data_list.append(file_data_step)
                else:
                    file_data_list.append(None)
            file_data_in[var_key_in] = file_data_list

        file_data_out = {}
        for var_key_out, var_ref_out in vars_file_out.items():
            file_data_list = []
            for var_ref_step in var_ref_out:
                if var_ref_step in list(self.file_data.keys()):
                    file_data_step = self.file_data[var_ref_step]
                    file_data_list.append(file_data_step)
                else:
                    file_data_list.append(None)
            file_data_out[var_key_out] = file_data_list

        # Data input file
        self.path_name_in = {}
        self.file_name_in = {}
        self.folder_name_in = {}
        for file_key_step, file_path_step in file_data_in.items():

            folder_name_list = []
            file_name_list = []
            path_name_list = []

            if variable_info_in[file_key_step]['id']['var_dims'][0] == 'var2d':
                for time_step in time_range:

                    data_tags_in_values = {'datetime_source': time_step, 'runtime_source': time_step,
                                           'sub_path_time_source': time_step, 'domain': self.data_domain}

                    for path_name_raw in file_path_step:
                        if path_name_raw is not None:
                            path_name_fill = fill_tags2string(path_name_raw, self.data_tags_template, data_tags_in_values)
                            folder_name_fill, file_name_fill = os.path.split(path_name_fill)
                        else:
                            file_name_fill = None
                            folder_name_fill = None
                            path_name_fill = None

                        path_name_list.append(path_name_fill)
                        folder_name_list.append(folder_name_fill)
                        file_name_list.append(file_name_fill)

                self.path_name_in[file_key_step] = path_name_list
                self.file_name_in[file_key_step] = file_name_list
                self.folder_name_in[file_key_step] = folder_name_list

            if variable_info_in[file_key_step]['id']['var_dims'][0] == 'var3d':

                data_tags_in_values = {'datetime_source': time_run, 'runtime_source': time_run,
                                       'sub_path_time_source': time_run, 'domain': self.data_domain}

                for path_name_raw in file_path_step:
                    if path_name_raw is not None:
                        path_name_fill = fill_tags2string(path_name_raw, self.data_tags_template, data_tags_in_values)
                        folder_name_fill, file_name_fill = os.path.split(path_name_fill)
                    else:
                        file_name_fill = None
                        folder_name_fill = None
                        path_name_fill = None

                    path_name_list.append(path_name_fill)
                    folder_name_list.append(folder_name_fill)
                    file_name_list.append(file_name_fill)

            self.path_name_in[file_key_step] = path_name_list
            self.file_name_in[file_key_step] = file_name_list
            self.folder_name_in[file_key_step] = folder_name_list

        path_availability = []
        for folder_name_list, path_name_list in zip(self.folder_name_in.values(), self.path_name_in.values()):
            for folder_name_step, path_name_step in zip(folder_name_list, path_name_list):
                if folder_name_step is not None:
                    if not os.path.exists(path_name_step):
                        log_stream.warning(' ===> File does not exist [' + path_name_step + ']')
                        path_availability.append(False)
                        raise FileNotFoundError(' Path does not exist [' + folder_name_step + ']')
                    else:
                        path_availability.append(True)
                else:
                    path_availability.append(True)

        self.file_availability = all(i is True for i in path_availability)

        # Data output
        self.path_name_out = {}
        self.file_name_out = {}
        self.folder_name_out = {}
        for file_key_step, file_path_step in file_data_out.items():

            data_tags_template = deepcopy(self.data_tags_template)
            data_tags_template.pop('ensemble', None)
            data_tags_out_values = {'datetime_outcome': self.time_run, 'runtime_source': self.time_run,
                                    'sub_path_time_outcome': self.time_run, 'domain': self.data_domain}

            folder_name_list = []
            file_name_list = []
            path_name_list = []
            for path_name_raw in file_path_step:
                if path_name_raw is not None:
                    path_name_fill = fill_tags2string(path_name_raw, self.data_tags_template, data_tags_out_values)
                    folder_name_fill, file_name_fill = os.path.split(path_name_fill)
                else:
                    file_name_fill = None
                    folder_name_fill = None
                    path_name_fill = None

                folder_name_list.append(folder_name_fill)
                file_name_list.append(file_name_fill)
                path_name_list.append(path_name_fill)

            self.file_name_out[file_key_step] = file_name_list
            self.folder_name_out[file_key_step] = folder_name_list
            self.path_name_out[file_key_step] = path_name_list

        for folder_name_list in list(self.folder_name_out.values()):
            for folder_name_step in folder_name_list:
                if folder_name_step is not None:
                    folder_name_root = re.split('[{}]', folder_name_step)[0]
                    if not os.path.exists(folder_name_root):
                        os.makedirs(folder_name_root)

        # Ancillary input file
        if file_ancillary_in is not None:
            data_tags_ancillary_values = {'datetime_ancillary': self.time_run, 'runtime_source': self.time_run,
                                          'sub_path_time_ancillary': self.time_run, 'domain': self.data_domain}

            path_ancillary_in_fill = fill_tags2string(file_ancillary_in, self.data_tags_template,
                                                      data_tags_ancillary_values)
            self.folder_ancillary_in, self.file_ancillary_in = os.path.split(path_ancillary_in_fill)
            self.path_ancillary_in = path_ancillary_in_fill
        else:
            self.folder_ancillary_in = None
            self.file_ancillary_in = None
            self.path_ancillary_in = None

        if self.folder_ancillary_in is not None:
            folder_ancillary_in_root = re.split('[{}]', self.folder_ancillary_in)[0]
            if not os.path.exists(folder_ancillary_in_root):
                os.makedirs(folder_ancillary_in_root)
        # Ancillary processing file
        if file_ancillary_processing is not None:
            data_tags_template = deepcopy(self.data_tags_template)
            data_tags_template.pop('ensemble', None)
            data_tags_ancillary_values = {'datetime_ancillary': self.time_run, 'runtime_source': self.time_run,
                                          'sub_path_time_ancillary': self.time_run, 'domain': self.data_domain}

            path_ancillary_processing_fill = fill_tags2string(file_ancillary_processing, data_tags_template,
                                                              data_tags_ancillary_values)
            self.folder_ancillary_processing, self.file_ancillary_processing = os.path.split(
                path_ancillary_processing_fill)
            self.path_ancillary_processing = path_ancillary_processing_fill
        else:
            self.folder_ancillary_processing = None
            self.file_ancillary_processing = None
            self.path_ancillary_processing = None

        if self.folder_ancillary_processing is not None:
            folder_ancillary_processing_root = re.split('[{}]', self.folder_ancillary_processing)[0]
            if not os.path.exists(folder_ancillary_processing_root):
                os.makedirs(folder_ancillary_processing_root)

        # Ancillary outcome file
        if file_ancillary_out is not None:
            data_tags_template = deepcopy(self.data_tags_template)
            data_tags_template.pop('ensemble', None)
            data_tags_ancillary_values = {'datetime_ancillary': self.time_run, 'runtime_source': self.time_run,
                                          'sub_path_time_ancillary': self.time_run, 'domain': self.data_domain}

            path_ancillary_out_fill = fill_tags2string(file_ancillary_out, data_tags_template,
                                                       data_tags_ancillary_values)
            self.folder_ancillary_out, self.file_ancillary_out = os.path.split(path_ancillary_out_fill)
            self.path_ancillary_out = path_ancillary_out_fill
        else:
            self.folder_ancillary_out = None
            self.file_ancillary_out = None
            self.path_ancillary_out = None

        if self.folder_ancillary_out is not None:
            folder_ancillary_out_root = re.split('[{}]', self.folder_ancillary_out)[0]
            if not os.path.exists(folder_ancillary_out_root):
                os.makedirs(folder_ancillary_out_root)

        self.var_info_redux_in, self.var_attrs_redux_in = flat_dictionary(variable_info_in)
        self.var_info_redux_out, self.var_attrs_redux_out = flat_dictionary(variable_info_out)

        # Check file availability (one at least)
        if self.file_availability:

            # Driver to read data
            self.driver_data_reader = DataReader(
                var_data=self.var_info_redux_in, file_data=self.path_name_in,
                folder_tmp=self.folder_ancillary_in, file_tmp=self.file_ancillary_in,
                var_tag_geo_x=self.var_tag_geo_x, var_tag_geo_y=self.var_tag_geo_y,
                var_tag_time=self.var_tag_time,
                file_tag_coord_geo_x=self.file_tag_coord_geo_x, file_tag_coord_geo_y=self.file_tag_coord_geo_y,
                file_tag_coord_time=self.file_tag_coord_time,
                file_tag_dim_geo_x=self.file_tag_dim_geo_x, file_tag_dim_geo_y=self.file_tag_dim_geo_y,
                file_tag_dim_time=self.file_tag_dim_time
            )

            # Driver to compose data
            self.driver_data_composer = DataComposer(
                var_info=self.var_info_redux_in, var_geo=self.data_geo, var_time=self.time_range,
                folder_tmp=self.folder_ancillary_processing, file_tmp=self.file_ancillary_processing,
                var_tag_geo_terrain=self.var_tag_geo_terrain,
                var_tag_geo_x=self.var_tag_geo_x, var_tag_geo_y=self.var_tag_geo_y, var_tag_time=self.var_tag_time,
                file_tag_coord_geo_x=self.file_tag_coord_geo_x, file_tag_coord_geo_y=self.file_tag_coord_geo_y,
                file_tag_coord_time=self.file_tag_coord_time,
                file_tag_dim_geo_x=self.file_tag_dim_geo_x, file_tag_dim_geo_y=self.file_tag_dim_geo_y,
                file_tag_dim_time=self.file_tag_dim_time,
            )

            # Driver to write data
            self.driver_data_writer = DataWriter(
                var_info=self.var_info_redux_out, var_attrs_list=self.var_attrs_redux_out['attributes'],
                var_geo=self.data_geo,
                folder_out=self.folder_name_out, file_out=self.file_name_out, tag_out=vars_file_out,
                var_tag_geo_terrain=self.var_tag_geo_terrain,
                var_tag_geo_x=self.var_tag_geo_x, var_tag_geo_y=self.var_tag_geo_y, var_tag_time=self.var_tag_time,
                dset_write_engine=file_out_write_engine,
                file_compression_mode=file_out_mode_zipping, file_compression_ext=file_out_ext_zipping
            )

        self.file_ancillary_in_updating = file_ancillary_in_updating
        self.file_ancillary_processing_updating = file_ancillary_processing_updating
        self.file_ancillary_out_updating = file_ancillary_out_updating

        self.file_out_updating = file_out_updating
        self.file_ancillary_tmp_cleaning = file_ancillary_tmp_cleaning

        self.file_out_mode_zipping = file_out_mode_zipping
        self.file_out_ext_zipping = file_out_ext_zipping

        self.file_out_write_engine = file_out_write_engine

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to clean temporary data
    def clean(self):

        # Check data availability
        if self.file_availability:

            file_tmp_reader = self.driver_data_reader.file_tmp
            folder_tmp_reader = self.driver_data_reader.folder_tmp

            file_tmp_composer = self.driver_data_composer.file_tmp
            folder_tmp_composer = self.driver_data_composer.folder_tmp

            if self.file_ancillary_tmp_cleaning:

                path_tmp = os.path.join(folder_tmp_reader, file_tmp_reader)
                if os.path.exists(path_tmp):
                    os.remove(path_tmp)
                path_tmp = os.path.join(folder_tmp_composer, file_tmp_composer)
                if os.path.exists(path_tmp):
                    os.remove(path_tmp)

                removeEmptyFolders(folder_tmp_reader)
                removeEmptyFolders(folder_tmp_composer)

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to collect data
    def collect(self):

        # -------------------------------------------------------------------------------------
        # Starting info
        log_stream.info(' ---> Collect datasets ... ')

        time_range = self.time_range
        time_run = self.time_run

        # Check data availability
        if self.file_availability:

            # Configure updating flag about ancillary in file
            if os.path.exists(self.driver_data_reader.file_tmp):
                if self.file_ancillary_in_updating:
                    os.remove(self.driver_data_reader.file_tmp)
            else:
                self.file_ancillary_in_updating = True

            if self.file_ancillary_in_updating:
                data_obj = self.driver_data_reader.organize_obj(time_range, time_run)
                # Ending info
                log_stream.info(' ---> Collect datasets ... DONE')
            else:
                data_obj = self.driver_data_reader.callback_obj()
                # Ending info
                log_stream.info(' ---> Collect datasets ... PREVIOUSLY DONE!')

        else:
            # Ending info
            log_stream.warning(' ---> Collect datasets ... SKIPPED! SOME/ALL INPUTS ARE NOT AVAILABLE!')
            data_obj = None

        return data_obj
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to process datasets
    def process(self, data_in_obj):

        # -------------------------------------------------------------------------------------
        # Starting info
        log_stream.info(' ---> Process datasets ... ')

        # Check data availability
        if self.file_availability:

            # Configure updating flag about ancillary processing file
            if os.path.exists(self.driver_data_composer.file_tmp):
                if self.file_ancillary_processing_updating:
                    os.remove(self.driver_data_composer.file_tmp)
            else:
                self.file_ancillary_processing_updating = True

            # Compute datasets to obtain variables
            if self.file_ancillary_processing_updating:
                data_out_obj = self.driver_data_composer.execute(data_in_obj)

                # Ending info
                log_stream.info(' ---> Process datasets ... DONE')
            else:
                data_out_obj = self.driver_data_composer.callback_obj()
                # Ending info
                log_stream.info(' ---> Process datasets ... PREVIOUSLY DONE!')

        else:
            # Ending info
            log_stream.warning(' ---> Process datasets ... SKIPPED! SOME/ALL INPUTS ARE NOT AVAILABLE!')
            data_out_obj = None

        return data_out_obj
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to save model
    def save(self, data_obj_in):

        # -------------------------------------------------------------------------------------
        # Starting info
        log_stream.info(' ---> Save datasets ... ')

        # Check data availability
        if self.file_availability:

            file_link = self.driver_data_writer.link_out

            # Configure updating flag about outcome file(s)
            for file_key, file_name in file_link.items():
                if os.path.exists(file_name):
                    if self.file_out_updating:
                        os.remove(file_name)
                    else:
                        self.file_out_updating = True
                        break
                else:
                    self.file_out_updating = True

            # Organize and save datasets in a common netcdf format
            if self.file_out_updating:
                data_obj_out = self.driver_data_writer.organize_obj(data_obj_in)
                file_name_out, file_status_out = self.driver_data_writer.dump_obj(data_obj_out)

                for file_status, (file_key, file_name) in zip(file_status_out, file_link.items()):
                    if not file_status:
                        # Warning info
                        log_stream.warning(' ---> Save datasets ... FAILED. File ' + file_name + ' not saved!')

                self.driver_data_writer.zip_obj(file_status_out)

                # Ending info
                log_stream.info(' ---> Save datasets ... DONE')

            else:
                # Ending info
                log_stream.info(' ---> Save datasets ... PREVIOUSLY DONE!')

        else:
            # Ending info
            log_stream.warning(' ---> Save datasets ... SKIPPED! SOME/ALL INPUTS ARE NOT AVAILABLE!')
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
