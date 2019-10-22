"""
Library Features:

Name:          lib_plot_map
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180918'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import os
from numpy import arange, min, max

os.environ["PROJ_LIB"] = "/home/fabio/Documents/Work_Area/Code_Development/Library/proj-5.2.0/share/proj/"

import matplotlib.pylab as plt
from mpl_toolkits.basemap import Basemap
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to plot map using pcolormesh
def plotMap_Pcolor(a2dData, a2dGeoX, a2dGeoY, a1dGeoBox=None,
                   dDataMin=0, dDataMax=10, sColorMap='RdBu_r', sCBarLabel='NA', sMapRes='l'):

    # Define latitude and longitude min and max
    if a1dGeoBox is not None:
        dGeoYMin = a1dGeoBox[0]
        dGeoXMin = a1dGeoBox[1]
        dGeoYMax = a1dGeoBox[2]
        dGeoXMax = a1dGeoBox[3]
    else:
        dGeoYMin = min(a2dGeoY)
        dGeoYMax = max(a2dGeoY)
        dGeoXMin = min(a2dGeoX)
        dGeoXMax = max(a2dGeoX)

    oFig = plt.figure(figsize=(18, 18))
    oBaseMap = Basemap(projection='cea', resolution=sMapRes,
                       llcrnrlat=dGeoYMin, llcrnrlon=dGeoXMin,
                       urcrnrlat=dGeoYMax, urcrnrlon=dGeoXMax
                       )

    oBaseMap.drawcoastlines(color='lightgray', linewidth=1.25)
    oBaseMap.drawcountries(color='gray')
    oBaseMap.drawmapboundary(fill_color='aqua')

    oBaseMap.pcolormesh(a2dGeoX, a2dGeoY, a2dData, latlon=True, cmap=sColorMap)

    oBaseMap.drawparallels(arange(dGeoYMin, dGeoYMax, 0.4), labels=[True, False, False, False])
    oBaseMap.drawmeridians(arange(dGeoXMin, dGeoXMax, 0.4), labels=[False, False, False, True])

    oBaseMap.colorbar(location='right', format='%d', label=sCBarLabel)

    plt.clim(dDataMin, dDataMax)
    plt.show()
# -------------------------------------------------------------------------------------
