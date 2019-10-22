
"""
Library Features:

Name:          lib_rfarm_utils_regrid
Author(s):     Mirko D'Andrea (mirko.dandrea@cimafoundation.org); Lorenzo Campo (lcampo@gmail.com)
Date:          '20170530'
Version:       '3.5.0'
"""
#######################################################################################
# Library
from scipy.interpolate import griddata
from scipy import meshgrid
import numpy as np
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to compute grid indexes
def gridIndex(a2dGeoX_IN, a2dGeoY_IN, a2dGeoX_OUT, a2dGeoY_OUT):
    
    iGeoDim_IN = a2dGeoX_IN.shape[0]*a2dGeoY_IN.shape[1]
    
    a1iGeoVal_IN = np.arange(0,iGeoDim_IN)
    
    a2iIndex_OUT = griddata((a2dGeoX_IN.ravel(), a2dGeoY_IN.ravel()),
                            a1iGeoVal_IN, 
                            (a2dGeoX_OUT, a2dGeoY_OUT), method='nearest')
                            
    return a2iIndex_OUT
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to regrid data (using interpolation function)
def gridData(a2dData_IN, a2dGeoX_IN, a2dGeoY_IN, a2dGeoX_OUT, a2dGeoY_OUT, sRegridMethod='nearest', dNoData=np.nan,):
    
    a2dData_OUT = griddata((a2dGeoX_IN.ravel(), a2dGeoY_IN.ravel()), 
                           a2dData_IN.ravel(),
                           (a2dGeoX_OUT, a2dGeoY_OUT), method=sRegridMethod, fill_value=dNoData)

    return a2dData_OUT
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute reference(s) and weight(s) to apply constant volume interpolating method
def getReferencesAndWeights(X1, Y1, X2, Y2):
    '''
    getReferencesAndWeights(X1, Y1, X2, Y2)
        ottiene i riferimenti per il regrid a volume costante.
        
        Parametri
        ---------
            X1, Y1: matrici bidimensioali delle coordinate delle griglie di input
            X2, Y2: matrici bidimensioali delle coordinate delle griglie di output
        
        Ritorna
        --------
            nIntersezioni_perc:     matrice dei pesi delle intersezioni 
            intersezioni_indici_I:  matrice degli indici I delle intersezioni
            intersezioni_indici_J:  matrice degli indici J delle intersezioni
        
    '''
    
    dx2 = X2[0, 1]-X2[0, 0]
    dy2 = Y2[0, 0]-Y2[1, 0]
    
    X2f = X2.ravel()
    Y2f = Y2.ravel()
    
    y2_d = Y2f-dy2/2
    y2_u = Y2f+dy2/2
        
    x2_l = X2f-dx2/2
    x2_r = X2f+dx2/2
    try:
        dx1 = X1[0, 1]-X1[0, 0]
        dy1 = Y1[0, 0]-Y1[1, 0]
    except Exception:
        dx1 = None
        dy1 = None

    x1_min = X1[0, 0]-dx1/2
    y1_max = Y1[0, 0]+dy1/2
    
    # ciclo sulle celle della griglia di destinazione
    nmax = (np.ceil(dx2/dx1)+1)**2 # numero massimo di celle della griglia di partenza che una cella della griglia
                                 # di arrivo puo intersecare
    
    iXYCount = X2f.shape[0]
    
    intersezioni_indici_I = np.ones((iXYCount, nmax)).astype('int32')
    intersezioni_indici_J = np.ones((iXYCount, nmax)).astype('int32')
    intersezioni_perc = np.zeros((iXYCount, nmax))

    I_min = np.floor(((X2f-(dx2/2)) - x1_min)/dx1).astype('int32')
    I_min[I_min<0] = 0
    I_max = np.floor(((X2f+(dx2/2)) - x1_min)/dx1).astype('int32')
    I_max[I_max>=X1.shape[1]] = X1.shape[1]-1
    
    J_min = np.floor((y1_max - (Y2f+(dy2/2)))/dy1).astype('int32')
    J_min[J_min<0] = 0
    J_max = np.floor((y1_max - (Y2f-(dy2/2)))/dy1).astype('int32')
    J_max[J_max>=Y1.shape[0]] = Y1.shape[0]-1 
    
    for i in range(0, iXYCount):
        # selezione celle di partenza che circondano la cella di arrivo (sottoinsieme degli indici)
        # ciclo sulle celle ci partenza selezionate e salvataggio delle coppie
        # indice-area di intersezione (frazione)

        YI = np.arange(J_min[i], J_max[i]+1, 1, dtype='int32')
        XI = np.arange(I_min[i], I_max[i]+1, 1, dtype='int32')
        
        [J,I] = meshgrid(XI, YI)
        
        If = I.ravel()
        Jf = J.ravel()
        
        iIJCount = If.shape[0]
        
        for ii in range(0, iIJCount):
            intersezioni_indici_I[i, ii]=If[ii]
            intersezioni_indici_J[i, ii]=Jf[ii]
            iI = If[ii]
            iJ = Jf[ii]
            intersect_width = np.nanmax(
                [0, np.nanmin([X1[iI,iJ]+dx1/2, x2_r[i]]) - np.nanmax([X1[iI,iJ]-dx1/2, x2_l[i]])])
            intersect_height = np.nanmax(
                [0, np.nanmin([Y1[iI,iJ]+dy1/2, y2_u[i]]) - np.nanmax([Y1[iI,iJ]-dy1/2, y2_d[i]])])
            
            intersezioni_perc[i, ii]=(intersect_width * intersect_height)
        if len(intersezioni_perc[i,:])>0 and np.nansum(intersezioni_perc[i,:])>0:
            intersezioni_perc[i, :] = intersezioni_perc[i,:] / np.nansum(intersezioni_perc[i,:])
#    sIntersezioni_perc = np.array([intersezioni_perc.sum(1),]* intersezioni_perc.shape[1]).transpose()
#    nIntersezioni_perc = intersezioni_perc/sIntersezioni_perc

    return intersezioni_perc, intersezioni_indici_I, intersezioni_indici_J
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to to apply constant volume interpolating method
def regridKVolume(A, X1, Y1, X2, Y2):

    '''
    regridKVolume(x1, y1, x2, y2, A)
        regrid esatto (per griglie a maglia rettangolare, si assume che le coordinate siano i centri cella)
    
    Parametri
    ---------
        A:      matrice di input
        X1, Y1: matrici bidimensioali delle coordinate delle griglie di input
        X2, Y2: matrici bidimensioali delle coordinate delle griglie di output

    Ritorna
    --------
        B:      matrice di output rigrigliata
    '''
    nIntersezioni_perc, intersezioni_indici_I, intersezioni_indici_J = getReferencesAndWeights(X1, Y1, X2, Y2)
    B = applyRegrid(A, X2.shape, intersezioni_indici_I, intersezioni_indici_J, nIntersezioni_perc)
    
    return B
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to apply regridding using constant volume interpolating method
def applyRegrid(A, gridShape, intersezioni_indici_I, intersezioni_indici_J, nIntersezioni_perc):

    '''
    applyRegrid(A, gridShape, intersezioni_indici_I, intersezioni_indici_J, nIntersezioni_perc)
        applica il regrid esatto utilizzando gli array ausiliari precalcolati con getReferencesAndWeights

    Parametri
    ---------
        A:                      matrice di input
        gridShape:              dimensione della griglia di output
        nIntersezioni_perc:     matrice dei pesi delle intersezioni 
        intersezioni_indici_I:  matrice degli indici I delle intersezioni
        intersezioni_indici_J:  matrice degli indici J delle intersezioni      
    Ritorna
    --------
        B:                      matrice di output rigrigliata      
    '''

    B = np.nansum((A[intersezioni_indici_I, intersezioni_indici_J]*nIntersezioni_perc), axis=1)
    B = B.reshape(gridShape)

    return B

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Class for constant volume interpolating method
class KVolumeRegridder:

    '''
    KVolumeRegridder
        classe di gestione del regrid a volume costante per griglie bidimensionali regolari, 
        con buffering degli indici e dei pesi
    '''

    outGridShape = None
    intersezioni_indici_I = None
    intersezioni_indici_J = None
    nIntersezioni_perc = None
    
    def __init__(self, X1, Y1, X2, Y2):

        '''
        KVolumeRegridder(X1, Y1, X2, Y2)
            inizializza un oggett usando la funzione getReferencesAndWeights
        Parametri
        ---------
            X1, Y1: matrici bidimensioali delle coordinate delle griglie di input
            X2, Y2: matrici bidimensioali delle coordinate delle griglie di output            
        '''

        self.outGridShape = X2.shape
        self.nIntersezioni_perc, self.intersezioni_indici_I, self.intersezioni_indici_J = getReferencesAndWeights(X1, Y1, X2, Y2)
    
    def applyBufferedRegrid(self, A):

        '''
        applyBufferedRegrid(A)
            applica il regrid utilizzando le griglie di inizializzazione
        Parametri
        ---------
            A:  matrice di input
        Ritorna
        --------
            B:  matrice di output rigrigliata
        '''

        B = applyRegrid(A, self.outGridShape, self.intersezioni_indici_I, self.intersezioni_indici_J, self.nIntersezioni_perc)
        return B

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Main method to test constant volume interpolating method
if __name__ == '__main__':

    x1=np.linspace(1.5, 18.5, 18, endpoint=True)
    y1=np.linspace(4.5, 33.5, 30, endpoint=True)
    x2=np.linspace(1.3, 18.7, 30, endpoint=True)
    y2=np.linspace(4.3, 33.7, 50, endpoint=True)

    [X1,Y1] = meshgrid(x1, y1)
    [X2,Y2] = meshgrid(x2, y2)

    A=np.random.random_sample(X1.shape)+0.01*(X1-10)**2+0.02*(Y1-20)**2
    print('somma A: ' + str(A.sum()))

    regridder = KVolumeRegridder(X1, np.flipud(Y1), X2, np.flipud(Y2))
    B = regridder.applyBufferedRegrid(A)    

    print('B: ' + str(np.nansum(B)*0.36))
    print('A: ' + str(np.nansum(A)))

# -------------------------------------------------------------------------------------
