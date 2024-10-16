"""
Class Features

Name:          drv_data_dynamic
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20230824'
Version:       '1.0.0'
"""

# -------------------------------------------------------------------------------------
# libraries
import logging
import os
import pandas as pd

from copy import deepcopy

from lib_info_args import logger_name
from lib_info_args import time_format_algorithm
from lib_info_args import (geo_dim_name_x, geo_dim_name_y, geo_coord_name_x, geo_coord_name_y,
                           geo_var_name_x, geo_var_name_y)

from lib_utils_time import set_time_run
from lib_utils_generic import make_folder, reset_folder
from lib_data_io_pickle import read_file_obj, write_file_obj
from lib_data_io_grib import read_file_grib, organize_file_grib
from lib_data_io_nc import (read_file_nc, organize_file_nc_xarray, organize_file_nc_library,
                            write_file_nc_xarray, write_file_nc_library)

from lib_data_io_gzip import zip_filename, unzip_filename

from lib_utils_io import fill_string_with_time, fill_string_with_info
from lib_utils_zip import remove_zip_extension, add_zip_extension

from lib_fx_methods import (extract_data,
                            transform_dset_2_data, transform_data_2_dset,
                            resample_data, mask_data, compose_data)

# set logger
alg_logger = logging.getLogger(logger_name)

# debug
import matplotlib.pylab as plt
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# class driver data
class DrvData:

    # method to initialize class
    def __init__(self, alg_time_reference, alg_time_now,
                 alg_static, alg_settings,
                 tag_section_flags='flags', tag_section_template='template',
                 tag_section_info='info', tag_section_variables='variables',
                 tag_section_methods='methods', tag_section_datasets='datasets',
                 tag_section_log='log', tag_section_tmp='tmp'):

        self.alg_time_reference = alg_time_reference
        self.alg_time_now = alg_time_now

        self.alg_static = alg_static

        self.alg_flags = alg_settings[tag_section_flags]
        self.alg_template_info = alg_settings[tag_section_template]['info']
        self.alg_template_time = alg_settings[tag_section_template]['time']
        self.alg_variables = alg_settings[tag_section_variables]
        self.alg_methods = alg_settings[tag_section_methods]
        self.alg_info = alg_settings[tag_section_info]

        self.alg_datasets_time = alg_settings[tag_section_datasets]['dynamic']['time']

        self.alg_datasets_src = alg_settings[tag_section_datasets]['dynamic']['source']
        self.alg_datasets_anc_raw = alg_settings[tag_section_datasets]['dynamic']['ancillary']['raw']
        self.alg_datasets_anc_def = alg_settings[tag_section_datasets]['dynamic']['ancillary']['def']
        self.alg_datasets_dst = alg_settings[tag_section_datasets]['dynamic']['destination']

        self.alg_log = alg_settings[tag_section_log]
        self.alg_tmp = alg_settings[tag_section_tmp]

        self.tag_folder_name, self.tag_file_name = 'folder_name', 'file_name'
        self.tag_variables, self.tag_compression, self.tag_format = 'variables', 'compression', 'format'

        self.reset_datasets_anc_raw = self.alg_flags['reset_datasets_ancillary_raw']
        self.reset_datasets_anc_def = self.alg_flags['reset_datasets_ancillary_def']
        self.reset_datasets_dst = self.alg_flags['reset_datasets_destination']
        self.reset_logs = self.alg_flags['reset_logs']

        self.file_collections_src = self.alg_datasets_src

        self.folder_name_anc_raw = self.alg_datasets_anc_raw[self.tag_folder_name]
        self.file_name_anc_raw = self.alg_datasets_anc_raw[self.tag_file_name]
        self.file_path_anc_raw = os.path.join(self.folder_name_anc_raw, self.file_name_anc_raw)

        self.folder_name_anc_def = self.alg_datasets_anc_def[self.tag_folder_name]
        self.file_name_anc_def = self.alg_datasets_anc_def[self.tag_file_name]
        self.file_path_anc_def = os.path.join(self.folder_name_anc_def, self.file_name_anc_def)

        self.folder_name_dst = self.alg_datasets_dst[self.tag_folder_name]
        self.file_name_dst = self.alg_datasets_dst[self.tag_file_name]
        self.file_path_dst = os.path.join(self.folder_name_dst, self.file_name_dst)
        self.format_dst = self.alg_datasets_dst[self.tag_format]
        self.compression_dst = self.alg_datasets_dst[self.tag_compression]
        self.variables_dst = self.alg_datasets_dst[self.tag_variables]

        self.grid_geo_x_src, self.grid_geo_y_src = self.alg_static['grid_geo_x_src'], self.alg_static['grid_geo_y_src']
        self.transform_src, self.proj_src = self.alg_static['transform_src'], self.alg_static['proj_src']
        self.grid_geo_values_dst = self.alg_static['grid_geo_values_dst']
        self.grid_geo_x_dst, self.grid_geo_y_dst = self.alg_static['grid_geo_x_dst'], self.alg_static['grid_geo_y_dst']
        self.transform_dst, self.proj_dst = self.alg_static['transform_dst'], self.alg_static['proj_dst']

        self.settings_organize_data = self.alg_methods['organize_data']
        self.settings_resample_data = self.alg_methods['resample_data']
        self.settings_compose_data = self.alg_methods['compose_data']
        self.settings_mask_data = self.alg_methods['mask_data']

        self.alg_time_reference = set_time_run(
            time_run=self.alg_time_reference, time_hour_reference=self.alg_datasets_time['data_hour_reference'])

    # method to define file string
    def __define_file_string(self, file_string_tmpl):
        file_string_def = fill_string_with_time(file_string_tmpl, self.alg_time_reference, self.alg_template_time)
        file_string_def = fill_string_with_info(file_string_def, self.alg_info, self.alg_template_info)
        return file_string_def

    # method to organize data
    def organize_data(self):

        # info start method
        alg_logger.info(' ---> Organize dynamic datasets ... ')

        # get time reference and time now
        alg_time_reference = self.alg_time_reference
        alg_time_now = self.alg_time_now

        # get algorithm variables
        alg_variables = self.alg_variables
        # get settings methods
        alg_settings_organize_data = self.settings_organize_data

        # get file path
        file_collections_src = self.file_collections_src
        file_path_anc_raw_tmpl, file_path_anc_def_tmpl = self.file_path_anc_raw, self.file_path_anc_def
        file_path_dst_tmpl = self.file_path_dst

        # method to define the ancillary file path(s)
        file_path_anc_raw_step = self.__define_file_string(file_path_anc_raw_tmpl)
        file_path_anc_def_step = self.__define_file_string(file_path_anc_def_tmpl)
        # method to define the destination file path
        file_path_dst_step = self.__define_file_string(file_path_dst_tmpl)

        # check file in according to compression flag
        if self.compression_dst:
            file_path_dst_step = add_zip_extension(file_path_dst_step)

        # clean ancillary datasets (if ancillary flag(s) is activated)
        if self.reset_datasets_anc_raw or self.reset_datasets_anc_def:
            if os.path.exists(file_path_anc_raw_step):
                os.remove(file_path_anc_raw_step)
            if os.path.exists(file_path_anc_def_step):
                os.remove(file_path_anc_def_step)
            if os.path.exists(file_path_dst_step):
                os.remove(file_path_dst_step)
        # clean destination datasets (if ancillary flag(s) is activated)
        if self.reset_datasets_dst:
            if os.path.exists(file_path_dst_step):
                os.remove(file_path_dst_step)
        # clean ancillary and destination datasets if are not available together
        if (not os.path.exists(file_path_anc_raw_step)) and (not os.path.exists(file_path_dst_step)):
            if os.path.exists(file_path_anc_raw_step):
                os.remove(file_path_anc_raw_step)
            if os.path.exists(file_path_anc_def_step):
                os.remove(file_path_anc_def_step)
            if os.path.exists(file_path_dst_step):
                os.remove(file_path_dst_step)

        # info start time reference
        alg_logger.info(' ----> Time reference "' + alg_time_reference.strftime(time_format_algorithm) + '" ... ')

        # check file ancillary availability
        if not os.path.exists(file_path_anc_raw_step):

            # iterate over time file(s)
            collections_dset_src, collections_attrs_src = None, None
            for file_data_tag, file_data_fields in file_collections_src.items():

                # info start time step
                alg_logger.info(' -----> Data "' + file_data_tag + '" ... ')

                # get file information
                folder_name_src_tmpl = file_data_fields[self.tag_folder_name]
                file_name_src_tmpl = file_data_fields[self.tag_file_name]
                file_compression_src = file_data_fields[self.tag_compression]
                file_variables_src = file_data_fields[self.tag_variables]

                # create file path (join folder and file name)
                file_path_src_tmpl = os.path.join(folder_name_src_tmpl, file_name_src_tmpl)
                # method to fill the filename(s)
                file_path_src_step = self.__define_file_string(file_path_src_tmpl)

                # info start file step
                alg_logger.info(' ------> Read file "' + file_path_src_step + '" ... ')

                # check file source availability
                if os.path.exists(file_path_src_step):

                    # check compression mode
                    if file_compression_src:
                        file_path_src_tmp = remove_zip_extension(file_path_src_step)
                        unzip_filename(file_path_src_step, file_path_src_tmp)
                    else:
                        file_path_src_tmp = deepcopy(file_path_src_step)

                    # get dataset source
                    obj_data_src, obj_attrs_src, obj_geo_src, obj_time_src = read_file_grib(
                        file_path_src_tmp, file_time_reference=alg_time_now,
                        file_variables=file_variables_src)

                    # organize dataset source
                    if obj_data_src is not None:
                        obj_dset_src, attrs_dset_src = organize_file_grib(
                            obj_data_src,
                            obj_time_src['time'], obj_geo_src['longitude'], obj_geo_src['latitude'],
                            obj_attrs=obj_attrs_src, obj_settings=alg_variables,
                            obj_method=alg_settings_organize_data,
                            reference_time=alg_time_reference)
                    else:
                        obj_dset_src, attrs_dset_src = None, None

                    # merge dataset source
                    if obj_dset_src is not None:

                        # store data collections
                        if collections_dset_src is None:
                            collections_dset_src = deepcopy(obj_dset_src)
                        else:
                            for (c_dim_name, c_dim_value), (s_dim_name, s_dim_value) in zip(
                                    collections_dset_src.dims.items(), obj_dset_src.dims.items()):
                                if c_dim_name != s_dim_name:
                                    raise ValueError('Dimension names are different or order is different')
                                else:
                                    if c_dim_value != s_dim_value:
                                        raise ValueError('Dimension values are different')
                            collections_dset_src = collections_dset_src.merge(obj_dset_src)

                        # store attrs collections
                        if collections_attrs_src is None:
                            collections_attrs_src = {}
                        collections_attrs_src = {**collections_attrs_src, **attrs_dset_src}

                    # info end file step
                    alg_logger.info(' ------> Read file "' + file_path_src_step + '" ... DONE ')

                else:

                    # info end file step
                    alg_logger.info(' ------> Read file "' + file_path_src_step +
                                    '" ... SKIPPED. File not available ')

                # info end time step
                alg_logger.info(' -----> Data "' + file_data_tag + '" ... DONE')

            # check collections datasets availability
            if collections_dset_src is not None:

                # check collections datasets not empty
                if len(collections_dset_src.dims) > 0:

                    # save variable(s) obj to ancillary file
                    folder_name_anc_raw_step, file_name_anc_raw_step = os.path.split(file_path_anc_raw_step)
                    make_folder(folder_name_anc_raw_step)

                    obj_src_collection = {'data': collections_dset_src, 'attrs': collections_attrs_src}
                    write_file_obj(file_path_anc_raw_step, obj_src_collection)

                    # info end time reference (success)
                    alg_logger.info(' ----> Time reference "' + alg_time_reference.strftime(time_format_algorithm) +
                                    '" ... DONE')

                else:
                    # info end time reference (dataset empty)
                    alg_logger.info(' ----> Time reference "' + alg_time_reference.strftime(time_format_algorithm) +
                                    '" ... FAILED. Source datasets are empty')
            else:
                # info end time reference (dataset empty)
                alg_logger.info(' ----> Time reference "' + alg_time_reference.strftime(time_format_algorithm) +
                                '" ... FAILED. Source datasets are not available')
        else:
            # info end time step
            alg_logger.info(' ----> Time reference "' + alg_time_reference.strftime(time_format_algorithm) +
                            '" ... SKIPPED. Datasets previously saved.')

        # info end method
        alg_logger.info(' ---> Organize dynamic datasets ... DONE')

    # method to analyze data
    def analyze_data(self):

        # info start method
        alg_logger.info(' ---> Analyze dynamic datasets ... ')

        # get time reference
        alg_time_reference = self.alg_time_reference

        # get file path
        file_path_anc_raw_tmpl, file_path_anc_def_tmpl = self.file_path_anc_raw, self.file_path_anc_def
        # get grid info
        grid_geo_x_src, grid_geo_y_src = self.grid_geo_x_src, self.grid_geo_y_src
        grid_geo_values_dst = self.grid_geo_values_dst
        grid_geo_x_dst, grid_geo_y_dst = self.grid_geo_x_dst, self.grid_geo_y_dst

        # get algorithm variables
        alg_variables = self.alg_variables

        # get settings methods
        settings_resample_data = self.settings_resample_data
        settings_mask_data = self.settings_mask_data
        settings_compose_data = self.settings_compose_data

        # info start time reference
        alg_logger.info(' ----> Time reference "' + alg_time_reference.strftime(time_format_algorithm) + '" ... ')

        # method to define the ancillary file path(s)
        file_path_anc_raw_step = self.__define_file_string(file_path_anc_raw_tmpl)
        file_path_anc_def_step = self.__define_file_string(file_path_anc_def_tmpl)

        # check file ancillary availability
        if not os.path.exists(file_path_anc_def_step):
            # check file source availability
            if os.path.exists(file_path_anc_raw_step):

                # info start get datasets
                alg_logger.info(' -----> (1) Get datasets ... ')
                # get datasets
                obj_collections_anc_raw_step = read_file_obj(file_path_anc_raw_step)
                # info end get datasets
                alg_logger.info(' -----> (1) Get datasets ... DONE')

                # info start extract datasets
                alg_logger.info(' -----> (2) Extract datasets ... ')
                # extract datasets
                (obj_data_anc_extract_step, obj_attrs_anc_extract_step,
                 obj_time_anc, obj_geo_x_anc, obj_geo_y_anc) = extract_data(
                    obj_collections_anc_raw_step,
                    var_name_time='time', var_name_geo_x='west_east', var_name_geo_y='south_north')
                # info end extract datasets
                alg_logger.info(' -----> (2) Extract datasets ... DONE')

                import numpy as np
                values_extract = np.flipud(obj_data_anc_extract_step['air_temperature'].values[0, :, :])

                # info start compose datasets
                alg_logger.info(' -----> (3) Compose datasets ... ')
                # compose datasets
                obj_data_anc_compose_step, obj_attrs_anc_compose_step = compose_data(
                    obj_data_anc_extract_step, obj_attrs_anc_extract_step, alg_time_reference, settings_compose_data)
                # info end compose datasets
                alg_logger.info(' -----> (3) Compose datasets ... DONE')

                values_compose = np.flipud(obj_data_anc_compose_step['air_temperature'].values[0, :, :])

                # info start transform datasets
                alg_logger.info(' -----> (4) Transform datasets ... ')
                # compose datasets
                obj_data_anc_ds2data_step, obj_attrs_anc_step = transform_dset_2_data(
                    obj_data_anc_compose_step, obj_attrs_anc_compose_step)
                # info start transform datasets
                alg_logger.info(' -----> (4) Transform datasets ... DONE')

                values_ds2data = np.flipud(obj_data_anc_ds2data_step['air_temperature'][0, :, :])

                # info start resample datasets
                alg_logger.info(' -----> (5) Resample datasets ... ')
                # resample datasets
                obj_data_anc_resample_step = resample_data(
                    obj_data_anc_ds2data_step, obj_geo_x_anc, obj_geo_y_anc,
                    grid_geo_x_dst, grid_geo_y_dst,
                    geo_resample_idx=True, geo_mask_dst=grid_geo_values_dst,
                    **settings_resample_data)
                # info end resample datasets
                alg_logger.info(' -----> (5) Resample datasets ... DONE')

                values_resample = obj_data_anc_resample_step['air_temperature'][0, :, :]

                # info start mask datasets
                alg_logger.info(' -----> (6) Mask datasets ... ')
                # mask datasets
                obj_data_anc_mask_step = mask_data(obj_data_anc_resample_step, **settings_mask_data)
                # info end mask datasets
                alg_logger.info(' -----> (6) Mask datasets ... DONE')

                values_mask = obj_data_anc_mask_step['air_temperature'][0, :, :]

                # info start mask datasets
                alg_logger.info(' -----> (7) Create datasets ... ')
                obj_data_anc_step = transform_data_2_dset(
                    obj_data_anc_mask_step, obj_time_anc, grid_geo_x_dst, grid_geo_y_dst)
                # info start mask datasets
                alg_logger.info(' -----> (7) Create datasets ... DONE')

                values_out = obj_data_anc_step['air_temperature'].values[0, :, :]

                """
                import matplotlib
                matplotlib.use('TkAgg')
                plt.figure()
                plt.imshow(values_extract)
                plt.colorbar()
                plt.figure()
                plt.imshow(values_compose)
                plt.colorbar()
                plt.show()
                plt.figure()
                plt.imshow(values_ds2data)
                plt.colorbar(); plt.clim(0,20)
                plt.figure()
                plt.imshow(values_resample)
                plt.colorbar(); plt.clim(0,20)
                plt.figure()
                plt.imshow(values_mask)
                plt.colorbar(); plt.clim(0,20)
                plt.figure()
                plt.imshow(values_out)
                plt.colorbar(); plt.clim(0,20)
                plt.show()
                """

                # info start resample datasets
                alg_logger.info(' -----> (8) Save datasets ... ')

                # save data in pickle format
                folder_name_anc_def_step, file_name_anc_def_step = os.path.split(file_path_anc_def_step)
                make_folder(folder_name_anc_def_step)

                obj_anc_collection = {'data': obj_data_anc_step, 'attrs': obj_attrs_anc_step}
                write_file_obj(file_path_anc_def_step, obj_anc_collection)

                # info start resample datasets
                alg_logger.info(' -----> (8) Save datasets ... DONE')

                # info end time group
                alg_logger.info(' ----> Time reference "' + alg_time_reference.strftime(time_format_algorithm) +
                                '" ... DONE')

            else:
                # info end time group
                alg_logger.info(' ----> Time reference "' + alg_time_reference.strftime(time_format_algorithm) +
                                '" ... FAILED. Source datasets not available')

        else:
            # info end time group
            alg_logger.info(' ----> Time reference "' + alg_time_reference.strftime(time_format_algorithm) +
                            '" ... SKIPPED. Destination datasets previously computed')

        # info end method
        alg_logger.info(' ---> Analyze dynamic datasets ... DONE')

    # method to save data
    def dump_data(self):

        # info start method
        alg_logger.info(' ---> Dump dynamic datasets ... ')

        # get time reference
        alg_time_reference = self.alg_time_reference

        # get file path
        file_path_anc_def_tmpl, file_path_dst_tmpl = self.file_path_anc_def, self.file_path_dst
        # get grid info
        grid_geo_x_dst, grid_geo_y_dst = self.grid_geo_x_dst, self.grid_geo_y_dst
        transform_dst, proj_dst = self.transform_dst, self.proj_dst

        # info start time step
        alg_logger.info(' ----> Time reference "' + alg_time_reference.strftime(time_format_algorithm) + '" ... ')

        # method to define the ancillary and destination file path(s)
        file_path_anc_def_step = self.__define_file_string(file_path_anc_def_tmpl)
        file_path_dst_step = self.__define_file_string(file_path_dst_tmpl)

        # check file in according to compression flag
        if self.compression_dst:
            file_path_dst_check = add_zip_extension(file_path_dst_step)
        else:
            file_path_dst_check = file_path_dst_step

        # check file destination availability
        if not os.path.exists(file_path_dst_check):
            # check file source availability
            if os.path.exists(file_path_anc_def_step):

                # method to get data obj
                obj_collections_anc_def_step = read_file_obj(file_path_anc_def_step)

                # extract datasets
                (obj_data_anc_def_step, obj_attrs_anc_def_step,
                 obj_time_anc_def_step, obj_geo_x_anc_def_step, obj_geo_y_anc_def_step) = extract_data(
                    obj_collections_anc_def_step,
                    var_name_time='time', var_name_geo_x='west_east', var_name_geo_y='south_north')

                # check destination format
                if self.format_dst == 'netcdf_xarray':

                    # method to organize netcdf dataset (by xarray library)
                    variable_dset = organize_file_nc_xarray(
                        obj_variable=obj_data_anc_def_step, obj_time=obj_time_anc_def_step,
                        obj_geo_x=obj_geo_x_anc_def_step, obj_geo_y=obj_geo_y_anc_def_step,
                        obj_var_name=self.variables_dst)

                    # method to write netcdf dataset (by xarray library)
                    folder_name_dst_step, file_name_dst_step = os.path.split(file_path_dst_step)
                    make_folder(folder_name_dst_step)
                    write_file_nc_xarray(file_path_dst_step, variable_dset)

                elif self.format_dst == 'netcdf_base':

                    # method to organize netcdf dataset (by base library)
                    (obj_data_anc_def_step, obj_attrs_anc_def_step,
                     obj_attrs_anc_geo_system_step, obj_attrs_anc_geo_x_step, obj_attrs_anc_geo_y_step) = (
                        organize_file_nc_library(obj_data_anc_def_step, obj_attrs_anc_def_step,
                                                 dset_map=self.variables_dst))

                    # method to write netcdf dataset (by base library)
                    folder_name_dst_step, file_name_dst_step = os.path.split(file_path_dst_step)
                    make_folder(folder_name_dst_step)
                    write_file_nc_library(
                        file_path_dst_step,
                        dset_data=obj_data_anc_def_step, dset_attrs=obj_attrs_anc_def_step,
                        dset_time=obj_time_anc_def_step,
                        dset_geo_x=obj_geo_x_anc_def_step, dset_geo_y=obj_geo_y_anc_def_step,
                        geo_system_attrs=obj_attrs_anc_geo_system_step,
                        geo_x_attrs=obj_attrs_anc_geo_x_step, geo_y_attrs=obj_attrs_anc_geo_y_step)

                else:
                    alg_logger.error(' ===> Destination format "' + self.format_dst + '" is not supported')
                    raise NotImplemented('Case not implemented yet')

                # apply compression to destination file
                if self.compression_dst:
                    file_path_dst_zip = add_zip_extension(file_path_dst_step)
                    zip_filename(file_path_dst_step, file_path_dst_zip)

                    if os.path.exists(file_path_dst_zip):
                        os.remove(file_path_dst_step)

                # info end time group
                alg_logger.info(' ----> Time reference "' + alg_time_reference.strftime(time_format_algorithm) +
                                '" ... DONE')
            else:
                # info end time group
                alg_logger.info(' ----> Time reference "' + alg_time_reference.strftime(time_format_algorithm) +
                                '" ... FAILED. Source datasets not available')

        else:
            # info end time group
            alg_logger.info(' ----> Time reference "' + alg_time_reference.strftime(time_format_algorithm) +
                            '" ... SKIPPED. Destination datasets previously computed')

        # info end method
        alg_logger.info(' ---> Dump dynamic datasets ... DONE')

# -------------------------------------------------------------------------------------
