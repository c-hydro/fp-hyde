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

from copy import deepcopy

from src.common.utils.lib_utils_op_system import createTemp

from src.hyde.algorithm.settings.model.rfarm.lib_rfarm_args import logger_name, time_format
from src.hyde.algorithm.utils.rfarm.lib_rfarm_generic import fill_tags2string

from src.hyde.model.rfarm.lib_rfarm_utils_generic import extendGrid, computeGrid, \
    computeEnsemble, computeTimeSteps, computeVar, checkResult, saveResult

import src.hyde.model.rfarm.lib_rfarm_core as lib_core

# Debug
import matplotlib.pylab as plt
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
    'folder_tmp': None,                         # tmp folder to store data
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
    lon_min_rf = None
    lon_max_rf = None
    lat_min_rf = None
    lat_max_rf = None

    data_rf = None
    data_slopes = None

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
                 model_algorithm="exec_nwp",
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
         self.lon_min_rf, self.lon_max_rf, self.lat_min_rf, self.lat_max_rf,
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
        if self.model_algorithm == 'exec_nwp':
            self.time_steps_rf = computeTimeSteps(time_start_in.strftime(time_format),
                                                  time_end_in.strftime(time_format),
                                                  time_delta_in,
                                                  time_delta_in / self.ratio_t,
                                                  time_format)

        elif self.model_algorithm == 'exec_expert_forecast':
            time_ratio = self.ct_sf / self.ratio_t
            self.time_steps_rf = computeTimeSteps(time_start_in.strftime(time_format),
                                                  time_end_in.strftime(time_format),
                                                  time_delta_in,
                                                  time_delta_in * time_ratio,
                                                  time_format)

        # Compute time steps for output data
        if self.model_algorithm == 'exec_nwp':
            self.time_steps_ref = computeTimeSteps(time_start_in.strftime(time_format),
                                                   time_end_in.strftime(time_format),
                                                   time_delta_in,
                                                   time_delta_in * self.ct_sf / (self.ratio_t * self.ct_sf),
                                                   time_format)
        elif self.model_algorithm == 'exec_expert_forecast':
            time_ratio = self.ct_sf / self.ratio_t
            self.time_steps_ref = computeTimeSteps(time_start_in.strftime(time_format),
                                                   time_end_in.strftime(time_format),
                                                   time_delta_in,
                                                   time_delta_in * time_ratio,
                                                   time_format)

        time_start_ref = pd.to_datetime(self.time_steps_ref[0])
        time_end_ref = pd.to_datetime(self.time_steps_ref[-1])
        time_delta_ref = ((time_end_ref - time_start_ref) / (self.time_steps_ref.__len__() - 1)).seconds

        if self.ct_sf > self.ratio_t:
            log_stream.error(' ===> The parameter "ct_sf" [' + str(self.ct_sf)
                             + '] is greater than "ratio_t" [' + str(self.ratio_t))
            log_stream.error(' ===> The effect is a shift in the disaggregated values. To be investigate and correct.')
            raise RuntimeError('Case not properly managed to under sample the dataset ')

        # Define RF variable(s)
        self.nt = self.time_steps_ref.__len__()
        self.ndelta = time_delta_in * self.ct_sf

        self.time_delta_in = time_delta_in
        self.time_delta_ref = time_delta_ref

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to configure model data
    def configure_data(self, values_in):

        # Time Ratio to convert accumulated rain to instantaneous rain
        time_ratio_rf = int(self.time_delta_in/self.time_delta_ref)

        # Call method to compute input datasets
        if self.model_algorithm == 'exec_nwp':
            self.data_rf = computeVar(values_in, time_ratio_rf,
                                      self.i_min_rf, self.i_max_rf, self.j_min_rf, self.j_max_rf)
            self.data_slopes = None
        elif self.model_algorithm == 'exec_expert_forecast':

            dim_geo_x = self.lons_ref.shape[0]
            dim_geo_y = self.lats_ref.shape[1]
            dim_time = self.time_steps_in.__len__()

            self.data_rf = np.zeros(shape=[dim_geo_x, dim_geo_y, dim_time])
            self.data_slopes = values_in

        # DEBUG
        # DEBUG START (DUMP DATA IN TIFF NETCDF FORMAT)
        # lon_rf_1d = np.linspace(self.lon_min_rf, self.lon_max_rf, self.nsl, endpoint=True)
        # lat_rf_1d = np.linspace(self.lat_min_rf, self.lat_max_rf, self.nsl, endpoint=True)
        # lon_rf_2d, lat_rf_2d = np.meshgrid(lon_rf_1d, lat_rf_1d)
        # lat_rf_2d = np.flipud(lat_rf_2d)
        # from src.hyde.model.rfarm.lib_rfarm_utils_generic import writeGeoTiff
        # file_name = '/home/fabio/test/rfarm/lami_2i_model_cut.tiff'
        # writeGeoTiff(file_name, self.data_rf[:, :, 1], lon_rf_2d, lat_rf_2d)

        # import matplotlib.pylab as plt
        # plt.figure(1)
        # plt.imshow(values_in[:, :, 0])
        # plt.colorbar()
        # plt.clim(0, 10)
        # plt.figure(2)
        # plt.imshow(self.data_rf[:, :, 0])
        # plt.colorbar()
        # plt.clim(0, 10)
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
    def execute_run(self, domain_name='domain', domain_id=1, domain_mask=None):

        # Choose computing mode
        if self.multi_core:
            raise NotImplemented('Ensembles method in multiprocessing mode not implemented yet')
            # Define process(es) for RF model using multi core mode
            # ensemble_status = self.worker_multi_core()
        else:
            # Define process(es) for RF model using single core mode
            ensemble_status = self.worker_single_core(domain_name, domain_id, domain_mask)

        # Save data in global workspace
        return ensemble_status

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to run model in single core
    def worker_single_core(self, domain_name, domain_id, domain_mask):

        # Get field name
        ensemble_var = self.model_var

        # Iterate over ensemble(s)
        ensemble_status = []
        for ensemble_id, (ensemble_filename, ensemble_n) in enumerate(zip(self.ensemble_filename, self.ensemble)):

            # Starting info
            log_stream.info(' ----> Set ensemble ' + str(ensemble_n) + ' ... ')

            if self.model_algorithm == 'exec_nwp':

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
                    # plt.clim(0, 10)

                    # plt.figure(2)
                    # plt.imshow(ensemble_rf[:, :, 1])
                    # plt.colorbar()
                    # plt.clim(0, 10)
                    # plt.show()

                else:

                    # Exit with null field(s) if all values are zeros
                    ensemble_rf = np.zeros([self.data_rf.shape[0]*self.ratio_s,
                                            self.data_rf.shape[1]*self.ratio_s,
                                            self.data_rf.shape[2]*int(int(self.nt)/int(self.nat))])

            elif self.model_algorithm == 'exec_expert_forecast':

                # Define time idx max
                time_idx_max = int(self.nat / self.ratio_t)

                # Iterate over time idx
                ensemble_rf_t = np.zeros([self.ns * self.ns, self.nat])
                for time_idx_step in range(0, time_idx_max):

                    time_idx_start = time_idx_step * self.ratio_t
                    time_idx_end = time_idx_step * self.ratio_t + self.ratio_t

                    # Iterate over subdomains
                    for area_tag, area_id, (slope_tag, slope_fields) in zip(domain_name, domain_id, self.data_slopes.items()):

                        # Starting info area
                        log_stream.info(' -----> Evaluate -- Area ' + area_tag + ' -- IdxMin: ' + str(time_idx_start) +
                                        ' -- IdxMax: ' + str(time_idx_end) + ' ... ')

                        assert(area_tag == slope_tag)

                        # Get alert area index
                        subdomain_mask = deepcopy(domain_mask)
                        subdomain_idx = np.argwhere(subdomain_mask.ravel() == area_id)

                        rain_avg = slope_fields['rain_average'][time_idx_step]
                        slope_s = slope_fields['slope_x'][time_idx_step]
                        slope_t = slope_fields['slope_t'][time_idx_step]

                        nat = int(self.nat / self.ratio_t)
                        ratio_t = int(self.ratio_t/nat)
                        ct_sf = self.ratio_t / self.ct_sf

                        # RainFarm disaggregation
                        """
                        Parameters example:
                        rain average: 0.0; slope s: 3.5; slope t: 0.5; ratio s: 1; ratio t/ nat: 3; 
                        cs_sf: 1; ct_sf: 1; nat: 4; ns: 644; ns: 644
                        """
                        [ensemble_rf_xyt, metagauss_rf] = self.lib_algorithm(
                            None,
                            self.ratio_s, ratio_t,
                            cssf=self.cs_sf, ctsf=ct_sf,
                            f=self.model_metagauss,
                            celle3_rainfarm=None,
                            sx=slope_s, st=slope_t,
                            nx=self.ns, ny=self.ns, nt=nat)

                        # Post-process result(s)
                        ensemble_rf_step = np.reshape(ensemble_rf_xyt, [self.ns * self.ns, self.ratio_t])

                        # Compute mean and weight(s)
                        ensemble_rf_avg = np.nanmean(ensemble_rf_step[subdomain_idx, :])
                        if ensemble_rf_avg > 0.0:
                            ensemble_rf_weights = rain_avg / self.ratio_t / ensemble_rf_avg
                        else:
                            ensemble_rf_weights = 0.0

                        # Normalized result(s) using weight(s)
                        ensemble_rf_t[subdomain_idx, time_idx_start:time_idx_end] = ensemble_rf_step[subdomain_idx, :] * ensemble_rf_weights

                        # Ending info area
                        log_stream.info(' -----> Evaluate -- Area ' + area_tag + ' -- IdxMin: ' + str(time_idx_start) +
                                        ' -- IdxMax: ' + str(time_idx_end) + ' ... DONE')

                # Reshape results in XYT format
                ensemble_rf = np.reshape(ensemble_rf_t, [self.ns, self.ns, self.nat])

                # Debug
                # plt.figure(1)
                # plt.imshow(ensemble_rf[:, :, 23])
                # plt.colorbar()
                # plt.show()

            else:
                log_stream.error(' ===> RainFarm application type is not correctly defined [' +
                                 self.model_algorithm + ']. Check your settings')
                raise NotImplemented('RainFarm application type not implemented yet')

            # Ensemble history
            ensemble_status.append(ensemble_filename)

            # Ensemble info
            ensemble_rf_avg = np.nanmean(ensemble_rf)
            ensemble_rf_min = np.nanmin(ensemble_rf)
            ensemble_rf_max = np.nanmax(ensemble_rf)
            log_stream.info(' -----> Evaluate'
                            ' -- Values Avg: ' + "{:.4f}".format(ensemble_rf_avg) +
                            ' -- Values Min: ' + "{:.4f}".format(ensemble_rf_min) +
                            ' -- Values Max: ' + "{:.4f}".format(ensemble_rf_max)
                            )

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
    # Method to run model in multi cores mode
    def worker_multicore(self):

        # Iterate over ensemble(s)
        ensemble_status = []
        for ensemble_id, ensemble_filename in enumerate(self.ensemble_filename):
            ensemble_status.append(ensemble_filename)
        return ensemble_status
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
