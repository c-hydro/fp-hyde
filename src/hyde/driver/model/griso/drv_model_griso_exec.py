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

from src.hyde.driver.model.griso.drv_model_griso_generic import deg2km, sub2ind, averageCells

# -------------------------------------------------------------------------------------
# Compute correlation, kernel and position of each rain gauge neighbourhood

def GrisoCorrel(rPluvio, cPluvio, corrFin, passoKm, a2dPosizioni, nRows, nCols):
    buffer = int(corrFin / passoKm / 2)

    # buffer on the domain
    nx = nCols + buffer * 2
    ny = nRows + buffer * 2
    a2dPosizioniExt = np.pad(a2dPosizioni, buffer, 'constant', constant_values=0)
    rPluvioExt = rPluvio + buffer
    cPluvioExt = cPluvio + buffer

    # calculate distance window
    distance = np.zeros([1 + buffer * 2, 1 + buffer * 2])
    x_arr, y_arr = np.mgrid[0:distance.shape[0], 0:distance.shape[1]]
    dist = np.sqrt((x_arr - buffer) ** 2 + (y_arr - buffer) ** 2)
    dist = dist * passoKm

    c0 = 0
    c1 = 1

    finestraCorrNull = c0 + c1 * (1 - 3 / 2 * dist / (corrFin / 2) + 1 / 2 * (dist / (corrFin / 2)) ** 3) * (dist < (corrFin / 2))

    a3dMatriceCorrStimata = np.empty([finestraCorrNull.shape[0], finestraCorrNull.shape[1], len(rPluvio)])
    rKernel = np.empty([finestraCorrNull.shape[0], finestraCorrNull.shape[1], len(rPluvio)])
    cKernel = np.empty([finestraCorrNull.shape[0], finestraCorrNull.shape[1], len(rPluvio)])
    a3dFinestraPosizioniExt = np.empty([finestraCorrNull.shape[0], finestraCorrNull.shape[1], len(rPluvio)])

    for i in np.arange(0, len(rPluvio), 1):
        a3dMatriceCorrStimata[:, :, i] = finestraCorrNull
        rKernel[:, :, i], cKernel[:, :, i] = np.meshgrid(
            np.arange(rPluvioExt[i] - buffer, rPluvioExt[i] + buffer + 1, 1),
            np.arange(cPluvioExt[i] - buffer, cPluvioExt[i] + buffer + 1, 1))
        a3dFinestraPosizioniExt[:, :, i] = a2dPosizioniExt[rPluvioExt[i] - buffer:rPluvioExt[i] + buffer + 1,
                                           cPluvioExt[i] - buffer:cPluvioExt[i] + buffer + 1]

    return a3dMatriceCorrStimata, rKernel, cKernel, a3dFinestraPosizioniExt, dist

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Compute GRISO interpolation over the extended matrix

def GrisoInterpola(dist, rPluvio, cPluvio, data, data0, nRows, nCols, scgampar, shgampar,
                   a3dMatriceCorrStimata, corrFin, passoKm, a3dFinestraPosizioniExt, rKernel, cKernel):
    from itertools import combinations

    mu = 0

    s0 = np.zeros([int((nRows + (corrFin / passoKm)) * (nCols + (corrFin / passoKm))), 1])
    sMax = np.zeros([int((nRows + (corrFin / passoKm)) * (nCols + (corrFin / passoKm))), 1])
    temp_impronta = np.zeros([int((nRows + (corrFin / passoKm)) * (nCols + (corrFin / passoKm))), 1])

    # write system
    A = np.zeros([len(rPluvio) + 1, len(rPluvio) + 1]);
    A[:, len(rPluvio)] = 1

    for k in np.arange(0, len(rPluvio)):
        corr = a3dMatriceCorrStimata[:, :, k]
        posiz = a3dFinestraPosizioniExt[:, :, k]
        A[posiz[posiz > 0].astype('int') - 1, k] = corr[posiz > 0]
        A[len(rPluvio), k] = 0
        A[k, k] = 1

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
                print(W)
            except np.linalg.LinAlgError:
                pass  # picked bad variables, can't solve

    for k in np.arange(0, len(rPluvio)):
        corr = a3dMatriceCorrStimata[:, :, k]
        temp = np.vstack(
            [rKernel[:, :, k].flatten('F'), cKernel[:, :, k].flatten('F'), np.zeros(cKernel[:, :, k].flatten('F').shape)]).T
        indKernel = np.apply_along_axis(sub2ind, 1, temp.astype('int'), nRows + (corrFin / passoKm),
                                        nCols + (corrFin / passoKm))
        s0[indKernel] = np.expand_dims(s0[indKernel].flatten('F') + corr.flatten('F') * W[k], 1)
        sMax[indKernel] = np.expand_dims(np.amax(np.vstack([sMax[indKernel].flatten('F'), corr.flatten('F')]), axis=0), 1)

    s0 = np.reshape(s0, (int(nRows + (corrFin / passoKm)), int(nCols + (corrFin / passoKm))), order='F').copy()
    sMax = np.reshape(sMax, (int(nRows + (corrFin / passoKm)), int(nCols + (corrFin / passoKm)))).copy()
    impronta = sMax
    impronta[impronta > 0] = 1
    errore = sMax

    s0 = s0 + W[len(rPluvio)]

    return s0
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# GRISO launcher

def GrisoExec(dst, lonGauge, latGauge, data, Grid):

    # generate lat-lon grid
    lonGrid = np.around(Grid.lon.values, decimals=5)
    latGrid = np.around(Grid.lat.values, decimals=5)
    gridx, gridy = np.meshgrid(lonGrid, latGrid)
    grid = pyresample.geometry.GridDefinition(lats=gridy, lons=gridx)

    corrFin = dst * 2

    # grid step should be integer and divisible per 2
    passoKm = deg2km(latGrid[0], lonGrid[0], latGrid[1], lonGrid[0])
    pixel = np.round(corrFin / 2 / passoKm)
    if not pixel % 2 == 0:
        pixel = pixel + 1
    passoKm = corrFin / 2 / pixel

    # extract grid coordinates (radius of influence is an approx of the radius where the script look for neighbours in meters)
    # not valid gauges are the ones out of the domain
    swath = pyresample.geometry.SwathDefinition(lons=lonGauge, lats=latGauge)
    _, is_valid, index_array, _ = pyresample.kd_tree.get_neighbour_info(
        source_geo_def=grid, target_geo_def=swath, radius_of_influence=1000*passoKm*2,
        neighbours=1)

    rPluvio, cPluvio = np.unravel_index(index_array, grid.shape)

    # if more rain gauges fall in the same cell they are averaged
    rPluvio, cPluvio, rainCell = averageCells(rPluvio, cPluvio, data[is_valid])

    # rain gauge ID: 1-max over the grid
    a2dPosizioni = np.squeeze(np.zeros(grid.shape))
    a2dPosizioni[rPluvio, cPluvio] = np.arange(1, rainCell.shape[0] + 1, 1)

    # matrici di correlazione stimata, Kernel (righe e colonne rispetto a mat estesa), posizioni delle stazioni in ogni sottogriglia
    a3dMatriceCorrStimata, rKernel, cKernel, a3dFinestraPosizioniExt, dist = GrisoCorrel(rPluvio, cPluvio, corrFin,
                                                                                         passoKm, a2dPosizioni,
                                                                                         grid.shape[0], grid.shape[1])

    # procedura di interpolazione
    s0 = GrisoInterpola(dist, rPluvio, cPluvio, rainCell, rainCell, grid.shape[0], grid.shape[1], 0, 0,
                        a3dMatriceCorrStimata, corrFin, passoKm, a3dFinestraPosizioniExt, rKernel, cKernel);
    s0[s0 < 0] = 0

    # riduco dalla griglia estesa a quella originale
    s0 = np.delete(s0, np.append(np.arange(0, (corrFin / passoKm / 2), 1),
                                 s0.shape[0] + np.arange(-(corrFin / passoKm / 2), 0)).astype(int), axis=0)
    a2dMappa = np.delete(s0, np.append(np.arange(0, (corrFin / passoKm / 2), 1),
                                       s0.shape[1] + np.arange(-(corrFin / passoKm / 2), 0)).astype(int), axis=1)

    return a2dMappa
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------