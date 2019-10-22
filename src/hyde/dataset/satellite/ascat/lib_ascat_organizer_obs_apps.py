# ----------------------------------------------------------------------------------------------------------------------
# Library
import os

import numpy as np
import pandas as pd

from inspect import signature
from copy import deepcopy

from src.hyde.algorithm.io.satellite.hsaf.lib_ascat_io_generic import write_points_data, create_dset, write_dset, \
    read_cell_data, read_analysis_data, read_points_data, write_cell_data, write_analysis_data
from src.hyde.algorithm.io.satellite.hsaf.lib_ascat_io_obs import assemble_data_obs
from src.hyde.algorithm.io.satellite.hsaf.lib_ascat_io_mod import assemble_data_contiguous
from src.hyde.algorithm.time.satellite.hsaf.lib_ascat_time import df_selecting_step
from src.hyde.algorithm.analysis.satellite.hsaf.lib_ascat_analysis import interpolate_point2map
import src.hyde.algorithm.analysis.satellite.hsaf.lib_ascat_analysis as scaling_methods_external

from src.hyde.algorithm.geo.satellite.hsaf.lib_ascat_geo import load_domain, data_2_map, data_2_show
from src.hyde.dataset.satellite.ascat.lib_ascat_driver_interface_obs import AscatDriverSsmCdr

from ascat.read_native.cdr import AscatSsmCdr
from ascat.read_native.bufr import AscatL2SsmBufrChunked

from pytesmo.time_series.filters import exp_filter
from pytesmo.scaling import get_scaling_function, get_scaling_method_lut

from pygeogrids.netcdf import load_grid
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Class to create Ascat gridded data
class AscatDriverMapping:

    def __init__(self, *args, **kwargs):

        # Get time information
        self.time = args[0]

        # initialize analysis time-series path
        if 'ts_path' in kwargs:
            self.ts_path = kwargs.pop('ts_path')
        else:
            raise ValueError('time-series path not defined')

        # initialize analysis time-series filename template
        if 'ts_filename_tmpl' in kwargs:
            self.ts_filename_tmpl = kwargs.pop('ts_filename_tmpl')
        else:
            raise ValueError('time-series filename template not defined')

        # initialize points path
        if 'points_path' in kwargs:
            self.pnt_path = kwargs.pop('points_path')
        else:
            raise ValueError('points path not defined')

        # initialize points filename template
        if 'points_filename_tmpl' in kwargs:
            self.pnt_filename_tmpl = kwargs.pop('points_filename_tmpl')
        else:
            raise ValueError('points filename template not defined')

        # initialize maps path
        if 'maps_path' in kwargs:
            self.map_path = kwargs.pop('maps_path')
        else:
            raise ValueError('maps path not defined')

        # initialize maps filename template
        if 'maps_filename_tmpl' in kwargs:
            self.map_filename_tmpl = kwargs.pop('maps_filename_tmpl')
        else:
            raise ValueError('maps filename template not defined')

        # initialize points updating flag
        if 'points_updating' in kwargs:
            self.pnt_updating = kwargs.pop('points_updating')
        else:
            self.pnt_updating = True

        # initialize maps updating flag
        if 'maps_updating' in kwargs:
            self.map_updating = kwargs.pop('maps_updating')
        else:
            self.map_updating = True

        # initialize grid path
        if 'grid_path' in kwargs:
            self.grid_path = kwargs.pop('grid_path')
        else:
            raise ValueError('grid path not defined')

        # initialize grid filename
        if 'grid_filename' in kwargs:
            self.grid_filename = kwargs.pop('grid_filename')
        else:
            raise ValueError('grid filename not defined')

        # initialize refernce path
        if 'reference_path' in kwargs:
            self.reference_path = kwargs.pop('reference_path')
        else:
            raise ValueError('reference path not defined')

        # initialize reference filename
        if 'reference_filename' in kwargs:
            self.reference_filename = kwargs.pop('reference_filename')
        else:
            raise ValueError('reference filename not defined')

        # initialize interpolation method
        if 'interp_method' in kwargs:
            self.interp_method = kwargs.pop('interp_method')
        else:
            raise ValueError('interpolation radius longitude not defined')

        # initialize interpolation radius longitude
        if 'interp_radius_lon' in kwargs:
            self.interp_radius_lon = kwargs.pop('interp_radius_lon')
        else:
            raise ValueError('interpolation radius longitude not defined')

        # initialize interpolation radius latitude
        if 'interp_radius_lat' in kwargs:
            self.interp_radius_lat = kwargs.pop('interp_radius_lat')
        else:
            raise ValueError('interpolation radius latitude not defined')

        self.target_grid = load_grid(os.path.join(self.grid_path, self.grid_filename))
        self.domain_grid, self.domain_obj = load_domain(os.path.join(self.reference_path, self.reference_filename))

    def get_points(self, cells, index_name='gpi'):

        # Get points filename
        pnt_filename = self.pnt_filename_tmpl

        if self.pnt_updating is True:
            if os.path.exists(os.path.join(self.pnt_path, pnt_filename)):
                os.remove(os.path.join(self.pnt_path, pnt_filename))

        if not os.path.exists(os.path.join(self.pnt_path, pnt_filename)):

            df_points = None
            for cell in cells:

                ts_filename_def = self.ts_filename_tmpl % cell

                if os.path.exists(os.path.join(self.ts_path, ts_filename_def)):

                    data = read_analysis_data(os.path.join(self.ts_path, ts_filename_def))

                    if data is not None:

                        gpis = list(data.keys())
                        timestamp = pd.Timestamp(self.time)
                        jdate = timestamp.to_julian_date()

                        for i, gpi in enumerate(gpis):

                            lon_gpi, lat_gpi = self.target_grid.gpi2lonlat(gpi)
                            df_gpi = data[gpi]

                            # drop index duplicate(s) (to avoid measurements at the same time)
                            df_gpi = df_gpi.loc[~df_gpi.index.duplicated(keep='first')]

                            if df_gpi is not None:
                                if not df_gpi.empty:

                                    series_gpi, time_diff_gpi, time_idx_gpi = df_selecting_step(df_gpi, timestamp)

                                    hours_diff_gpi = time_diff_gpi / np.timedelta64(1, 'h')
                                    time_gpi = series_gpi.name
                                    jdate_gpi =series_gpi.name.to_julian_date()

                                    series_dict = {'lat': lat_gpi, 'lon': lon_gpi, 'cell': cell, 'gpi': gpi, 'id': i,
                                                   'time_ref': timestamp, 'time_delta': time_diff_gpi, 'time': time_gpi,
                                                   'jdate_ref': jdate, 'hours_delta': hours_diff_gpi, 'jdate': jdate_gpi}

                                    for name_idx in series_gpi.index:
                                        value_idx = series_gpi[name_idx]
                                        series_dict[name_idx] = value_idx

                                else:
                                    series_dict = {'lat': lat_gpi, 'lon': lon_gpi, 'cell': cell, 'gpi': gpi, 'id': i,
                                                   'time_ref': timestamp, 'time_delta': pd.NaT, 'time': pd.NaT,
                                                   'jdate_ref': jdate, 'hours_delta': np.nan, 'jdate': np.nan}
                                    for name_idx in series_gpi.index:
                                        series_dict[name_idx] = np.nan
                            else:
                                series_dict = {'lat': lat_gpi, 'lon': lon_gpi, 'cell': cell, 'gpi': gpi, 'id': i,
                                               'time_ref': timestamp, 'time_delta': pd.NaT, 'time': pd.NaT,
                                               'jdate_ref': jdate, 'hours_delta': np.nan, 'jdate': np.nan}
                                for name_idx in series_gpi.index:
                                    series_dict[name_idx] = np.nan

                            series_step = pd.Series(series_dict)
                            if df_points is None:
                                df_points = series_step.to_frame().T
                            else:
                                df_points = pd.concat([df_points, series_step.to_frame().T])

            df_points.set_index(index_name, inplace=True)
            write_points_data(os.path.join(self.pnt_path, pnt_filename), df_points)
        else:
            df_points = read_points_data(os.path.join(self.pnt_path, pnt_filename))

        return df_points

    def points_2_map(self, points, attrs=None, col_x='lon', col_y='lat', cols_excluded=None, no_data=0):

        if cols_excluded is None:
            cols_excluded = ['time_ref', 'time_delta', 'time']

        x_point = points[col_x].values
        y_point = points[col_y].values

        x_map = self.domain_obj['lons']
        y_map = self.domain_obj['lats']
        values_map = self.domain_obj['values']
        time_map = self.time

        cols = list(points.columns)
        cols.remove(col_x)
        cols.remove(col_y)

        for col_excluded in cols_excluded:
            if col_excluded in cols:
                cols.remove(col_excluded)

        ws_map = {}
        attr_map = {}
        for col in cols:

            # DEBUG START
            # col = 'swi_t_6_scaled'
            # DEBUG END

            if attrs:
                if col in attrs:
                    field = attrs[col]
                    attr_map[col] = field

            point = points[col]
            data_point = point.values

            idx_nans = np.where(np.isnan(np.array(data_point, dtype=float)))[0]

            if idx_nans.__len__() > 0:
                data_point_finite = np.delete(data_point, idx_nans)
                x_point_finite = np.delete(x_point, idx_nans)
                y_point_finite = np.delete(y_point, idx_nans)
            else:
                data_point_finite = data_point
                x_point_finite = x_point
                y_point_finite = y_point

            data_map_interp = interpolate_point2map(x_point_finite, y_point_finite, data_point_finite, x_map, y_map,
                                                    interp_method=self.interp_method,
                                                    interp_radius_lon=self.interp_radius_lon,
                                                    interp_radius_lat=self.interp_radius_lat)

            data_map_interp = deepcopy(data_map_interp.astype(float))

            idx_undef = np.where(values_map.ravel() <= no_data)[0]

            data_array_interp = data_map_interp.ravel()
            data_array_interp[idx_undef] = -9999.0

            data_map_select = np.reshape(data_array_interp, [x_map.shape[0], y_map.shape[1]])

            # debug plotting
            # data_2_map(data_map_interp, x_map, y_map, vmin=0, vmax=100)
            # data_2_map(data_map_select, x_map, y_map, vmin=0, vmax=100)
            # data_2_show(data_map_select)

            ws_map[col] = data_map_select

        dset_map = create_dset(time_map, ws_map, values_map, x_map, y_map, attrs=attr_map)

        return dset_map

    def write_data(self, dset, attrs=None):

        map_filename = self.map_filename_tmpl

        if self.map_updating is True:
            if os.path.exists(os.path.join(self.map_path, map_filename)):
                os.remove(os.path.join(self.map_path, map_filename))

        if not os.path.exists(os.path.join(self.map_path, map_filename)):
            write_dset(os.path.join(self.map_path, map_filename), dset, attrs=attrs)


# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Class to drive time series in contiguous format
class AscatDriverTS:

    def __init__(self, *args, **kwargs):

        # initialize input time-series path
        if 'ts_path_in' in kwargs:
            self.ts_path_in = kwargs.pop('ts_path_in')
        else:
            raise ValueError('input time-series path not defined')

        # initialize outcome time-series path
        if 'ts_path_out' in kwargs:
            self.ts_path_out = kwargs.pop('ts_path_out')
        else:
            raise ValueError('outcome time-series path not defined')

        # initialize input time-series filename template
        if 'ts_filename_tmpl_in' in kwargs:
            self.ts_filename_tmpl_in = kwargs.pop('ts_filename_tmpl_in')
        else:
            raise ValueError('input time-series filename template not defined')

        # initialize outcome time-series filename template
        if 'ts_filename_tmpl_out' in kwargs:
            self.ts_filename_tmpl_out = kwargs.pop('ts_filename_tmpl_out')
        else:
            raise ValueError('outcome time-series filename template not defined')

        # initialize data record grid path
        if 'grid_path_dr' in kwargs:
            self.grid_path_dr = kwargs.pop('grid_path_dr')
        else:
            raise ValueError('data record grid path not defined')

        # initialize data record grid filename
        if 'grid_filename_dr' in kwargs:
            self.grid_filename_dr = kwargs.pop('grid_filename_dr')
        else:
            raise ValueError('data record grid filename not defined')

        # initialize time start
        if 'time_start' in kwargs:
            self.time_start = kwargs.pop('time_start')
        else:
            self.time_start = None

        # initialize time end
        if 'time_end' in kwargs:
            self.time_end = kwargs.pop('time_end')
        else:
            self.time_end = None

        # initialize time frequency
        if 'time_frequency' in kwargs:
            self.time_frequency = kwargs.pop('time_frequency')
        else:
            self.time_frequency = 'D'

        # initialize variable name
        if 'var_name' in kwargs:
            self.var_name = kwargs.pop('var_name')
        else:
            self.var_name = ['sm', 'sm_noise', 'proc_flag', 'corr_flag']

        self.ts_grid = load_grid(os.path.join(self.grid_path_dr, self.grid_filename_dr))

        if (self.time_start is not None) and (self.time_end is not None):
            self.time_period = pd.date_range(start=self.time_start, end=self.time_end, freq=self.time_frequency)
        else:
            self.time_period = None

    def get_data(self, cell):

        ts_filename_def_in = self.ts_filename_tmpl_in % cell

        ws = read_analysis_data(os.path.join(self.ts_path_in, ts_filename_def_in))

        return ws

    def assemble_data(self, ws):

        ts_vars = self.var_name_scaled + self.var_name

        ws_data_assembled, ws_attrs_assembled = assemble_data_contiguous(
            ws, self.ts_grid, ts_vars, dates_ts=self.time_period)
        return ws_data_assembled, ws_attrs_assembled

    def gpi_2_cell(self, gpi):
        return self.ts_grid.gpi2cell(gpi)

    def write_data(self, ws_data, ws_attrs):

        if ws_data:
            gpis = list(np.asarray(ws_data['location_id'], dtype=int))
            cell = int(np.unique(self.gpi_2_cell(gpis))[0])

            ts_filename_def = self.ts_filename_tmpl % cell

            write_cell_data(os.path.join(self.ts_path, ts_filename_def), ws_data, ws_attrs)

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Class to analyze Ascat time-series
class AscatDriverAnalysis:

    def __init__(self, *args, **kwargs):

        # initialize input time-series path
        if 'ts_path' in kwargs:
            self.ts_path = kwargs.pop('ts_path')
        else:
            raise ValueError('time-series path not defined')

        # initialize input time-series filename template
        if 'ts_filename_tmpl' in kwargs:
            self.ts_filename_tmpl = kwargs.pop('ts_filename_tmpl')
        else:
            raise ValueError('time-series filename template not defined')

        # initialize grid path
        if 'grid_path' in kwargs:
            self.grid_path = kwargs.pop('grid_path')
        else:
            raise ValueError('grid path not defined')

        # initialize grid filename
        if 'grid_filename' in kwargs:
            self.grid_filename = kwargs.pop('grid_filename')
        else:
            raise ValueError('grid filename not defined')

        self.target_grid = load_grid(os.path.join(self.grid_path, self.grid_filename))

        # initialize soil moisture variable name
        if 'var_sm' in kwargs:
            self.var_sm = kwargs.pop('var_sm')
        else:
            self.var_sm = 'sm'

        # initialize swi raw variable name
        if 'var_swi_raw_tmpl' in kwargs:
            self.var_swi_raw_tmpl = kwargs.pop('var_swi_raw_tmpl')
        else:
            self.var_swi_raw_tmpl = ['swi_t_06', 'swi_t_12', 'swi_t_32']

        # initialize swi scaled variable name
        if 'var_swi_scaled_tmpl' in kwargs:
            self.var_swi_scaled_tmpl = kwargs.pop('var_swi_scaled_tmpl')
        else:
            self.var_swi_scaled_tmpl = ['swi_scaled_t_06', 'swi_scaled_t_12', 'swi_scaled_t_32']

        # initialize soil moisture ctime integer list
        if 'var_swi_ctime' in kwargs:
            self.var_swi_ctime = kwargs.pop('var_swi_ctime')
        else:
            self.var_swi_ctime = [6, 12, 32]

        # initialize scaling method
        if 'var_scaling_method' in kwargs:
            self.scaling_method = kwargs.pop('var_scaling_method')

            if hasattr(scaling_methods_external, self.scaling_method):
                self.scaling_method_function = getattr(scaling_methods_external, self.scaling_method)
            elif self.scaling_method in list(get_scaling_method_lut().keys()):
                self.scaling_method_function = get_scaling_function(self.scaling_method)
            else:
                self.scaling_method_function = None
        else:
            self.scaling_method_function = None

        if self.scaling_method_function is not None:
            self.scaling_method_args = list(signature(self.scaling_method_function).parameters.keys()).__len__()
        else:
            self.scaling_method_args = None

    def analyze_data_vars_2(self, nrt_ts, dr_ts_obs):

        if (self.var_sm in nrt_ts) and (self.var_sm in dr_ts_obs):

            # Get julian dates of time series
            nrt_jd = nrt_ts[self.var_sm].index.to_julian_date().get_values()
            # nrt_jd = nrt_ts[self.var_sm].index.to_julian_date().to_numpy()
            dr_jd_obs = dr_ts_obs[self.var_sm].index.to_julian_date().get_values()
            # dr_jd_obs = dr_ts_obs[self.var_sm].index.to_julian_date().to_numpy()

            nrt_ts[self.var_sm] = nrt_ts[self.var_sm].dropna()
            dr_ts_obs[self.var_sm] = dr_ts_obs[self.var_sm].dropna()

            # Get values of time series
            nrt_values = nrt_ts[self.var_sm].values.astype(np.float64)
            dr_values_obs = dr_ts_obs[self.var_sm].values.astype(np.float64)

            # Apply filter to compute swi
            for ctime, var_swi_raw, var_swi_scaled in zip(
                    self.var_swi_ctime, self.var_swi_raw_tmpl, self.var_swi_scaled_tmpl):

                # Compute swi
                nrt_ts[var_swi_raw] = exp_filter(nrt_values, nrt_jd, ctime=ctime)
                dr_ts_obs[var_swi_raw] = exp_filter(dr_values_obs, dr_jd_obs, ctime=ctime)

                if self.var_scaling_method_function is not None:
                    nrt_ts[var_swi_scaled] = self.var_scaling_method_function(
                        nrt_ts[var_swi_raw], dr_ts_obs[var_swi_raw])

            ws = nrt_ts

        else:
            ws = None

        return ws

    def analyze_data_vars_3(self, nrt_ts, dr_ts_obs, dr_ts_mod, var_ts_mod=None):

        if (self.var_sm in nrt_ts) and (self.var_sm in dr_ts_obs):

            # Get julian dates of time series
            nrt_jd = nrt_ts[self.var_sm].index.to_julian_date().get_values()
            dr_jd_obs = dr_ts_obs[self.var_sm].index.to_julian_date().get_values()

            nrt_ts[self.var_sm] = nrt_ts[self.var_sm].dropna()
            dr_ts_obs[self.var_sm] = dr_ts_obs[self.var_sm].dropna()

            # Get values of time series
            nrt_values = nrt_ts[self.var_sm].values.astype(np.float64)
            dr_values_obs = dr_ts_obs[self.var_sm].values.astype(np.float64)

            # Apply filter to compute swi
            for ctime, var_mod, var_swi_raw, var_swi_scaled in zip(
                    self.var_swi_ctime, var_ts_mod, self.var_swi_raw_tmpl, self.var_swi_scaled_tmpl):

                # Compute swi
                nrt_ts[var_swi_raw] = exp_filter(nrt_values, nrt_jd, ctime=ctime)
                dr_ts_obs[var_swi_raw] = exp_filter(dr_values_obs, dr_jd_obs, ctime=ctime)

                # Compute scaled variable(s)
                if self.scaling_method_function is not None:

                    nrt_ts[var_swi_scaled] = self.scaling_method_function(
                        nrt_ts[var_swi_raw], dr_ts_obs[var_swi_raw], dr_ts_mod[var_mod])

                    # nrt_values_scaled = nrt_ts[var_swi_scaled].values
                    # nrt_values_raw = nrt_ts[var_swi_raw].values

            ws = nrt_ts

        else:
            ws = None

        return ws

    def gpi_2_cell(self, gpi):

        return self.target_grid.gpi2cell(gpi)

    def write_empty(self, cell):

        ts_filename_def = self.ts_filename_tmpl % cell
        write_analysis_data(os.path.join(self.ts_path, ts_filename_def), None)

    def write_data(self, ws):

        if ws:

            gpis = list(ws.keys())
            cell = int(np.unique(self.gpi_2_cell(gpis))[0])
            ts_filename_def = self.ts_filename_tmpl % cell

            write_analysis_data(os.path.join(self.ts_path, ts_filename_def), ws)

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Class to convert Ascat time-series
class AscatDriverConversion:

    def __init__(self, *args, **kwargs):

        # initialise input time-series paths
        if 'ts_path_in' in kwargs:
            self.ts_path_in = kwargs.pop('ts_path_in')
        else:
            raise ValueError('input time-series path not defined')

        # initialise outcome time-series paths
        if 'ts_path_out' in kwargs:
            self.ts_path_out = kwargs.pop('ts_path_out')
        else:
            raise ValueError('outcome time-series path not defined')

        # initialise input filename template
        if 'ts_filename_tmpl_in' in kwargs:
            self.ts_filename_tmpl_in = kwargs.pop('ts_filename_tmpl_in')
        else:
            raise ValueError('input time-series filename template not defined')

        # initialise output filename template
        if 'ts_filename_tmpl_out' in kwargs:
            self.ts_filename_tmpl_out = kwargs.pop('ts_filename_tmpl_out')
        else:
            raise ValueError('input time-series filename template not defined')

        # initialise grid path
        if 'grid_path' in kwargs:
            self.grid_path = kwargs.pop('grid_path')
        else:
            raise ValueError('grid path not defined')

        # initialise grid filename
        if 'grid_filename' in kwargs:
            self.grid_filename = kwargs.pop('grid_filename')
        else:
            raise ValueError('grid filename not defined')

        # initialise parameters list
        if 'parameters' in kwargs:
            self.parameters = kwargs.pop('parameters')
        else:
            self.parameters = ['sm']

        self.target_grid = load_grid(os.path.join(self.grid_path, self.grid_filename))
        self.target_cells = np.unique(self.target_grid.activearrcell)

        self.cell = None

    # Method to get data from netcdf file
    def get_data(self, cell):

        # Set cell
        self.cell = cell

        # Iterate over filename(s)
        ws = []
        for ascat_path_in, ascat_filename_tmpl_in in zip(self.ts_path_in, self.ts_filename_tmpl_in):

            ascat_filename_def_in = ascat_filename_tmpl_in % cell

            # Check file availability
            if os.path.exists(os.path.join(ascat_path_in, ascat_filename_def_in)):

                # Read data
                data, var_attrs, global_attrs = read_cell_data(
                    os.path.join(ascat_path_in, ascat_filename_def_in), self.parameters)
                ws.append(data)

        return ws

    # Method to assemble data
    def assemble_data(self, data):

        gpis, lons, lats = self.target_grid.grid_points_for_cell(self.cell)
        data_assembled, attrs_assembled = assemble_data_obs(data, gpis, self.parameters)
        return data_assembled, attrs_assembled

    # Method to write data to netcdf file
    def write_data(self, data, attrs_data, attrs_file=None):

        ts_filename_def_out = self.ts_filename_tmpl_out % self.cell

        if data:
            write_cell_data(os.path.join(self.ts_path_out, ts_filename_def_out),
                            data, attrs_data, attrs_file, time_dim_name='obs')

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Class to wrap ASCAT dr time-series
class AscatDriverDR(AscatDriverSsmCdr):

    def __init__(self, *args, **kwargs):

        # initialise static layer paths
        if 'ts_path' in kwargs:
            self.ts_path = kwargs.pop('ts_path')
        else:
            raise ValueError('time-series path not defined')

        # initialise static layer paths
        if 'ts_filename_tmpl' in kwargs:
            self.ts_filename_tmpl = kwargs.pop('ts_filename_tmpl')
        else:
            raise ValueError('time-series filename template not defined')

        # initialise static layer paths
        if 'grid_path' in kwargs:
            self.grid_path = kwargs.pop('grid_path')
        else:
            raise ValueError('grid path not defined')

        # initialise static layer paths
        if 'grid_filename' in kwargs:
            self.grid_filename = kwargs.pop('grid_filename')
        else:
            raise ValueError('grid filename not defined')

        # initialise static layer paths
        if 'ts_type_ref' in kwargs:
            self.ts_type_ref = kwargs.pop('ts_type_ref')
        else:
            self.ts_type_ref = np.nan

        # variable valid range
        self.var_sm_range = [0, 100]

        super(AscatDriverDR, self).__init__(cdr_path=self.ts_path, grid_path=self.grid_path,
                                            cdr_tmpl_filename=self.ts_filename_tmpl,
                                            grid_filename=self.grid_filename,
                                            **kwargs)

    def read_ts(self, *args, **kwargs):

        try:
            ts_obj = super(AscatDriverDR, self).read(*args, **kwargs)
            ts = ts_obj.data

            ts['type_ref'] = self.ts_type_ref

            if ts.size == 0:
                ts = pd.DataFrame()
            else:
                ts = ts[ts['sm'].between(self.var_sm_range[0], self.var_sm_range[1])]

        except Exception as ex:

            ts = pd.DataFrame()

        return ts


# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Class to wrap ASCAT nrt time-series
class AscatDriverNRT(AscatSsmCdr):

    def __init__(self, *args, **kwargs):

        # initialise static layer paths
        if 'ts_path' in kwargs:
            self.ts_path = kwargs.pop('ts_path')
        else:
            raise ValueError('time-series path not defined')

        # initialise static layer paths
        if 'ts_filename_tmpl' in kwargs:
            self.ts_filename_tmpl = kwargs.pop('ts_filename_tmpl')
        else:
            raise ValueError('time-series filename template not defined')

        # initialise static layer paths
        if 'grid_path' in kwargs:
            self.grid_path = kwargs.pop('grid_path')
        else:
            raise ValueError('grid path not defined')

        # initialise static layer paths
        if 'grid_filename' in kwargs:
            self.grid_filename = kwargs.pop('grid_filename')
        else:
            raise ValueError('grid filename not defined')

        # variable valid range
        self.var_sm_range = [0, 100]

        super(AscatDriverNRT, self).__init__(cdr_path=self.ts_path, grid_path=self.grid_path,
                                             grid_filename=self.grid_filename,
                                             **kwargs)

    def read_ts(self, *args, **kwargs):

        try:
            ts_obj = super(AscatDriverNRT, self).read(*args, **kwargs)
            ts = ts_obj.data

            if ts.size == 0:
                ts = pd.DataFrame()
            else:
                ts = ts[ts['sm'].between(self.var_sm_range[0], self.var_sm_range[1])]

        except Exception as ex:

            ts = pd.DataFrame()

        return ts

# ----------------------------------------------------------------------------------------------------------------------
