# ----------------------------------------------------------------------------------------------------------------------
# Library
import os

import numpy as np
import pandas as pd

from inspect import signature
from copy import deepcopy
from pygeogrids import BasicGrid
from pygeogrids.netcdf import load_grid, save_grid

from pytesmo.scaling import get_scaling_function, get_scaling_method_lut

from src.hyde.algorithm.geo.satellite.hsaf.lib_ascat_geo import load_domain
from src.hyde.algorithm.time.satellite.hsaf.lib_ascat_time import df_selecting_step
import src.hyde.algorithm.analysis.satellite.hsaf.lib_ascat_analysis as scaling_methods_external
from src.hyde.algorithm.analysis.satellite.hsaf.lib_ascat_analysis import interpolate_grid2map

from src.hyde.algorithm.io.satellite.hsaf.lib_ascat_io_mod import assemble_data_mod, assemble_data_contiguous
from src.hyde.algorithm.io.satellite.hsaf.lib_ascat_io_generic import write_cell_data, write_analysis_data, \
    read_analysis_data, write_points_data, read_points_data, read_dset, create_dset, write_dset
from src.hyde.dataset.satellite.ascat.lib_ascat_driver_interface_mod import AscatDs, AscatTs

# Debug method(s)
from src.hyde.algorithm.geo.satellite.hsaf.lib_ascat_geo import data_2_map, data_2_show
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Class to drive data in gridded format
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

        # initialize domain path
        if 'domain_path' in kwargs:
            self.domain_path = kwargs.pop('domain_path')
        else:
            raise ValueError('domain path not defined')

        # initialize domain filename
        if 'domain_filename' in kwargs:
            self.domain_filename = kwargs.pop('domain_filename')
        else:
            raise ValueError('reference filename not defined')

        self.ts_grid = load_grid(os.path.join(self.grid_path, self.grid_filename))
        self.domain_grid, self.domain_obj = load_domain(os.path.join(self.domain_path, self.domain_filename))

    def get_points(self, cells, index_name='gpi'):

        if self.pnt_updating is True:
            if os.path.exists(os.path.join(self.pnt_path, self.pnt_filename_tmpl)):
                os.remove(os.path.join(self.pnt_path, self.pnt_filename_tmpl))

        if not os.path.exists(os.path.join(self.pnt_path, self.pnt_filename_tmpl)):

            df_points = None
            for cell in cells:

                ts_filename_def = self.ts_filename_tmpl % cell

                data = read_analysis_data(os.path.join(self.ts_path, ts_filename_def))
                gpis = list(data.keys())
                timestamp = pd.Timestamp(self.time)
                jdate = timestamp.to_julian_date()

                for i, gpi in enumerate(gpis):

                    lon_gpi, lat_gpi = self.ts_grid.gpi2lonlat(gpi)
                    df_gpi = data[gpi]
                    vars_gpi = list(df_gpi.columns)

                    # drop index duplicate(s) (to avoid measurements at the same time)
                    df_gpi = df_gpi.loc[~df_gpi.index.duplicated(keep='first')]

                    if df_gpi is not None:
                        if not df_gpi.empty:

                            series_gpi, time_diff_gpi, time_idx_gpi = df_selecting_step(df_gpi, timestamp)

                            hours_diff_gpi = time_diff_gpi / np.timedelta64(1, 'h')
                            time_gpi = series_gpi.name
                            jdate_gpi = series_gpi.name.to_julian_date()

                            series_dict = {'lat': lat_gpi, 'lon': lon_gpi, 'cell': cell, 'gpi': gpi, 'id': i,
                                           'time_ref': timestamp, 'time_delta': time_diff_gpi, 'time': time_gpi,
                                           'jdate_ref': jdate, 'hours_delta': hours_diff_gpi, 'jdate': jdate_gpi}

                            for var_gpi in vars_gpi:
                                value_idx = series_gpi[var_gpi]
                                series_dict[var_gpi] = value_idx

                        else:
                            series_dict = {'lat': lat_gpi, 'lon': lon_gpi, 'cell': cell, 'gpi': gpi, 'id': i,
                                           'time_ref': timestamp, 'time_delta': pd.NaT, 'time': pd.NaT,
                                           'jdate_ref': jdate, 'hours_delta': np.nan, 'jdate': np.nan}
                            for var_gpi in vars_gpi:
                                series_dict[var_gpi] = np.nan
                    else:
                        series_dict = {'lat': lat_gpi, 'lon': lon_gpi, 'cell': cell, 'gpi': gpi, 'id': i,
                                       'time_ref': timestamp, 'time_delta': pd.NaT, 'time': pd.NaT,
                                       'jdate_ref': jdate, 'hours_delta': np.nan, 'jdate': np.nan}
                        for var_gpi in vars_gpi:
                            series_dict[var_gpi] = np.nan

                    series_step = pd.Series(series_dict)
                    if df_points is None:
                        df_points = series_step.to_frame().T
                    else:
                        df_points = pd.concat([df_points, series_step.to_frame().T], sort=True)

            df_points.set_index(index_name, inplace=True)
            write_points_data(os.path.join(self.pnt_path, self.pnt_filename_tmpl), df_points)
        else:
            df_points = read_points_data(os.path.join(self.pnt_path, self.pnt_filename_tmpl))

        return df_points

    def points_2_map(self, points, attrs=None, col_x='lon', col_y='lat', cols_excluded=None, no_data=0):

        if cols_excluded is None:
            cols_excluded = ['time_ref', 'time_delta', 'time']

        x_point = points[col_x].values
        y_point = points[col_y].values

        x_map = self.domain_obj['lons']
        y_map = self.domain_obj['lats']
        values_map = self.domain_obj['values'].astype(float)
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

            data_map_interp = interpolate_grid2map(x_point_finite, y_point_finite, data_point_finite, x_map, y_map)
            data_map_interp = deepcopy(data_map_interp.astype(float))

            idx_undef = np.where(values_map.ravel() <= no_data)[0]

            data_array_interp = data_map_interp.ravel()
            data_array_interp[idx_undef] = -9999.0
            data_map_select = np.reshape(data_array_interp, [x_map.shape[0], y_map.shape[1]])

            # debug plotting
            # data_2_map(data_map_select, x_map, y_map)
            # data_2_map(data_map_drop, x_map, y_map)
            # data_2_show(data_map_select)

            ws_map[col] = data_map_select

        dset_map = create_dset(time_map, ws_map, values_map, x_map, y_map, attrs=attr_map)

        return dset_map

    def write_data(self, dset, attrs=None):

        if self.map_updating is True:
            if os.path.exists(os.path.join(self.map_path, self.map_filename_tmpl)):
                os.remove(os.path.join(self.map_path, self.map_filename_tmpl))

        if not os.path.exists(os.path.join(self.map_path, self.map_filename_tmpl)):
            write_dset(os.path.join(self.map_path, self.map_filename_tmpl), dset, attrs=attrs)

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Class to drive time series in contiguous format
class AscatDriverTS:

    def __init__(self, *args, **kwargs):

        # initialize analysis path
        if 'analysis_path' in kwargs:
            self.analysis_path = kwargs.pop('analysis_path')
        else:
            raise ValueError('analysis path not defined')

        # initialize analysis filename template
        if 'analysis_filename_tmpl' in kwargs:
            self.analysis_filename_tmpl = kwargs.pop('analysis_filename_tmpl')
        else:
            raise ValueError('analysis filename template not defined')

        # initialize time-series path
        if 'ts_path' in kwargs:
            self.ts_path = kwargs.pop('ts_path')
        else:
            raise ValueError('time-series path not defined')

        # initialize time-series filename template
        if 'ts_filename_tmpl' in kwargs:
            self.ts_filename_tmpl = kwargs.pop('ts_filename_tmpl')
        else:
            raise ValueError('time-series filename template not defined')

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

        # initialize scaled data record grid path
        if 'grid_path_dr_scaled' in kwargs:
            self.grid_path_dr_scaled = kwargs.pop('grid_path_dr_scaled')
        else:
            raise ValueError('scaled data record grid path not defined')

        # initialize scaled data record grid filename
        if 'grid_filename_dr_scaled' in kwargs:
            self.grid_filename_dr_scaled = kwargs.pop('grid_filename_dr_scaled')
        else:
            raise ValueError('scaled data record grid filename not defined')

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
            self.var_name = ['var_0_7', 'var_0_28', 'var_0_100']

        # initialize scaled variable name(s)
        if 'var_name_scaled' in kwargs:
            self.var_name_scaled = kwargs.pop('var_name_scaled')
        else:
            self.var_name_scaled = ['var_scaled_0_7', 'var_scaled_0_28', 'var_scaled_0_100']

        self.ts_grid = load_grid(os.path.join(self.grid_path_dr, self.grid_filename_dr))

        if not os.path.exists(os.path.join(self.grid_path_dr_scaled, self.grid_filename_dr_scaled)):
            save_grid(os.path.join(self.grid_path_dr_scaled, self.grid_filename_dr_scaled), self.ts_grid)

        if (self.time_start is not None) and (self.time_end is not None):
            self.time_period = pd.date_range(start=self.time_start, end=self.time_end, freq=self.time_frequency)
        else:
            self.time_period = None

    def get_data(self, cell):

        analysis_filename_def = self.analysis_filename_tmpl % cell

        ws = read_analysis_data(os.path.join(self.analysis_path, analysis_filename_def))

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
# Class to drive analysis
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

        # initialize variable name
        if 'var_name' in kwargs:
            self.var_name = kwargs.pop('var_name')
        else:
            self.var_name = ['var_0_7', 'var_0_28', 'var_0_100']

        # initialize scaled variable name(s)
        if 'var_name_scaled' in kwargs:
            self.var_name_scaled = kwargs.pop('var_name_scaled')
        else:
            self.var_name_scaled = ['var_scaled_0_7', 'var_scaled_0_28', 'var_scaled_0_100']

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

        self.ts_grid = load_grid(os.path.join(self.grid_path, self.grid_filename))

    def analyze_data(self, nrt_ts, dr_ts):

        for var_name, var_name_scaled in zip(self.var_name, self.var_name_scaled):

            if (var_name in nrt_ts) and (var_name in dr_ts):

                # Filter data using finite values
                nrt_ts[var_name] = nrt_ts[var_name].dropna()
                dr_ts[var_name] = dr_ts[var_name].dropna()

                # Get values of time series
                nrt_ts[var_name] = nrt_ts[var_name].values.astype(np.float64)
                dr_ts[var_name] = dr_ts[var_name].values.astype(np.float64)

                # Apply scaling method (if defined correctly)
                if self.scaling_method_function is not None:
                    nrt_ts[var_name_scaled] = self.scaling_method_function(
                        nrt_ts[var_name], dr_ts[var_name])
        return nrt_ts

    def gpi_2_cell(self, gpi):

        return self.ts_grid.gpi2cell(gpi)

    def write_data(self, ws):

        gpis = list(ws.keys())
        cell = int(np.unique(self.gpi_2_cell(gpis))[0])

        ts_filename_def = self.ts_filename_tmpl % cell

        write_analysis_data(os.path.join(self.ts_path, ts_filename_def), ws)


# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Class to drive data record reading
class AscatDriverDR(AscatTs):

    # Method to init class
    def __init__(self, **kwargs):

        # initialize data record path
        if "ts_path" in kwargs:
            self.ts_path = kwargs.pop('ts_path')
        else:
            raise ValueError('data record path not defined')

        # initialise static layer paths
        if 'ts_filename_tmpl' in kwargs:
            self.ts_filename_tmpl = kwargs.pop('ts_filename_tmpl')
        else:
            raise ValueError('data record filename template not defined')

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

        if 'scale_factor'in kwargs:
            self.var_scale_factor = kwargs.pop('scale_factor')
        else:
            raise ValueError('scale factor not defined')

        if 'valid_range' in kwargs:
            self.var_range = kwargs.pop('valid_range')
        else:
            raise ValueError('valid range not defined')

        self.ts_grid = load_grid(os.path.join(self.grid_path, self.grid_filename))

        self.ts_filename_format = os.path.splitext(self.ts_filename_tmpl)[0]

        super(AscatDriverDR, self).__init__(ts_path=self.ts_path, ts_name=self.ts_filename_format,
                                            grid_path=self.grid_path, **kwargs)

    # Method to read time-series
    def read_ts(self, *args, **kwargs):

        try:

            ts = super(AscatDriverDR, self).read(*args)

            if ts.size == 0:
                ts = pd.DataFrame()
            else:

                for var in list(ts.columns):
                    ts[var] = ts[var] * self.var_scale_factor
                    ts = ts[ts[var].between(self.var_range[0], self.var_range[1])]

        except Exception as e:

            ts = pd.DataFrame()

        return ts

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Class to drive nrt reading
class AscatDriverNRT(AscatTs):

    # Method to init class
    def __init__(self, **kwargs):

        # initialize data record path
        if "ts_path" in kwargs:
            self.ts_path = kwargs.pop('ts_path')
        else:
            raise ValueError('nrt path not defined')

        # initialise static layer paths
        if 'ts_filename_tmpl' in kwargs:
            self.ts_filename_tmpl = kwargs.pop('ts_filename_tmpl')
        else:
            raise ValueError('nrt filename template not defined')

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

        if 'scale_factor'in kwargs:
            self.var_scale_factor = kwargs.pop('scale_factor')
        else:
            raise ValueError('scale factor not defined')

        if 'valid_range'in kwargs:
            self.var_range = kwargs.pop('valid_range')
        else:
            raise ValueError('valid range not defined')

        self.var_n = 1

        self.ts_filename_format = os.path.splitext(self.ts_filename_tmpl)[0]

        super(AscatDriverNRT, self).__init__(ts_path=self.ts_path, ts_name=self.ts_filename_format, **kwargs)

    # Method to read time-series
    def read_ts(self, *args, **kwargs):

        try:

            ts = super(AscatDriverNRT, self).read(*args)
            ts = ts.head(n=self.var_n)

            if ts.size == 0:
                ts = pd.DataFrame()
            else:

                for var in list(ts.columns):
                    ts[var] = ts[var] * self.var_scale_factor
                    ts = ts[ts[var].between(self.var_range[0], self.var_range[1])]

        except Exception as e:

            ts = pd.DataFrame()

        return ts

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Class to drive Ascat time-series conversion
class AscatDriverConversion(AscatDs):

    def __init__(self, *args, **kwargs):

        # Define time and time format
        self.time = args[0]

        # initialise input data path
        if 'data_path_in' in kwargs:
            self.data_path_in = kwargs.pop('data_path_in')
        else:
            raise ValueError('input data path not defined')

        # initialise input filename template
        if 'data_filename_tmpl_in' in kwargs:
            self.data_filename_tmpl_in = kwargs.pop('data_filename_tmpl_in')
        else:
            raise ValueError('input data filename template not defined')

        # initialise outcome data paths
        if 'data_path_out' in kwargs:
            self.data_path_out = kwargs.pop('data_path_out')
        else:
            raise ValueError('outcome data path not defined')

        # initialise outcome filename template
        if 'data_filename_tmpl_out' in kwargs:
            self.data_filename_tmpl_out = kwargs.pop('data_filename_tmpl_out')
        else:
            raise ValueError('outcome data filename template not defined')

        # initialise grid path
        if 'grid_path_nrt' in kwargs:
            self.grid_path_nrt = kwargs.pop('grid_path_nrt')
        else:
            raise ValueError('grid path data record not defined')

        # initialise grid filename
        if 'grid_filename_nrt' in kwargs:
            self.grid_filename_nrt = kwargs.pop('grid_filename_nrt')
        else:
            raise ValueError('grid filename not defined')

        # initialise grid path
        if 'grid_path_reference' in kwargs:
            self.grid_path_reference = kwargs.pop('grid_path_reference')
        else:
            raise ValueError('grid path reference not defined')

        # initialise grid filename
        if 'grid_filename_reference' in kwargs:
            self.grid_filename_reference = kwargs.pop('grid_filename_reference')
        else:
            raise ValueError('grid filename reference not defined')

        # initialise grid filename
        if 'parameters' in kwargs:
            self.parameters = kwargs.pop('parameters')
        else:
            self.parameters = ['var_0_7', 'var_0_28', 'var_0_100']

        if 'tmpl_tags' in kwargs:
            self.tmpl_tags = kwargs.pop('tmpl_tags')
        else:
            self.tmpl_tags = {}

        self.grid_reference = load_grid(os.path.join(self.grid_path_reference, self.grid_filename_reference))
        self.cells_reference = np.unique(self.grid_reference.activearrcell)

        self.grid_nrt = None

        super(AscatDriverConversion, self).__init__(self.data_path_in,
                                                    data_filename_tmpl=self.data_filename_tmpl_in,
                                                    parameter=self.parameters,
                                                    array_1D=True,
                                                    path_grid=self.grid_path_nrt,
                                                    filename_grid=self.grid_filename_nrt)

    def get_data(self):

        obj = super(AscatDriverConversion, self).read(self.time)
        values = obj.data

        if self.grid_nrt is None:
            lons = obj.lon
            lats = obj.lat
            self.grid_nrt = BasicGrid(lons, lats)

        return values

    def assemble_data(self, data):

        gpis_lut = self.grid_nrt.calc_lut(self.grid_reference, max_dist=35000).data

        idx_selected = np.where(gpis_lut > 0)[0]
        gpis_selected = gpis_lut[idx_selected]

        lons_selected, lats_selected = self.grid_reference.gpi2lonlat(gpis_selected)

        data_assembled, attrs_assembled = assemble_data_mod(data, gpis_selected, lons_selected, lats_selected,
                                                            idxs=idx_selected,
                                                            time=self.time)
        return data_assembled, attrs_assembled

    def write_data(self, data, attrs_data, attrs_file=None):

        write_cell_data(os.path.join(self.data_path_out, self.data_filename_tmpl_out),
                        data, attrs_data, attrs_file)

# ----------------------------------------------------------------------------------------------------------------------
