"""
Library Features:

Name:          lib_data_io_binary
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20201203'
Version:       '1.5.0'
"""
#################################################################################
# Library
import logging
import numpy as np
import struct

# Debug
import matplotlib.pylab as plt
#################################################################################


# --------------------------------------------------------------------------------
# Method to write 2d variable in binary format (saved as 1d integer array)
def write_var2d(file_name, file_data, file_format='i', scale_factor=10):

    # Open file handle
    file_handle = open(file_name, 'wb')

    # Define nodata value
    no_data = -9999.0
    no_data = no_data / scale_factor

    # Values shape
    file_n = file_data.shape[0] * file_data.shape[1]
    # Values format
    data_format = file_format * file_n

    # Define nodata value (instead of NaN values)
    file_data[np.where(np.isnan(file_data))] = no_data

    # NOTA BENE:
    # NON OCCORRE FARE IL FLIPUD SE LE VAR SONO ORIENTATE IN MODO CORRETTO partendo da angolo
    # IN BASSO A SX [sud-->nord ovest --> est]
    # a1iVarData = np.int32((numpy.flipud(a2dVarData)).reshape(iNVals, order='F') * iScaleFactor)

    array_data = np.int32(((file_data)).reshape(file_n, order='F') * scale_factor)
    data_binary = struct.pack(data_format, *(array_data))

    # Write and close file handle
    file_handle.write(data_binary)
    file_handle.close()

# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to read 2d variable in binary format (saved as 1d integer array)
def read_var2d(file_name, rows, cols, file_format='i', scale_factor=10):

    # Open file handle
    file_handle = open(file_name, 'rb')

    # Values shape (1d)
    file_n = rows * cols
    # Values format
    data_format = file_format * file_n
    # Open and read binary file
    file_stream = file_handle.read(-1)
    array_data = struct.unpack(data_format, file_stream)

    # Reshape binary file in Fortran order and scale Data (float32)
    file_data = np.reshape(array_data, (rows, cols), order='F')
    file_data = np.float32(file_data / scale_factor)

    # Close file handle
    file_handle.close()

    # Debug
    # plt.figure(1)
    # plt.imshow(a2dVarDataCheck); plt.colorbar()
    # plt.show()

    return file_data

# --------------------------------------------------------------------------------
