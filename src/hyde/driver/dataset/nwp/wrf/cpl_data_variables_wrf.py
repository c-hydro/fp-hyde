"""
Library Features:

Name:          cpl_data_variables_wrf
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20200302'
Version:       '1.0.0'
"""
#################################################################################
# Library
import logging
import inspect

import numpy as np

import src.hyde.dataset.nwp.wrf.lib_wrf_time as var_fx_time
import src.hyde.dataset.nwp.wrf.lib_wrf_variables as var_fx_archive

from src.hyde.algorithm.io.nwp.wrf.lib_wrf_io_generic import create_darray_2d, create_darray_3d
from src.hyde.algorithm.settings.nwp.wrf.lib_wrf_args import logger_name, time_units, time_format, time_calendar

# Logging
log_stream = logging.getLogger(logger_name)

# Debug
import matplotlib.pylab as plt
#################################################################################


# -------------------------------------------------------------------------------------
# Class data object
class DataObj(dict):
    pass
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class to compute data variable
class DataVariables:

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, info_key, var_dset, var_geo_x, var_geo_y,
                 domain_values, domain_geo_x, domain_geo_y,
                 var_fx=None, **kwargs):

        self.info_key = info_key

        self.var_dset_geo_x = var_geo_x
        self.var_dset_geo_y = var_geo_y

        self.domain_values = domain_values
        self.domain_geo_x = domain_geo_x
        self.domain_geo_y = domain_geo_y

        if 'file_tag_coord_time' in kwargs:
            file_tag_coord_time = kwargs['file_tag_coord_time']
        else:
            file_tag_coord_time = 'time'
        if 'file_tag_coord_geo_x' in kwargs:
            file_tag_coord_geo_x = kwargs['file_tag_coord_geo_x']
        else:
            file_tag_coord_geo_x = 'longitude'
        if 'file_tag_coord_geo_y' in kwargs:
            file_tag_coord_geo_y = kwargs['file_tag_coord_geo_y']
        else:
            file_tag_coord_geo_y = 'latitude'

        if 'file_tag_dim_time' in kwargs:
            file_tag_dim_time = kwargs['file_tag_dim_time']
        else:
            file_tag_dim_time = 'time'
        if 'file_tag_dim_geo_x' in kwargs:
            file_tag_dim_geo_x = kwargs['file_tag_dim_geo_x']
        else:
            file_tag_dim_geo_x = 'longitude'
        if 'file_tag_dim_geo_y' in kwargs:
            file_tag_dim_geo_y = kwargs['file_tag_dim_geo_y']
        else:
            file_tag_dim_geo_y = 'latitude'

        self.domain_da = create_darray_2d(domain_values, domain_geo_x, domain_geo_y,
                                          dim_key_x='longitude', dim_key_y='latitude',
                                          dim_name_x='longitude', dim_name_y='latitude',
                                          dims_order=['latitude', 'longitude'])

        if not isinstance(var_fx, list):
            var_fx = [var_fx]

        self.var_fx = var_fx
        self.tag_units = kwargs['file_tag_units']
        self.tag_step_type = kwargs['file_tag_step_type']
        #self.tag_time = kwargs['file_tag_time']

        var_units = 'NA'
        if 'var_units' in kwargs:
            var_units = kwargs['var_units']
        var_step_type = 'NA'
        if 'var_step_type' in kwargs:
            var_step_type = kwargs['var_step_type']

        var_name_tmp = var_dset.data_vars
        var_units_tmp = var_units
        var_step_type_tmp = var_step_type

        var_attrs_tmp = []
        for var_step in var_name_tmp:
            var_attrs_step = var_dset[var_step].attrs
            var_attrs_tmp.append(var_attrs_step)

        self.var_dset_data = var_dset
        self.var_dset_name = list(var_name_tmp)
        self.var_dset_attrs = var_attrs_tmp

        self.var_dset_units = var_units_tmp
        self.var_dset_step_type = var_step_type_tmp

        self.file_tag_coord_time = file_tag_coord_time
        self.file_tag_coord_geo_x = file_tag_coord_geo_x
        self.file_tag_coord_geo_y = file_tag_coord_geo_y

        self.file_tag_dim_time = file_tag_dim_time
        self.file_tag_dim_geo_x = file_tag_dim_geo_x
        self.file_tag_dim_geo_y = file_tag_dim_geo_y

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to select computing function
    @staticmethod
    def __findFx(var_fx):
        if hasattr(var_fx_archive, var_fx):
            obj_fx = getattr(var_fx_archive, var_fx)
        else:
            obj_fx = None
        return obj_fx
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to scale time
    @staticmethod
    def __time_scaling(time_range_in, time_range_out):

        time_size_in = time_range_in.shape[0]
        time_size_out = time_range_out.shape[0]

        if time_size_out > time_size_in:
            time_scale = int(time_size_out / time_size_in)
        elif time_size_out == time_size_in:
            time_scale = 1
        else:
            log_stream.error(' ==> Time scale definition not implemented!')
            raise NotImplementedError('Time scale definition not implemented yet!')

        return time_scale
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to scale variable according with step type definition
    @staticmethod
    def __var_scaling(var_da_raw, var_step_type, var_time_scaling, var_dim_scaling='time'):

        if (var_step_type == 'accum') or (var_step_type == 'accumulated'):
            var_da_filled = var_da_raw.bfill(dim=var_dim_scaling)
            var_da_scaled = var_da_filled / var_time_scaling
        elif (var_step_type == 'instant') or (var_step_type == 'instantaneous'):
            var_da_filled = var_da_raw.bfill(dim=var_dim_scaling)
            var_da_scaled = var_da_filled
        elif (var_step_type == 'avg') or (var_step_type == 'average'):
            var_da_filled = var_da_raw.bfill(dim=var_dim_scaling)
            var_da_scaled = var_da_filled
        else:
            log_stream.error(' ==> Var scale definition not implemented!')
            raise NotImplementedError('Var scale definition not implemented yet!')

        return var_da_scaled
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to configure fx
    def configure_fx(self):

        var_fx = self.var_fx

        var_dset_data = self.var_dset_data
        var_dset_time = var_dset_data[self.file_tag_dim_time]
        var_dset_name = self.var_dset_name
        var_dset_attrs = self.var_dset_attrs

        var_dset_units = self.var_dset_units
        var_dset_step_type = self.var_dset_step_type

        var_dset_time = var_fx_time.getVarTime(var_dset_time)
        var_dset_attrs = var_fx_archive.getVarAttributes(var_dset_attrs)

        geo_dset = self.domain_da

        fx_vars_link = {}
        fx_vars_def = []
        fx_vars_na = []
        for var_fx_step, var_name_step in zip(var_fx, var_dset_name):
            if var_fx_step is not None:
                fx_vars_def.append(var_name_step)
                if var_fx_step not in list(fx_vars_link.keys()):
                    fx_vars_link[var_fx_step] = [var_name_step]
                else:
                    var_name_tmp = fx_vars_link[var_fx_step]
                    var_name_tmp.extend([var_name_step])
                    fx_vars_link[var_fx_step] = var_name_tmp
            else:
                fx_vars_na.append(var_name_step)

        fx_vars = fx_vars_def + fx_vars_na

        obj_fx_frame = None
        for name_fx in fx_vars_link.keys():
            # Starting info
            log_stream.info(' ----> Apply computing function(s) to ' + str(fx_vars) +
                            ' variable(s) ... ')

            # Check function definition
            if name_fx is not None:
                obj_fx_handle = self.__findFx(name_fx)
                obj_fx_signature = inspect.signature(obj_fx_handle)
                obj_fx_parameters = obj_fx_signature.parameters.values()

                obj_fx_dictionary = dict(var_dset=var_dset_data, var_name=fx_vars, var_units=var_dset_units,
                                         var_step_type=var_dset_step_type, geo_dset=geo_dset,
                                         var_time=[self.file_tag_coord_time],
                                         var_geo_x=[self.file_tag_coord_geo_x],
                                         var_geo_y=[self.file_tag_coord_geo_y])

                obj_fx_args = {}
                for obj_fx_id, obj_fx_name in enumerate(obj_fx_parameters):
                    var_name_param = obj_fx_name.name

                    if var_name_param in list(obj_fx_dictionary.keys()):
                        obj_fx_args[var_name_param] = obj_fx_dictionary[var_name_param]

                # Call function with mutable argument(s)
                obj_fx_result = obj_fx_handle(**obj_fx_args)

                # Save result in a common workspace
                if obj_fx_frame is None:
                    obj_fx_frame = obj_fx_result
                else:
                    obj_fx_frame = obj_fx_frame.combine_first(obj_fx_result)

                # Ending info for defined function
                log_stream.info(' ----> Apply computing function(s) to ' + str(fx_vars) +
                                ' variable(s) ... DONE')

            else:
                # Ending info for undefined function
                log_stream.info(' ----> Apply computing function(s) to ' + str(fx_vars) +
                                ' variable(s) ... SKIPPED.')

        return obj_fx_frame, var_dset_time, var_dset_attrs

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to configure data
    def configure_data(self, var_dset_raw, var_time_period_raw, var_time_period_expected):

        # Get variable(s) name
        var_name_raw = self.var_dset_name
        var_step_type_raw = self.var_dset_step_type

        # Iterate over dataset(s)
        var_dset_out = None
        for var_name_step, var_step_type_step, var_dset_step in zip(var_name_raw, var_step_type_raw, var_dset_raw):

            # Get data array
            var_da_step = var_dset_raw[var_name_step]

            # Get variable, data, time and attributes of expected data
            var_data_expected = np.zeros([var_da_step.shape[0], var_da_step.shape[1], var_time_period_expected.shape[0]])
            var_data_expected[:, :, :] = np.nan
            var_da_expected = create_darray_3d(var_data_expected, var_time_period_expected,
                                               self.var_dset_geo_x, self.var_dset_geo_y,
                                               dim_key_time='time', dim_key_x='longitude', dim_key_y='latitude',
                                               dim_name_x='longitude', dim_name_y='latitude', dim_name_time='time',
                                               dims_order=['latitude', 'longitude', 'time'])

            # Scale time
            var_time_scale = self.__time_scaling(var_time_period_raw, var_time_period_expected)

            # Combine raw and expected data arrays
            var_da_unfilled = var_da_expected.combine_first(var_da_step)

            # Scale variable according with type and time scales
            var_da_scaled = self.__var_scaling(var_da_unfilled, var_step_type_step, var_time_scale)
            # Perform interpolation and masking of datasets
            var_da_interp = var_da_scaled.interp(latitude=self.domain_geo_y[:, 0], longitude=self.domain_geo_x[0, :],
                                                 method='nearest')
            var_da_masked = var_da_interp.where(self.domain_da != -9999)

            var_dset_masked = var_da_masked.to_dataset(name=var_name_step)

            if var_dset_out is None:
                var_dset_out = var_dset_masked
            else:
                var_dset_out = var_dset_out.combine_first(var_dset_masked)

        return var_dset_out

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class to compute model variable
class ModelVariables(DataVariables):

    # Method to initialize class
    def __init__(self, info_key, var_data, var_geo_x, var_geo_y,
                 domain_values, domain_geo_x, domain_geo_y,
                 var_fx=None, **kwargs):

        kwargs['file_tag_time'] = 'time'

        if 'var_name' not in kwargs:
            kwargs['var_name'] = 'NA'
        if 'var_units' not in kwargs:
            kwargs['var_units'] = 'NA'
        if 'var_step_type' not in kwargs:
            kwargs['var_step_type'] = 'NA'

        super().__init__(info_key, var_data, var_geo_x, var_geo_y,
                         domain_values, domain_geo_x, domain_geo_y,
                         var_fx=var_fx, **kwargs)

# -------------------------------------------------------------------------------------
