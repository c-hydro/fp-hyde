"""
Library Features:

Name:          Lib_Model_RainFarm_Apps
Author(s):     Fabio Delogu     (fabio.delogu@cimafoundation.org)
               Nicola Rebora    (nicola.rebora@cimafoundation.org)
               Mirko D'Andrea   (mirko.dandrea@cimafoundation.org)
               Lorenzo Campo    (lcampo@gmail.com)
Date:          '20171114'
Version:       '3.0.1'
"""

from __future__ import division
import numpy as np
import numpy.fft as fft

# import matplotlib.pylab as plt

if 'nanmean' not in dir(np):
    import scipy.stats
    np.nanmean = scipy.stats.nanmean

def fft3d(z):
    '''Calcola i parametri di slope'''
    
    ns, ns, nt = z.shape

    zf = np.abs(fft.fftn(z)/(ns*ns*nt))**2

    zf0 = zf

    ns_int = int(ns / 2)

    zf[ns_int, :, :] = zf0[ns_int, :, :]/2
    zf[:, ns_int, :] = zf0[:, ns_int, :]/2
    zf[:, :, ns_int] = zf0[:, :, ns_int]/2

    fs = np.reshape(np.sum(zf,2), (ns,ns), order='F')
    ft = np.reshape(np.sum(np.sum(zf, 0), 0), (nt,1), order='F')

    fs = fft.fftshift(fs)
    
    #import scipy.io as sio
    #oMat = sio.loadmat('fs.mat')
    
    #fs = oMat['fs']
    
    #plt.figure(1)
    #plt.imshow(fs, interpolation='none'); plt.colorbar()
    #plt.show()

    nn = np.zeros((ns, 1))
    fx = np.zeros((ns, 1))
    
    #storemat = np.zeros([100,8]);
    #f = 0
    for j in np.arange(-ns/2, ns/2):
        for i in np.arange(-ns/2, ns/2):
            k2 = np.sqrt(i*i+j*j)
            ik2 = int(np.floor(k2 + 1.5))  # Fabio: index issue in python
            if ik2 > 1:
                
                ii = int(i + ns/2 + 1)
                jj = int(j + ns/2 + 1)
                value_fs = fs[ii-1, jj-1]
                value_fx = fx[ik2-1]
                value_nn = nn[ik2-1] + 1
                
                value_fx_tot = value_fx + value_fs
                
                #### DEBUG START
                #print( str(i) + ' ' + str(j) + ' ' + str(f))
                #storemat[f,0] = k2;
                #storemat[f,1] = ik2;
                #storemat[f,2] = ii;
                #storemat[f,3] = jj;
                #storemat[f,4] = value_fs;
                #storemat[f,5] = value_fx;
                #storemat[f,6] = value_nn;
                #storemat[f,7] = value_fx_tot;
                #f = f+1
                #### DEBUG END
                
                fx[ik2-1] = value_fx_tot
                nn[ik2-1] = value_nn

    
    #sio.savemat('storemat_python.mat', mdict={'storemat': storemat})

    ns_int = int(ns / 2)
    nt_int = int(nt / 2)

    ft = ft[1:nt_int + 1]
    fx = fx[1:ns_int + 1]/nn[1:ns_int + 1]
    fy = fx.copy()

    return fx, fy, ft

def fitallslopes(fx, fy, ft, xr, tr):
    '''
    '''    
    #ns = len(fx)
    #nt = len(ft)
    #    ns=20 nt=20
    sx = fitslope(fx, xr)
    sy = fitslope(fy, xr)
    st = fitslope(ft, tr)
    sx = np.abs(sx)
    st = np.abs(st)
    sy = np.abs(sy)
    #    sx=(sx+sy)*0.5
    sx = sx-1
    #print(' -----> Slopes: sx=%f sy=%f st=%f'%(sx, sy, st))
    return sx, sy, st

def fitslope(fx, ii):
    '''
    '''
    nr, nc = fx.shape
    s = np.zeros((nc,))

    for i in range(0, nc):
        ss = np.polyfit(np.log(ii+1), np.log(fx[ii, i]), 1)
        s[i] = ss[0]

    return s

def agg_xyt(zi, nax, nay, nat):

    nax = int(nax)
    nay = int(nay)
    nat = int(nat)

    nx, ny, nt = zi.shape
    if nay==nax and nat==nt:
        sf = nx/nax
        xa = np.squeeze(np.nanmean(np.reshape(zi, (sf, int(nx*ny*nt/sf)),
                                              order='F'), 0))
        xz = np.reshape(np.nanmean(np.reshape(xa.T, (int(nx/sf), sf, int(ny/sf), nt),
                                              order='F'), 1), (nax,nay,nt),
                         order='F')
    else:
        xdim = int(nx/nax)
        ydim = int(ny/nay)
        tdim = int(nt/nat)
        rx = np.arange(0, nx, xdim)
        ry = np.arange(0, ny, ydim)
        rt = np.arange(0, nt, tdim)
        xz = np.zeros((nax, nay, nat))
        for i in range(0, xdim):
            for j in range(0, ydim):
                for k in range(0, tdim):
                    xz = xz + zi[np.ix_(i+rx, j+ry, k+rt)]
                
            
        
        xz = xz/(xdim*ydim*tdim)
        
    return xz


def initmetagauss(sx,st,ns,nt):
    '''
    kx = initmetagauss(sx,st,nso,nto)
    
    Generates the amplitudes f for a metagaussian field of size nso x nso x nto
    with slopes sx and st, no padding
    '''

    sx = np.abs(sx)
    st = np.abs(st)

    kx = np.concatenate((np.arange(0, ns/2+1), np.arange(-ns/2+1, 0))).T
    kx = kx.reshape((ns,1)).dot(np.ones((1,ns)))
    kx = np.expand_dims(kx, 2)
    kx = np.tile(kx, (1, 1, nt))
    kx = kx**2 + kx.transpose((1, 0, 2))**2
    kx[0,0,:]=0.000001


    kt = np.concatenate((np.arange(0, nt/2+1), np.arange(-nt/2+1, 0))).T
    kt = kt.reshape((nt,1)).dot(np.ones((1,ns)))
    
    kt = np.expand_dims(kt, 2)
    kt = np.tile(kt, (1, 1, ns))
    kt = kt.transpose((2, 1, 0))**2
    kt[:,:,0]=0.000001

    kx = (kx**(-(sx+1)/4)) * kt**(-st/4)

    kx[0, 0, 0] = 0
    kx[0, 0, :] = 0 
    kx[:,:,0] = 0

    kx = kx/np.sqrt(np.sum(np.abs(kx.flat)**2)) * ns * ns * nt
    
    return kx


def metagauss(f):
    '''    
    g=metagauss(sx,st,nso,nto)
    Generates a metagaussian field of size ns x ns x nt with slopes sx and st
    this version creates an output in fourier space and does not use padding
    '''
    ns,ns,nt = f.shape

    #    phases as fft of a gaussian noise random field
    
    ph = np.random.randn(ns,ns,nt)

    ph = fft.fftn(ph)
    ph = ph/np.abs(ph)
    ph[0,0,0] = 0
    ph = f*ph

    ph = fft.ifftn(ph).real
    return ph


def interpola_xyt(z, nx, ny, nt):
    '''
    '''
    nax,nay,nat = z.shape

    xdim = int(nx/nax)
    ydim = int(ny/nay)
    tdim = int(nt/nat)
    # # ir=1:xdim jr=ydim kr=1:tdim
    rx = np.arange(0, nx, xdim).astype('int32')
    ry = np.arange(0, ny, ydim).astype('int32')
    rt = np.arange(0, nt, tdim).astype('int32')

    zi = np.zeros((nx,ny,nt))

    for i in range(0, xdim):
        for j in range(0, ydim):
            for k in range(0, tdim):
                zi[np.ix_(i+rx, j+ry, k+rt)] = z
    return zi
