"""
Library Features:

Name:          lib_snowblending_variables
Author(s):     Francesco Avanzi (francesco.avanzi@cimafoundation.org), Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210525'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging
import numpy as np

from copy import deepcopy

from lib_snowblending_analysis_interpolation_grid import interp_grid2map
from lib_snowblending_analysis_filtering_grid import filter_grid2uniformarea

# Debug
import matplotlib.pylab as plt
logging.getLogger('matplotlib').setLevel(logging.WARNING)
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to mask data map
def mask_data(var_data, var_geo_x, var_geo_y,
              ref_geo_x, ref_geo_y, ref_geo_z, ref_epsg='4326', ref_no_data=-9999.0, ref_geo_index=None,
              var_units='-', var_missing_value=-9999.0, var_fill_value=-9999.0, fx_interp_method='nearest',
              fx_nodata=-9999.0, fx_flag_masks=None, fx_flag_values=None, fx_flag_meanings=None,
              fx_pixel_size_aggregation=None):

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

    if fx_flag_masks is None:
        logging.error(' ===> Datasets masked values must be defined')
        raise IOError('None object is not allowed for masked values')
    if fx_flag_values is None:
        logging.error(' ===> Datasets source values must be defined')
        raise IOError('None object is not allowed for datasets source values')
    if fx_flag_meanings is None:
        logging.error(' ===> Datasets source meanings must be defined')
        raise IOError('None object is not allowed for datasets source meanings')

    var_data_step = deepcopy(var_data)
    for mask, value, meaning in zip(fx_flag_masks, fx_flag_values, fx_flag_meanings):

        logging.info(' --------> Mask ' + meaning + ' case ... ')

        value_equal = None
        value_min = None
        value_max = None
        if isinstance(value, str):
            value_equal = int(value)
        elif isinstance(value, list):
            value_min = int(value[0])
            value_max = int(value[1])
        else:
            logging.error(' ===> Datasets values not permitted')
            raise NotImplementedError('Case not implemented yet')

        mask_equal = None
        mask_min = None
        mask_max = None
        if isinstance(mask, str):
            mask_equal = int(mask)
        elif isinstance(mask, list):
            mask_min = int(mask[0])
            mask_max = int(mask[1])
        else:
            logging.error(' ===> Datasets masked values not permitted')
            raise NotImplementedError('Case not implemented yet')

        if mask_equal is not None:
            if value_equal is not None:
                var_data_step[var_data == value_equal] = mask_equal
            elif (value_min is not None) and (value_max is not None):
                var_data_step[(var_data >= value_min) & (var_data <= value_max)] = mask_equal
            else:
                logging.error(' ===> Datasets source values not permitted')
                raise NotImplementedError('Case not implemented yet')

        if (mask_min is not None) and (mask_max is not None):
            if mask_min != value_min:
                logging.error(' ===> Datasets masked values not permitted')
                raise NotImplementedError('Case not implemented yet')
            if mask_max != value_max:
                logging.error(' ===> Datasets masked values not permitted')
                raise NotImplementedError('Case not implemented yet')

        logging.info(' --------> Mask ' + meaning + ' case ... DONE')

    # Filter data to uniform area
    if fx_pixel_size_aggregation is not None:
        var_filter_step = filter_grid2uniformarea(var_data_step, fx_pixel_size_aggregation)
    else:
        var_filter_step = var_data_step

    # Interpolate grid data to map
    grid_data = interp_grid2map(var_grid_geo_x, var_grid_geo_y, var_filter_step, ref_grid_geo_x, ref_grid_geo_y,
                                nodata=fx_nodata, interp_method=fx_interp_method, index_out=ref_geo_index)

    # Filter data nan and over domain
    grid_data[np.isnan(grid_data)] = var_missing_value
    grid_data[np.isnan(ref_geo_z)] = var_fill_value
    grid_data[ref_geo_z == ref_no_data] = var_fill_value

    return grid_data
# -------------------------------------------------------------------------------------
