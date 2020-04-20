# -------------------------------------------------------------------------------------
# Library
import tempfile
import rasterio
import numpy as np

from os import remove
from os.path import join, exists
from scipy.interpolate import griddata

from src.hyde.algorithm.utils.satellite.hsaf.lib_ascat_generic import random_string, exec_process
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to clip data 2D/3D using a min/max threshold(s) and assign a missing value
def clip_map(map, valid_range=[None, None], missing_value=None):

    # Set variable valid range
    if valid_range is not None:
        if valid_range[0] is not None:
            valid_range_min = float(valid_range[0])
        else:
            valid_range_min = None
        if valid_range[1] is not None:
            valid_range_max = float(valid_range[1])
        else:
            valid_range_max = None
        # Set variable missing value
        if missing_value is None:
            missing_value_min = valid_range_min
            missing_value_max = valid_range_max
        else:
            missing_value_min = missing_value
            missing_value_max = missing_value

        # Apply min and max condition(s)
        if valid_range_min is not None:
            map = map.where(map >= valid_range_min, missing_value_min)
        if valid_range_max is not None:
            map = map.where(map <= valid_range_max, missing_value_max)

        return map
    else:
        return map

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create csv ancillary file
def create_file_csv(file_name_csv, var_data, var_name='values', lons_name='x', lats_name='y',
                    file_format='%10.4f', file_delimiter=','):
    file_handle = open(file_name_csv, 'w')
    file_handle.write(lons_name + ',' + lats_name + ',' + var_name + '\n')
    np.savetxt(file_handle, var_data, fmt=file_format, delimiter=file_delimiter, newline='\n')
    file_handle.close()
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create vrt ancillary file
def create_file_vrt(file_name_vrt, file_name_csv, layer_name, var_name='values', lons_name='x', lats_name='y'):

    file_handle = open(file_name_vrt, 'w')
    file_handle.write('<OGRVRTDataSource>\n')
    file_handle.write('    <OGRVRTLayer name="' + layer_name + '">\n')
    file_handle.write('        <SrcDataSource>' + file_name_csv + '</SrcDataSource>\n')
    file_handle.write('    <GeometryType>wkbPoint</GeometryType>\n')
    file_handle.write('    <LayerSRS>WGS84</LayerSRS>\n')
    file_handle.write(
        '    <GeometryField encoding="PointFromColumns" x="' +
        lons_name + '" y="' + lats_name + '" z="' + var_name + '"/>\n')
    file_handle.write('    </OGRVRTLayer>\n')
    file_handle.write('</OGRVRTDataSource>\n')
    file_handle.close()

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to interpolate data using scattered data
def interpolate_point2map(lons_in, lats_in, values_in, lons_out, lats_out,
                          interp_nodata=-9999,
                          interp_method='nearest', interp_option=None,
                          interp_radius_lon=None, interp_radius_lat=None,
                          values_tmp='values', lons_tmp='x', lats_tmp='y',
                          epsg_code=4326, folder_tmp=None):

    # Define temporary folder
    if folder_tmp is None:
        folder_tmp = tempfile.mkdtemp()

    # Define layer name (using a random string)
    layer_tmp = random_string()

    # Check interpolation radius x and y
    if (interp_radius_lon is None) or (interp_radius_lat is None):
        raise TypeError

    # Define temporary file(s)
    file_tmp_csv = join(folder_tmp, layer_tmp + '.csv')
    file_tmp_vrt = join(folder_tmp, layer_tmp + '.vrt')
    file_tmp_tiff = join(folder_tmp, layer_tmp + '.tif')

    # Define geographical information
    lon_out_min = min(lons_out.ravel())
    lon_out_max = max(lons_out.ravel())
    lat_out_min = min(lats_out.ravel())
    lat_out_max = max(lats_out.ravel())
    lon_out_cols = lons_out.shape[0]
    lat_out_rows = lats_out.shape[1]

    # Define dataset for interpolating function
    data_in = np.zeros(shape=[values_in.shape[0], 3])
    data_in[:, 0] = lons_in
    data_in[:, 1] = lats_in
    data_in[:, 2] = values_in

    # Create csv file
    create_file_csv(file_tmp_csv, data_in, values_tmp, lons_tmp, lats_tmp)

    # Create vrt file
    create_file_vrt(file_tmp_vrt, file_tmp_csv, layer_tmp, values_tmp, lons_tmp, lats_tmp)

    # Grid option(s)
    if interp_method == 'nearest':
        if interp_option is None:
            interp_option = ('-a nearest:radius1=' + str(interp_radius_lon) + ':radius2=' +
                             str(interp_radius_lat) + ':angle=0.0:nodata=' + str(interp_nodata))

    elif interp_method == 'idw':
        if interp_option is None:
            interp_option = ('-a invdist:power=2.0:smoothing=0.0:radius1=' + str(interp_radius_lon) + ':radius2=' +
                             str(interp_radius_lat) + ':angle=0.0:nodata=' + str(interp_nodata))

    else:
        raise NotImplementedError

    # Execute line command definition (using gdal_grid)
    cmp_line = ('gdal_grid -zfield "' + values_tmp + '"  -txe ' +
                str(lon_out_min) + ' ' + str(lon_out_max) + ' -tye ' +
                str(lat_out_min) + ' ' + str(lat_out_max) + ' -a_srs EPSG:' + str(epsg_code) + ' ' +
                interp_option + ' -outsize ' + str(lat_out_rows) + ' ' + str(lon_out_cols) +
                ' -of GTiff -ot Float32 -l ' + layer_tmp + ' ' +
                file_tmp_vrt + ' ' + file_tmp_tiff + ' --config GDAL_NUM_THREADS ALL_CPUS')

    # Execute algorithm
    [std_out, std_error, std_exit] = exec_process(command_line=cmp_line, command_path=folder_tmp)

    # Read data in tiff format and get values
    data_tmp = rasterio.open(file_tmp_tiff)
    values_tmp = data_tmp.read()

    # Image postprocessing to obtain 2d, south-north, east-west data
    values_out = values_tmp[0, :, :]
    values_out = np.flipud(values_out)

    # Delete tmp file(s)
    if exists(file_tmp_csv):
        remove(file_tmp_csv)
    if exists(file_tmp_vrt):
        remove(file_tmp_vrt)
    if exists(file_tmp_tiff):
        remove(file_tmp_tiff)

    return values_out
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to interpolate points to grid using gridded data
def interpolate_grid2map(lons_in, lats_in, values_in, lons_out, lats_out, nodata=-9999, interp_method='nearest'):

    values_out = griddata((lons_in.ravel(), lats_in.ravel()), values_in.ravel(),
                          (lons_out, lats_out), method=interp_method,
                          fill_value=nodata)
    return values_out
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to scale data using a mean-std scaling method
def mean_std(src_nrt, src_dr, ref_dr):

    return ((src_nrt - np.mean(src_dr)) /
            np.std(src_dr)) * np.std(ref_dr) + np.mean(ref_dr)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to scale data using mix-max normalized scaling method
def norm_min_max(src, ref):

    ref_min = np.min(ref) / 100
    ref_max = np.max(ref) / 100

    src = src / 100

    norm_src = (src - ref_min) / (ref_max - ref_min) * 100

    return norm_src
# -------------------------------------------------------------------------------------
