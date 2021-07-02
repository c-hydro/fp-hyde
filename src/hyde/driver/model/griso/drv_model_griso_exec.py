"""
Library Features:

Name:          drv_model_griso_exec
Author(s):     Andrea Libertino (andrea.libertino@cimafoundation.org)
Date:          '20210315'
Version:       '1.1.0'
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

from src.hyde.driver.model.griso.drv_model_griso_generic import deg2km, sub2ind, averageCells, cart2pol

# -------------------------------------------------------------------------------------
# Prepare input data for GRISO
def GrisoPreproc(corrFin, lonGauge, latGauge, data_gauge, data_sat=None, Grid=None):

    logging.info(' ---> Compute grid...')
    # generate lat-lon grid
    lonGrid = np.around(Grid.lon.values, decimals=5)
    latGrid = np.around(Grid.lat.values, decimals=5)
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
    # extract grid coordinates (radius of influence is an approx of the radius where the script look for neighbours in meters)
    # not valid gauges are the ones out of the domain
    swath = pyresample.geometry.SwathDefinition(lons=lonGauge, lats=latGauge)
    _, is_valid, index_array, _ = pyresample.kd_tree.get_neighbour_info(
        source_geo_def=grid, target_geo_def=swath, radius_of_influence=1000*passoKm*2,
        neighbours=1)

    rPluvio, cPluvio = np.unravel_index(index_array, grid.shape)

    # if more rain gauges fall in the same cell they are averaged
    rPluvio_uniq, cPluvio_uniq, gauge_value = averageCells(rPluvio, cPluvio, data_gauge[is_valid])

    # (equivalent) rain gauge ID: 1-max over the grid
    gauge_codes = np.arange(1, gauge_value.shape[0] + 1, 1)

    # generate grid with (equivalent) rain-gauge locations
    a2dPosizioni = np.squeeze(np.zeros(grid.shape))
    a2dPosizioni[rPluvio_uniq, cPluvio_uniq] = gauge_codes

    # calculate grid data for modified conditional merging
    if not data_sat is None:
        _, _, grid_value = averageCells(rPluvio, cPluvio, data_sat[is_valid])

        if Grid.lat.values[-1] < Grid.lat.values[0]:
            grid_rain = np.flipud(Grid['precip'].values)
        else:
            grid_rain = Grid['precip'].values
    else:
        grid_value = None
        grid_rain = None

    # generate dataframe with all the point data
    point_data = pd.DataFrame(index=gauge_codes, data={"rPluvio":rPluvio_uniq, "cPluvio":cPluvio_uniq, "gauge_value":gauge_value, "grid_value":grid_value})
    logging.info(' ---> Grid point values...DONE')

    return point_data, a2dPosizioni, grid_rain, grid, passoKm

# -------------------------------------------------------------------------------------
# Compute correlation, kernel and position of each rain gauge neighbourhood
def GrisoCorrel(rPluvio, cPluvio, corrFin, z, passoKm, a2dPosizioni, nRows, nCols, vp_pluvio, corr_type='fixed'):

    logging.info(' ---> Initialize correlation estimation...')
    buffer = int(corrFin / passoKm / 2)

    # Threshold for valid gridded data
    p0 = 0.0001

    # buffer on the domain
    nx = nCols + buffer * 2
    ny = nRows + buffer * 2

    # matrices of distances from the center of the GRISO windows
    y_arr, x_arr = np.mgrid[0:1+buffer*2, 0:1+buffer*2]
    dist = np.sqrt((x_arr - buffer) ** 2 + (y_arr - buffer) ** 2)
    dist = dist * passoKm

    bins_ddfin = np.round(dist, 4)

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

    c0 = 0
    c1 = 1

    finestraCorrNull = c0 + c1 * (1 - 3 / 2 * dist / 5 + 1 / 2 * (dist / 5) ** 3) * (dist < 5)                  ######VERIFICA QUESTO VALORE 5
    # IPOTESI: c0 + c1 * (1 - 3 / 2 * dist / (5 * passoKm) + 1 / 2 * (dist / (5*passoKm)) ** 3) * (dist < (5*passoKm))
    #finestraCorrMax = c0 + c1 * (1 - 3 / 2 * dist / (corrFin / 2) + 1 / 2 * (dist / (corrFin / 2)) ** 3) * (dist < (corrFin / 2))
    finestraCorrMax = c0 + c1 * (1 - 3 / 2 * dist / (corrFin / 2) + 1 / 2 * (dist / (corrFin / 2)) ** 3) * (dist < (corrFin / 2))
    #finestraCorrMax2 = c0 + c1 * (1 - 3 / 2 * dist / (corrFin /(passoKm * 2)) + 1 / 2 * (dist / (corrFin /(passoKm * 2))) ** 3) * (dist < (corrFin /(passoKm * 2)))

    logging.info(' ---> Initialize correlation estimation...DONE')

    logging.info(' ---> Estimate correlation features for ' + str(len(vp_pluvio)) + ' single grid cells...')

    CorrStimata = {}
    Lambda = {}
    FinestraPosizioniExt ={}

    for ind, (R,C,rain_pluvio) in enumerate(zip(rPluvioExt,cPluvioExt,vp_pluvio)):
        logging.info(' ---> Cell ' + str(ind +1) + ' of ' + str(len(vp_pluvio)))
        if corr_type is 'fixed':
            CorrStim = finestraCorrMax
            Lambda[ind + 1] = buffer
        else:
            finestra_radar = zExt[R-buffer:R+buffer+1,C-buffer:C+buffer+1]
            finestra_radar[bins_ddfin>=corrFin/2] = np.nan
            pixel_validi = finestra_radar[finestra_radar >= p0]

            # If the neighbourhood is complete (no border) and made of constant values
            if len(pixel_validi)==numero_massimo and all(pixel_validi==finestra_radar[R,C]) and finestra_radar[R,C]!=0:
                CorrStim = finestraCorrMax
                Lambda[ind + 1] = buffer

            # se almeno 10 punti sulla finestra che superano la soglia p0?????
            elif len(pixel_validi) < (100/passoKm) and rain_pluvio>0.2:
                CorrStim = finestraCorrMax
                Lambda[ind + 1] = buffer

            elif len(pixel_validi) > (100/passoKm):
                finestra1 = np.nan_to_num(finestra_radar - np.nanmean(finestra_radar),0)
                a2dxcorrfin = correlate(finestra1, finestra1, mode='full', method='auto')
                CorrEmpirica = a2dxcorrfin[buffer:-buffer,buffer:-buffer]/a2dMappaNumCoppie/np.nanvar(finestra_radar)
                CorrEmpirica[dist > (corrFin / 2)] = 0

                # If there are more correlation items, I consider only the one centred on the central pixel
                CorrGroups = measure.label(np.where(CorrEmpirica>0,1,0))
                if len(np.unique(CorrGroups))>1:
                    CorrEmpirica = np.where(CorrGroups == CorrGroups[buffer,buffer], CorrEmpirica, 0)

                CorrEmpirica[CorrEmpirica<0] = 0
                CorrStim = CorrEmpirica
                Lambda[ind + 1] = 100
            else:
                CorrStim = finestraCorrNull
                Lambda[ind + 1] = 5

        FinestraPosizioniExt[ind +1] = xr.DataArray(data=a2dPosizioniExt[R - buffer:R + buffer + 1, C - buffer:C + buffer + 1], dims=['rows','cols'], coords={'rows': np.arange(R - buffer, R + buffer + 1, 1), 'cols': np.arange(C - buffer, C + buffer + 1, 1)}).reindex({'rows': np.arange(0, a2dPosizioniExt.shape[0], 1), 'cols': np.arange(0, a2dPosizioniExt.shape[1], 1)}, fill_value=0)
        CorrStimata[ind + 1] = xr.DataArray(data=CorrStim, dims=['rows', 'cols'],
                                                    coords={'rows': np.arange(R - buffer, R + buffer + 1, 1),
                                                            'cols': np.arange(C - buffer, C + buffer + 1, 1)}).reindex(
            {'rows': np.arange(0, a2dPosizioniExt.shape[0], 1), 'cols': np.arange(0, a2dPosizioniExt.shape[1], 1)},
            fill_value=0)

    correl_features = dict(zip(('CorrStimata', 'Lambda', 'FinestraPosizioniExt', 'dist'),
                               (CorrStimata, Lambda, FinestraPosizioniExt, dist)))

    logging.info(' ---> Estimate correlation features...DONE')

    return correl_features

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Compute GRISO interpolation over the extended matrix
def GrisoInterpola(rPluvio, cPluvio, data, a3dMatriceCorrStimata, corrFin, passoKm, a3dFinestraPosizioniExt):

   # Average null
    mu = 0

    logging.info(' ---> Write and solve system...')
    # write system
    A = np.zeros([len(rPluvio) + 1, len(rPluvio) + 1])
    A[:, len(rPluvio)] = 1

    for k in np.arange(0, len(rPluvio)):
        corr = a3dMatriceCorrStimata[k + 1].values
        posiz = a3dFinestraPosizioniExt[k + 1].values
        A[posiz[posiz > 0].astype('int') - 1, k] = corr[posiz > 0]
        A[len(rPluvio), k] = 0
        A[k -1, k-1] = 1

    # system solving
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
    s0 = np.zeros(a3dMatriceCorrStimata[k + 1].values.shape)

    for ind, k in enumerate(np.arange(0, len(rPluvio))):
        s0 += (a3dMatriceCorrStimata[k+1].values*W[k])

    #old interpolation routine
    #s0 = np.zeros([int((nRows + (corrFin / passoKm)) * (nCols + (corrFin / passoKm))), 1])
    #for ind, k in enumerate(np.arange(0, len(rPluvio))):
    #    logging.info(' ---> Cell ' + str(ind + 1) + ' of ' + str(len(rPluvio)))
    #    corr = a3dMatriceCorrStimata[k+1]
    #    temp = np.vstack([rKernel[k+1].flatten('F'), cKernel[k+1].flatten('F'), np.zeros(cKernel[k+1].flatten('F').shape)]).T
    #    indKernel = np.apply_along_axis(sub2ind, 1, temp.astype('int'), nRows + (corrFin / passoKm), nCols + (corrFin / passoKm))
    #    s0[indKernel] = np.expand_dims(s0[indKernel].flatten('F') + corr.flatten('F') * W[k], 1)
    #s0 = np.reshape(s0, (int(nRows + (corrFin / passoKm)), int(nCols + (corrFin / passoKm))), order='F').copy()

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