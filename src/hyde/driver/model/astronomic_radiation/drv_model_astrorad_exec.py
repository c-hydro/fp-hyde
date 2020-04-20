"""
Library Features:

Name:          drv_model_astrorad_exec
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20200215'
Version:       '1.5.0'
"""
#################################################################################
# Library
import logging
import os
import pandas as pd
import numpy as np

from src.common.utils.lib_utils_op_system import createTemp

from src.hyde.algorithm.settings.model.astronomic_radiation.lib_astrorad_args import logger_name, \
    lookup_table_cf_default, var_list_default

from src.hyde.model.astronomic_radiation.lib_astrorad_apps import computeParameters
from src.hyde.model.astronomic_radiation.lib_astrorad_utils import computeCloudFactor

import src.hyde.model.astronomic_radiation.lib_astrorad_core as lib_core

# Logging
log_stream = logging.getLogger(logger_name)
#################################################################################


# -------------------------------------------------------------------------------------
# Class data object
class DataObj(dict):
    pass
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class to configure and run Astronomic Radiation model
class AstroRadModel:

    # -------------------------------------------------------------------------------------
    geo_lz = None
    geo_lm = None
    geo_phi = None
    param_gsc = None
    param_as = None
    param_bs = None

    var_data_cf = None
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, var_data, var_time, geo_z, geo_x, geo_y,
                 var_name='cloud_factor',
                 model_algorithm='execAstroRad_FAO',
                 folder_name_tmp=None, file_name_tmp='astrorad_tmp.workspace'):

        self.var_data = var_data
        self.var_time = var_time

        if var_name not in var_list_default:
            log_stream.error(' ===> Datasets name not allowed. Check your settings!')
            raise IOError('Datasets name not included in the allowed items')

        self.var_name = var_name

        self.geo_z = geo_z
        self.geo_x = geo_x
        self.geo_y = geo_y

        self.model_algorithm = model_algorithm

        if folder_name_tmp is None:
            self.folder_name_tmp = createTemp()
        else:
            self.folder_name_tmp = folder_name_tmp
        if file_name_tmp is None:
            log_stream.error( ' ===> Temporary file name is defined by None')
            raise IOError('Temporary file name is defined by None')
        else:
            self.file_name_tmp = file_name_tmp

        if hasattr(lib_core, self.model_algorithm):
            self.lib_algorithm = getattr(lib_core, self.model_algorithm)
        else:
            log_stream.error(' ===> AstroRad application not found! Check your settings!')
            raise ModuleNotFoundError('AstroRad application not found in library')

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to configure model datasets
    def configure_model_datasets(self, lookup_table_cf=None):

        if lookup_table_cf is None:
            lookup_table_cf = lookup_table_cf_default

        if self.var_name == 'rain':
            var_data_cf = computeCloudFactor(self.var_data, lookup_table_cf)
        elif self.var_name == 'cloud_factor':
            var_data_cf = self.var_data
        else:
            log_stream.error(' ===> Datasets name not allowed. Check your settings!')
            raise IOError('Datasets name not included in the allowed items')

        return var_data_cf

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to configure model parameters
    def configure_model_parameters(self):

        # Method from apps library to set model parameters
        [geo_lz, geo_lm, geo_phi, param_gsc, param_as, param_bs] = computeParameters(self.geo_x, self.geo_y)

        model_params = DataObj()
        model_params.geo_lz = geo_lz
        model_params.geo_lm = geo_lm
        model_params.geo_phi = geo_phi
        model_params.param_gsc = param_gsc
        model_params.param_as = param_as
        model_params.param_bs = param_bs

        return model_params

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to configure model time(s)
    def configure_model_time(self):

        var_time = self.var_time

        time_steps = var_time.size
        time_from = pd.Timestamp(var_time[0].values)
        time_to = pd.Timestamp(var_time[-1].values)

        time_delta = (time_to - time_from) / (time_steps - 1)
        time_delta = time_delta.seconds
        time_delta = pd.Timedelta(time_delta, unit='s')

        time_period = pd.to_datetime(var_time.values)

        model_time = DataObj()
        model_time.time_period = time_period
        model_time.time_delta = time_delta

        return model_time

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to recover run status
    def callback_run(self):
        pass
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to execute model
    def execute_run(self, model_dset, model_time, model_params):

        # Get data information
        var_data_cf = model_dset
        # Get geographical information
        geo_z = self.geo_z

        # Get time information
        time_delta = model_time.time_delta
        time_period = model_time.time_period
        # Get parameters information
        geo_lz = model_params.geo_lz
        geo_lm = model_params.geo_lm
        geo_phi = model_params.geo_phi
        param_gsc = model_params.param_gsc
        param_bs = model_params.param_bs
        param_as = model_params.param_as

        # Define process(es) for AstroRad model
        model_results_ar, model_results_k = self.lib_algorithm(
            var_data_cf, geo_z, time_period, time_delta,
            geo_lz, geo_lm, geo_phi,
            param_gsc, param_as, param_bs)

        # Save data in global workspace
        return model_results_ar, model_results_k

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
