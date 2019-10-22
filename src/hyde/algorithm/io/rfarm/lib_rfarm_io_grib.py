# -------------------------------------------------------------------------------------
# Libraries
import numpy as np
import pandas as pd

from src.hyde.dataset.nwp.lami.lib_lami_2i_time import computeTime
from src.hyde.dataset.nwp.lami.lib_lami_2i_variables import computeRain

from src.hyde.algorithm.settings.rfarm.lib_rfarm_args import time_format, time_calendar, time_units, time_type

# Debug
# import matplotlib.pylab as plt
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read data for lami-2i
def read_data_lami_2i(file_handle, file_drv, var_name='Total Precipitation'):

    # Get geographical information
    var_geox, var_geoy = file_drv.oFileLibrary.getVarGeo_LAMI_2i(file_handle)

    # Get time steps
    var_time = file_drv.oFileLibrary.getVarTime_LAMI_2i(file_handle, var_name)[var_name]

    # Get data values
    var_data = file_drv.oFileLibrary.getVar3D_LAMI_2i(file_handle, var_name)[var_name]

    # Set correct south-north and west-east direction(s)
    var_n = var_data.shape[2]
    for i in range(0, var_n):
        var_data[:, :, i] = np.flipud(var_data[:, :, i])
    var_geoy = np.flipud(var_geoy)

    return var_data, var_time, var_geox, var_geoy
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to convert time for lami-2i
def convert_time_lami_2i(var_time_idx, var_time_exp=None):
    var_time_date = computeTime(var_time_idx, time_format)[0]
    var_time_cmp = pd.to_datetime(var_time_date)

    if var_time_exp.equals(var_time_cmp):
        var_time_series = var_time_exp
    else:
        var_freq_inferred = var_time_cmp.inferred_freq
        var_time_series = pd.date_range(start=var_time_cmp[0],
                                        periods=list(var_time_cmp.values).__len__(),
                                        freq=var_freq_inferred)

    return var_time_series
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to convert data for lami-2i
def convert_data_lami_2i(var_data_raw, var_units, var_type_feat='accumulated'):
    var_data_def = computeRain(var_data_raw, oVarUnits=[var_units],  oVarType=[var_type_feat])
    return var_data_def
# -------------------------------------------------------------------------------------
