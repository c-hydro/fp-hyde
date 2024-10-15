"""
Library Features:

Name:          lib_data_io_pickle
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20230727'
Version:       '1.0.0'
"""

# ----------------------------------------------------------------------------------------------------------------------
# libraries
import logging
import os
import pickle
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to read file obj
def read_file_obj(file_name):
    if os.path.exists(file_name):
        file_data = pickle.load(open(file_name, "rb"))
    else:
        logging.warning(' ===> File obj "' + file_name + '" not found')
        file_data = None
    return file_data
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# method to write file obj
def write_file_obj(file_name, file_data):
    if os.path.exists(file_name):
        os.remove(file_name)
    with open(file_name, 'wb') as handle:
        pickle.dump(file_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
# ----------------------------------------------------------------------------------------------------------------------
