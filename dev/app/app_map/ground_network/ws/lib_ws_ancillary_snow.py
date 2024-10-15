"""
Library Features:

Name:          lib_ws_ancillary_snow
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180918'
Version:       '1.0.0'
"""

#######################################################################################
# Library
import logging
import os
import tempfile
import rasterio

import numpy as np

from time import sleep

from lib_ws_generic import random_string, delete_folder, make_folder
from lib_ws_process import exec_process

# Debug
import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Command line to compute predictor(s) data
command_line_predictor = dict(
    slope_data={
        'command_line': 'gdaldem slope {file_name_in} {file_name_out} -s 111120'
    },
    aspect_data={
        'command_line': 'gdaldem aspect {file_name_in} {file_name_out}'
    },
    roughness_data={
        'command_line': 'gdaldem roughness {file_name_in} {file_name_out}'
    },
    hillshade_data={
        'command_line': 'gdaldem hillshade {file_name_in} {file_name_out} -s 111120'
    }
)
# Command line to compute geographical data
command_line_utils = dict(
    translate_data={
        'command_line': 'gdal_translate -of AAIGrid {file_name_in} {file_name_out}'
    }
)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute snow predictor(s)
def compute_predictor(file_path_in, file_path_out, command_line_data, command_line_geo=None):

    if command_line_geo is None:
        command_line_geo = command_line_utils['translate_data']['command_line']

    file_name_tmp = random_string() + '.tiff'
    folder_name_tmp = tempfile.mkdtemp()
    file_path_tmp = os.path.join(folder_name_tmp, file_name_tmp)

    make_folder(folder_name_tmp)

    # Execute command-line for computing data
    command_line_tmp = command_line_data.format(**{'file_name_in': file_path_in, 'file_name_out': file_path_tmp})
    [std_out_data, std_err_data, std_exit_data] = exec_process(command_line_tmp)
    sleep(5)

    # Read temporary data in tiff format
    with rasterio.open(file_path_tmp, mode='r+') as dset_tmp:
        data_tmp = dset_tmp.read()
        values_tmp = data_tmp[0, :, :]
    # Read input data in ascii format
    with rasterio.open(file_path_in, mode='r+') as dset_in:
        data_in = dset_in.read()
        values_in = data_in[0, :, :]

    # Execute command-line for translating data
    command_line_tmp = command_line_geo.format(**{'file_name_in': file_path_tmp, 'file_name_out': file_path_out})
    [std_out_geo, std_err_geo, std_exit_geo] = exec_process(command_line_tmp)

    # Read output data in ascii format
    with rasterio.open(file_path_out, mode='r+') as dset_out:
        data_out = dset_out.read()
        values_out = data_out[0, :, :]

    # Remove temporary folder and its content
    delete_folder(folder_name_tmp)

    # Debug
    # plt.figure(1)
    # plt.imshow(values_in)
    # plt.figure(2)
    # plt.imshow(values_tmp)
    # plt.figure(3)
    # plt.imshow(values_out)
    # plt.show()

    return values_out

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to compute snow kernel
def compute_kernel(ref_geo_data, ref_geo_x, ref_geo_y, geo_cellsize_x, geo_cellsize_y,
                   var_index_x, var_index_y, radius_influnce):

    # -------------------------------------------------------------------------------------
    # Dynamic values (NEW)
    earth_radius = 6378388  # (Radius)
    earth_ellipsoid = 0.00672267  # (Ellipsoid)

    # dx = (R * cos(lat)) / (sqrt(1 - e2 * sqr(sin(lat)))) * PI / 180
    dx = (earth_radius * np.cos(ref_geo_y * np.pi / 180)) / (np.sqrt(1 - earth_ellipsoid * np.sqrt(np.sin(ref_geo_y * np.pi / 180)))) * np.pi / 180
    # dy = (R * (1 - e2)) / pow((1 - e2 * sqr(sin(lat))),1.5) * PI / 180
    dy = (earth_radius * (1 - earth_ellipsoid)) / np.power((1 - earth_ellipsoid * np.sqrt(np.sin(ref_geo_y / 180))), 1.5) * np.pi / 180

    # a2dGeoAreaKm = ((a2dDX/(1/dGeoXCellSize)) * (a2dDY/(1/dGeoYCellSize))) / 1000000 # [km^2]
    geo_area = ((dx / (1 / geo_cellsize_x)) * (dy / (1 / geo_cellsize_y)))  # [m^2]

    # Area, Mean Dx and Dy values (meters)
    geo_mx = np.sqrt(np.nanmean(geo_area))
    geo_my = np.sqrt(np.nanmean(geo_area))
    geo_mm = np.mean([geo_mx, geo_my])

    # Pixel(s) interpolation
    pixel_distance = np.int32(radius_influnce * 1000 / geo_mm)

    # Compute gridded indexes
    ref_index_x = np.linspace(0, ref_geo_data.shape[1], ref_geo_data.shape[1])
    ref_index_y = np.linspace(0, ref_geo_data.shape[0], ref_geo_data.shape[0])
    grid_index_x, grid_index_y = np.meshgrid(ref_index_x, ref_index_y)

    # Cycle(s) on snow sensor(s)
    grid_weights = np.zeros([ref_geo_data.shape[0], ref_geo_data.shape[1]])
    for index_x, index_y in zip(var_index_x, var_index_y):

        # Compute distance index matrix
        grid_index_distance = np.zeros([ref_geo_data.shape[0], ref_geo_data.shape[1]])
        grid_index_distance = np.sqrt((grid_index_y - index_y) ** 2 + (grid_index_x - index_x) ** 2)

        # Weight(s) matrix
        grid_index_pixels = np.zeros([ref_geo_data.shape[0], ref_geo_data.shape[1]])
        grid_index_pixels = np.where(grid_index_distance < pixel_distance)

        grid_weights[grid_index_pixels] = grid_weights[grid_index_pixels] + \
            (pixel_distance ** 2 - grid_index_distance[grid_index_pixels] ** 2) /\
            (pixel_distance ** 2 + grid_index_distance[grid_index_pixels] ** 2) / len(var_index_x)

    return grid_weights
    # --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
