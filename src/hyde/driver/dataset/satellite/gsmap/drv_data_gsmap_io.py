"""
Library Features:

Name:          drv_data_gsmap_io
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20200302'
Version:       '1.0.0'
"""
#################################################################################
# Library
import logging
import os

import numpy as np
import pandas as pd

from src.common.zip.lib_data_zip_gzip import openZip, zipFile, closeZip

from src.hyde.algorithm.io.satellite.gsmap.lib_gsmap_io_generic import write_obj, read_obj
from src.hyde.algorithm.io.satellite.gsmap.lib_gsmap_io_generic import create_darray_3d, create_dset, write_dset
from src.hyde.algorithm.io.satellite.gsmap.lib_gsmap_io_nc import read_data_gsmap

from src.common.default.lib_default_conventions import oVarConventions as var_conventions_default
from src.hyde.algorithm.settings.satellite.gsmap.lib_gsmap_args import logger_name, time_units, time_format, time_calendar

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
# Class to write data
class DataWriter:

    def __init__(self,
                 var_info=None, var_attrs_list = None, var_geo=None, var_time=None,
                 folder_out=None, file_out=None, tag_out=None,
                 var_tag_geo_terrain='terrain', var_tag_geo_x='geo_x', var_tag_geo_y='geo_y', var_tag_time='time',
                 dset_write_engine='netcdf', dset_compression_level=9, dset_format='NETCDF4',
                 file_compression_mode=False, file_compression_ext='.gz', file_priority=None):

        self.var_info = var_info
        self.var_attrs_list = var_attrs_list
        self.var_geo = var_geo
        self.var_time = var_time

        self.var_tag_time = var_tag_time
        self.var_tag_geo_terrain = var_tag_geo_terrain
        self.var_tag_geo_x = var_tag_geo_y
        self.var_tag_geo_y = var_tag_geo_x

        self.folder_out = folder_out
        self.file_out = file_out
        self.tag_out = tag_out

        link_out = {}

        for tag_key, tag_value in self.tag_out.items():
            for tag_value_step in tag_value:
                for (folder_key, folder_value), (file_key, file_value) in zip(
                        self.folder_out.items(), self.file_out.items()):

                    for folder_value_step, file_value_step in zip(folder_value, file_value):

                        if (folder_value_step is not None) and (file_value_step is not None):
                            if not os.path.exists(folder_value_step):
                                os.makedirs(folder_value_step)
                            if tag_value_step not in list(link_out.keys()):
                                link_out[tag_value_step] = [os.path.join(folder_value_step, file_value_step)]
                            else:
                                link_tmp = link_out[tag_value_step]
                                link_tmp.extend([os.path.join(folder_value_step, file_value_step)])
                                link_out[tag_value_step] = list(set(link_tmp))

        self.link_out = link_out
        self.dset_format = dset_format
        self.dset_compression_level = dset_compression_level
        self.dset_write_engine = dset_write_engine

        self.file_compression_mode = file_compression_mode
        self.file_compression_ext = file_compression_ext.replace('.','')

        self.file_priority = file_priority

        self.link_zip = {}
        if self.file_compression_mode:
            file_list_zip = []
            for file_key, file_list_unzip in self.link_out.items():
                for file_name_unzip in file_list_unzip:
                    file_name_zip = os.path.join(file_name_unzip + "." + self.file_compression_ext)
                    file_list_zip.append(file_name_zip)

                self.link_zip[file_key] = file_list_zip
        else:
            self.link_zip = None

    def organize_obj(self, data_obj_in):

        # Starting info
        log_stream.info(' ----> Organize data ... ')

        var_info = self.var_info
        var_time = self.var_time

        folder_out = self.folder_out
        file_out = self.file_out

        dset_ref = self.file_priority['ref']
        dset_other = self.file_priority['other']

        var_geo_values = data_obj_in[self.var_tag_geo_terrain]
        var_geo_x = data_obj_in[self.var_tag_geo_x]
        var_geo_y = data_obj_in[self.var_tag_geo_y]

        if hasattr(data_obj_in[self.var_tag_geo_terrain], 'attrs'):
            var_geo_attrs = data_obj_in[self.var_tag_geo_terrain].attrs
        else:
            var_geo_attrs = var_conventions_default['terrain']

        data_obj_out = {}
        for var_key, var_data in var_info.items():

            log_stream.info(' -----> VarKey ' + var_key + ' ... ')

            dset_obj_step = data_obj_in[var_key]
            dset_time_step = pd.to_datetime(data_obj_in[var_key][self.var_tag_time].values)
            dset_vars = list(dset_obj_step.data_vars)

            settings_vars = var_data['var_name']
            settings_file = var_data['var_file']
            settings_dims = var_data['var_dims']

            var_timestamp = var_time[var_key]
            var_folder_out = folder_out[var_key]
            var_file_out = file_out[var_key]

            for var_id, (var_dset_name, var_data_name, var_data_file, var_data_dims) in \
                    enumerate(zip(dset_vars, settings_vars, settings_file, settings_dims)):

                if var_data_file is not None:

                    for var_timestep, var_folder_step, var_file_step in zip(var_timestamp,var_folder_out, var_file_out):

                        log_stream.info(' ------> VarTime ' + str(var_timestep) + ' ... ')

                        if var_timestep in dset_time_step:

                            dset_obj_sliced = dset_obj_step.sel({self.var_tag_time: var_timestep})

                            var_data_values = dset_obj_sliced[var_dset_name].values
                            var_data_time = dset_obj_sliced[self.var_tag_time].values

                            if isinstance(var_data_time, np.datetime64):
                                var_data_time = [var_data_time]
                            elif isinstance(var_data_time, np.ndarray):
                                pass
                            else:
                                log_stream.error(' ==> Datasets time format is not allowed')
                                raise NotImplemented('Datasets time format not implemented yet')

                            var_data_attrs = {attr_key: var_data[attr_key][var_id] for attr_key in self.var_attrs_list}

                            var_dset_step = create_dset(var_data_time=var_data_time,
                                                        var_data_name=var_data_name, var_data_values=var_data_values,
                                                        var_data_attrs=var_data_attrs,
                                                        var_geo_1d=False,
                                                        var_geo_name='terrain', var_geo_values=var_geo_values,
                                                        var_geo_x=var_geo_x, var_geo_y=var_geo_y,
                                                        var_geo_attrs=var_geo_attrs)

                            if not os.path.exists(var_folder_step):
                                os.makedirs(var_folder_step)
                            var_path_step = os.path.join(var_folder_step, var_file_step)

                            if var_data_dims == 'var3d':
                                if var_data_file not in data_obj_out:
                                    data_obj_out[var_data_file] = var_dset_step
                                else:
                                    var_dset_tmp = data_obj_out[var_data_file]
                                    var_dset_merge = var_dset_tmp.merge(var_dset_step, join='right')
                                    data_obj_out[var_data_file] = var_dset_merge

                                log_stream.info(' ------> VarTime ' + str(var_timestep) + ' ... OK')

                            elif var_data_dims == 'var2d':

                                if var_data_file not in data_obj_out:
                                    data_obj_out[var_data_file] = {}

                                if var_path_step not in data_obj_out[var_data_file]:
                                    data_obj_out[var_data_file][var_path_step] = var_dset_step
                                    log_stream.info(' ------> VarTime ' + str(var_timestep) + ' ... OK')
                                else:
                                    if var_key == dset_ref:
                                        data_obj_out[var_data_file][var_path_step] = var_dset_step
                                        log_stream.info(' ------> VarTime ' + str(var_timestep) +
                                                        ' ... UPDATE. Data has updated by the reference datasets')
                                    else:
                                        log_stream.info(' ------> VarTime ' + str(var_timestep) +
                                                        ' ... SKIPPED. Data previously saved by the reference datasets')
                            else:
                                log_stream.error(' ==> Datasets dims format is not allowed')
                                raise NotImplemented('Datasets dims format not implemented yet')

                            log_stream.info(' ------> TimeStep ' + str(var_timestep) + ' ... DONE')

                        else:
                            log_stream.warning(' ------> TimeStep ' + str(var_timestep) +
                                               ' ... FAILED. Data not available in datasets')

            log_stream.info(' -----> VarKey ' + var_key + ' ... DONE')

        # Ending info
        log_stream.info(' ----> Organize data ... DONE')

        return data_obj_out

    def dump_obj(self, data_obj):

        # Starting info
        log_stream.info(' ----> Dump data ... ')

        dump_status = []
        file_status = []
        for link_file, dset_out in data_obj.items():

            if isinstance(dset_out, dict):
                file_name_out = list(dset_out.keys())
                dset_out = list(dset_out.values())
            else:
                if link_file in list(self.link_out.keys()):
                    file_name_out = [self.link_out[link_file]]
                    dset_out = [dset_out]
                else:
                    log_stream.error(' ==> Datasets data are not available')
                    raise IOError('Check your datasets during dumping procedure')

            for file_name_step, dset_step in zip(file_name_out, dset_out):
                if file_name_out is not None:

                    # Write dset
                    write_dset(file_name_step,
                               dset_data=dset_step, dset_format=self.dset_format,
                               dset_compression=self.dset_compression_level, dset_engine=self.dset_write_engine)

                    file_status.append(file_name_step)
                    dump_status.append(True)
                else:
                    file_status.append(None)
                    dump_status.append(False)

        # Ending info
        log_stream.info(' ----> Dump data ... DONE')

        return file_status, dump_status

    def zip_obj(self):

        # Starting info
        log_stream.info(' ----> Zip data ... ')

        file_zip = list(self.link_zip.values())[0]
        file_zip.sort()
        file_out = list(self.link_out.values())[0]
        file_out.sort()

        file_compression_mode = self.file_compression_mode

        if file_compression_mode:
            for file_out_step, file_zip_step in zip(file_out, file_zip):
                if os.path.exists(file_out_step):

                    if os.path.exists(file_zip_step):
                        os.remove(file_zip_step)

                    if os.path.exists(file_out_step):
                        file_handle_in, file_handle_out = openZip(file_out_step, file_zip_step, 'z')

                        zipFile(file_handle_in, file_handle_out)
                        closeZip(file_handle_in, file_handle_out)
                    else:
                        # Ending info
                        log_stream.warning(' ----> Zip data ... SKIPPED. File ' + file_out_step + ' not available')

                    if os.path.exists(file_zip_step) and os.path.exists(file_out_step):
                        os.remove(file_out_step)

                else:
                    # Ending info
                    log_stream.warning(' ----> Zip data ... SKIPPED. File ' + file_out_step + ' not saved')

            # Ending info
            log_stream.info(' ----> Zip data ... DONE')

        else:
            # Ending info
            log_stream.info(' ----> Zip data ... SKIPPED. Zip not activated')

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class to read data
class DataReader:

    def __init__(self,
                 var_data=None, file_data=None,
                 folder_tmp=None, file_tmp='nwp_source_in.workspace',
                 var_tag_geo_x='geo_x', var_tag_geo_y='geo_y', var_tag_time='time',
                 file_tag_coord_geo_x='lon', file_tag_coord_geo_y='lat', file_tag_coord_time='time',
                 file_tag_dim_geo_x='lon', file_tag_dim_geo_y='lat', file_tag_dim_time='time'):

        self.var_data = var_data
        self.file_data = file_data

        self.var_tag_time = var_tag_time
        self.var_tag_geo_x = var_tag_geo_y
        self.var_tag_geo_y = var_tag_geo_x

        self.file_tag_coord_time = file_tag_coord_time
        self.file_tag_coord_geo_x = file_tag_coord_geo_x
        self.file_tag_coord_geo_y = file_tag_coord_geo_y

        self.file_tag_dim_time = file_tag_dim_time
        self.file_tag_dim_geo_x = file_tag_dim_geo_x
        self.file_tag_dim_geo_y = file_tag_dim_geo_y

        self.folder_tmp = folder_tmp
        self.file_tmp = file_tmp

        found_data = []
        for file_key, file_list in self.file_data.items():
            if not isinstance(file_list, list):
                file_list = [file_list]
            for file_step in file_list:
                if file_step is not None:
                    if os.path.exists(file_step):
                        found_data.append(True)
                    else:
                        log_stream.error(' ===> Variable for ' + file_key + ' File ' + file_step + ' NOT FOUND!')
                        found_data.append(False)
                        raise IOError(' Expected file not found! Check your input!')
                else:
                    log_stream.warning(' ===> Variable for ' + file_key + ' File NOT SET!')
                    found_data.append(True)
                    break

        self.found_data = all(i is True for i in found_data)

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

    def organize_obj(self, time_range):

        # Starting info
        log_stream.info(' ----> Get data ... ')

        # Get information
        var_data = self.var_data
        file_data = self.file_data

        # Check file data availability
        var_frame = {}
        for (var_key, var_info), (file_key, file_list) in zip(var_data.items(), file_data.items()):

            var_source_list = var_info['var_source']
            var_format_list = var_info['var_format']
            var_dims_list = var_info['var_dims']
            var_name_list = var_info['var_name']

            if not isinstance(var_source_list, list):
                var_source_list = [var_source_list]
            if not isinstance(var_format_list, list):
                var_format_list = [var_format_list]
            if not isinstance(var_dims_list, list):
                var_dims_list = [var_dims_list]
            if not isinstance(var_name_list, list):
                var_name_list = [var_name_list]

            var_id = {}
            for var_id_step, var_name_step in enumerate(var_name_list):
                var_id[var_name_step] = int(var_id_step)

            # Starting info
            log_stream.info(' ----->  VarKey ' + var_key + ' ... ')

            if file_list.__len__() > 1:

                n_var = var_source_list.__len__()
                n_file = file_list.__len__()
                step_ratio = int(n_file / n_var)

                var_source_list_fill = []
                var_format_list_fill = []
                var_dims_list_fill = []
                var_name_list_fill = []
                time_range_fill = None
                for var_source_id, var_source_step in enumerate(var_name_list):
                    var_source_list_fill.extend([var_source_list[var_source_id]] * step_ratio)
                    var_format_list_fill.extend([var_format_list[var_source_id]] * step_ratio)
                    var_dims_list_fill.extend([var_dims_list[var_source_id]] * step_ratio)
                    var_name_list_fill.extend([var_name_list[var_source_id]] * step_ratio)

                    if time_range_fill is None:
                        time_range_fill = time_range
                    else:
                        time_range_fill = time_range_fill.append(time_range)

                if n_var > 1:
                    idx_start = np.arange(0, n_file, n_var).tolist()
                    idx_end = np.arange(n_var, n_file + n_var, n_var).tolist()

                    file_arrange = {}
                    for start_id, end_id in zip(idx_start, idx_end):
                        file_tmp = file_list[start_id: end_id]
                        for i in range(0, n_var):
                            file_i = [file_tmp[i]]
                            if i not in list(file_arrange.keys()):
                                file_arrange[i] = file_i
                            else:
                                file_spool = file_arrange[i]
                                file_spool.extend(file_i)
                                file_arrange[i] = file_spool

                    file_list_fill = []
                    for file_subset in file_arrange.values():
                        file_list_fill.extend(file_subset)
                else:
                    file_list_fill = file_list

            else:
                var_source_list_fill = var_source_list
                var_format_list_fill = var_format_list
                var_dims_list_fill = var_dims_list
                var_name_list_fill = var_name_list
                file_list_fill = file_list
                time_range_fill = time_range

            var_dset_data = None
            var_dset_name = []
            var_frame[var_key] = {}
            for file_id, (var_source, var_format, var_dims, var_name, file_name, time_step) in enumerate(
                    zip(var_source_list_fill, var_format_list_fill, var_dims_list_fill,
                        var_name_list_fill, file_list_fill, time_range_fill)):

                if isinstance(var_name, str):
                    var_id_step = 0
                elif isinstance(var_name, list):
                    var_id_step = var_id[var_name]
                    raise NotImplementedError('Variable idx list not allowed!')
                else:
                    raise NotImplementedError('Variable idx type  not allowed!')

                log_stream.info(' ------>  VarKey ' + var_key + ' :: VarName ' + var_name +
                                ' :: TimeStep ' + str(time_step) + ' ... ')

                if (file_name is not None) and (os.path.exists(file_name)):

                    if var_format == 'netcdf':

                        if var_source == 'gsmap':

                            if var_dims == 'var2d':
                                [file_data_raw, _,
                                 file_geo_x, file_geo_y] = read_data_gsmap(
                                    file_name, var_name,
                                    tag_coord_geo_x=self.file_tag_coord_geo_x,
                                    tag_coord_geo_y=self.file_tag_coord_geo_y,
                                    tag_coord_time=self.file_tag_coord_time,
                                    tag_dim_geo_x=self.file_tag_dim_geo_x,
                                    tag_dim_geo_y=self.file_tag_dim_geo_y,
                                    tag_dim_time=self.file_tag_dim_time
                                )

                                name_data_raw = file_data_raw[var_id_step].name
                                file_dset_raw = file_data_raw[var_id_step].to_dataset(name=name_data_raw)

                                if self.var_tag_geo_x not in list(var_data.keys()):
                                    var_frame[self.var_tag_geo_x] = file_geo_x
                                if self.var_tag_geo_y not in list(var_data.keys()):
                                    var_frame[self.var_tag_geo_y] = file_geo_y

                                var_dset_name.append(name_data_raw)
                                if var_dset_data is None:
                                    var_dset_data = file_dset_raw
                                else:
                                    var_dset_data = var_dset_data.combine_first(file_dset_raw)

                                log_stream.info(' ------>  VarKey ' + var_key + ' :: VarName ' + var_name +
                                                ' :: TimeStep ' + str(time_step) + ' ... DONE')

                            elif var_dims == 'var3d':

                                [file_data_raw, _,
                                 file_geo_x, file_geo_y] = read_data_gsmap(
                                    file_name, var_name,
                                    tag_coord_geo_x=self.file_tag_coord_geo_x,
                                    tag_coord_geo_y=self.file_tag_coord_geo_y,
                                    tag_coord_time=self.file_tag_coord_time,
                                    tag_dim_geo_x=self.file_tag_dim_geo_x,
                                    tag_dim_geo_y=self.file_tag_dim_geo_y,
                                    tag_dim_time=self.file_tag_dim_time
                                )

                                name_data_raw = file_data_raw[var_id_step].name
                                file_dset_raw = file_data_raw[var_id_step].to_dataset(name=name_data_raw)

                                if self.var_tag_geo_x not in list(var_data.keys()):
                                    var_frame[self.var_tag_geo_x] = file_geo_x
                                if self.var_tag_geo_y not in list(var_data.keys()):
                                    var_frame[self.var_tag_geo_y] = file_geo_y

                                var_dset_name.append(name_data_raw)
                                if var_dset_data is None:
                                    var_dset_data = file_dset_raw
                                else:
                                    var_dset_data = var_dset_data.combine_first(file_dset_raw)

                                log_stream.info(' ------>  VarKey ' + var_key + ' :: VarName ' + var_name +
                                                ' :: TimeStep ' + str(time_step) + ' ... DONE')

                            else:
                                log_stream.error(' ===>  VarKey ' + var_key + ' :: VarName ' + var_name +
                                                 ' :: TimeStep ' + str(time_step) + ' ... FAILED!')
                                raise NotImplementedError('File source dims not allowed!')
                        else:
                            log_stream.error(' ===>  VarKey ' + var_key + ' :: VarName ' + var_name +
                                             ' :: TimeStep ' + str(time_step) + ' ... FAILED!')
                            raise NotImplementedError('File source dims not implemented!')
                    else:
                        log_stream.error(' ===>  VarKey ' + var_key + ' :: VarName ' + var_name +
                                         ' :: TimeStep ' + str(time_step) + ' ... FAILED!')
                        raise NotImplementedError('File source library not implemented!')
                else:

                    if var_key in list(var_frame.keys()):
                        log_stream.warning(' ===>  VarKey ' + var_key + ' :: VarName ' + var_name +
                                           ' :: TimeStep ' + str(time_step) + ' ... NULL. FILE NOT DEFINED!')

                        var_frame_step = None
                        for var_name_tmp in var_dset_name:
                            if var_name_tmp in list(var_dset_data.data_vars):
                                var_frame_step = var_dset_data[var_name_tmp]
                                break

                        if var_name not in list(var_dset_data.data_vars):

                            if var_frame_step is not None:
                                var_frame_null = np.zeros([var_frame_step.shape[0],
                                                           var_frame_step.shape[1], var_frame_step.shape[2]])
                                var_frame_null[:, :, :] = np.nan

                                var_time_null = var_frame_step[self.file_tag_coord_time]
                                var_geo_x_null = var_frame_step[self.file_tag_coord_geo_x].values
                                var_geo_y_null = var_frame_step[self.file_tag_coord_geo_y].values

                                var_da_null = create_darray_3d(
                                    var_frame_null, var_time_null, var_geo_x_null, var_geo_y_null,
                                    dim_key_time=self.file_tag_coord_time,
                                    dim_key_x=self.file_tag_coord_geo_x, dim_key_y=self.file_tag_coord_geo_y,
                                    dim_name_x=self.file_tag_dim_geo_x, dim_name_y=self.file_tag_dim_geo_y,
                                    dim_name_time=self.file_tag_dim_time,
                                    dims_order=[self.file_tag_dim_time, self.file_tag_dim_geo_y, self.file_tag_dim_geo_x])

                                var_dset_null = var_da_null.to_dataset(name=var_name)

                                if var_dset_data is None:
                                    var_dset_data = var_dset_null
                                else:
                                    var_dset_data = var_dset_data.combine_first(var_dset_null)
                            else:
                                log_stream.warning(' ===>  VarKey ' + var_key + ' :: VarName ' + var_name +
                                                   ' :: TimeStep ' + str(time_step) + ' ... NULL. DATASETS NOT FOUND!')
                                var_dset_data = None
                                break
                        else:
                            log_stream.warning(' ===>  VarKey ' + var_key + ' :: VarName ' + var_name
                                               + ' :: TimeStep ' + str(time_step) +
                                               ' ... SKIPPED. DATA NULL ALREADY AVAILABLE IN DATASETS)')

                    else:
                        log_stream.warning(' ===>  VarKey ' + var_key + ' :: VarName ' + var_name +
                                           ' :: TimeStep ' + str(time_step) + ' ... NULL. FILE NOT FOUND!')
                        var_dset_data = None
                        break

            # Store in a frame
            var_frame[var_key] = var_dset_data

            # Ending info
            log_stream.info(' ----->  VarKey ' + var_key + ' ... DONE')

        # Dump tmp file
        write_obj(self.file_tmp, var_frame)

        # Ending info
        log_stream.info(' ----> Get data ... DONE')

        return var_frame

# -------------------------------------------------------------------------------------
