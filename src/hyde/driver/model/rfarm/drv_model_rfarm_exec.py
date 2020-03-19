"""
Library Features:

Name:          drv_model_rfarm_exec
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

from src.common.utils.lib_utils_op_system import createTemp

from src.hyde.algorithm.settings.model.rfarm.lib_rfarm_args import logger_name, time_format
from src.hyde.algorithm.utils.rfarm.lib_rfarm_generic import fill_tags2string

from src.hyde.model.rfarm.lib_rfarm_utils_generic import extendGrid, computeGrid, \
    computeEnsemble, computeTimeSteps, computeVar, checkResult, saveResult

import src.hyde.model.rfarm.lib_rfarm_core as lib_core

# Logging
log_stream = logging.getLogger(logger_name)
#################################################################################


# -------------------------------------------------------------------------------------
# Dictionary of model default parameter(s)
model_parameters_default = {
    'ensemble': {'start': 1, 'end': 2},         # ensemble n (min values EnsMin=1, EnsMax=1)
    'ratio_s': 4,          	                    # spatial disaggregated ratio (min value == 1)
    'ratio_t': 6,                               # time disaggregated ratio (min value == 1)
    'slope_s': None,                            # fft spatial slope (undefined == None)
    'slope_t': None,                            # fft temporal slope (undefined == None)
    'cs_sf': 4,                                 # reliable spatial scale (spatial/Csst)
    'ct_sf': 2,                                 # reliable time scale (time model aggregated Ctsf times)
    'multi_core': False,                        # multi core process (False or True)
    'domain_extension': 0,      	            # domain extended buffer (min value = 0) [km]
    'folder_tmp': None,                          # tmp folder to store data
    'filename_tmp': 'rf_{ensemble}.pkl'         # tmp filename to store data
}
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class to configure and run Rainfarm model
class RFarmModel:

    # -------------------------------------------------------------------------------------
    # Initialize class variable(s)
    time_steps_in = None
    time_steps_rel = None
    time_steps_rf = None
    time_steps_ref = None

    time_delta_in = None
    time_delta_ref = None

    lons_ref = None
    lats_ref = None

    lons_rf = None
    lats_rf = None
    index_rf = None

    ll_lon_rf = None
    ll_lat_rf = None
    i_min_rf = None
    i_max_rf = None
    j_min_rf = None
    j_max_rf = None

    data_rf = None

    nt = None
    ndelta = None

    ns = None
    nsl = None
    nr = None
    nas = None
    ntl = None
    nat = None

    ensemble_status = None
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self,
                 ensemble_n=model_parameters_default['ensemble'],
                 ensemble_format='{:03d}',
                 ratio_s=model_parameters_default['ratio_s'],
                 ratio_t=model_parameters_default['ratio_t'],
                 slope_s=model_parameters_default['slope_s'],
                 slope_t=model_parameters_default['slope_t'],
                 cs_sf=model_parameters_default['cs_sf'],
                 ct_sf=model_parameters_default['ct_sf'],
                 multi_core=model_parameters_default['multi_core'],
                 domain_extension=model_parameters_default['domain_extension'],
                 folder_tmp=model_parameters_default['folder_tmp'],
                 filename_tmp=model_parameters_default['filename_tmp'],
                 model_algorithm="execRF_NWP",
                 model_var="Rain",
                 model_metagauss=None,
                 ):

        self.ratio_s = ratio_s
        self.ratio_t = ratio_t
        self.slope_s = slope_s
        self.slope_t = slope_t
        self.cs_sf = cs_sf
        self.ct_sf = ct_sf
        self.multi_core = multi_core
        self.domain_extension = domain_extension

        if folder_tmp is None:
            self.folder_tmp = createTemp(model_parameters_default['folder_tmp'])
        else:
            self.folder_tmp = folder_tmp
        if filename_tmp is None:
            self.filename_tmp = model_parameters_default['filename_tmp']
        else:
            self.filename_tmp = filename_tmp

        self.model_algorithm = model_algorithm
        self.model_var = model_var
        self.model_metagauss = model_metagauss

        self.ensemble = computeEnsemble(ensemble_n['start'], ensemble_n['end'])

        self.ensemble_filename = []
        for ensemble_id in self.ensemble:

            tags_tmpl = {'ensemble': ensemble_format}
            tags_values = {'ensemble':  ensemble_format.format(ensemble_id)}
            folder_tmp = fill_tags2string(self.folder_tmp, tags_tmpl, tags_values)
            filename_tmp = fill_tags2string(self.filename_tmp, tags_tmpl, tags_values)
            self.ensemble_filename.append(os.path.join(folder_tmp, filename_tmp))

            if not os.path.exists(folder_tmp):
                os.makedirs(folder_tmp)

        if hasattr(lib_core, self.model_algorithm):
            self.lib_algorithm = getattr(lib_core, self.model_algorithm)
        else:
            log_stream.error(' ----> ERROR in defining rainfarm algorithm - Check your settings!')
            raise ModuleNotFoundError

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to configure model grid(s)
    def configure_grid(self, lons_in, lats_in, lons_ref, lats_ref, res_lon_ref, res_lat_ref, domain_extension=0):

        # Call method to compute model grid
        self.lons_ref, self.lats_ref = extendGrid(lons_in, lats_in, lons_ref, lats_ref, res_lon_ref, res_lat_ref,
                                                  domain_extension)

        # Call algorithm to compute rainfarm model grid
        [self.lons_rf, self.lats_rf, self.index_rf,
         self.ll_lon_rf, self.ll_lat_rf,
         self.i_min_rf, self.i_max_rf, self.j_min_rf, self.j_max_rf,
         ratio_s_upd, res_geo_rf,
         res_pixels_rf] = computeGrid(lons_in, lats_in, self.lons_ref, self.lats_ref,
                                      res_lon_ref, res_lat_ref,
                                      self.ratio_s)
        # Define RF variable(s)
        self.ns = res_geo_rf
        self.nsl = res_pixels_rf
        self.nr = 1
        self.nas = res_pixels_rf

        self.ratio_s = ratio_s_upd

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to configure model time(s)
    def configure_time(self, time_in):

        # Configure time in
        time_start_in = pd.to_datetime(str(time_in[0]))
        time_end_in = pd.to_datetime(str(time_in[-1]))
        time_delta_in = ((time_end_in - time_start_in) / (time_in.__len__() - 1)).seconds

        # Compute time steps for input time length
        self.time_steps_in = computeTimeSteps(time_start_in.strftime(time_format),
                                              time_end_in.strftime(time_format),
                                              time_delta_in,
                                              time_delta_in,
                                              time_format)

        # Compute time steps for reliable time length
        self.time_steps_rel = computeTimeSteps(time_start_in.strftime(time_format),
                                               time_end_in.strftime(time_format),
                                               time_delta_in,
                                               time_delta_in * self.ct_sf,
                                               time_format)

        # Compute time steps for rainfarm disaggregation
        self.time_steps_rf = computeTimeSteps(time_start_in.strftime(time_format),
                                              time_end_in.strftime(time_format),
                                              time_delta_in,
                                              time_delta_in / self.ratio_t,
                                              time_format)
        # Compute time steps for output data
        self.time_steps_ref = computeTimeSteps(time_start_in.strftime(time_format),
                                               time_end_in.strftime(time_format),
                                               time_delta_in,
                                               time_delta_in * self.ct_sf / (self.ratio_t * self.ct_sf),
                                               time_format)

        time_start_ref = pd.to_datetime(self.time_steps_ref[0])
        time_end_ref = pd.to_datetime(self.time_steps_ref[-1])
        time_delta_ref = ((time_end_ref - time_start_ref) / (self.time_steps_ref.__len__() - 1)).seconds

        # Define RF variable(s)
        self.nt = self.time_steps_ref.__len__()
        self.ndelta = time_delta_in * self.ct_sf

        self.time_delta_in = time_delta_in
        self.time_delta_ref = time_delta_ref

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to configure model data
    def configure_data(self, values_in):

        # Time Ratio to convert accumulated rain to istantaneous rain
        time_ratio_rf = int(self.time_delta_in/self.time_delta_ref)

        # Call method to compute rainfarm model data
        self.data_rf = computeVar(values_in, time_ratio_rf,
                                  self.i_min_rf, self.i_max_rf, self.j_min_rf, self.j_max_rf)

        # DEBUG
        # import matplotlib.pylab as plt
        # plt.figure(1)
        # plt.imshow(values_in[:, :, 2])
        # plt.colorbar()
        # plt.clim(0, 20)
        # plt.figure(2)
        # plt.imshow(self.data_rf[:, :, 2])
        # plt.colorbar()
        # plt.clim(0, 20)
        # plt.show()
        # DEBUG

        # Define RF variable(s)
        self.ntl = self.data_rf.shape[2]
        self.nat = self.data_rf.shape[2]

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to recover run status
    def callback_run(self):
        ensemble_status = []
        for ensemble_id, (ensemble_filename, ensemble_n) in enumerate(zip(self.ensemble_filename, self.ensemble)):
            # Starting info
            log_stream.error(' ----> Callback ensemble ' + str(ensemble_n) + ' ... ')
            if os.path.exists(ensemble_filename):
                ensemble_status.append(ensemble_filename)
                # Ending info
                log_stream.error(' ----> Callback ensemble ' + str(ensemble_n) + ' ... DONE')
            else:
                # Ending info
                log_stream.error(' ----> Callback ensemble ' + str(ensemble_n) + ' ... FAILED! FILE NOT FOUND')
        return ensemble_status
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to execute model
    def execute_run(self):

        # Choose computing mode
        if self.multi_core:
            raise NotImplemented
            # Define process(es) for RF model using multi core mode
            # ensemble_status = self.workerMultiCore()
        else:
            # Define process(es) for RF model using single core mode
            ensemble_status = self.workerSingleCore()

        # Save data in global workspace
        return ensemble_status

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to run model in single core
    def workerSingleCore(self):

        # Get field name
        ensemble_var = self.model_var

        # Iterate over ensemble(s)
        ensemble_status = []
        for ensemble_id, (ensemble_filename, ensemble_n) in enumerate(zip(self.ensemble_filename, self.ensemble)):

            # Starting info
            log_stream.info(' ----> Set ensemble ' + str(ensemble_n) + ' ... ')

            # Run RF model
            if np.any(self.data_rf):

                # Disaggregation (if some value(s) are not null)
                [ensemble_rf, metagauss_rf] = self.lib_algorithm(
                    self.data_rf,
                    self.ratio_s, self.ratio_t,
                    cssf=self.cs_sf, ctsf=self.ct_sf,
                    f=self.model_metagauss,
                    celle3_rainfarm=None,
                    sx=self.slope_s, st=self.slope_t)

                # Check disaggregated result(s)
                checkResult(self.data_rf, ensemble_rf, self.ratio_s, self.ratio_t)

                # DEBUG
                # import matplotlib.pylab as plt
                # plt.figure(1)
                # plt.imshow(self.data_rf[:, :, 1])
                # plt.colorbar()
                # plt.clim(0, 100)

                # plt.figure(2)
                # plt.imshow(ensemble_rf[:, :, 1])
                # plt.colorbar()
                # plt.clim(0, 100)
                # plt.show()

            else:

                # Exit with null field(s) if all values are zeros
                ensemble_rf = np.zeros([self.data_rf.shape[0]*self.ratio_s,
                                        self.data_rf.shape[1]*self.ratio_s,
                                        self.data_rf.shape[2]*int(int(self.nt)/int(self.nat))])

            # Ensemble history
            ensemble_status.append(ensemble_filename)

            # Dump ensemble to free memory
            saveResult(ensemble_filename, ensemble_var, ensemble_rf,
                       self.lons_rf, self.lats_rf, self.time_steps_rf,
                       self.lons_ref, self.lats_ref, self.time_steps_ref,
                       geoindex_in=self.index_rf)

            # Ending info
            log_stream.info(' ----> Set ensemble ' + str(ensemble_n) + ' ... DONE')

        # Return status of ensemble(s)
        return ensemble_status
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to run model in single core
    def workerMultiCore(self):

        # Iterate over ensemble(s)
        ensemble_status = []
        for ensemble_id, ensemble_filename in enumerate(self.ensemble_filename):
            ensemble_status.append(ensemble_filename)
        return ensemble_status
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
