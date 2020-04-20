"""
Library Features:

Name:          drv_model_rfarm_apps
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190903'
Version:       '1.0.0'
"""
#################################################################################
# Library
import logging
import os

import numpy as np
import pandas as pd

from src.common.zip.lib_data_zip_gzip import openZip, zipFile, closeZip
from src.common.default.lib_default_conventions import oVarConventions as var_def_conventions
from src.common.utils.lib_utils_apps_file import handleFileData
from src.common.utils.lib_utils_op_dict import mergeDict

from src.hyde.algorithm.io.model.rfarm.lib_rfarm_io_generic import create_darray_3d, create_dset, write_dset
from src.hyde.algorithm.io.model.rfarm.lib_rfarm_io_grib import read_data_lami_2i
from src.hyde.algorithm.io.model.rfarm.lib_rfarm_io_grib import convert_data_lami_2i, convert_time_lami_2i
from src.hyde.algorithm.io.model.rfarm.lib_rfarm_io_netcdf import read_data_wrf
from src.hyde.algorithm.io.model.rfarm.lib_rfarm_io_netcdf import convert_data_wrf, convert_time_wrf
from src.hyde.algorithm.io.model.rfarm.lib_rfarm_io_generic import write_obj, read_obj
from src.hyde.algorithm.utils.rfarm.lib_rfarm_generic import fill_tags2string
from src.hyde.algorithm.settings.model.rfarm.lib_rfarm_args import logger_name

from src.hyde.model.rfarm.lib_rfarm_utils_generic import computeEnsemble

from src.common.utils.lib_utils_op_system import createTemp

# Logging
log_stream = logging.getLogger(logger_name)
#################################################################################


# -------------------------------------------------------------------------------------
# Class data object
class DataObj(dict):
    pass
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class to organize result(s)
class RFarmResult:

    def __init__(self, ensemble_group_in,
                 ensemble_n=None, ensemble_format='{:03d}',
                 ensemble_zip=False, ext_zip_type='.gz',
                 folder_out=None, filename_out='rfarm_{ensemble}.nc',
                 var_name='Rain', var_dims='var3d', var_attrs=None,
                 dim_x_name='X', dim_y_name='Y', write_engine='netcdf4'):

        if ensemble_n is None:
            ensemble_n = {'start': 1, 'end': 2}

        self.ensemble = computeEnsemble(ensemble_n['start'], ensemble_n['end'])

        if isinstance(ensemble_group_in, str):
            ensemble_group_in = [ensemble_group_in]

        self.ensemble_group_in = ensemble_group_in
        self.ensemble_n = ensemble_n
        self.ensemble_format = ensemble_format
        self.ensemble_zip = ensemble_zip

        self.var_name = var_name
        self.var_dims = var_dims
        self.var_attrs_dict = {var_name: var_attrs}

        self.folder_out = folder_out
        self.filename_out = filename_out
        self.ext_zip_type = ext_zip_type

        self.dim_x_name = dim_x_name
        self.dim_y_name = dim_y_name

        self.write_engine = write_engine

        if self.folder_out is None:
            self.folder_out = createTemp()

        if self.filename_out is None:
            raise TypeError

        self.ensemble_group_out = []
        self.zip_group_out = []
        for ensemble_id in self.ensemble:

            tags_tmpl = {'ensemble': ensemble_format}
            tags_values = {'ensemble':  ensemble_format.format(ensemble_id)}

            folder_out = fill_tags2string(self.folder_out, tags_tmpl, tags_values)
            filename_out = fill_tags2string(self.filename_out, tags_tmpl, tags_values)
            self.ensemble_group_out.append(os.path.join(folder_out, filename_out))

            if not os.path.exists(folder_out):
                os.makedirs(folder_out)

            filezip_out = filename_out + self.ext_zip_type
            self.zip_group_out.append(os.path.join(folder_out, filezip_out))

    def zip_result(self):

        # Zip result file according with zipping flag
        if self.ensemble_zip:
            for ensemble_name, filename_out, filezip_out in zip(self.ensemble, self.ensemble_group_out, self.zip_group_out):

                # Starting info
                log_stream.info(' ----> Zip ensemble ' + str(ensemble_name) + ' ... ')

                if os.path.exists(filezip_out):
                    os.remove(filezip_out)

                if os.path.exists(filename_out):
                    file_handle_in, file_handle_out = openZip(filename_out, filezip_out, 'z')

                    zipFile(file_handle_in, file_handle_out)
                    closeZip(file_handle_in, file_handle_out)

                    # Starting info
                    log_stream.info(' ----> Zip ensemble ' + str(ensemble_name) + ' ... DONE')

                else:
                    # Starting info
                    log_stream.warning(' ----> Zip ensemble ' + str(ensemble_name) +
                                       ' ... FAILED! File unzipped not found!')

                if os.path.exists(filezip_out) and os.path.exists(filename_out):
                    os.remove(filename_out)

    def organize_result(self, ensemble_obj, terrain, lons, lats, terrain_name='Terrain',
                        compression_level=0):

        # Check ensemble expected with ensemble(s) saved
        if isinstance(ensemble_obj, str):
            ensemble_obj = [ensemble_obj]

        for ensemble_found in ensemble_obj:
            if ensemble_found not in self.ensemble_group_in:
                log_stream.warning(' -----> File not found: ' + ensemble_found)

        # Terrain attributes
        terrain_attr_dict = {}
        for var_def_key, var_def_value in var_def_conventions.items():
            if terrain_name.lower() == var_def_key.lower():
                terrain_attr_dict[terrain_name] = var_def_value

        # Var attributes
        var_attrs_dict = self.var_attrs_dict

        # Iterate over ensemble(s)
        for filename_id, (ensemble_name, filename_in, filename_out) in enumerate(
                zip(self.ensemble, self.ensemble_group_in, self.ensemble_group_out)):

            # Starting info
            log_stream.info(' ----> Dump ensemble ' + str(ensemble_name) + ' ... ')

            # Check file availability
            if os.path.exists(filename_in):

                # Get data
                da_out = read_obj(filename_in)

                # Extract values and time
                values_out_raw = da_out.values
                time_out = pd.to_datetime(list(da_out.time.values))

                # Organized values to save in a correct 3D format
                values_out_def = np.zeros([values_out_raw.shape[0], values_out_raw.shape[1], values_out_raw.shape[2]])
                values_out_def[:, :, :] = np.nan
                for id in range(0, values_out_raw.shape[0]):
                    values_out_def[id, :, :] = np.flipud(values_out_raw[id, :, :])

                    # DEBUG
                    # import matplotlib.pylab as plt
                    # plt.figure(1)
                    # plt.imshow(values_out_raw[id, :, :])
                    # plt.colorbar()
                    # plt.clim(0, 100)
                    # plt.figure(2)
                    # plt.imshow(values_out_def[id, :, :])
                    # plt.colorbar()
                    # plt.clim(0, 100)
                    # plt.show()
                    # DEBUG

                # Create dset
                dset_out = create_dset(time_out, values_out_def,
                                       np.flipud(terrain), lons, np.flipud(lats),
                                       var_name=self.var_name,
                                       terrain_name=terrain_name,
                                       var_attrs=var_attrs_dict[self.var_name],
                                       terrain_attrs=terrain_attr_dict[terrain_name],
                                       dim_x_name=self.dim_x_name,
                                       dim_y_name=self.dim_y_name)
                # Write dset
                write_dset(filename_out, dset_out, attrs=mergeDict(var_attrs_dict, terrain_attr_dict),
                           compression=compression_level, engine=self.write_engine)

                # Ending info
                log_stream.info(' ----> Dump ensemble ' + str(ensemble_name) + ' ... DONE')

            else:
                # Ending info
                log_stream.warning(' ----> Dump ensemble ' + str(ensemble_name) + ' ... FAILED! Data not available!')

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class to read data
class RFarmData:

    def __init__(self, folder_data_first, filename_data_first,
                 folder_data_list=None, filename_data_list=None,
                 var_dims='var3d', var_type='istantaneous', var_name='Rain', var_units='mm',
                 file_format=None, file_source=None,
                 folder_tmp=None, filename_tmp='rfarm_data.nc'
                 ):

        self.folder_data_first = folder_data_first
        self.filename_data_first = filename_data_first

        self.var_dims_data = var_dims
        self.var_type_data = var_type
        self.var_name_data = var_name
        self.var_units_data = var_units

        self.file_format_data = file_format
        self.file_source_data = file_source

        self.folder_data_list = folder_data_list
        self.filename_data_list = filename_data_list

        if self.file_format_data is None:
            raise TypeError
        if self.file_source_data is None:
            raise TypeError

        self.file_data_first = os.path.join(self.folder_data_first, self.filename_data_first)

        if os.path.exists(self.file_data_first):
            self.found_data_first = True
        else:
            self.found_data_first = False

        self.file_data_list = []
        if self.var_dims_data == 'var2d':
            for folder_data_step, filename_data_step in zip(self.folder_data_list, self.filename_data_list):
                self.file_data_list.append(os.path.join(folder_data_step, filename_data_step))
        elif self.var_dims_data == 'var3d':
            self.file_data_list = None
        else:
            raise NotImplementedError

        self.folder_tmp = folder_tmp
        self.filename_tmp = filename_tmp

        if folder_tmp is None:
            self.folder_tmp = createTemp()

        if self.filename_tmp is None:
            raise TypeError

        if not os.path.exists(self.folder_tmp):
            os.makedirs(self.folder_tmp)

        self.file_tmp = os.path.join(self.folder_tmp, self.filename_tmp)

    def callback_data(self):

        var_obj = read_obj(self.file_tmp)
        return var_obj

    def organize_data(self, file_time_data=None):

        # Starting info
        log_stream.info(' ----> Get data ... ')

        # Check file data availability
        if self.found_data_first:

            [file_handle, file_drv, file_open] = handleFileData(self.file_data_first,
                                                                sFileType=self.file_format_data)
            if file_open:

                if self.file_format_data == 'grib':

                    if self.file_source_data == 'lami_2i':

                        if self.var_dims_data == 'var2d':
                            log_stream.error(' ----> Get data ... FAILED! FILE SOURCE DIMS NOT IMPLEMENTED!')
                            raise NotImplementedError
                        elif self.var_dims_data == 'var3d':

                            [var_data_raw, var_time_idx,
                             var_geox, var_geoy] = read_data_lami_2i(file_handle, file_drv, self.var_name_data)

                            var_time = convert_time_lami_2i(var_time_idx, file_time_data)
                            var_data = convert_data_lami_2i(var_data_raw, self.var_units_data, self.var_type_data)

                        else:
                            log_stream.error(' ----> Get data ... FAILED! FILE SOURCE DIMS NOT IMPLEMENTED!')
                            raise NotImplementedError
                    else:
                        log_stream.error(' ----> Get data ... FAILED! FILE SOURCE LIBRARY NOT IMPLEMENTED!')
                        raise NotImplementedError

                elif self.file_format_data == 'netcdf':

                    if self.file_source_data == 'wrf':

                        if self.var_dims_data == 'var2d':

                            if self.var_type_data == 'accumulated':
                                file_data_list = [self.file_data_first] + self.file_data_list
                            elif self.var_type_data == 'istantaneous':
                                file_data_list = self.file_data_list
                            else:
                                log_stream.error(' ----> Get data ... FAILED! FILE SOURCE TYPE NOT IMPLEMENTED!')
                                raise NotImplementedError

                            [var_data_raw, var_time_idx,
                             var_geox, var_geoy] = read_data_wrf(file_data_list)

                            var_time = convert_time_wrf(var_time_idx, file_time_data, self.var_type_data)
                            var_data = convert_data_wrf(var_data_raw, self.var_units_data, self.var_type_data)

                        elif self.var_dims_data == 'var3d':
                            log_stream.error(' ----> Get data ... FAILED! FILE SOURCE DIMS NOT IMPLEMENTED!')
                            raise NotImplementedError
                        else:
                            log_stream.error(' ----> Get data ... FAILED! FILE SOURCE DIMS NOT IMPLEMENTED!')
                            raise NotImplementedError

                    else:
                        log_stream.error(' ----> Get data ... FAILED! FILE SOURCE LIBRARY NOT IMPLEMENTED!')
                        raise NotImplementedError

                else:
                    log_stream.error(' ----> Get data ... FAILED! FILE TYPE LIBRARY NOT IMPLEMENTED!')
                    raise NotImplementedError

                # Create data array
                if var_data is not None:
                    var_da = create_darray_3d(var_data, var_time, var_geox, var_geoy)
                    # Dump tmp file
                    write_obj(self.file_tmp, var_da)

                    # DEBUG STARY
                    # file_test = self.file_tmp.split()[0] + '.nc'
                    # dset_test = var_da.to_dataset(name='Rain')
                    # dset_test.to_netcdf(path=file_test)
                    # DEBUG END

                    # Ending info
                    log_stream.info(' ----> Get data ... DONE')
                else:
                    # Ending info
                    var_da = None
                    log_stream.warning(' ----> Get data ... FAILED! DATA NOT AVAILABLE!')

            else:
                # Ending info
                var_da = None
                log_stream.warning(' ----> Get data ... FAILED! FILE NOT CORRECTLY OPENED!')

        else:
            # Ending info
            var_da = None
            log_stream.warning(' ----> Get data ... FAILED! FIRST FILE OF DATA NOT FOUND')

        return var_da

# -------------------------------------------------------------------------------------
