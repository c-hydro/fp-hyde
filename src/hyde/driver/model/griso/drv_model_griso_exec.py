"""
Library Features:

Name:          drv_model_griso_generic
Author(s):     Andrea Libertino (andrea.libertino@cimafoundation.org)
               Flavio Pignone (flavio.pignone@cimafoundation.org)
Date:          '20211026'
Version:       '2.0.0'
"""

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Complete library
import numpy as np
import pyresample
import logging
from scipy.signal import correlate
from copy import deepcopy
import pandas as pd
from itertools import combinations
import xarray as xr
import matplotlib.pyplot as plt
from multiprocessing import Pool, Manager

from src.hyde.driver.model.griso.drv_model_griso_generic import deg2km, spheric, averageCells, cart2pol, sphericalFit

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# function for preparing griso input data
def GrisoPreproc(corrFin, lonGauge, latGauge, data_gauge, data_sat=None, Grid=None):

    logging.info(' ---> Compute grid...')
    # generate lat-lon grid
    lonGrid = np.around(Grid.lon.values, decimals=10)
    latGrid = np.around(Grid.lat.values, decimals=10)
    gridx, gridy = np.meshgrid(lonGrid, latGrid)
    grid = pyresample.geometry.GridDefinition(lats=gridy, lons=gridx)

    # grid step should be integer and divisible per 2
    passoKm = deg2km(latGrid[0], lonGrid[0], latGrid[1], lonGrid[0])
    pixel = np.round(corrFin / 2 / passoKm)
    if not pixel % 2 == 0:
        pixel = pixel + 1
    passoKm = corrFin / 2 / pixel

    logging.info(' ---> Grid step: ' + str(passoKm) + ' km')
    logging.info(' ---> Compute grid...DONE')

    logging.info(' ---> Grid point values...')

    # extract grid coordinates
    swath = pyresample.geometry.SwathDefinition(lons=lonGauge, lats=latGauge)
    _, is_valid, index_array, _ = pyresample.kd_tree.get_neighbour_info(
        source_geo_def=grid, target_geo_def=swath, radius_of_influence=np.Inf,
        neighbours=1)

    rPluvio, cPluvio = np.unravel_index(index_array, grid.shape)

    # if more rain gauges fall in the same cell they are averaged
    rPluvio_uniq, cPluvio_uniq, gauge_value = averageCells(rPluvio, cPluvio, data_gauge[is_valid])

    # calculate grid data for modified conditional merging
    if not data_sat is None:
        _, _, grid_value = averageCells(rPluvio, cPluvio, data_sat[is_valid])

        if Grid.lat.values[-1] < Grid.lat.values[0]:
            grid_rain = np.flipud(Grid['precip'].values)
        else:
            grid_rain = Grid['precip'].values
    else:
        grid_value = np.empty(gauge_value.shape)
        grid_rain = None

    mat_in = np.vstack((rPluvio_uniq, cPluvio_uniq, gauge_value, grid_value)).T
    gauge_codes = np.arange(1, gauge_value.shape[0] + 1, 1)
    # gridded nan values (related to gauges falling out of the radar radius) are queued, to be cutted off in the intepolation phase
    point_data = pd.DataFrame(mat_in[np.argsort(mat_in[:, 3])], index=gauge_codes, columns=["rPluvio", "cPluvio", "gauge_value", "grid_value"])
    # point_data = pd.DataFrame(mat_in, index=gauge_codes, columns=["rPluvio", "cPluvio", "gauge_value", "grid_value"])

    # generate grid with (equivalent) rain-gauge locations
    a2dPosizioni = np.squeeze(np.zeros(grid.shape))
    a2dPosizioni[point_data["rPluvio"].values.astype(np.int), point_data["cPluvio"].values.astype(np.int)] = gauge_codes

    logging.info(' ---> Grid point values...DONE')

    return point_data, a2dPosizioni, grid_rain, grid, passoKm

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# function for computing correlation, kernel and position of each rain gauge neighbourhood
def GrisoCorrel(row_gauge, col_gauge, corrFin, rs_field, cellsize_km, gauge_position_map, value_gauge, corr_type='fixed'):

    logging.info(' ---> Initialize correlation estimation...')

    global dist_km
    global corr_null_fit_window
    global corr_max_fit_window
    global gauge_pairs_map_window
    global df_gauge_ext
    global rs_field_ext
    global gauge_position_map_ext

    # Kernel features
    rs_null_threshold = 0                                          # Threshold for valid gridded data

    corr_null_radius_km = 5                                        # Minimum correlation (km)
    corr_max_radius_km = corrFin / 2                               # Maximum correlation (km)
    corr_max_radius_cells = int(corr_max_radius_km / cellsize_km)  # Maximum correlation (n cells) used also for buffer

    # Spherical variogram fixed parameters
    nugget = 0
    sill = 1

    # matrices of distances from the center of the GRISO windows
    y_arr, x_arr = np.mgrid[0:1+corr_max_radius_cells*2, 0:1+corr_max_radius_cells*2]
    dist_cells = np.sqrt((x_arr - corr_max_radius_cells) ** 2 + (y_arr - corr_max_radius_cells) ** 2)
    dist_km = dist_cells * cellsize_km
    bins_dist_km = np.round(dist_km, 4)

    if corr_type is not 'fixed':
        # calculate map of maximum number of pair for each cell of the GRISO window
        mask_window = np.where(bins_dist_km <= corrFin / 2, 1, 0)
        gauge_pairs_map_window = np.zeros_like(mask_window, dtype=np.int)

        for ind, (dove_y, dove_x) in enumerate(zip(np.where(mask_window==1)[0],np.where(mask_window==1)[1])):
            logging.info(' ---> Cell ' + str(ind) + ' of ' + str(len(np.where(mask_window==1)[0])))
            r = np.where(mask_window==1,cart2pol(x_arr-dove_y,y_arr-dove_x)[0]*cellsize_km,np.nan)
            r[r>corrFin/2] = np.nan
            gauge_pairs_map_window += np.where(r>0,1,0)

    rs_field_ext = np.pad(np.squeeze(rs_field), corr_max_radius_cells, 'constant', constant_values=np.nan)
    gauge_position_map_ext = np.pad(gauge_position_map, corr_max_radius_cells, 'constant', constant_values=0)
    row_gauge_ext = row_gauge + corr_max_radius_cells
    col_gauge_ext = col_gauge + corr_max_radius_cells
    df_gauge_ext = pd.DataFrame(np.vstack((row_gauge_ext,col_gauge_ext,value_gauge)).T, index=np.arange(1,len(value_gauge)+1,1), columns=["row","col","value"])

    corr_null_fit_window = spheric(dist_km, corr_null_radius_km, nugget, sill)
    corr_null_fit_window[dist_km > corr_null_radius_km] = 0
    corr_max_fit_window = spheric(dist_km, corr_max_radius_km, nugget, sill)
    corr_max_fit_window[dist_km > corr_max_radius_km] = 0

    logging.info(' ---> Initialize correlation estimation...DONE')

    logging.info(' ---> Estimate correlation features for ' + str(len(value_gauge)) + ' single grid cells...')

    dict_griso_settings = {"corr_null_radius_km": corr_null_radius_km, "corr_max_radius_km": corr_max_radius_km, "cellsize_km": cellsize_km, "rs_null_threshold": rs_null_threshold, "corr_type": corr_type}

    mp = False
    mp_mode = 'async'

    if mp is not True:
        dict_correlation_outcomes = {"dict_corr_fit_window": {}, "dict_gauge_position_map_ext_window": {},
                                     "dict_window_Rll_Cll": {}, "dict_range_fit": {}}
        for ind in df_gauge_ext.index.values:
            logging.info(' ---> Cell ' + str(ind) + ' of ' + str(len(value_gauge)))
            GrisoLocalKernel(ind, dict_griso_settings, dict_correlation_outcomes)
    else:
        cpu_n = 4
        manager = Manager()
        dict_correlation_outcomes = {}
        dict_correlation_outcomes["dict_corr_fit_window"] = manager.dict()
        dict_correlation_outcomes["dict_gauge_position_map_ext_window"] = manager.dict()
        dict_correlation_outcomes["dict_window_Rll_Cll"] = manager.dict()
        dict_correlation_outcomes["dict_range_fit"] = manager.dict()
        exec_pool = Pool(cpu_n)
        logging.info(' ---> Compute ' + str(len(value_gauge)) + ' cells in parallel mode')
        if mp_mode == 'sync':
            from functools import partial
            with Pool(processes=cpu_n, maxtasksperchild=1) as exec_pool:
                exec_pool.map(partial(GrisoLocalKernel, dict_griso_settings=dict_griso_settings, dict_correlation_outcomes=dict_correlation_outcomes), [ind for ind in df_gauge_ext.index.values], chunksize=20)
                exec_pool.close()
                exec_pool.join()
        elif mp_mode == 'async':
            for ind in df_gauge_ext.index.values:
                exec_pool.apply_async(GrisoLocalKernel, args=(ind, dict_griso_settings, dict_correlation_outcomes))
            exec_pool.close()
            exec_pool.join()

    correl_features = {'dict_window_Rll_Cll': dict_correlation_outcomes["dict_window_Rll_Cll"],
                       'dict_corr_fit_window' : dict_correlation_outcomes["dict_corr_fit_window"],
                       'dict_range_fit': dict_correlation_outcomes["dict_range_fit"],
                       'dict_gauge_position_map_ext_window':dict_correlation_outcomes["dict_gauge_position_map_ext_window"],
                       'dist': dist_km, 'rs_ext_field_size': gauge_position_map_ext.shape,
                       'corr_max_radius_cells' : corr_max_radius_cells}

    logging.info(' ---> Estimate correlation features...DONE')

    return correl_features

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
def GrisoLocalKernel(ind, dict_griso_settings, dict_correlation_outcomes):

    buffer = int(dict_griso_settings["corr_max_radius_km"]/dict_griso_settings["cellsize_km"])
    R = df_gauge_ext.loc[ind]["row"]
    C = df_gauge_ext.loc[ind]["col"]
    gauge_rain = df_gauge_ext.loc[ind]["value"]

    if dict_griso_settings["corr_type"] is 'fixed':
        corr_fit_window = corr_max_fit_window
        radius_fit = dict_griso_settings["corr_max_radius_km"]
    else:
        rs_window = deepcopy(rs_field_ext[int(R - buffer):int(R + buffer + 1), int(C - buffer):int(C + buffer + 1)])
        rs_window[dist_km > dict_griso_settings["corr_max_radius_km"]] = np.nan
        valid_pixel = rs_window[rs_window >= dict_griso_settings["rs_null_threshold"]]  # p0]

        # If the neighbourhood is complete (no border) and made of constant values
        if len(valid_pixel) == np.count_nonzero(~np.isnan(rs_window)) and all(
                valid_pixel == rs_window[buffer, buffer]) or np.nansum(rs_window)==0:
            corr_fit_window = deepcopy(corr_max_fit_window)
            radius_fit = dict_griso_settings["corr_max_radius_km"]

        # If there are less than 100 valix pixels in the surrounding of a station that recorded rainfall
        elif len(valid_pixel) < (100 / dict_griso_settings["cellsize_km"]) and gauge_rain > 0.2:
            corr_fit_window = deepcopy(corr_max_fit_window)
            radius_fit = dict_griso_settings["corr_max_radius_km"]

        # If there are more than 100 valid pixels in the surrounding of a station
        elif len(valid_pixel) > (100 / dict_griso_settings["cellsize_km"]):
            rs_field_norm_window = np.nan_to_num(rs_window - np.nanmean(rs_window), 0)
            gauge_pairs_map_window[gauge_pairs_map_window==0]=-1
            rs_field_corr = correlate(rs_field_norm_window, rs_field_norm_window, mode='full', method='auto')
            corr_sample_window = rs_field_corr[buffer:-buffer, buffer:-buffer] / gauge_pairs_map_window / np.nanvar(rs_window)
            corr_sample_window[corr_sample_window<0] = 0

            corr_sample_window[dist_km > (dict_griso_settings["corr_max_radius_km"])] = 0
            corr_fit_window, radius_fit = sphericalFit(dist_km,corr_sample_window,dict_griso_settings["corr_null_radius_km"],dict_griso_settings["corr_max_radius_km"], dict_griso_settings["corr_max_radius_km"]-dict_griso_settings["cellsize_km"], corr_null=corr_null_fit_window)
            corr_fit_window[dist_km > (dict_griso_settings["corr_max_radius_km"])] = 0
        else:
            corr_fit_window = deepcopy(corr_null_fit_window)
            radius_fit = dict_griso_settings["corr_null_radius_km"]

    corr_fit_window[corr_fit_window < 0.001] = 0

    gauge_position_map_ext_window = gauge_position_map_ext[int(R - buffer):int(R + buffer + 1),
                                    int(C - buffer):int(C + buffer + 1)].astype(int)
    Rll_Cll = np.array((int(R - buffer), int(C - buffer)))

    dict_correlation_outcomes["dict_corr_fit_window"][ind] = corr_fit_window
    dict_correlation_outcomes["dict_gauge_position_map_ext_window"][ind] = gauge_position_map_ext_window
    dict_correlation_outcomes["dict_window_Rll_Cll"][ind] = Rll_Cll
    dict_correlation_outcomes["dict_range_fit"][ind] = radius_fit

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# compute GRISO interpolation over the extended matrix
def GrisoInterpola(row_gauge, col_gauge, data, correl_features):

    # average null
    mu = 0

    # if rain gauge fall in radar null field remove the gauges from the correlation system
    row_gauge = row_gauge[~np.isnan(data)]
    col_gauge = col_gauge[~np.isnan(data)]
    data = data[~np.isnan(data)]

    logging.info(' ---> Write and solve system...')
    # Write system
    A = np.zeros([len(row_gauge) + 1, len(row_gauge) + 1])
    A[:, len(row_gauge)] = 1

    for k in np.arange(0, len(row_gauge)):
        corr = correl_features["dict_corr_fit_window"][k + 1]
        posiz = correl_features["dict_gauge_position_map_ext_window"][k + 1]
        # if rain gauge fall in radar null field remove the gauge from the position matrix
        posiz[posiz>len(row_gauge)]=0
        A[posiz[posiz > 0].astype('int') - 1, k] = corr[posiz > 0]
        A[len(row_gauge), k] = 0
        A[k, k] = 1

    # System solving
    b = np.append(data, mu)

    num_vars = A.shape[1]
    rank = np.linalg.matrix_rank(A)
    if rank == num_vars:
        W = np.linalg.lstsq(A, b, rcond=-1)[0]  # not under-determined
    else:
        for nz in combinations(range(num_vars), rank):  # the variables not set to zero
            try:
                W = np.zeros((num_vars, 1))
                W[nz, :] = np.asarray(np.linalg.solve(A[:, nz], b))
            except np.linalg.LinAlgError:
                pass  # picked bad variables, can't solve

    logging.info(' ---> Write and solve system...DONE')

    logging.info(' ---> Interpolate rainfall with GRISO...')

    # Interpolation
    s0 = np.zeros(correl_features['rs_ext_field_size'])

    for k in np.arange(0, len(row_gauge)):
        temp = np.zeros(correl_features['rs_ext_field_size'])
        temp[correl_features['dict_window_Rll_Cll'][k+1][0]:correl_features['dict_window_Rll_Cll'][k+1][0] + correl_features["dict_corr_fit_window"][k+1].shape[0],
        correl_features['dict_window_Rll_Cll'][k+1][1]:correl_features['dict_window_Rll_Cll'][k+1][1] + correl_features["dict_corr_fit_window"][k+1].shape[1]] = correl_features["dict_corr_fit_window"][k+1]*W[k]
        s0 += temp

    s0 = s0 + W[len(row_gauge)]
    s0[s0 < 0] = 0

    # Reduce the extended matrix to original size
    s0 = np.delete(s0, np.append(np.arange(0, correl_features['corr_max_radius_cells'], 1),
                                 s0.shape[0] + np.arange(-correl_features['corr_max_radius_cells'], 0)).astype(int), axis=0)
    a2dMappa = np.delete(s0, np.append(np.arange(0, correl_features['corr_max_radius_cells'], 1),
                                       s0.shape[1] + np.arange(-correl_features['corr_max_radius_cells'], 0)).astype(int), axis=1)

    logging.info(' ---> Interpolate rainfall with GRISO...DONE')
    return a2dMappa
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
