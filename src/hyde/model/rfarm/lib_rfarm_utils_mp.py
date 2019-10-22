"""
Library Features:

Name:           lib_rfarm_utils_mp
Author(s):      Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:           '20170530'
Version:        '3.5.0'
"""

#######################################################################################
# Logging
import logging

import os
import multiprocessing as mp

from src.hyde.algorithm.settings.rfarm.lib_rfarm_args import logger_name

log_stream = logging.getLogger(logger_name)

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to get process id
def getProcessInfo(sTitle):
    # Info
    log_stream.info(' ------> Info: ' + str(sTitle) + ' ModuleName: ' + str(__name__))

    if hasattr(os, 'getppid'):  # only available on Unix
        log_stream.info(' -------> Parent process id: ' + str(os.getppid()))

    log_stream.info(' -------> Process id: ' + str(os.getppid()))

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get process signal start
def getProcessSignalStart():
    # Info
    log_stream.info(' ------> Process: ' + str(mp.current_process().name) + ' ... START')

# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get process signal end
def getProcessSignalEnd(oP):
    # Info
    log_stream.info(' ------> Process: ' + str(oP.name) + ' ExitCode: ' + str(oP.exitcode) + ' ... CLOSED')

# -------------------------------------------------------------------------------------
