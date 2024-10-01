# -------------------------------------------------------------------------------------
# Libraries
import numpy as np

from netCDF4 import num2date

# Definition(s)
time_units = 'days since 1858-11-17 00:00:00'
time_format = '%Y%m%d%H%M'

sm_var = 'sm'
sm_noise_var = 'sm_noise'
proc_flag_var = 'proc_flag'
corr_flag_var = 'corr_flag'

time_var = 'time'
lat_var = 'lat'
lon_var = 'lon'
alt_var = 'alt'
loc_ids_var = 'location_id'
loc_idx_var = 'locationIndex'
loc_lut_var = 'row_size'

loc_dim_name = 'locations'
obs_dim_name = 'obs'
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to organize data
def assemble_data_obs(data, gpis, parameters='sm'):

    if not isinstance(parameters, list):
        parameters = [parameters]

    # List of dynamic variable(s)
    vars_ts = parameters

    if not isinstance(data, list):
        data = [data]

    ws_data_assembled = {}
    ws_attrs_assembled = {}
    for var in vars_ts:

        values_ts_assembled = None
        time_ts_assembled = None
        row_ts_assembled = None

        idx_ts = np.array([])
        gpi_ts = np.array([])
        lon_ts = np.array([])
        lat_ts = np.array([])
        alt_ts = np.array([])
        count_ts = np.array([])

        for i, gpi in enumerate(gpis):

            values_ts = None
            time_ts = None
            row_ts = None

            for dset in data:

                name = str(var)
                values = dset[name][:].data

                time = dset[time_var][:].data

                loc = dset[loc_ids_var][:].data
                idx = dset[loc_idx_var][:].data
                lut = dset[loc_lut_var][:]

                lat = dset[lat_var][:]
                lon = dset[lon_var][:]
                alt = dset[alt_var][:]

                lut_cumsum = np.cumsum(lut)
                lut_diff = np.diff(np.insert(lut_cumsum, 0, 0))
                lut_end = lut_cumsum
                lut_start = lut_cumsum - lut_diff

                if gpi in loc:

                    idx_pos = np.where(gpi == loc)[0][0]

                    lut_start_loc = lut_start[idx_pos]
                    lut_end_loc = lut_end[idx_pos]

                    idx_loc = idx[idx_pos]
                    gpi_loc = loc[idx_pos]
                    lat_loc = lat[idx_pos]
                    lon_loc = lon[idx_pos]
                    alt_loc = alt[idx_pos].data

                    values_loc = values[lut_start_loc:lut_end_loc]
                    time_loc = time[lut_start_loc:lut_end_loc]

                    n_loc = values_loc.__len__()

                    if values_ts is None:
                        values_ts = np.array([])
                        time_ts = np.array([])
                        row_ts = np.array([])

                    time_ts = np.concatenate([time_ts, time_loc])
                    row_ts = np.concatenate([row_ts, np.asarray(n_loc * np.ones(1))])
                    values_ts = np.concatenate([values_ts, values_loc])

                    if gpi_loc not in gpi_ts:

                        if gpi_ts.size == 0:
                            idx_ts = np.array(idx_loc)
                            gpi_ts = np.array(gpi_loc)
                            lon_ts = np.array(lon_loc)
                            lat_ts = np.array(lat_loc)
                            alt_ts = np.array(alt_loc)
                            count_ts = np.array(i)
                        else:
                            idx_ts = np.append(idx_ts, idx_loc)
                            gpi_ts = np.append(gpi_ts, gpi_loc)
                            lon_ts = np.append(lon_ts, lon_loc)
                            lat_ts = np.append(lat_ts, lat_loc)
                            alt_ts = np.append(alt_ts, alt_loc)
                            count_ts = np.append(count_ts, i)

            if (values_ts is not None) and (time_ts is not None):

                idx_sort = np.argsort(time_ts)

                values_ts_sort = values_ts[idx_sort]
                time_ts_sort = time_ts[idx_sort]

                n_ts_sort = values_ts_sort.__len__()

                if values_ts_assembled is None:
                    values_ts_assembled = np.array([])
                    time_ts_assembled = np.array([])
                    row_ts_assembled = np.array([])

                time_ts_assembled = np.concatenate([time_ts_assembled, time_ts_sort])
                row_ts_assembled = np.concatenate([row_ts_assembled, np.asarray(n_ts_sort * np.ones(1))])
                values_ts_assembled = np.concatenate([values_ts_assembled, values_ts_sort])

        if values_ts_assembled is not None:

            ws_data_assembled[name] = values_ts_assembled

            if 'time' not in ws_data_assembled:
                date_ts_assembled = num2date(time_ts_assembled, units=time_units, calendar='standard')
                ws_data_assembled['time'] = date_ts_assembled
                ws_attrs_assembled['time'] = \
                    {'standard_name': 'time',
                     'long_name': 'time of measurement',
                     'units': time_units}

            if loc_lut_var not in ws_data_assembled:
                ws_data_assembled[loc_lut_var] = np.asarray(row_ts_assembled, dtype=int)
                ws_attrs_assembled[loc_lut_var] = \
                    {'long_name': 'number of observations at this location',
                     'sample_dimension': row_ts_assembled.__len__()}

            if lon_var not in ws_data_assembled:
                ws_data_assembled[lon_var] = lon_ts
            if lat_var not in ws_data_assembled:
                ws_data_assembled[lat_var] = lat_ts
            if alt_var not in ws_data_assembled:
                ws_data_assembled[alt_var] = alt_ts
            if loc_ids_var not in ws_data_assembled:
                ws_data_assembled[loc_ids_var] = gpi_ts
            if loc_idx_var not in ws_data_assembled:
                ws_data_assembled[loc_idx_var] = idx_ts

    return ws_data_assembled, ws_attrs_assembled
# -------------------------------------------------------------------------------------
