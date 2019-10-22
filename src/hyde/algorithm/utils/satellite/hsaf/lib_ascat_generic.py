# -------------------------------------------------------------------------------------
# Library
import subprocess
import numpy as np

from random import randint
from netCDF4 import Dataset
from datetime import datetime

from os import remove, chdir
from os.path import join, exists
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to execute process
def exec_process(command_line=None, command_path=None):

    try:

        # Execute command-line
        chdir(command_path)
        process_handle = subprocess.Popen(
            command_line, shell=True,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Read standard output
        while True:
            std_out = process_handle.stdout.readline()
            if isinstance(std_out, bytes):
                std_out = std_out.decode('UTF-8')

            if std_out == '' and process_handle.poll() is not None:

                if process_handle.poll() == 0:
                    break
                else:
                    raise RuntimeError

            if std_out:
                std_out = str(std_out.strip())

        # Collect stdout and stderr and exitcode
        std_out, std_error = process_handle.communicate()
        std_exit = process_handle.poll()

        if std_out == b'' or std_out == '':
            std_out = None
        if std_error == b'' or std_error == '':
            std_error = None

        # Return variable(s)
        return std_out, std_error, std_exit

    except subprocess.CalledProcessError:
        # Exit code for process error
        raise IOError

    except OSError:
        # Exit code for os error
        raise OSError

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to add time in a unfilled string (path or filename)
def fill_tags2string(string_raw, tags_format=None, tags_filling=None):

    apply_tags = False
    if string_raw is not None:
        for tag in list(tags_format.keys()):
            if tag in string_raw:
                apply_tags = True
                break

    if apply_tags:
        string_filled = string_raw.format(**tags_format)

        for tag_format_name, tag_format_value in list(tags_format.items()):

            if tag_format_name in list(tags_filling.keys()):
                tag_filling_value = tags_filling[tag_format_name]
                if tag_filling_value is not None:

                    if isinstance(tag_filling_value, datetime):
                        tag_filling_value = tag_filling_value.strftime(tag_format_value)

                    string_filled = string_filled.replace(tag_format_value, tag_filling_value)

        string_filled = string_filled.replace('//', '/')
        return string_filled
    else:
        return string_raw
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to delete time-series filename
def delete_file_cell(path_ts, filename_ts='%04d.nc', cells=None):

    if cells is not None:
        for i, cell in enumerate(cells):

            filename_ts_def = filename_ts % cell
            file_ts = join(path_ts, filename_ts_def)
            if exists(file_ts):
                remove(file_ts)

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to check time-series filename availability
def check_filename(path_ts, path_grid, filename_ts='%04d.nc',
                   filename_grid='TUW_WARP5_grid_info_2_3.nc', var_cell='cell'):

    dset_grid = Dataset(join(path_grid, filename_grid), 'r')
    cells = np.unique(dset_grid.variables[var_cell][:])

    n = cells.__len__()

    file_available = np.ones(n, dtype=np.bool)
    file_available[:] = False
    for i, cell in enumerate(cells):

        filename_ts_def = filename_ts % cell
        file_ts = join(path_ts, filename_ts_def)
        if exists(file_ts):
            file_available[i] = True

    if np.any(file_available == False):
        return False
    else:
        return True
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to create a random string
def random_string(string_root='temporary', string_sep='_', n_rand_min=0, n_rand_max=1000):

    # Generate random number
    n_rand = str(randint(n_rand_min, n_rand_max))
    # Generate time now
    time_now = datetime.now().strftime('%Y%m%d-%H%M%S_%f')

    # Concatenate string(s) with defined separator
    string_rand = string_sep.join([string_root, time_now, n_rand])

    return string_rand
# -------------------------------------------------------------------------------------
