# -------------------------------------------------------------------------------------
# Libraries
import logging
import os
import subprocess

from bin.downloader.modis.lib_utils_system import remove_url
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to execute mrt command-line
def execute_mrt_cmd(mrt_cmd):
    # Create process handle
    process_handle = subprocess.Popen(mrt_cmd, shell=True,
                                      stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    # Execute command-line
    process_handle.communicate()
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define mrt resample settings file
def define_mrt_resample_file(file_name_in, file_name_parameters, file_name_out,
                             spatial_subset_type='OUTPUT_PROJ_COORDS', resampling_type='NN',
                             proj='GEO', datum='WGS84'):

    # Define resample file
    file_lines = dict()
    file_lines[0] = str('INPUT_FILENAME = ' + file_name_in) + '\n'
    file_lines[1] = str('SPATIAL_SUBSET_TYPE = ' + spatial_subset_type) + '\n'
    file_lines[2] = str('OUTPUT_FILENAME =  ' + file_name_out) + '\n'
    file_lines[3] = str('RESAMPLING_TYPE = ' + resampling_type) + '\n'
    file_lines[4] = str('OUTPUT_PROJECTION_TYPE = ' + proj) + '\n'
    file_lines[5] = str('DATUM =  ' + datum) + '\n'

    # Open, write and close parameters file
    file_handle = open(file_name_parameters, 'w')
    file_handle.writelines(file_lines.values())
    file_handle.close()

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define mrt resample command-line
def define_mrt_resample_cmd(file_name_parameters,
                            mrt_folder='/mrt-4.1/bin/', mrt_executable='mrtmosaic'):

    cmd_resample = (os.path.join(mrt_folder, mrt_executable) + ' -p ' + file_name_parameters)

    return cmd_resample

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define mrt mosaic settings file
def define_mrt_mosaic_file(file_name_tile, tile_list):

    # Create tile dictionary
    tile_dict = None
    for tile_id, tile_step in enumerate(tile_list):
        if (tile_step is not None) and (os.path.exists(tile_step)):
            if tile_dict is None:
                tile_dict = {}
            tile_dict[tile_id] = tile_step + '\n'
        else:
            if tile_step is not None:
                logging.warning(' ===> Tile ' + tile_step + ' not found! Domain coverage could not be completed.')
            else:
                logging.warning(' ===> Tile expected with id ' + str(tile_id) + ' is not available. Object is None')

    if tile_dict is not None:
        file_handle = open(file_name_tile, 'w')
        file_handle.writelines(tile_dict.values())
        file_handle.close()
        return True
    else:
        return False

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to define mrt mosaic command-line
def define_mrt_mosaic_cmd(file_name_tile_in, file_name_tile_out,
                          mrt_folder='/mrt-4.1/bin/', mrt_executable='mrtmosaic'):

    cmd_mosaic = (os.path.join(mrt_folder, mrt_executable) +
                  ' -i ' + file_name_tile_in + ' -o ' + file_name_tile_out)

    return cmd_mosaic

# -------------------------------------------------------------------------------------
