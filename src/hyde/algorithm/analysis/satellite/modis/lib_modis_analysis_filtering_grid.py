# -------------------------------------------------------------------------------------
# Library
import logging
from scipy import ndimage

# Debug
# import matplotlib.pylab as plt
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Filter variable using a uniform area
def filter_grid2uniformarea(var_data, pixel_size_length=100):
    # Compute filter
    var_filtered = ndimage.uniform_filter(var_data, size=pixel_size_length, mode='nearest')

    # Debug
    # plt.figure(1)
    # plt.imshow(a2dVarData,interpolation = 'none'); plt.colorbar(); plt.clim(0 ,1)
    # plt.figure(2)
    # plt.imshow(a2dVarFilter,interpolation = 'none'); plt.colorbar(); plt.clim(0 ,1)
    # plt.show()

    # Return value
    return var_filtered
# -------------------------------------------------------------------------------------
