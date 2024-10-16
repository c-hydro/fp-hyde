"""
Library Features:

Name:          lib_utils_logging
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210408'
Version:       '1.0.0'
"""

# ----------------------------------------------------------------------------------------------------------------------
# libraries
import logging
import functools
import os
import logging.config
import glob

from lib_info_args import logger_name as logger_name_default
from lib_info_args import logger_file as logger_file_default
from lib_info_args import logger_handle as logger_handle_default
from lib_info_args import logger_format as logger_formatter_default
from lib_utils_system import make_folder

# debugging
# import matplotlib.pylab as plt
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Method to set logging file
def set_logging_file(logger_file=logger_file_default, logger_name=logger_name_default,
                     logger_handle=logger_handle_default, logger_formatter=logger_formatter_default,
                     logger_history=False, logger_history_maxfiles=12,
                     logger_extra_tags=None):

    # Set to flush progressbar output in logging stream handle
    # progressbar.streams.wrap_stderr()

    if logger_extra_tags is not None:
        for extra_key, extra_value in logger_extra_tags.items():
            logger_file = logger_file.replace(extra_key, ':')
            string_count = logger_file.count(':')
            extra_value = [extra_value] * string_count
            logger_file = logger_file.format(*extra_value)

    logger_folder_name, logger_file_name = os.path.split(logger_file)
    make_folder(logger_folder_name)

    # Save old logger file (to check run in the past)
    if logger_history:
        store_logging_file(logger_file, logger_file_max=logger_history_maxfiles)

    # Remove old logging file
    if os.path.exists(logger_file):
        os.remove(logger_file)

    # Open logger
    logging.getLogger(logger_name)
    logging.root.setLevel(logging.DEBUG)

    # Set logger handle type
    if logger_handle == 'file':

        # Set logger handler obj
        logger_handle_1 = logging.FileHandler(logger_file, 'w')
        logger_handle_2 = logging.StreamHandler()
        # Set logger level
        logger_handle_1.setLevel(logging.DEBUG)
        logger_handle_2.setLevel(logging.DEBUG)
        # Set logger formatter
        logger_handle_1.setFormatter(logging.Formatter(logger_formatter))
        logger_handle_2.setFormatter(logging.Formatter(logger_formatter))
        # Add handle to logger
        logging.getLogger('').addHandler(logger_handle_1)
        logging.getLogger('').addHandler(logger_handle_2)

    elif logger_handle == 'stream':

        # Set logger handler obj
        logging.StreamHandler()
        # Set logger level
        logger_handle.setLevel(logging.DEBUG)
        # Set logger formatter
        logger_handle.setFormatter(logging.Formatter(logger_formatter))
        # Add handle to logger
        logging.getLogger('').addHandler(logger_handle)

    else:

        # Set logger handler obj
        logging.NullHandler()
        # Add handle to logger
        logging.getLogger('').addHandler(logger_handle)

# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Method to store logging file (to save execution history)
def store_logging_file(logger_file, logger_ext='.old.{}', logger_file_max=12):

    # Get logger folder
    logger_folder = os.path.split(logger_file)[0]

    # Iterate to store old logging file
    if os.path.exists(logger_file):

        logger_file_loop = logger_file
        logger_file_id = 0
        while os.path.exists(logger_file_loop):
            logger_file_id = logger_file_id + 1
            logger_file_loop = logger_file + logger_ext.format(logger_file_id)

            if logger_file_id > logger_file_max:
                logger_file_obj = glob.glob(os.path.join(logger_folder, '*'))
                for logger_file_step in logger_file_obj:
                    if logger_file_step.startswith(logger_file):
                        os.remove(logger_file_step)
                logger_file_loop = logger_file
                break

        if logger_file_loop:
            if logger_file != logger_file_loop:
                os.rename(logger_file, logger_file_loop)
# ----------------------------------------------------------------------------------------------------------------------
