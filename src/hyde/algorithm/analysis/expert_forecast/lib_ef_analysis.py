"""
Library Features:

Name:          lib_ef_analysis
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20201102'
Version:       '1.0.0'
"""
#######################################################################################
# Libraries
import logging
import numpy as np
#######################################################################################


# -------------------------------------------------------------------------------------
# Find slopes value
def find_slopes(rain_avg_data, rain_peak_data,
                rain_avg_array, slope_x_array, slope_y_array, slope_t_array, vm_data):

    try:

        # Iterate over rain array(s)
        slope_x_list = []
        slope_y_list = []
        slope_t_list = []
        for rain_avg_step, rain_peak_step in zip(rain_avg_data, rain_peak_data):

            # Compute index linked with mean value
            rain_avg_cmp = np.abs(rain_avg_array - rain_avg_step)
            idx_min = np.where(rain_avg_cmp == np.min(rain_avg_cmp))[0]

            # Get S as function of VM
            s_data = np.reshape(vm_data[idx_min[0], :, :], [vm_data.shape[1], vm_data.shape[2]])

            # Compute index linked with max value
            rain_peak_cmp = np.abs(s_data - rain_peak_step)
            [idx_sx, idx_st] = np.where(rain_peak_cmp == np.min(rain_peak_cmp))

            # Get slope(s) X, Y and T
            slope_x_value = slope_x_array[idx_sx][0]
            slope_y_value = slope_x_value
            slope_t_value = slope_t_array[idx_st][0]

            slope_x_list.append(slope_x_value)
            slope_y_list.append(slope_y_value)
            slope_t_list.append(slope_t_value)

        slope_x_data = np.asarray(slope_x_list)
        slope_y_data = np.asarray(slope_y_list)
        slope_t_data = np.asarray(slope_t_list)

    except BaseException as base_exp:

        logging.error(' ===> Slopes are not correctly defined')
        raise RuntimeError('Error in computing slopes ' + str(base_exp))

    return slope_x_data, slope_y_data, slope_t_data
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Compute slopes arrays
def compute_slopes(vm_data,
                   tag_vm='vm', tag_ravg='r_avg', tag_slope_x='sx', tag_slope_y='sy', tag_slope_t='st',
                   var_sx_min=0.5, var_sx_max=3.5, var_sx_resolution=0.2,
                   var_sy_min=0.5, var_sy_max=3.5, var_sy_resolution=0.2,
                   var_st_min=0.5, var_st_max=3.5, var_st_resolution=0.2):

    # Fitted rain average array (update 20 feb 2014)
    var_ravg_array = np.array([1, 5, 10, 15, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120])

    # Fitted slope X (update 20 feb 2014)
    var_sx_step = int((var_sx_max - var_sx_min)/var_sx_resolution + 1)
    var_sx_array = np.linspace(var_sx_min, var_sx_max, var_sx_step, endpoint=True)

    # Fitted slope Y (update 20 feb 2014)
    var_sy_step = int((var_sy_max - var_sy_min)/var_sy_resolution + 1)
    var_sy_array = np.linspace(var_sy_min, var_sy_max, var_sy_step, endpoint=True)

    # Fitted slope T (update 20 feb 2014)
    var_st_step = int((var_st_max - var_st_min)/var_st_resolution + 1)
    var_st_array = np.linspace(var_st_min, var_st_max, var_st_step, endpoint=True)

    # TEST START
    # Test value(s)
    var_rmax = 18.0
    var_ravg = 10.0

    # Compute index linked with mean value
    var_ravg_cmp = np.abs(var_ravg_array - var_ravg)
    idx_min = np.where(var_ravg_cmp == np.min(var_ravg_cmp))

    # Get S as function of VM
    s_data = np.reshape(vm_data[idx_min[0], :, :], [vm_data.shape[1], vm_data.shape[2]])

    # Compute index linked with max value
    var_rmax_cmp = np.abs(s_data - var_rmax)
    [idx_sx, idx_st] = np.where(var_rmax_cmp == np.min(var_rmax_cmp))

    # Get slope(s) X, Y and T
    var_sx = var_sx_array[idx_sx][0]
    var_sy = var_sx
    var_st = var_st_array[idx_st][0]
    # TEST END

    # Save data
    var_obj = {tag_vm: vm_data, tag_ravg: var_ravg_array,
               tag_slope_x: var_sx_array, tag_slope_y: var_sy_array, tag_slope_t: var_st_array}

    return var_obj
# -------------------------------------------------------------------------------------
