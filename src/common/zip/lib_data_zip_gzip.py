"""
Library Features:

Name:          lib_data_zip_gzip
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20190913'
Version:       '2.1.0'
"""
#################################################################################
# Library
import logging
import gzip

# Logging
log_stream = logging.getLogger(__name__)
#################################################################################


# --------------------------------------------------------------------------------
# Method to open zip file
def openZip(filename_in, filename_out, zip_mode='z'):

    # Check method
    try:

        # Open file
        if zip_mode == 'z':  # zip mode
            file_handle_in = open(filename_in, 'rb')
            file_handle_out = gzip.open(filename_out, 'wb')
        elif zip_mode == 'u':  # unzip mode
            file_handle_in = gzip.GzipFile(filename_in, "rb")
            file_handle_out = open(filename_out, "wb")
        else:
            log_stream.error(' =====> ERROR: in open file (GZip Zip) not valid zip mode flag')
            raise NotImplemented

        # Pass file handle(s)
        return file_handle_in, file_handle_out

    except IOError as oError:
        log_stream.error(' =====> ERROR: in open file (GZip Zip)' + ' [' + str(oError) + ']')
        raise IOError
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to close zip file
def closeZip(file_handle_in=None, file_handle_out=None):
    if file_handle_in:
        file_handle_in.close()
    if file_handle_out:
        file_handle_out.close()
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to zip file
def zipFile(file_handle_in=None, file_handle_out=None):
    if file_handle_in and file_handle_out:
        file_handle_out.writelines(file_handle_in)
    else:
        log_stream.error(' =====> ERROR: in zip file (GZip Zip)')
        raise IOError
# --------------------------------------------------------------------------------


# --------------------------------------------------------------------------------
# Method to unzip file
def unzipFile(file_handle_in=None, file_handle_out=None):
    if file_handle_in and file_handle_out:
        oDecompressData = file_handle_in.read()
        file_handle_out.write(oDecompressData)
    else:
        log_stream.error(' =====> ERROR: in unzip file (GZip Zip)')
        raise IOError
# --------------------------------------------------------------------------------
