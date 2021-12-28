"""
Library Features:

Name:           lib_rfarm_core
Author(s):      Fabio Delogu (fabio.delogu@cimafoundation.org)
                Mirko D'Andrea (mirko.dandrea@cimafoundation.org)
Date:           '20190905'
Version:        '3.5.1'
"""

#######################################################################################
# Logging
import logging
import numpy as np

import src.hyde.model.rfarm.lib_rfarm_apps as lib_apps
from src.hyde.algorithm.settings.model.rfarm.lib_rfarm_args import logger_name

log_stream = logging.getLogger(logger_name)

# Debug
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to run RF model (nwp mode)
def exec_nwp(X, xscale, tscale, cssf, ctsf,
             f=None, celle3_rainfarm=None,
             sx=None, st=None):
    '''
    x=rainfarm(X,sx,st,xscale,cssf,csst)
    INPUT
        X = matrice 3D di dimensioni nx * nx * nt, nx
        xscale = fattore di scala spaziale (numero intero)
        tscale = fattore di scala temporale (numero intero)
        cssf = scala spaziale affidabile
                (numero intero, 1 = risoluzione nativa)
        ctsf = scala temporale affidabile
                (numero intero, 1 = risoluzione nativa)
        f = ampiezze per il campo metagaussiano,  OPZIONALE
        celle3_rainfarm = matrice per l'interpolazione,   OPZIONALE
        sx = penza spettrale spaziale,    OPZIONALE
        st = penza spettrale temporale,    OPZIONALE

    OUTPUT
        x = matrice 3D con il campo disaggregato di dimensioni (nx*xscale) *
            (nx*xscale) * (nt*tscale)
        f = ampiezze per il campo metagaussiano calcolate
    '''

    # Info start
    log_stream.info(' ------> Run RF model (NWP Mode) ... ')

    # X and Y scale(s)
    yscale = xscale

    # X istantaneous rain data
    alfa = 1
    nx, ny, nt = X.shape
    if cssf == 1 and ctsf == 1:
        pa = X
    else:
        pa = lib_apps.agg_xyt(X[:, :, 0:nt], nx / cssf, ny / cssf, nt / ctsf)

    # ====> START DEBUG DATA
    # from scipy.io import savemat
    # from os.path import join
    # path = '/home/fabio/Desktop/PyCharm_Workspace/RainFarm/Data/Data_Dynamic/Source/ecmwf0100/'
    # file = 'rain_debug.mat'
    # data = {'data': pa}
    # savemat(join(path,file), data)
    # import matplotlib.pylab as plt
    # plt.figure(1)
    # plt.imshow(pa[:, : ,0], interpolation='none'); plt.colorbar()
    # plt.show()
    # ====> END DEBUG DATA

    # Find spectral slopes
    sy = sx
    if sx is None and st is None:
        fxp, fyp, ftp = lib_apps.fft3d(X)

        kmin = 2
        kmax = min(15, len(fxp) - 1)
        wmin = 2
        wmax = min(9, len(ftp) - 1)

        sx, sy, st = lib_apps.fitallslopes(
            fxp, fyp, ftp,
            np.arange(kmin, kmax),
            np.arange(wmin, wmax))

        # INIT: prepare f field for metagauss
        # np.random.rand('state',sum(100*clock))  ##ok<RAND> #
        # seme random differente per ogni run del modello

    # Info slope(s)
    log_stream.info(' -------> Slopes: sx=%f sy=%f st=%f' % (sx, sy, st))

    if f is None:
        f = lib_apps.initmetagauss(sx, st, nx * xscale, nt * tscale)

    # Generate meta-gaussian field
    g = lib_apps.metagauss(f)

    # Nonlinear transform
    r = np.exp(alfa * g[0:nx * xscale, 0:ny * yscale, 0:nt * tscale])

    # We want the aggregated field to be the same as pa
    ga = lib_apps.agg_xyt(r, nx / cssf, ny / cssf, nt / ctsf)
    ca = pa / ga
    if celle3_rainfarm is None:
        cai = lib_apps.interpola_xyt(ca, nx * xscale, ny * yscale, nt * tscale)
    else:
        cai = np.reshape(ca[celle3_rainfarm], (nx * xscale, ny * yscale, nt * tscale),
                         order='F')

    # Define final rain field
    x = cai * r

    # Info end
    log_stream.info(' ------> Run RF model (NWP Mode) ... OK')

    # Return variable(s)
    return x, f

# -------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to run RF model (expert forecast mode)
def exec_expert_forecast(X, xscale, tscale, cssf, ctsf,
                         f=None, celle3_rainfarm=None,
                         sx=None, st=None, nx=None, ny=None, nt=None):

    '''
    x=rainfarm(X,sx,st,xscale,cssf,csst)
    INPUT
        X = matrice 3D di dimensioni nx * nx * nt, nx
        xscale = fattore di scala spaziale (numero intero)
        tscale = fattore di scala temporale (numero intero)
        cssf = scala spaziale affidabile
                (numero intero, 1 = risoluzione nativa)
        ctsf = scala temporale affidabile
                (numero intero, 1 = risoluzione nativa)
        f = ampiezze per il campo metagaussiano,  OPZIONALE
        celle3_rainfarm = matrice per l'interpolazione,   OPZIONALE
        sx = penza spettrale spaziale,    OPZIONALE
        st = penza spettrale temporale,    OPZIONALE

    OUTPUT
        x = matrice 3D con il campo disaggregato di dimensioni (nx*xscale) *
            (nx*xscale) * (nt*tscale)
        f = ampiezze per il campo metagaussiano calcolate
    '''

    # Info start
    log_stream.info(' ------> Run RF model (ExpertForecast Mode) ... ')

    # Nx and NY
    if X is not None:
        if X.ndim == 2:
            nx, ny = X.shape
            nt = nt
        elif X.ndim == 3:
            nx, ny, nt = X.shape
    elif X is None:
        X = np.float64(1.0)
        nx = nx
        ny = ny
        nt = nt
        cssf = nx
        ctsf = nt

    # Alpha
    alfa = 1

    if cssf == 1 and ctsf == 1:
        pa = X
    else:
        if X.ndim == 0:
            pa = X
        elif X.ndim == 3:
            pa = lib_apps.agg_xyt(X[:, :, 0:nt], nx / cssf, ny / cssf, nt / ctsf)

    # ====> START DEBUG DATA
    # import scipy.io as sio
    # Data = {}
    # Data['rain'] = X
    # sio.savemat('rain_debug.mat',Data)

    # plt.figure(1)
    # plt.imshow(X[:,:,0], interpolation='none'); plt.colorbar()
    # plt.show()
    # ====> END DEBUG DATA

    # Find spectral slopes
    if sx is None and st is None:

        fxp, fyp, ftp = lib_apps.fft3d(X)

        kmin = 3
        kmax = min(15, len(fxp) - 1)
        wmin = 3
        wmax = min(9, len(ftp) - 1)

        sx, sy, st = Lib_Apps.fitallslopes(fxp, fyp, ftp,
                                         np.arange(kmin, kmax + 1),
                                         np.arange(wmin, wmax + 1))

        # INIT: prepare f field for metagauss
        # np.random.rand('state',sum(100*clock))  ##ok<RAND> #
        # seme random differente per ogni run del modello
    else:
        sx = sx
        sy = sx
        st = st

    # Info slope(s)
    log_stream.info(' -------> Slopes: sx=%f sy=%f st=%f' % (sx, sy, st))

    if f is None:
        f = lib_apps.initmetagauss(sx, st, ny * xscale, nt * tscale)

    # Generate metagaussian field
    g = lib_apps.metagauss(f)

    # Nonlinear transform
    g = np.exp(alfa * g[0:ny * xscale, 0:ny * xscale, 0:nt * tscale])

    # We want the aggregated field to be the same as pa
    ga = lib_apps.agg_xyt(g, nx / cssf, ny / cssf, nt / ctsf)

    ca = pa / ga

    if ca.ndim == 0:

        x = ca * g

        x[np.where(x <= 0.25 * X)] = 0.0

    elif ca.ndim == 3:

        if celle3_rainfarm is None:
            cai = lib_apps.interpola_xyt(ca, nx * xscale, ny * xscale, nt * tscale)
        else:
            cai = np.reshape(ca[celle3_rainfarm], (nx * xscale, ny * xscale, nt * tscale),
                             order='F')
        x = cai * g

    # Info end
    log_stream.info(' ------> Run RF model (ExpertForecast Mode) ... OK')

    # Return variable(s)
    return x, f
    # --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
