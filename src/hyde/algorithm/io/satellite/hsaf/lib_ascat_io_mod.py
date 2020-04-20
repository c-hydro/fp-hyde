# -------------------------------------------------------------------------------------
# Libraries
import numpy as np

from netCDF4 import Dataset

# Definition(s)
time_units = 'days since 1858-11-17 00:00:00'
time_format = '%Y%m%d%H%M'

time_var = 'time'
lat_var = 'lat'
lon_var = 'lon'
alt_var = 'alt'
loc_ids_var = 'location_id'
loc_idx_var = 'locationIndex'
loc_lut_var = 'row_size'

loc_dim_name = 'locations'
obs_dim_name = 'time'
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read cell data
def read_data_mod(filename, var_list='var_0_7'):

    # Variable(s) list
    if isinstance(var_list, str):
        var_list = [var_list]

    # Open file in nc format
    dset = Dataset(filename, mode='r')
    vars = dset.variables

    # Get global attributes
    file_attrs = {}
    for attr_name in dset.ncattrs():
        file_attrs[attr_name] = getattr(dset, attr_name)

    # Get registry data
    lons_dset = dset.variables[lon_var][:]
    lats_dset = dset.variables[lat_var][:]
    alts_dset = dset.variables[alt_var][:]

    # Get indexed variable(s)
    var_idx_dset = dset.variables[loc_idx_var][:]
    var_time_dset = dset.variables[time_var][:]
    var_gpis_dset = dset.variables[loc_ids_var][:]
    var_rows_dset = dset.variables[loc_lut_var][:]

    ws_data = {}
    ws_attrs = {}
    for var_name in vars:
        var_name = str(var_name)
        var_data_dset = dset.variables[var_name][:]

        if var_name in var_list:

            ws_data[var_name] = var_data_dset

            if time_var not in ws_data:
                ws_data[time_var] = var_time_dset
                ws_attrs[time_var] = \
                    {'standard_name': 'time',
                     'long_name': 'time of measurement',
                     'units': time_units}

            if loc_lut_var not in ws_data:
                ws_data[loc_lut_var] = np.asarray(var_rows_dset, dtype=int)
                ws_attrs[loc_lut_var] = \
                    {'long_name': 'number of observations at this location',
                     'sample_dimension': var_rows_dset.__len__()}

            if loc_ids_var not in ws_data:
                ws_data[loc_ids_var] = var_gpis_dset
            if loc_idx_var not in ws_data:
                ws_data[loc_idx_var] = var_idx_dset

            if lon_var not in ws_data:
                ws_data[lon_var] = lons_dset
            if lat_var not in ws_data:
                ws_data[lat_var] = lats_dset
            if alt_var not in ws_data:
                ws_data[alt_var] = alts_dset

    dset.close()

    return ws_data, ws_attrs, file_attrs

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to assemble data in contiguous format
def assemble_data_contiguous(data_ts, grid_ts, vars_ts=None, dates_ts=None):

    if vars_ts is None:
        vars_ts = ['var40', 'var_0_7']

    count_ts = np.array([])
    gpis_ts = np.array([])
    lons_ts = np.array([])
    lats_ts = np.array([])
    alts_ts = np.array([])
    time_ts = None

    n_gpi = data_ts.__len__()

    values_idx = []
    values_dict = {}
    for id, (gpi, data) in enumerate(data_ts.items()):

        lon, lat = grid_ts.gpi2lonlat(gpi)
        alt = -9999

        data = data_ts[gpi]
        count = data.index.__len__()

        if count > 0:

            values_idx.append(id)

            time_sort = None
            for var in vars_ts:

                values = data[var].values

                if values.size > 0:

                    times = data[var].index.to_pydatetime()

                    if dates_ts is None:
                        dates_ref = times
                        times_ref_list = [t.strftime(time_format) for t in times]
                    else:
                        dates_ref = dates_ts.to_pydatetime()
                        times_ref_list = [t.strftime(time_format) for t in dates_ref]

                    time_idx = []
                    times_list = [t.strftime(time_format) for t in times]
                    for time_step in times_list:
                        if time_step in times_ref_list:
                            ix = times_ref_list.index(time_step)
                            time_idx.append(ix)

                    idx_sort = np.argsort(times)
                    values_sort = values[idx_sort]

                    n_time = times_ref_list.__len__()

                    if time_ts is None:
                        time_ts = dates_ref

                    if time_ts.__len__() != times.__len__():
                        time_idx_check = []
                        time_ts_ref = [t.strftime(time_format) for t in dates_ref]
                        time_ts_check = [t.strftime(time_format) for t in times]
                        for time_check in time_ts_check:
                            if time_check in time_ts_ref:
                                ix = time_ts_ref.index(time_check)
                                time_idx_check.append(ix)
                        time_idx = time_idx_check

                    if time_sort is None:
                        time_sort = times[idx_sort]

                    if var not in values_dict:
                        values_2d = np.zeros([n_gpi, n_time])
                        values_2d[:, :] = -9999.0

                        values_2d[id, time_idx] = values_sort

                        values_dict[var] = {}
                        values_dict[var] = values_2d

                    else:
                        values_2d = values_dict[var]
                        values_2d[id, time_idx] = values_sort
                        values_dict[var] = values_2d
                else:

                    values_2d = values_dict[var]
                    values_2d[id, :] = -9999.0
                    values_dict[var] = values_2d

            gpis_ts = np.concatenate([gpis_ts, np.asarray(gpi * np.ones(1))])
            lons_ts = np.concatenate([lons_ts, np.asarray(lon * np.ones(1))])
            lats_ts = np.concatenate([lats_ts, np.asarray(lat * np.ones(1))])
            alts_ts = np.concatenate([alts_ts, np.asarray(alt * np.ones(1))])
            count_ts = np.concatenate([count_ts, np.asarray(count * np.ones(1))])

    n_loc = gpis_ts.__len__()
    locations = np.linspace(0, n_loc - 1, n_loc)

    if n_loc > 0:
        ws_data_assembled = {}
        ws_attrs_assembled = {}
        for var_name in values_dict:

            values_var = values_dict[var_name]
            values_var_selected = values_var[values_idx, :]
            ws_data_assembled[var_name] = values_var_selected

            if 'time' not in ws_data_assembled:
                ws_data_assembled['time'] = time_ts
                ws_attrs_assembled['time'] = \
                    {'standard_name': 'time',
                     'long_name': 'time of measurement',
                     'units': time_units}

            if loc_lut_var not in ws_data_assembled:
                ws_data_assembled[loc_lut_var] = count_ts
                ws_attrs_assembled[loc_lut_var] = \
                    {'long_name': 'number of observations at this location',
                     'sample_dimension': count_ts.__len__()}

            if lon_var not in ws_data_assembled:
                ws_data_assembled[lon_var] = lons_ts
            if lat_var not in ws_data_assembled:
                ws_data_assembled[lat_var] = lats_ts
            if alt_var not in ws_data_assembled:
                ws_data_assembled[alt_var] = alts_ts
            if loc_ids_var not in ws_data_assembled:
                ws_data_assembled[loc_ids_var] = gpis_ts
            if loc_idx_var not in ws_data_assembled:
                ws_data_assembled[loc_idx_var] = locations

    else:
        ws_data_assembled = None
        ws_attrs_assembled = None

    return ws_data_assembled, ws_attrs_assembled

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to assemble data
def assemble_data_mod(data, gpis, lons, lats, idxs=None, alts=None, time=None):

    n_loc = gpis.__len__()

    time_assembled = np.zeros([n_loc])
    row_assembled = np.zeros([n_loc])

    if time is not None:
        time_assembled[:] = time.strftime(time_format)
    if alts is None:
        alts = np.zeros([n_loc])
        alts[:] = np.nan

    row_assembled[:] = 1
    locations = np.linspace(0, n_loc -1, n_loc)

    ws_data_assembled = {}
    ws_attrs_assembled = {}
    for var_name in data:

        if idxs is None:
            ws_data_assembled[var_name] = data[var_name]
        else:
            ws_data_assembled[var_name] = data[var_name][idxs]

        if 'time' not in ws_data_assembled:
            ws_data_assembled['time'] = time_assembled
            ws_attrs_assembled['time'] = \
                {'standard_name': 'time',
                 'long_name': 'time of measurement',
                 'units': time_units}

        if loc_lut_var not in ws_data_assembled:
            ws_data_assembled[loc_lut_var] = np.asarray(row_assembled, dtype=int)
            ws_attrs_assembled[loc_lut_var] = \
                {'long_name': 'number of observations at this location',
                 'sample_dimension': row_assembled.__len__()}

        if lon_var not in ws_data_assembled:
            ws_data_assembled[lon_var] = lons
        if lat_var not in ws_data_assembled:
            ws_data_assembled[lat_var] = lats
        if alt_var not in ws_data_assembled:
            ws_data_assembled[alt_var] = alts
        if loc_ids_var not in ws_data_assembled:
            ws_data_assembled[loc_ids_var] = gpis
        if loc_idx_var not in ws_data_assembled:
            ws_data_assembled[loc_idx_var] = locations

    return ws_data_assembled, ws_attrs_assembled
# -------------------------------------------------------------------------------------
