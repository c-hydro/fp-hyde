"""
Library Features:

Name:          lib_hs_process
Author(s):     Francesco Avanzi (francesco.avanzi@cimafoundation.org), Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20210525'
Version:       '1.0.0'
"""
#######################################################################################
# Library
import logging
import subprocess

import os

from os import stat, chmod

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to make executable a bash file
def make_process(file):
    mode = stat(file).st_mode
    mode |= (mode & 0o444) >> 2    # copy R bits to X
    chmod(file, mode)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to execute process
def exec_process(command_line=None, command_path=None):

    try:

        # Info command-line start
        logging.info(' ---> Process execution: ' + command_line + ' ... ')

        # Execute command-line
        if command_path is not None:
            os.chdir(command_path)
        process_handle = subprocess.Popen(
            command_line, shell=True,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Read standard output
        while True:
            string_out = process_handle.stdout.readline()
            if isinstance(string_out, bytes):
                string_out = string_out.decode('UTF-8')

            if string_out == '' and process_handle.poll() is not None:

                if process_handle.poll() == 0:
                    break
                else:
                    logging.error(' ===> Run failed! Check command-line settings!')
                    raise RuntimeError('Error in executing process')
            if string_out:
                logging.info(str(string_out.strip()))

        # Collect stdout and stderr and exitcode
        std_out, std_err = process_handle.communicate()
        std_exit = process_handle.poll()

        if std_out == b'' or std_out == '':
            std_out = None
        if std_err == b'' or std_err == '':
            std_err = None

        # Check stream process
        stream_process(std_out, std_err)

        # Info command-line end
        logging.info(' ---> Process execution: ' + command_line + ' ... DONE')
        return std_out, std_err, std_exit

    except subprocess.CalledProcessError:
        # Exit code for process error
        logging.error(' ===> Process execution FAILED! Errors in the called executable!')
        raise RuntimeError('Errors in the called executable')

    except OSError:
        # Exit code for os error
        logging.error(' ===> Process execution FAILED!')
        raise RuntimeError('Executable not found!')

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to stream process
def stream_process(std_out=None, std_err=None):

    if std_out is None and std_err is None:
        return True
    else:
        logging.warning(' ===> Exception occurred during process execution!')
        return False
# -------------------------------------------------------------------------------------
