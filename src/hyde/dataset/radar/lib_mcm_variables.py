"""
Library Features:

Name:          lib_mcm_variables
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20201206'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging
import numpy as np

from copy import deepcopy

from src.hyde.algorithm.analysis.radar.lib_mcm_analysis_interpolation_grid import interp_grid2map

# Debug
import matplotlib.pylab as plt
logging.getLogger('matplotlib').setLevel(logging.WARNING)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to compute rain map
def compute_rain(var_data, var_geo_x, var_geo_y,
                 ref_geo_x, ref_geo_y, ref_geo_z, ref_epsg='4326', ref_no_data=-9999.0, ref_geo_index=None,
                 var_units='mm/h', var_missing_value=-9999.0, var_fill_value=-9999.0,
                 fx_nodata=-9999.0, fx_interp_method='nearest'):

    if var_units is None:
        logging.warning(' ===> Rain variable unit is undefined; set to [mm/h]')
        var_units = 'mm/h'
    if var_units != 'mm/h':
        logging.warning(' ===> Rain variable units in wrong format; expected in [mm/h], passed in [' +
                        var_units + ']')

    if var_data.ndim != 2:
        logging.error(' ===> Variable dimensions are not allowed')
        raise IOError('Variable data format must be equal to 2')

    if ref_geo_x.ndim == 1 and ref_geo_y.ndim == 1:
        ref_grid_geo_x, ref_grid_geo_y = np.meshgrid(ref_geo_x, ref_geo_y)
    elif ref_geo_x.ndim == 2 and ref_geo_y.ndim == 2:
        ref_grid_geo_x = ref_geo_x
        ref_grid_geo_y = ref_geo_y
    else:
        logging.error(' ===> Reference dimensions in bed format')
        raise IOError('Geographical data format not allowed')

    if var_geo_x.ndim == 1 and var_geo_y.ndim == 1:
        var_grid_geo_x, var_grid_geo_y = np.meshgrid(var_geo_x, var_geo_y)
    elif var_geo_x.ndim == 2 and var_geo_y.ndim == 2:
        var_grid_geo_x = var_geo_x
        var_grid_geo_y = var_geo_y
    else:
        logging.error(' ===> Variable dimensions in bed format')
        raise IOError('Variable data format not allowed')

    # Interpolate grid data to map
    grid_data = interp_grid2map(var_grid_geo_x, var_grid_geo_y, var_data, ref_grid_geo_x, ref_grid_geo_y,
                                nodata=fx_nodata, interp_method=fx_interp_method, index_out=ref_geo_index)

    # Filter data nan and over domain
    grid_data[np.isnan(grid_data)] = var_missing_value
    grid_data[np.isnan(ref_geo_z)] = var_fill_value
    grid_data[ref_geo_z == ref_no_data] = np.nan

    return grid_data
# -------------------------------------------------------------------------------------
