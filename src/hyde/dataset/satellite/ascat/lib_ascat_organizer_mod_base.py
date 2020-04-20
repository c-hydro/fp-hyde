# ----------------------------------------------------------------------------------------------------------------------
# Library
import os
import numpy as np
import progressbar

from copy import deepcopy
from shutil import copy2

from pygeogrids.netcdf import load_grid
from pygeogrids import BasicGrid
from repurpose.img2ts import Img2Ts

from src.hyde.algorithm.utils.satellite.hsaf.lib_ascat_generic import delete_file_cell, fill_tags2string
from src.hyde.algorithm.geo.satellite.hsaf.lib_ascat_geo import load_domain

from src.hyde.dataset.satellite.ascat.lib_ascat_organizer_mod_apps import AscatDriverConversion, \
    AscatDriverDR, AscatDriverNRT, AscatDriverAnalysis, AscatDriverTS, AscatDriverMapping

from src.hyde.dataset.satellite.ascat.lib_ascat_driver_interface_mod import AscatDs
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Class to organize time-series
class AscatOrganizerNRT:

    # ----------------------------------------------------------------------------------------------------------------------
    # Method to initialize class
    def __init__(self, time_run,
                 ascat_path_in,
                 ascat_path_out,
                 ascat_path_dr,
                 ascat_path_analysis,
                 ascat_path_points,
                 ascat_path_maps,
                 grid_path_ref_domain,
                 grid_path_dr,
                 grid_path_ref_global,
                 domain_path,
                 ascat_filename_tmpl_in='{cell}.nc',
                 ascat_filename_tmpl_out='rzsm_{cell}.nc',
                 ascat_filename_tmpl_dr='H140_{cell}.nc',
                 ascat_filename_tmpl_analysis='rzsm_analysis_{datetime}.workspace',
                 ascat_filename_tmpl_points='rzsm_points_{datetime}.workspace',
                 ascat_filename_tmpl_maps='rzsm_maps_{datetime}.nc',
                 grid_filename_ref_domain=None,
                 grid_filename_dr='grid.nc',
                 grid_filename_ref_global='TUW_WARP5_grid_info_2_3.nc',
                 domain_filename=None,
                 tmpl_tags=None,
                 tmpl_values=None,
                 parameters=None,
                 parameters_scaled=None,
                 time_start=None, time_end=None,
                 img_buffer=50,
                 cellsize_lat=5.0,
                 cellsize_lon=5.0,
                 ascat_updating_out=True,
                 ascat_updating_analysis=True,
                 ascat_updating_points=True,
                 ascat_updating_maps=True
                 ):

        self.time_run = time_run

        if time_start is None:
            time_start = self.time_run
        if time_end is None:
            time_end = self.time_run

        self.time_start = time_start
        self.time_end = time_end

        if tmpl_tags is None:
            tmpl_tags = {'datetime': '%Y%m%d%H%M', 'sub_path_time': '%Y/%m/%d', 'cell': '%04d',
                         'time_start': 'from_%Y%m%d%H%M', 'time_end': 'to_%Y%m%d%H%M'}
        self.tmpl_tags = tmpl_tags
        if tmpl_values is None:
            tmpl_values = {'datetime':  None, 'sub_path_time': None, 'cell': None,
                           'time_start': self.time_start, 'time_end': self.time_end}
        self.tmpl_values = tmpl_values

        self.ascat_path_dataset_in_check = ascat_path_in
        self.ascat_filename_dataset_in_check = ascat_filename_tmpl_in

        ascat_path_in = fill_tags2string(ascat_path_in, self.tmpl_tags, self.tmpl_values)
        ascat_filename_tmpl_in = fill_tags2string(ascat_filename_tmpl_in, self.tmpl_tags, self.tmpl_values)

        self.ascat_path_in = ascat_path_in
        self.ascat_filename_tmpl_in = ascat_filename_tmpl_in

        tmpl_values_out = deepcopy(self.tmpl_values)
        tmpl_values_out['sub_path_time'] = self.time_run
        tmpl_values_out['datetime'] = self.time_run

        ascat_path_out = fill_tags2string(ascat_path_out, self.tmpl_tags, tmpl_values_out)
        ascat_filename_tmpl_out = fill_tags2string(ascat_filename_tmpl_out, self.tmpl_tags, tmpl_values_out)
        if ascat_path_out is not None and ascat_filename_tmpl_out is not None:
            if not os.path.exists(ascat_path_out):
                os.makedirs(ascat_path_out)
        self.ascat_path_out = ascat_path_out
        self.ascat_filename_tmpl_out = ascat_filename_tmpl_out

        tmpl_values_analysis = deepcopy(self.tmpl_values)
        tmpl_values_analysis['sub_path_time'] = self.time_run
        tmpl_values_analysis['datetime'] = self.time_run

        ascat_path_analysis = fill_tags2string(ascat_path_analysis, self.tmpl_tags, tmpl_values_analysis)
        ascat_filename_tmpl_analysis = fill_tags2string(ascat_filename_tmpl_analysis, self.tmpl_tags, tmpl_values_analysis)
        if ascat_path_analysis is not None and ascat_filename_tmpl_analysis is not None:
            if not os.path.exists(ascat_path_analysis):
                os.makedirs(ascat_path_analysis)
        self.ascat_path_analysis = ascat_path_analysis
        self.ascat_filename_tmpl_analysis = ascat_filename_tmpl_analysis

        ascat_path_dr = fill_tags2string(ascat_path_dr, self.tmpl_tags, self.tmpl_values)
        ascat_filename_tmpl_dr = fill_tags2string(ascat_filename_tmpl_dr, self.tmpl_tags, self.tmpl_values)
        if ascat_path_dr is not None and ascat_filename_tmpl_dr is not None:
            if not os.path.exists(ascat_path_dr):
                os.makedirs(ascat_path_dr)
        self.ascat_path_dr = ascat_path_dr
        self.ascat_filename_tmpl_dr = ascat_filename_tmpl_dr

        tmpl_values_points = deepcopy(self.tmpl_values)
        tmpl_values_points['sub_path_time'] = self.time_run
        tmpl_values_points['datetime'] = self.time_run

        ascat_path_points = fill_tags2string(ascat_path_points, self.tmpl_tags, tmpl_values_points)
        ascat_filename_tmpl_points = fill_tags2string(ascat_filename_tmpl_points, self.tmpl_tags, tmpl_values_points)
        if ascat_path_points is not None and ascat_filename_tmpl_points is not None:
            if not os.path.exists(ascat_path_points):
                os.makedirs(ascat_path_points)
        self.ascat_path_points = ascat_path_points
        self.ascat_filename_tmpl_points = ascat_filename_tmpl_points

        tmpl_values_maps = deepcopy(self.tmpl_values)
        tmpl_values_maps['sub_path_time'] = self.time_run
        tmpl_values_maps['datetime'] = self.time_run

        ascat_path_maps = fill_tags2string(ascat_path_maps, self.tmpl_tags, tmpl_values_maps)
        ascat_filename_tmpl_maps = fill_tags2string(ascat_filename_tmpl_maps, self.tmpl_tags, tmpl_values_maps)
        if ascat_path_maps is not None and ascat_filename_tmpl_maps is not None:
            if not os.path.exists(ascat_path_maps):
                os.makedirs(ascat_path_maps)
        self.ascat_path_maps = ascat_path_maps
        self.ascat_filename_tmpl_maps = ascat_filename_tmpl_maps

        grid_path_dr = fill_tags2string(grid_path_dr, self.tmpl_tags, self.tmpl_values)
        grid_filename_dr = fill_tags2string(grid_filename_dr, self.tmpl_tags, self.tmpl_values)

        if grid_path_dr is not None and grid_filename_dr is not None:
            if not os.path.exists(grid_path_dr):
                os.makedirs(grid_path_dr)
        self.grid_path_dr = grid_path_dr
        self.grid_filename_dr = grid_filename_dr

        self.domain_path = domain_path
        self.domain_filename = domain_filename

        self.grid_path_ref_domain = grid_path_ref_domain
        self.grid_filename_ref_domain = grid_filename_ref_domain

        self.grid_path_ref_global = grid_path_ref_global
        self.grid_filename_ref_global = grid_filename_ref_global

        if self.grid_path_ref_global is not None and self.grid_filename_ref_global is not None:
            if os.path.exists(os.path.join(self.grid_path_ref_global, self.grid_filename_ref_global)):
                self.dr_grid_global = load_grid(os.path.join(grid_path_ref_global, grid_filename_ref_global))
                self.dr_cells_global = np.unique(self.dr_grid_global.activearrcell).data
            else:
                self.dr_grid_global = None
                self.dr_cells_global = None
        else:
            self.dr_grid_global = None
            self.dr_cells_global = None

        if self.grid_path_dr is not None and self.grid_filename_dr is not None:
            if os.path.exists(os.path.join(self.grid_path_dr, self.grid_filename_dr)):
                self.dr_grid = load_grid(os.path.join(self.grid_path_dr, self.grid_filename_dr))
                self.dr_cells = np.unique(self.dr_grid.activearrcell).data
            else:
                self.dr_grid = None
                self.dr_cells = None
        else:
            self.dr_grid = None
            self.dr_cells = None

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

        if self.dr_cells is not None:
            self.domain_cells = np.intersect1d(self.dr_cells_global, self.dr_cells)
        else:
            self.domain_cells = self.dr_cells_global

        self.img_buffer = img_buffer

        if parameters is None:
            parameters = ['var_0_7', 'var_0_28', 'var_0_100']
        self.parameters = parameters

        if parameters_scaled is None:
            parameters_scaled = ['var_scaled_0_7', 'var_scaled_0_28', 'var_scaled_0_100']
        self.parameters_scaled = parameters_scaled

        self.ascat_path_in_main_folder = self.ascat_path_in.split(tmpl_tags['sub_path_time'])[0]
        self.ascat_path_in_sub_folder = [tmpl_tags['sub_path_time']]

        self.ascat_path_out_main_folder = self.ascat_path_out.split(tmpl_tags['sub_path_time'])[0]
        self.ascat_path_out_sub_folder = [tmpl_tags['sub_path_time']]

        self.ascat_path_analysis_main_folder = self.ascat_path_analysis.split(tmpl_tags['sub_path_time'])[0]
        self.ascat_path_analysis_sub_folder = [tmpl_tags['sub_path_time']]

        self.dataset_in = AscatDs(
            self.ascat_path_in_main_folder,
            data_subpath_tmpl=self.ascat_path_in_sub_folder,
            data_filename_tmpl=self.ascat_filename_tmpl_in,
            parameter=self.parameters, array_1D=True,
            path_grid=self.grid_path_ref_domain, filename_grid=self.grid_filename_ref_domain)

        tmpl_values_check = deepcopy(self.tmpl_values)
        tmpl_values_check['sub_path_time'] = self.time_run
        tmpl_values_check['datetime'] = self.time_run

        # Load dataset data with checking file availability to avoid loading error if file does not exist
        ascat_path_check = fill_tags2string(self.ascat_path_dataset_in_check, self.tmpl_tags, tmpl_values_check)
        ascat_filename_check = fill_tags2string(self.ascat_filename_dataset_in_check, self.tmpl_tags, tmpl_values_check)

        if os.path.exists(os.path.join(ascat_path_check, ascat_filename_check)):
            data_in = self.dataset_in.read(self.time_run)
            lons_in = data_in.lon
            lats_in = data_in.lat
            self.grid_in = BasicGrid(lons_in, lats_in)
            self.grid_in = self.grid_in.to_cell_grid(cellsize_lat=cellsize_lat, cellsize_lon=cellsize_lon)
            self.cells_in = np.unique(self.grid_in.activearrcell)
        else:
            self.grid_in = None
            self.cells_in = None

        # Updating flags
        self.ascat_updating_out = ascat_updating_out
        self.ascat_updating_analysis = ascat_updating_analysis
        self.ascat_updating_points = ascat_updating_points
        self.ascat_updating_maps = ascat_updating_maps

        if self.cells_in is not None:
            if self.ascat_updating_out:
                delete_file_cell(self.ascat_path_out, filename_ts=self.ascat_filename_tmpl_out,
                                 cells=self.cells_in)
            if self.ascat_updating_analysis:
                delete_file_cell(self.ascat_path_analysis, filename_ts=self.ascat_filename_tmpl_analysis,
                                 cells=self.cells_in)
            if self.ascat_updating_points:
                delete_file_cell(self.ascat_path_points, filename_ts=self.ascat_filename_tmpl_points,
                                 cells=self.cells_in)
            if self.ascat_updating_maps:
                delete_file_cell(self.ascat_path_maps, filename_ts=self.ascat_filename_tmpl_maps,
                                 cells=self.cells_in)

    # ----------------------------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------------------------
    # Method to compose nrt data
    def composer(self):

        ascat_driver_reshuffle_nrt = Img2Ts(
            input_dataset=self.dataset_in,
            outputpath=self.ascat_path_out,
            startdate=self.time_run, enddate=self.time_run,
            input_grid=self.grid_in, filename_templ=self.ascat_filename_tmpl_out,
            imgbuffer=self.img_buffer, cellsize_lat=5.0, cellsize_lon=5.0,
            global_attr=None,
            zlib=True,
            unlim_chunksize=1000,
            ts_attributes=None)

        ascat_driver_reshuffle_nrt.calc()

    # ----------------------------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------------------------
    # Method to analyze and scale nrt data
    def analyzer(self, scaling_method='norm_min_max'):

        ascat_driver_dr = AscatDriverDR(
            ts_path=self.ascat_path_dr,
            grid_path=self.grid_path_dr,
            ts_filename_tmpl=self.ascat_filename_tmpl_dr,
            grid_filename=self.grid_filename_dr,
            scale_factor=1, valid_range=[0, 100])

        ascat_driver_nrt = AscatDriverNRT(
            ts_path=self.ascat_path_out,
            grid_path=self.grid_path_ref_domain,
            ts_filename_tmpl=self.ascat_filename_tmpl_out,
            grid_filename=self.grid_filename_ref_domain,
            scale_factor=100, valid_range=[0, 100])

        ascat_driver_analysis = AscatDriverAnalysis(
            ts_path=self.ascat_path_analysis,
            grid_path=self.grid_path_dr,
            ts_filename_tmpl=self.ascat_filename_tmpl_analysis,
            grid_filename=self.grid_filename_dr,
            var_name=self.parameters,
            var_name_scaled=self.parameters_scaled,
            var_scaling_method=scaling_method)

        # Set progress bar widget(s)
        pbar_widgets = [
            ' ===== Analyzing data progress: ', progressbar.Percentage(),
            ' ', progressbar.Bar(marker=progressbar.RotatingMarker()),
            ' ', progressbar.ETA(),
        ]

        pbar_handle = progressbar.ProgressBar(widgets=pbar_widgets, redirect_stdout=True)
        for cell in pbar_handle(self.domain_cells):

            gpis_ts, lons_ts, lats_ts = ascat_driver_dr.ts_grid.grid_points_for_cell(cell)

            analysis_ts = {}
            for gpi_ts, lon_ts, lat_ts in zip(gpis_ts, lons_ts, lats_ts):

                # Get dr data
                dr_ts = ascat_driver_dr.read_ts(gpi_ts)
                # Get nrt data
                nrt_ts = ascat_driver_nrt.read_ts(gpi_ts)

                # Compute analysis data
                analysis_ts[gpi_ts] = ascat_driver_analysis.analyze_data(nrt_ts, dr_ts)

            # Save analysis data
            ascat_driver_analysis.write_data(analysis_ts)

    # ----------------------------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------------------------
    # Method to map nrt data over domain reference
    def mapper(self, parameters_attrs=None):

        ascat_driver_mapping = AscatDriverMapping(
            self.time_run,
            ts_path=self.ascat_path_analysis,
            grid_path=self.grid_path_dr,
            domain_path=self.domain_path,
            ts_filename_tmpl=self.ascat_filename_tmpl_analysis,
            grid_filename=self.grid_filename_dr,
            domain_filename=self.domain_filename,
            points_path=self.ascat_path_points,
            points_filename_tmpl=self.ascat_filename_tmpl_points,
            points_updating=self.ascat_updating_points,
            maps_path=self.ascat_path_maps,
            maps_filename_tmpl=self.ascat_filename_tmpl_maps,
            maps_updating=self.ascat_updating_maps
        )

        # Get point(s) over domain cell(s)
        points = ascat_driver_mapping.get_points(self.domain_cells)

        # Compute maps intepolating point(s) over domain reference
        maps = ascat_driver_mapping.points_2_map(points, attrs=parameters_attrs)

        # Write maps to file in netcdf format
        ascat_driver_mapping.write_data(maps, attrs=parameters_attrs)

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Class to organize data record
class AscatOrganizerDataRecord(AscatOrganizerNRT):

    def __init__(self, time_run,
                 ascat_path_in,
                 ascat_path_out,
                 ascat_path_dr,
                 ascat_path_analysis,
                 ascat_path_points,
                 ascat_path_maps,
                 grid_path_ref_domain,
                 grid_path_dr,
                 grid_path_ref_global,
                 domain_path,
                 ascat_filename_tmpl_in='{cell}.nc',
                 ascat_filename_tmpl_out='rzsm_{cell}.nc',
                 ascat_filename_tmpl_dr='H140_{cell}.nc',
                 ascat_filename_tmpl_analysis='rzsm_analysis_{datetime}.workspace',
                 ascat_filename_tmpl_points='rzsm_points_{datetime}.workspace',
                 ascat_filename_tmpl_maps='rzsm_maps_{datetime}.nc',
                 grid_filename_ref_domain=None,
                 grid_filename_dr='grid.nc',
                 grid_filename_ref_global='TUW_WARP5_grid_info_2_3.nc',
                 domain_filename=None,
                 tmpl_tags=None,
                 tmpl_values=None,
                 parameters=None,
                 parameters_scaled=None,
                 time_start=None, time_end=None,
                 img_buffer=50,
                 ascat_updating_out=True,
                 ascat_updating_analysis=True,
                 ascat_updating_dr=True
                 ):

        self.ascat_updating_dr = ascat_updating_dr

        tmpl_tags = {'datetime': '%Y%m%d%H%M', 'sub_path_time': '%Y/%m/%d', 'cell': '%04d',
                     'time_start': 'from_%Y%m%d', 'time_end': 'to_%Y%m%d'}

        tmpl_values = {'datetime':  None, 'sub_path_time': None, 'cell': None,
                       'time_start': time_start, 'time_end': time_end}

        super(AscatOrganizerDataRecord, self).__init__(
            time_run,
            ascat_path_in=ascat_path_in,
            ascat_path_out=ascat_path_out,
            ascat_path_dr=ascat_path_dr,
            ascat_path_analysis=ascat_path_analysis,
            ascat_path_points=ascat_path_points,
            ascat_path_maps=ascat_path_maps,
            grid_path_ref_domain=grid_path_ref_domain,
            grid_path_dr=grid_path_dr,
            grid_path_ref_global=grid_path_ref_global,
            domain_path=domain_path,
            ascat_filename_tmpl_in=ascat_filename_tmpl_in,
            ascat_filename_tmpl_out=ascat_filename_tmpl_out,
            ascat_filename_tmpl_dr=ascat_filename_tmpl_dr,
            ascat_filename_tmpl_analysis=ascat_filename_tmpl_analysis,
            ascat_filename_tmpl_points=ascat_filename_tmpl_points,
            ascat_filename_tmpl_maps=ascat_filename_tmpl_maps,
            grid_filename_ref_domain=grid_filename_ref_domain,
            grid_filename_dr=grid_filename_dr,
            grid_filename_ref_global=grid_filename_ref_global,
            domain_filename=domain_filename,
            tmpl_tags=tmpl_tags,
            tmpl_values=tmpl_values,
            parameters=parameters,
            parameters_scaled=parameters_scaled,
            time_start=time_start, time_end=time_end,
            img_buffer=img_buffer,
            ascat_updating_out=ascat_updating_out,
            ascat_updating_analysis=ascat_updating_analysis,
            ascat_updating_points=False,
            ascat_updating_maps=False
        )

    # ----------------------------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------------------------
    # Method to reshuffle gridded data in data record format
    def reshuffler(self):

        ascat_driver_reshuffler_dr = Img2Ts(
            input_dataset=self.dataset_in,
            outputpath=self.ascat_path_out,
            filename_templ=self.ascat_filename_tmpl_out,
            startdate=self.time_start, enddate=self.time_end,
            input_grid=self.grid_in,
            imgbuffer=self.img_buffer, cellsize_lat=5.0, cellsize_lon=5.0,
            global_attr=None,
            zlib=True,
            unlim_chunksize=1000,
            ts_attributes=None)

        ascat_driver_reshuffler_dr.calc()

        if self.ascat_path_out != self.grid_path_dr:
            if os.path.exists(os.path.join(self.ascat_path_out, self.grid_filename_dr)):
                copy2(os.path.join(self.ascat_path_out, self.grid_filename_dr),
                      os.path.join(self.ascat_path_out, self.grid_path_dr))
                os.remove(os.path.join(self.ascat_path_out, self.grid_filename_dr))

    # ----------------------------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------------------------
    # Method to analyze data record
    def analyzer(self, scaling_method='norm_min_max'):

        ascat_driver_dr = AscatDriverDR(
            ts_path=self.ascat_path_out,
            grid_path=self.grid_path_dr,
            ts_filename_tmpl=self.ascat_filename_tmpl_out,
            grid_filename=self.grid_filename_dr,
            scale_factor=100, valid_range=[0, 100])

        ascat_driver_analysis = AscatDriverAnalysis(
            ts_path=self.ascat_path_analysis,
            grid_path=self.grid_path_dr,
            ts_filename_tmpl=self.ascat_filename_tmpl_analysis,
            grid_filename=self.grid_filename_dr,
            var_name=self.parameters,
            var_name_scaled=self.parameters_scaled,
            var_scaling_method=scaling_method)

        # Set progress bar widget(s)
        pbar_widgets = [
            ' ===== Analyzing data progress: ', progressbar.Percentage(),
            ' ', progressbar.Bar(marker=progressbar.RotatingMarker()),
            ' ', progressbar.ETA(),
        ]

        pbar_handle = progressbar.ProgressBar(widgets=pbar_widgets, redirect_stdout=True)
        for cell in pbar_handle(self.domain_cells):

            gpis_ts, lons_ts, lats_ts = ascat_driver_dr.ts_grid.grid_points_for_cell(cell)

            analysis_ts = {}
            for gpi_ts, lon_ts, lat_ts in zip(gpis_ts, lons_ts, lats_ts):

                # Reset time reference in class
                ascat_driver_dr.dates = None

                # Get dr data
                dr_ts = ascat_driver_dr.read_ts(gpi_ts)

                # Compute analysis data
                analysis_ts[gpi_ts] = ascat_driver_analysis.analyze_data(dr_ts, dr_ts)

            # Save analysis data
            ascat_driver_analysis.write_data(analysis_ts)

    # ----------------------------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------------------------
    # Method to write data in ts format
    def writer(self):

        ascat_driver_ts = AscatDriverTS(
            analysis_path=self.ascat_path_analysis,
            ts_path=self.ascat_path_dr,
            grid_path_dr=self.grid_path_dr,
            grid_path_dr_scaled=self.ascat_path_dr,
            analysis_filename_tmpl=self.ascat_filename_tmpl_analysis,
            ts_filename_tmpl=self.ascat_filename_tmpl_dr,
            grid_filename_dr='grid.nc',
            grid_filename_dr_scaled='grid.nc',
            var_name=self.parameters,
            var_name_scaled=self.parameters_scaled,
            time_start=self.time_start, time_end=self.time_end
        )

        # Set progress bar widget(s)
        pbar_widgets = [
            ' ===== Writing data progress: ', progressbar.Percentage(),
            ' ', progressbar.Bar(marker=progressbar.RotatingMarker()),
            ' ', progressbar.ETA(),
        ]

        # Iterate over cell(s)
        pbar_handle = progressbar.ProgressBar(widgets=pbar_widgets, redirect_stdout=True)
        for cell in pbar_handle(self.domain_cells):

            # Read data in pickle format
            data_ts = ascat_driver_ts.get_data(cell)
            # Assemble data in contiguous format
            data_ts_assembled, attrs_ts_assembled = ascat_driver_ts.assemble_data(data_ts)
            # Write data in cell file
            ascat_driver_ts.write_data(data_ts_assembled, attrs_ts_assembled)

# ----------------------------------------------------------------------------------------------------------------------
