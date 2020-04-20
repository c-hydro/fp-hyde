# ----------------------------------------------------------------------------------------------------------------------
# Library
import os
import numpy as np
import progressbar

from copy import deepcopy

from src.hyde.algorithm.geo.satellite.hsaf.lib_ascat_geo import load_domain
from src.hyde.algorithm.utils.satellite.hsaf.lib_ascat_generic import delete_file_cell, fill_tags2string

from src.hyde.dataset.satellite.ascat.lib_ascat_organizer_obs_apps import AscatDriverNRT, AscatDriverTS, \
    AscatDriverAnalysis, AscatDriverConversion, AscatDriverMapping
from src.hyde.dataset.satellite.ascat.lib_ascat_organizer_obs_apps import AscatDriverDR as AscatDriverDR_OBS
from src.hyde.dataset.satellite.ascat.lib_ascat_organizer_mod_apps import AscatDriverDR as AscatDriverDR_MOD

from pygeogrids.netcdf import load_grid
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Class to organize nrt time-series
class AscatOrganizerNRT:

    def __init__(self, time_run,
                 ascat_path_in,
                 ascat_path_out,
                 ascat_path_analysis,
                 ascat_path_points,
                 ascat_path_maps,
                 ascat_path_dr_obs_global,
                 ascat_path_dr_obs_domain,
                 ascat_path_dr_mod,
                 grid_path_dr_obs_global,
                 grid_path_dr_obs_domain,
                 grid_path_dr_mod,
                 domain_path,
                 ascat_filename_tmpl_in='{cell}.nc',
                 ascat_filename_tmpl_out='ssm_{cell}.nc',
                 ascat_filename_tmpl_analysis='analysis_{datetime}.workspace',
                 ascat_filename_tmpl_points='points_{datetime}.workspace',
                 ascat_filename_tmpl_maps='ascat_{datetime}.nc',
                 ascat_filename_tmpl_dr_obs_global='H115_{cell}.nc',
                 ascat_filename_tmpl_dr_obs_domain='H115_{cell}_domain.nc',
                 ascat_filename_tmpl_dr_mod='H115_{cell}_domain.nc',
                 grid_filename_dr_obs_global='TUW_WARP5_grid_info_2_3.nc',
                 grid_filename_dr_obs_domain='TUW_WARP5_grid_info_2_3.nc',
                 grid_filename_dr_mod='grid.nc',
                 domain_filename=None,
                 tmpl_tags=None,
                 tmpl_values=None,
                 parameters=None,
                 parameters_tmpl_filtered=None,
                 parameters_tmpl_scaled=None,
                 parameters_tmpl_mod=None,
                 time_start=None, time_end=None,
                 ascat_updating_out=True,
                 ascat_updating_analysis=True,
                 ascat_updating_points=True,
                 ascat_updating_maps=True
                 ):

        # Get time information
        self.time_run = time_run

        if time_start is None:
            time_start = self.time_run
        if time_end is None:
            time_end = self.time_run

        self.time_start = time_start
        self.time_end = time_end

        # Get tags and values template
        if tmpl_tags is None:
            tmpl_tags = {'datetime': '%Y%m%d%H%M', 'sub_path_time': '%Y/%m/%d', 'cell': '%04d',
                         'time_start': 'from_%Y%m%d%H%M', 'time_end': 'to_%Y%m%d%H%M', 'ctime': '%02d'}
        self.tmpl_tags = tmpl_tags
        if tmpl_values is None:
            tmpl_values = {'datetime':  None, 'sub_path_time': None, 'cell': None,
                           'time_start': self.time_start, 'time_end': self.time_end, 'ctime': None}
        self.tmpl_values = tmpl_values

        # Check format of nrt in path(s) and filename(s) input (convert to list)
        if isinstance(ascat_path_in, str):
            ascat_path_in = [ascat_path_in]

        if isinstance(ascat_filename_tmpl_in, str):
            ascat_filename_tmpl_in = [ascat_filename_tmpl_in]

        # Define nrt in path(s) and filename(s)
        tmpl_values = deepcopy(self.tmpl_values)
        tmpl_values['sub_path_time'] = self.time_run
        tmpl_values['datetime'] = self.time_run

        ascat_path_in_def = []
        ascat_filename_in_def = []
        for ascat_path_step_in, ascat_filename_step_in in zip(ascat_path_in, ascat_filename_tmpl_in):

            ascat_path_step_in = fill_tags2string(ascat_path_step_in, self.tmpl_tags, tmpl_values)
            ascat_filename_step_in = fill_tags2string(ascat_filename_step_in, self.tmpl_tags, tmpl_values)

            ascat_path_in_def.append(ascat_path_step_in)
            ascat_filename_in_def.append(ascat_filename_step_in)

        self.ascat_path_in = ascat_path_in_def
        self.ascat_filename_tmpl_in = ascat_filename_in_def

        # Define nrt out path(s) and filename(s) outcome
        tmpl_values = deepcopy(self.tmpl_values)
        tmpl_values['sub_path_time'] = self.time_run
        tmpl_values['datetime'] = self.time_run

        ascat_path_out = fill_tags2string(ascat_path_out, self.tmpl_tags, tmpl_values)
        ascat_filename_tmpl_out = fill_tags2string(ascat_filename_tmpl_out, self.tmpl_tags, tmpl_values)

        if ascat_path_out is not None and ascat_filename_tmpl_out is not None:
            if not os.path.exists(ascat_path_out):
                os.makedirs(ascat_path_out)
        self.ascat_path_out = ascat_path_out
        self.ascat_filename_tmpl_out = ascat_filename_tmpl_out

        # Define nrt path(s) and filename(s) analysis
        tmpl_values = deepcopy(self.tmpl_values)
        tmpl_values['sub_path_time'] = self.time_run
        tmpl_values['datetime'] = self.time_run

        ascat_path_analysis = fill_tags2string(ascat_path_analysis, self.tmpl_tags, tmpl_values)
        ascat_filename_tmpl_analysis = fill_tags2string(ascat_filename_tmpl_analysis, self.tmpl_tags, tmpl_values)

        if ascat_path_analysis is not None and ascat_filename_tmpl_analysis is not None:
            if not os.path.exists(ascat_path_analysis):
                os.makedirs(ascat_path_analysis)
        self.ascat_path_analysis = ascat_path_analysis
        self.ascat_filename_tmpl_analysis = ascat_filename_tmpl_analysis

        # Define nrt path(s) and filename(s) point(s)
        tmpl_values = deepcopy(self.tmpl_values)
        tmpl_values['sub_path_time'] = self.time_run
        tmpl_values['datetime'] = self.time_run

        ascat_path_points = fill_tags2string(ascat_path_points, self.tmpl_tags, tmpl_values)
        ascat_filename_tmpl_points = fill_tags2string(ascat_filename_tmpl_points, self.tmpl_tags, tmpl_values)

        if ascat_path_points is not None and ascat_filename_tmpl_points is not None:
            if not os.path.exists(ascat_path_points):
                os.makedirs(ascat_path_points)
        self.ascat_path_points = ascat_path_points
        self.ascat_filename_tmpl_points = ascat_filename_tmpl_points

        # Define nrt path(s) and filename(s) maps
        tmpl_values = deepcopy(self.tmpl_values)
        tmpl_values['sub_path_time'] = self.time_run
        tmpl_values['datetime'] = self.time_run

        ascat_path_maps = fill_tags2string(ascat_path_maps, self.tmpl_tags, tmpl_values)
        ascat_filename_tmpl_maps = fill_tags2string(ascat_filename_tmpl_maps, self.tmpl_tags, tmpl_values)

        if ascat_path_maps is not None and ascat_filename_tmpl_maps is not None:
            if not os.path.exists(ascat_path_maps):
                os.makedirs(ascat_path_maps)
        self.ascat_path_maps = ascat_path_maps
        self.ascat_filename_tmpl_maps = ascat_filename_tmpl_maps

        # Data record path(s) and filename(s)
        self.ascat_path_dr_obs_global = ascat_path_dr_obs_global
        self.ascat_filename_tmpl_dr_obs_global = ascat_filename_tmpl_dr_obs_global

        self.ascat_path_dr_obs_domain = ascat_path_dr_obs_domain
        self.ascat_filename_tmpl_dr_obs_domain = ascat_filename_tmpl_dr_obs_domain

        self.ascat_path_dr_mod = ascat_path_dr_mod
        self.ascat_filename_tmpl_dr_mod = ascat_filename_tmpl_dr_mod

        self.grid_path_dr_obs_global = grid_path_dr_obs_global
        self.grid_filename_dr_obs_global = grid_filename_dr_obs_global

        self.grid_path_dr_obs_domain = grid_path_dr_obs_domain
        self.grid_filename_dr_obs_domain = grid_filename_dr_obs_domain

        self.grid_path_dr_mod = grid_path_dr_mod
        self.grid_filename_dr_mod = grid_filename_dr_mod

        # Domain path and filename
        self.domain_path = domain_path
        self.domain_filename = domain_filename

        # Set data record and grid (obs global dataset)
        if self.grid_path_dr_obs_global is not None and self.grid_filename_dr_obs_global is not None:
            if os.path.exists(os.path.join(self.grid_path_dr_obs_global, self.grid_filename_dr_obs_global)):
                self.dr_grid_obs_global = load_grid(os.path.join(self.grid_path_dr_obs_global, self.grid_filename_dr_obs_global))
                self.dr_cells_obs_global = np.unique(self.dr_grid_obs_global.activearrcell).data
            else:
                self.dr_grid_obs_global = None
                self.dr_cells_obs_global = None
        else:
            self.dr_grid_obs_global = None
            self.dr_cells_obs_global = None

        # Set data record and grid (obs domain dataset)
        if self.grid_path_dr_obs_domain is not None and self.grid_filename_dr_obs_domain is not None:
            if os.path.exists(os.path.join(self.grid_path_dr_obs_domain, self.grid_filename_dr_obs_domain)):
                self.dr_grid_obs_domain = load_grid(os.path.join(self.grid_path_dr_obs_domain, self.grid_filename_dr_obs_domain))
                self.dr_cells_obs_domain = np.unique(self.dr_grid_obs_domain.activearrcell).data
            else:
                self.dr_grid_obs_domain = None
                self.dr_cells_obs_domain = None
        else:
            self.dr_grid_obs_domain = None
            self.dr_cells_obs_domain = None

        # Set data record and grid (mod dataset)
        if self.grid_path_dr_mod is not None and self.grid_filename_dr_mod is not None:
            if os.path.exists(os.path.join(self.grid_path_dr_mod, self.grid_filename_dr_mod)):
                self.dr_grid_mod = load_grid(os.path.join(self.grid_path_dr_mod, self.grid_filename_dr_mod))
                self.dr_cells_mod = np.unique(self.dr_grid_mod.activearrcell).data
            else:
                self.dr_grid_mod = None
                self.dr_cells_mod = None
        else:
            self.dr_grid_mod = None
            self.dr_cells_mod = None

        if self.domain_path is not None and self.domain_filename is not None:
            if os.path.exists(os.path.join(self.domain_path, self.domain_filename)):
                self.domain_grid, self.domain_obj = load_domain(os.path.join(self.domain_path, self.domain_filename))
                self.domain_cells = np.unique(self.domain_grid.activearrcell)
            else:
                self.domain_grid = None
                self.domain_cells = None
        else:
            self.domain_grid = None
            self.domain_cells = None

        # Parameters definition(s)
        if parameters is None:
            parameters = ['sm', 'sm_noise', 'proc_flag', 'corr_flag']
        self.parameters = parameters

        if parameters_tmpl_filtered is None:
            parameters_tmpl_filtered = 'var_swi_{ctime}'

        parameters_tmpl_filtered = fill_tags2string(parameters_tmpl_filtered, self.tmpl_tags, self.tmpl_values)
        self.parameters_tmpl_filtered = parameters_tmpl_filtered

        if parameters_tmpl_scaled is None:
            parameters_tmpl_scaled = 'var_swi_{ctime}_scaled'
        parameters_tmpl_scaled = fill_tags2string(parameters_tmpl_scaled, self.tmpl_tags, self.tmpl_values)
        self.parameters_tmpl_scaled = parameters_tmpl_scaled

        if parameters_tmpl_mod is None:
            parameters_tmpl_mod = ['var_scaled_0_7', 'var_scaled_0_28', 'var_scaled_0_100']
        self.parameters_tmpl_mod = parameters_tmpl_mod

        # Updating flags
        self.ascat_updating_out = ascat_updating_out
        self.ascat_updating_analysis = ascat_updating_analysis
        self.ascat_updating_points = ascat_updating_points
        self.ascat_updating_maps = ascat_updating_maps

        if self.ascat_updating_out:
            delete_file_cell(self.ascat_path_out, filename_ts=self.ascat_filename_tmpl_out,
                             cells=self.dr_cells_obs_domain)
        if self.ascat_updating_analysis:
            delete_file_cell(self.ascat_path_analysis, filename_ts=self.ascat_filename_tmpl_analysis,
                             cells=self.dr_cells_obs_domain)
        if self.ascat_updating_points:
            delete_file_cell(self.ascat_path_points, filename_ts=self.ascat_filename_tmpl_points,
                             cells=self.dr_cells_obs_domain)
        if self.ascat_updating_maps:
            delete_file_cell(self.ascat_path_maps, filename_ts=self.ascat_filename_tmpl_maps,
                             cells=self.dr_cells_obs_domain)

    # ----------------------------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------------------------
    # Method to compose cell data
    def composer(self):

        # Initialize data conversion class
        ascat_driver_conversion = AscatDriverConversion(
            ts_path_in=self.ascat_path_in, ts_filename_tmpl_in=self.ascat_filename_tmpl_in,
            ts_path_out=self.ascat_path_out, ts_filename_tmpl_out=self.ascat_filename_tmpl_out,
            grid_path=self.grid_path_dr_obs_domain, grid_filename=self.grid_filename_dr_obs_domain,
            parameters=self.parameters)

        # Set progress bar widget(s)
        pbar_widgets = [
            ' ===== Converting data progress: ', progressbar.Percentage(),
            ' ', progressbar.Bar(marker=progressbar.RotatingMarker()),
            ' ', progressbar.ETA(),
        ]

        # Iterate over cell(s)
        pbar_handle = progressbar.ProgressBar(widgets=pbar_widgets, redirect_stdout=True)
        for cell in pbar_handle(self.domain_cells):

            # Get data
            data = ascat_driver_conversion.get_data(cell)
            # Assemble data
            data_assembled, attrs_assembled = ascat_driver_conversion.assemble_data(data)
            # Save data
            ascat_driver_conversion.write_data(data_assembled, attrs_assembled, None)

    # ----------------------------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------------------------
    # Method to analyze cell data
    def analyzer(self, var_sm='sm', var_swi_ctime=None, var_scaling_method='min_max'):

        # Initialize nrt driver class
        ascat_driver_nrt = AscatDriverNRT(
            ts_path=self.ascat_path_out,
            grid_path=self.grid_path_dr_obs_global,
            ts_filename_tmpl=self.ascat_filename_tmpl_out,
            grid_filename=self.grid_filename_dr_obs_global)

        # Initialize data record global obs driver class
        ascat_driver_dr_obs_global = AscatDriverDR_OBS(
            ts_path=self.ascat_path_dr_obs_global,
            grid_path=self.grid_path_dr_obs_global,
            ts_filename_tmpl=self.ascat_filename_tmpl_dr_obs_global,
            grid_filename=self.grid_filename_dr_obs_global,
            ts_type_ref=1)

        # Initialize data record domain obs driver class
        ascat_driver_dr_obs_domain = AscatDriverDR_OBS(
            ts_path=self.ascat_path_dr_obs_domain,
            grid_path=self.grid_path_dr_obs_domain,
            ts_filename_tmpl=self.ascat_filename_tmpl_dr_obs_domain,
            grid_filename=self.grid_filename_dr_obs_domain,
            ts_type_ref=2)

        # Initialize data record mod driver class
        ascat_driver_dr_mod = AscatDriverDR_MOD(
            ts_path=self.ascat_path_dr_mod,
            grid_path=self.grid_path_dr_mod,
            ts_filename_tmpl=self.ascat_filename_tmpl_dr_mod,
            grid_filename=self.grid_filename_dr_mod,
            scale_factor=1, valid_range=[0, 100])

        # Initialize analysis driver class
        ascat_driver_analysis = AscatDriverAnalysis(
            ts_path=self.ascat_path_analysis,
            grid_path=self.grid_path_dr_obs_global,
            ts_filename_tmpl=self.ascat_filename_tmpl_analysis,
            grid_filename=self.grid_filename_dr_obs_global,
            var_sm=var_sm,
            var_swi_raw_tmpl=self.parameters_tmpl_filtered, var_swi_scaled_tmpl=self.parameters_tmpl_scaled,
            var_swi_ctime=var_swi_ctime,
            var_scaling_method=var_scaling_method)

        # Set progress bar widget(s)
        pbar_widgets = [
            ' ===== Analyzing data progress: ', progressbar.Percentage(),
            ' ', progressbar.Bar(marker=progressbar.RotatingMarker()),
            ' ', progressbar.ETA(),
        ]

        # Iterate over cell(s)
        pbar_handle = progressbar.ProgressBar(widgets=pbar_widgets, redirect_stdout=True)
        for cell in pbar_handle(self.domain_cells):

            # DEBUG START
            # cell = 1430
            # DEBUG END

            # Get global obs gpis, lons and lats using cell reference
            gpis_obs_global, lons, lats = self.dr_grid_obs_global.grid_points_for_cell(cell)
            # Get domain obs gpis
            gpis_obs_domain = self.dr_grid_obs_domain.find_nearest_gpi(lons, lats)[0]
            # Get mod gpis and cells
            gpis_mod = self.dr_grid_mod.find_nearest_gpi(lons, lats)[0]
            cells_mod = self.dr_grid_mod.gpi2cell(gpis_mod)

            # Find idxs of cells equal to pivot cell (for removing cells not equal to pivot cell)
            cells_idx = np.where(cells_mod == cell)

            # Select data using idx of selected cell
            gpis_obs_global_idx = gpis_obs_global[cells_idx]
            gpis_obs_domain_idx = gpis_obs_domain[cells_idx]
            gpis_mod_idx = gpis_mod[cells_idx]
            cells_mod_idx = cells_mod[cells_idx]
            lons_idx = lons[cells_idx]
            lats_idx = lats[cells_idx]

            # Iterate over gpi(s)
            analysis_ts = {}
            for gpi_obs_global, gpi_global_domain, gpi_mod, cell_mod, lon, lat in \
                    zip(gpis_obs_global_idx, gpis_obs_domain_idx, gpis_mod_idx, cells_mod_idx, lons_idx, lats_idx):

                # DEBUG START
                # gpi_test = gpi_obs_global
                # #gpi_test = 2123317
                # idx = np.where(gpis_obs_global == gpi_test)[0][0]
                # gpi_obs_global = gpis_obs_global[idx]
                # gpi_global_domain = gpis_obs_domain[idx]
                # gpi_mod = gpis_mod[idx]
                # cell_mod = cells_mod[idx]
                # lon = lons[idx]
                # lat = lats[idx]
                # DEBUG END

                # Get nrt obs data
                nrt_ts = ascat_driver_nrt.read_ts(gpi_obs_global)

                # Get dr obs data
                dr_ts_obs = ascat_driver_dr_obs_global.read_ts(gpi_obs_global)

                if dr_ts_obs.empty:
                    dr_ts_obs = ascat_driver_dr_obs_domain.read_ts(gpi_obs_global)
                    nrt_ts['type_ref'] = ascat_driver_dr_obs_domain.ts_type_ref
                else:
                    nrt_ts['type_ref'] = ascat_driver_dr_obs_global.ts_type_ref

                # Get dr mod data
                dr_ts_mod = ascat_driver_dr_mod.read_ts(gpi_mod)

                # Compute analysis data
                if ascat_driver_analysis.scaling_method_args == 3:

                    if (not nrt_ts.empty) and (not dr_ts_obs.empty) and (not dr_ts_mod.empty):

                        analysis_ts[gpi_obs_global] = ascat_driver_analysis.analyze_data_vars_3(
                            nrt_ts, dr_ts_obs, dr_ts_mod, var_ts_mod=self.parameters_tmpl_mod)

                elif ascat_driver_analysis.scaling_method_args == 2:

                    if (not nrt_ts.empty) and (not dr_ts_mod.empty):

                        analysis_ts[gpi_obs_global] = ascat_driver_analysis.analyze_data_vars_2(nrt_ts, dr_ts_mod)

                elif ascat_driver_analysis.scaling_method_args is None:
                    pass

            # Save analysis data
            if analysis_ts:
                ascat_driver_analysis.write_data(analysis_ts)
            else:
                ascat_driver_analysis.write_empty(cell)

    # ----------------------------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------------------------
    # Method to map nrt data over domain reference
    def mapper(self, parameters_attrs=None):

        # Initialize map driver class
        ascat_driver_mapping = AscatDriverMapping(
            self.time_run,
            ts_path=self.ascat_path_analysis,
            grid_path=self.grid_path_dr_obs_global,
            reference_path=self.domain_path,
            ts_filename_tmpl=self.ascat_filename_tmpl_analysis,
            grid_filename=self.grid_filename_dr_obs_global,
            reference_filename=self.domain_filename,
            points_path=self.ascat_path_points,
            points_filename_tmpl=self.ascat_filename_tmpl_points,
            points_updating=self.ascat_updating_points,
            maps_path=self.ascat_path_maps,
            maps_filename_tmpl=self.ascat_filename_tmpl_maps,
            maps_updating=self.ascat_updating_maps,
            interp_method='nearest',
            interp_radius_lon=0.5,
            interp_radius_lat=0.5
        )

        # Get data point(s)
        points = ascat_driver_mapping.get_points(self.domain_cells)
        # Interpolate points over domain
        maps = ascat_driver_mapping.points_2_map(points, attrs=parameters_attrs)
        # Save maps to netcdf file
        ascat_driver_mapping.write_data(maps, attrs=parameters_attrs)

    # ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Class to organize data record time-series
class AscatOrganizerDataRecord(AscatOrganizerNRT):

    def __init__(self, time_run,
                 ascat_path_in,
                 ascat_path_out,
                 grid_path_dr,
                 domain_path,
                 ascat_filename_tmpl_dr_domain_in='{cell}.nc',
                 ascat_filename_tmpl_dr_domain_out='ssm_{cell}.nc',
                 grid_filename_dr='TUW_WARP5_grid_info_2_3.nc',
                 domain_filename=None,
                 tmpl_tags=None,
                 tmpl_values=None,
                 parameters=None,
                 time_start=None, time_end=None,
                 ascat_updating_out=True):

        tmpl_tags = {'datetime': '%Y%m%d%H%M', 'sub_path_time': '%Y/%m/%d', 'cell': '%04d',
                     'time_start': 'from_%Y%m%d', 'time_end': 'to_%Y%m%d'}

        tmpl_values = {'datetime':  None, 'sub_path_time': None, 'cell': None,
                       'time_start': time_start, 'time_end': time_end}

        super(AscatOrganizerDataRecord, self).__init__(
            time_run,
            ascat_path_in=ascat_path_in,
            ascat_path_out=ascat_path_out,
            ascat_path_analysis=None,
            ascat_path_points=None,
            ascat_path_maps=None,
            ascat_path_dr_obs_global=None,
            ascat_path_dr_obs_domain=None,
            ascat_path_dr_mod=None,
            grid_path_dr_obs_global=None,
            grid_path_dr_obs_domain=grid_path_dr,
            grid_path_dr_mod=None,
            domain_path=domain_path,
            ascat_filename_tmpl_in=ascat_filename_tmpl_dr_domain_in,
            ascat_filename_tmpl_out=ascat_filename_tmpl_dr_domain_out,
            ascat_filename_tmpl_analysis='',
            ascat_filename_tmpl_points='',
            ascat_filename_tmpl_maps='',
            ascat_filename_tmpl_dr_obs_global='',
            ascat_filename_tmpl_dr_obs_domain='',
            ascat_filename_tmpl_dr_mod='',
            grid_filename_dr_obs_global='',
            grid_filename_dr_obs_domain=grid_filename_dr,
            grid_filename_dr_mod='',
            domain_filename=domain_filename,
            tmpl_tags=tmpl_tags,
            tmpl_values=tmpl_values,
            parameters=parameters,
            parameters_tmpl_filtered=None,
            parameters_tmpl_scaled=None,
            parameters_tmpl_mod=None,
            time_start=time_start, time_end=time_end,
            ascat_updating_out=ascat_updating_out,
            ascat_updating_analysis=False,
            ascat_updating_points=False,
            ascat_updating_maps=False)

    # ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------ù
