"""
Library Features:

Name:          drv_data_gfs_exec
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20200302'
Version:       '1.0.0'
"""
#################################################################################
# Library
import logging
import os

from src.hyde.driver.dataset.nwp.gfs.cpl_data_variables_gfs_025 import DataVariables, ModelVariables

from src.hyde.algorithm.settings.nwp.gfs.lib_gfs_args import logger_name
from src.hyde.algorithm.io.nwp.gfs.lib_gfs_io_generic import write_obj, read_obj

from src.common.utils.lib_utils_op_system import createTemp

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
# Class to compose data
class DataComposer:

    def __init__(self,
                 var_info=None, var_geo=None, var_time=None,
                 folder_tmp=None, file_tmp='nwp_source.workspace',
                 var_tag_geo_terrain='terrain',
                 var_tag_geo_x='geo_x', var_tag_geo_y='geo_y', var_tag_time='time',
                 file_tag_geo_x='geo_x', file_tag_geo_y='geo_y', file_tag_time='time'
                 ):

        self.var_info = var_info
        self.var_geo = var_geo
        self.var_time = var_time

        self.folder_tmp = folder_tmp
        self.file_tmp = file_tmp

        self.var_tag_terrain = var_tag_geo_terrain
        self.var_tag_time = var_tag_time
        self.var_tag_geo_x = var_tag_geo_y
        self.var_tag_geo_y = var_tag_geo_x

        self.var_tag_units = 'units'
        self.var_tag_step_type = 'var_type'

        self.file_tag_time = file_tag_time
        self.file_tag_geo_x = file_tag_geo_x
        self.file_tag_geo_y = file_tag_geo_y

        self.file_tag_units = None
        self.file_tag_step_type = None

        if folder_tmp is None:
            self.folder_tmp = createTemp()

        if self.file_tmp is None:
            raise TypeError

        if not os.path.exists(self.folder_tmp):
            os.makedirs(self.folder_tmp)

        self.file_tmp = os.path.join(self.folder_tmp, self.file_tmp)

    def callback_obj(self):

        var_obj = read_obj(self.file_tmp)
        return var_obj

    def execute(self, var_data):

        var_time_period_expected = self.var_time

        domain_values = self.var_geo['values']
        domain_geo_x = self.var_geo['longitude']
        domain_geo_y = self.var_geo['latitude']

        file_tag_time = self.file_tag_time
        file_tag_geo_x = self.file_tag_geo_x
        file_tag_geo_y = self.file_tag_geo_y

        var_frame = {}
        for info_key, info_step in self.var_info.items():

            # Starting info
            log_stream.info(' ----> Compose variable: ' + info_key + ' ... ')

            var_name = info_step['var_name']
            var_step_type = info_step['var_type']
            var_units = info_step['units']

            # Get data
            var_dset = var_data[info_key]
            var_geo_x = var_data[self.var_tag_geo_x]
            var_geo_y = var_data[self.var_tag_geo_y]

            if self.var_tag_geo_x not in list(var_frame.keys()):
                var_frame[self.var_tag_geo_x] = domain_geo_x
            if self.var_tag_geo_y not in list(var_frame.keys()):
                var_frame[self.var_tag_geo_y] = domain_geo_y
            if self.var_tag_terrain not in list(var_frame.keys()):
                var_frame[self.var_tag_terrain] = domain_values

            # Initialize computing driver
            if 'var_method_compute' in list(info_step.keys()):

                driver_var_cmp = DataVariables(info_key=info_key, var_name=var_name,
                                               var_units=var_units, var_step_type=var_step_type,
                                               var_dset=var_dset, var_geo_x=var_geo_x, var_geo_y=var_geo_y,
                                               domain_values=domain_values,
                                               domain_geo_x=domain_geo_x, domain_geo_y=domain_geo_y,
                                               var_fx=info_step['var_method_compute'],
                                               file_tag_units=None,
                                               file_tag_step_type=None,
                                               file_tag_time=file_tag_time,
                                               file_tag_geo_x=file_tag_geo_x, file_tag_geo_y=file_tag_geo_y)

                # Get variable, data, time and attributes of raw data
                var_data_raw, var_time_raw, var_attr_raw = driver_var_cmp.configure_fx()
                var_time_period_raw = var_time_raw.time_period

                # Compute, fill and mask data
                var_da_masked = driver_var_cmp.configure_data(var_data_raw,
                                                              var_time_period_raw, var_time_period_expected)

                log_stream.info(' ----> Compose variable: ' + info_key + ' ... DONE')

            else:
                log_stream.info(' ----> Compose variable: ' + info_key + ' ... SKIPPED. Computing method not defined')
                var_da_masked = None

            # Store data in a common workspace
            var_frame[info_key] = var_da_masked

        # Dump tmp file
        write_obj(self.file_tmp, var_frame)

        return var_frame

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class to analyzer data
class DataAnalyzer(DataComposer):

    def __init__(self,
                 var_info=None, var_geo=None, var_time=None,
                 folder_tmp=None, file_tmp='nwp_outcome.workspace',
                 tag_geo_terrain='terrain', tag_geo_x='geo_x', tag_geo_y='geo_y', tag_time='time'
                 ):

        self.tag_geo_terrain = tag_geo_terrain
        self.tag_geo_x = tag_geo_x
        self.tag_geo_y = tag_geo_y
        self.tag_time = tag_time

        super().__init__(var_info, var_geo, var_time,
                         folder_tmp=folder_tmp, file_tmp=file_tmp,
                         var_tag_geo_terrain=self.tag_geo_terrain,
                         var_tag_geo_x=self.tag_geo_x, var_tag_geo_y=self.tag_geo_y,
                         var_tag_time=self.tag_time
                         )

    def merge_obj(self, var_obj_ref, var_obj_ancillary):

        tag_geo_static = [self.tag_geo_terrain, self.tag_geo_x, self.tag_geo_y]

        for var_key_ancillary, var_dset_ancillary in var_obj_ancillary.items():
            if var_key_ancillary not in tag_geo_static:
                if var_dset_ancillary is not None:
                    if var_key_ancillary in list(var_obj_ref.keys()):

                        var_dset_ref = var_obj_ref[var_key_ancillary]

                        var_dset_merge = var_dset_ref.merge(var_dset_ancillary, join='right')
                        var_obj_ref[var_key_ancillary] = var_dset_merge

        return var_obj_ref

    def execute(self, var_data):

        domain_values = self.var_geo['values']
        domain_geo_x = self.var_geo['longitude']
        domain_geo_y = self.var_geo['latitude']

        file_tag_time = self.file_tag_time
        file_tag_units = self.file_tag_units
        file_tag_step_type = self.file_tag_step_type

        var_frame = {}
        for info_key, info_step in self.var_info.items():

            # Starting info
            log_stream.info(' ----> Analyze variable: ' + info_key + ' ... ')

            # Get data
            var_values = var_data[info_key]
            var_geo_x = var_data[self.var_tag_geo_x]
            var_geo_y = var_data[self.var_tag_geo_y]

            if self.var_tag_geo_x not in list(var_frame.keys()):
                var_frame[self.var_tag_geo_x] = domain_geo_x
            if self.var_tag_geo_y not in list(var_frame.keys()):
                var_frame[self.var_tag_geo_y] = domain_geo_y
            if self.var_tag_terrain not in list(var_frame.keys()):
                var_frame[self.var_tag_terrain] = domain_values

            # Initialize computing driver
            if 'var_method_compute' in list(info_step.keys()):

                driver_var_cmp = ModelVariables(info_key=info_key,
                                                var_data=var_values, var_geo_x=var_geo_x, var_geo_y=var_geo_y,
                                                domain_values=domain_values,
                                                domain_geo_x=domain_geo_x, domain_geo_y=domain_geo_y,
                                                var_name=info_step['var_name'],
                                                var_units=info_step['units'],
                                                var_step_type=info_step['var_type'],
                                                var_fx=info_step['var_method_compute'],
                                                file_tag_units=file_tag_units,
                                                file_tag_step_type=file_tag_step_type,
                                                file_tag_time=file_tag_time)

                var_data_cmp, var_time_cmp, var_attr_cmp = driver_var_cmp.configure_fx()

                log_stream.info(' ----> Analyze variable: ' + info_key + ' ... DONE')

            else:
                log_stream.info(' ----> Analyze variable: ' + info_key + ' ... SKIPPED. Computing method not defined')
                var_data_cmp = None

            # Store data in a common workspace
            var_frame[info_key] = var_data_cmp

        # Dump tmp file
        var_frame = self.merge_obj(var_data, var_frame)
        write_obj(self.file_tmp, var_frame)

        return var_frame
# -------------------------------------------------------------------------------------
