
import logging
import numpy as np
import rasterio
import os

from copy import deepcopy
from osgeo import gdal, gdalconst
from rasterio.transform import Affine

from lib_utils_io import create_darray_2d

logging.getLogger('rasterio').setLevel(logging.WARNING)


# -------------------------------------------------------------------------------------
# Method to translate file in tiff format
def translate_file_type(filename_src, filename_dest, fileinfo={}, src_type='.h5', dest_type='GTiff'):

    if (src_type == '.h5') and (filename_src.endswith(src_type)):

        file_suffix = fileinfo['prefix']
        file_tree = fileinfo['tree']

        fileroot_src = file_suffix + filename_src + file_tree

        gdal.Translate(filename_dest, fileroot_src,
                       outputSRS="+proj=cea +lon_0=0 +lat_ts=30 +ellps=WGS84 +units=m",
                       format=dest_type, outputBounds=[-17367530.45, 7314540.76, 17367530.45, -7314540.76],
                       noData=-9999)

    else:
        logging.error(' ===> Translate options are not available!')
        raise NotImplementedError('Translate options not implemented yet')
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read tiff file
def reproject_file_tiff(file_name_in, file_name_out,
                        file_wide_out, file_high_out, file_geotrans_out, file_proj_out):

    if isinstance(file_geotrans_out, Affine):
        file_geotrans_out = file_geotrans_out.to_gdal()

    dset_tiff_out = gdal.GetDriverByName('GTiff').Create(
        file_name_out, file_wide_out, file_high_out, 1, gdalconst.GDT_Float32)
    dset_tiff_out.SetGeoTransform(file_geotrans_out)
    dset_tiff_out.SetProjection(file_proj_out)

    dset_tiff_in = gdal.Open(file_name_in, gdalconst.GA_ReadOnly)
    dset_proj_in = dset_tiff_in.GetProjection()
    dset_geotrans_in = dset_tiff_in.GetGeoTransform()
    dset_data_in = dset_tiff_in.ReadAsArray()
    dset_band_in = dset_tiff_in.GetRasterBand(1)

    # Reproject from input file to output file set with out information
    gdal.ReprojectImage(dset_tiff_in, dset_tiff_out, dset_proj_in, file_proj_out,
                        gdalconst.GRA_NearestNeighbour)
    return dset_tiff_out
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to read geographical file
def read_file_geo(file_name):

    if os.path.exists(file_name):
        if file_name.endswith('tif') or file_name.endswith('.tiff'):

            dset = rasterio.open(file_name)
            bounds = dset.bounds
            res = dset.res
            transform = dset.transform
            data = dset.read()
            values = data[0, :, :]
            proj = dset.crs.wkt
            geotrans = dset.transform

            decimal_round = 7

            center_right = bounds.right - (res[0] / 2)
            center_left = bounds.left + (res[0] / 2)
            center_top = bounds.top - (res[1] / 2)
            center_bottom = bounds.bottom + (res[1] / 2)

            lon = np.arange(center_left, center_right + np.abs(res[0] / 2), np.abs(res[0]), float)
            lat = np.arange(center_bottom, center_top + np.abs(res[0] / 2), np.abs(res[1]), float)
            lons, lats = np.meshgrid(lon, lat)

            min_lon_round = round(np.min(lons), decimal_round)
            max_lon_round = round(np.max(lons), decimal_round)
            min_lat_round = round(np.min(lats), decimal_round)
            max_lat_round = round(np.max(lats), decimal_round)

            center_right_round = round(center_right, decimal_round)
            center_left_round = round(center_left, decimal_round)
            center_bottom_round = round(center_bottom, decimal_round)
            center_top_round = round(center_top, decimal_round)

            assert min_lon_round == center_left_round
            assert max_lon_round == center_right_round
            assert min_lat_round == center_bottom_round
            assert max_lat_round == center_top_round

            lats = np.flipud(lats)

            mask_values = np.where(values != 255, 1, 0)
            mask_idx = np.where(mask_values.ravel() == 0)

            dims = values.shape
            values_tmp = np.float32(deepcopy(values.ravel()))
            values_tmp[mask_idx] = np.nan
            values_masked = np.reshape(values_tmp, [dims[0], dims[1]])

            high = dims[0]
            wide = dims[1]

            # handle_file = gdal.Open(file_name)
            # da_proj = handle_file.GetProjection()
            # da_geotrans = handle_file.GetGeoTransform()
            # da_wide = handle_file.RasterXSize   # 2 dims
            # da_high = handle_file.RasterYSize   # 1 dims

            da_frame = create_darray_2d(values_masked, lons, lats, coord_name_x='west_east', coord_name_y='south_north',
                                        dim_name_x='west_east', dim_name_y='south_north', name='geo_values')

            da_mask = create_darray_2d(mask_values, lons, lats, coord_name_x='west_east', coord_name_y='south_north',
                                       dim_name_x='west_east', dim_name_y='south_north', name='geo_mask')

        else:

            logging.error(' ===> Geographical file ' + file_name + ' format unknown')
            raise NotImplementedError('File type reader not implemented yet')
    else:
        logging.error(' ===> Geographical file ' + file_name + ' not found')
        raise IOError('Geographical file location or name is wrong')

    return da_frame, da_mask, wide, high, proj, geotrans, mask_idx
# -------------------------------------------------------------------------------------
