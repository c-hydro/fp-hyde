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
from skimage import measure
import pandas as pd
from itertools import combinations
import xarray as xr
import matplotlib.pyplot as plt

from src.hyde.driver.model.griso.drv_model_griso_generic import deg2km, sub2ind, averageCells, cart2pol, sphericalFit

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
def GrisoCorrel(rPluvio, cPluvio, corrFin, z, passoKm, a2dPosizioni, nRows, nCols, vp_pluvio, corr_type='fixed'):

    logging.info(' ---> Initialize correlation estimation...')
    buffer = int(corrFin / passoKm / 2)

    # Threshold for valid gridded data
    p0 = 0.0001
    corr_null_radius = 5

    # Spherical variogram fixed parameters
    c0 = 0          # Nugget
    c1 = 1          # Sill

    # buffer on the domain
    nx = nCols + buffer * 2
    ny = nRows + buffer * 2

    # matrices of distances from the center of the GRISO windows
    y_arr, x_arr = np.mgrid[0:1+buffer*2, 0:1+buffer*2]
    dist = np.sqrt((x_arr - buffer) ** 2 + (y_arr - buffer) ** 2)
    dist = dist * passoKm

    bins_ddfin = np.round(dist, 4)
    # dist = np.round(dist, 4)

    if corr_type is not 'fixed':
        # calculate map of maximum number of pair for each cell of the GRISO window
        finestra_in = np.where(bins_ddfin <= corrFin / 2, 1, 0)
        numero_massimo = np.nansum(finestra_in)
        a2dMappaNumCoppie = np.zeros_like(finestra_in, dtype=np.int)

        for ind, (dove_y, dove_x) in enumerate(zip(np.where(finestra_in==1)[0],np.where(finestra_in==1)[1])):
            logging.info(' ---> Cell ' + str(ind) + ' of ' + str(len(np.where(finestra_in==1)[0])))
            r = np.where(finestra_in==1,cart2pol(x_arr-dove_y,y_arr-dove_x)[0]*passoKm,np.nan)
            r[r>corrFin/2] = np.nan
            a2dMappaNumCoppie += np.where(r>0,1,0)

    zExt = np.pad(np.squeeze(z), buffer, 'constant', constant_values=np.nan)
    a2dPosizioniExt = np.pad(a2dPosizioni, buffer, 'constant', constant_values=0)
    rPluvioExt = rPluvio + buffer
    cPluvioExt = cPluvio + buffer

    finestraCorrNull = c0 + c1 * (1 - 3 / 2 * dist / corr_null_radius + 1 / 2 * (dist / corr_null_radius) ** 3) * (dist < corr_null_radius)                  ######VERIFICA QUESTO VALORE 5
    # IPOTESI: c0 + c1 * (1 - 3 / 2 * dist / (5 * passoKm) + 1 / 2 * (dist / (5*passoKm)) ** 3) * (dist < (5*passoKm))
    #finestraCorrMax = c0 + c1 * (1 - 3 / 2 * dist / (corrFin / 2) + 1 / 2 * (dist / (corrFin / 2)) ** 3) * (dist < (corrFin / 2))
    finestraCorrMax = c0 + c1 * (1 - 3 / 2 * dist / (corrFin / 2) + 1 / 2 * (dist / (corrFin / 2)) ** 3) * (dist < (corrFin / 2))
    #finestraCorrMax2 = c0 + c1 * (1 - 3 / 2 * dist / (corrFin /(passoKm * 2)) + 1 / 2 * (dist / (corrFin /(passoKm * 2))) ** 3) * (dist < (corrFin /(passoKm * 2)))

    logging.info(' ---> Initialize correlation estimation...DONE')

    logging.info(' ---> Estimate correlation features for ' + str(len(vp_pluvio)) + ' single grid cells...')

    CorrStimata = {}
    Lambda = {}
    FinestraPosizioniExt = {}
    Rows_cols = {}

    corrStimNulla = deepcopy(finestraCorrNull)
    corrStimNulla[dist > corr_null_radius] = 0
    corrStimMax = deepcopy(finestraCorrMax)
    corrStimMax[dist > (corrFin / 2)] = 0

    for ind, (R,C,rain_pluvio) in enumerate(zip(rPluvioExt,cPluvioExt,vp_pluvio), start = 1):
        # For each point fits spherical kernel
        logging.info(' ---> Cell ' + str(ind) + ' of ' + str(len(vp_pluvio)))
        FinestraPosizioniExt[ind], Rows_cols[ind], CorrStimata[ind], Lambda[ind] = GrisoLocalKernel(R, C, rain_pluvio, zExt, dist, numero_massimo, a2dPosizioniExt, a2dMappaNumCoppie, corrStimMax, corrStimNulla, corr_null_radius, corrFin, passoKm, corr_type)

    correl_features = dict(zip(('Rows_cols','CorrStimata', 'Lambda', 'FinestraPosizioniExt', 'dist','PosizioniExt'),
                               (Rows_cols,CorrStimata, Lambda, FinestraPosizioniExt, dist,a2dPosizioniExt)))

    logging.info(' ---> Estimate correlation features...DONE')

    return correl_features

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
def GrisoLocalKernel(R, C, rain_pluvio, zExt, dist, numero_massimo, a2dPosizioniExt, a2dMappaNumCoppie, corrStimMax, corrStimNulla, corr_null_radius, corrFin, passoKm, corr_type, c0=0, c1=1):

    buffer = int(corrFin / passoKm / 2)

    if corr_type is 'fixed':
        CorrStim = corrStimMax
        radius = buffer
    else:
        finestra_radar = deepcopy(zExt[int(R - buffer):int(R + buffer + 1), int(C - buffer):int(C + buffer + 1)])
        finestra_radar[dist > corrFin / 2] = np.nan
        pixel_validi = finestra_radar[finestra_radar >= 0]  # p0]

        # If the neighbourhood is complete (no border) and made of constant values
        if len(pixel_validi) == numero_massimo and all(
                pixel_validi == finestra_radar[int(corrFin / 2), int(corrFin / 2)]):  # and finestra_radar[R,C]!=0:
            CorrStim = deepcopy(corrStimMax)
            radius = buffer

        # se almeno 10 punti sulla finestra che superano la soglia p0?????
        elif len(pixel_validi) < (100 / passoKm) and rain_pluvio > 0.2:
            CorrStim = deepcopy(corrStimMax)
            radius = buffer

        elif len(pixel_validi) > (100 / passoKm):
            finestra1 = np.nan_to_num(finestra_radar - np.nanmean(finestra_radar), 0)
            a2dxcorrfin = correlate(finestra1, finestra1, mode='full', method='auto')
            CorrEmpirica = a2dxcorrfin[buffer:-buffer, buffer:-buffer] / a2dMappaNumCoppie / np.nanvar(finestra_radar)

            if np.isnan(CorrEmpirica[int(corrFin / 2), int(corrFin / 2)]):  # Se tutta mappa radar è 0
                CorrStim = deepcopy(corrStimMax)  # corrStimMax
                radius = buffer
            else:
                CorrEmpirica[dist > (corrFin / 2)] = 0
                CorrStim, radius = sphericalFit(dist,CorrEmpirica,corr_null_radius,corrFin / 2, corrFin / 2-passoKm)
                CorrStim[dist > (corrFin / 2)] = 0
        else:
            CorrStim = deepcopy(corrStimNulla)
            radius = corr_null_radius

    CorrStim[CorrStim < 0.001] = 0

    finestra_posizioni_ext = a2dPosizioniExt[int(R - buffer):int(R + buffer + 1),
                                    int(C - buffer):int(C + buffer + 1)].astype(int)
    rows_cols = np.array((int(R - buffer), int(C - buffer)))
    corr_stimata = CorrStim

    return finestra_posizioni_ext, rows_cols, corr_stimata, radius
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# compute GRISO interpolation over the extended matrix
def GrisoInterpola(rPluvio, cPluvio, data, a3dMatriceCorrStimata, corrFin, passoKm, a3dFinestraPosizioniExt, a2dPosizioniExt, Rows_cols):

   # average null
    mu = 0

    # if rain gauge fall in radar null field remove the gauges from the correlation system
    rPluvio = rPluvio[~np.isnan(data)]
    cPluvio = cPluvio[~np.isnan(data)]
    data = data[~np.isnan(data)]

    logging.info(' ---> Write and solve system...')
    # write system
    A = np.zeros([len(rPluvio) + 1, len(rPluvio) + 1])
    A[:, len(rPluvio)] = 1

    for k in np.arange(0, len(rPluvio)):
        corr = a3dMatriceCorrStimata[k + 1]  #.values
        posiz = a3dFinestraPosizioniExt[k + 1]   #.values
        posiz[posiz>len(rPluvio)]=0                                     # if rain gauge fall in radar null field remove the gauge from the position matrix
        A[posiz[posiz > 0].astype('int') - 1, k] = corr[posiz > 0]
        A[len(rPluvio), k] = 0
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
    s0 = np.zeros(a2dPosizioniExt.shape)

    for ind, k in enumerate(np.arange(0, len(rPluvio))):
        temp = np.zeros(a2dPosizioniExt.shape)
        temp[Rows_cols[k+1][0]:Rows_cols[k+1][0] + a3dMatriceCorrStimata[k+1].shape[0],
        Rows_cols[k+1][1]:Rows_cols[k+1][1] + a3dMatriceCorrStimata[k+1].shape[1]] = a3dMatriceCorrStimata[k+1]*W[k]
        s0 += temp

    s0 = s0 + W[len(rPluvio)]
    s0[s0 < 0] = 0

    # Reduce the extended matrix to original size
    s0 = np.delete(s0, np.append(np.arange(0, (corrFin / passoKm / 2), 1),
                                 s0.shape[0] + np.arange(-(corrFin / passoKm / 2), 0)).astype(int), axis=0)
    a2dMappa = np.delete(s0, np.append(np.arange(0, (corrFin / passoKm / 2), 1),
                                       s0.shape[1] + np.arange(-(corrFin / passoKm / 2), 0)).astype(int), axis=1)


    logging.info(' ---> Interpolate rainfall with GRISO...DONE')
    return a2dMappa
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
