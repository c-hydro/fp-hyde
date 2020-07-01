"""
Library Features:

Name:          lib_utils_apps_process
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180521'
Version:       '2.0.7'
"""
#######################################################################################
# Library
import logging
import os
import time
import subprocess
import signal

from inspect import currentframe, getframeinfo
from os import stat, chmod

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
#######################################################################################

# -------------------------------------------------------------------------------------
# Method to make executable a bash file
def makeProcess(file):
    mode = stat(file).st_mode
    mode |= (mode & 0o444) >> 2    # copy R bits to X
    chmod(file, mode)
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to check process
def checkProcess(sCLine=None, sCPath=None, iTimeError=0.001, iTimeWait=1, iTimePool=0.1):

    # Info checking starting
    oLogStream.info(' -----> Process checking: ' + sCLine + ' ... ')

    # Checking command before execution (to find errors) with a given time
    os.chdir(sCPath)
    oProcess = subprocess.Popen(sCLine, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    oProcess.poll()

    # Check process to control library or memory error(s)
    while oProcess.returncode is None and iTimeWait > 0:
        time.sleep(iTimePool)
        iTimeWait -= iTimePool
        oProcess.poll()

    # Condition to define if process checking is fine or not
    if iTimeWait <= 0:              # process request stops for time out

        # Checking process for run until time-out
        iPID = oProcess.pid + 1     # There is a difference between python-pid and htop-pid (+1)
        os.kill(iPID, signal.SIGTERM)
        # Information process for run until time-out
        oLogStream.info(' -----> Process checking: ' + sCLine + ' ... OK [run time-out]')

    elif iTimeWait < iTimeError:  # process request stops for errors

        # Checking stops for error(s)
        oFrameInfo = getframeinfo(currentframe())
        # Information about stop for error(s)
        oLogStream.info(' -----> Process checking: ' + sCLine + ' ... FAILED!')
        Exc.getExc(' =====> ERROR: process checking failed for library or memory errors!', 1, 1,
                   oFrameInfo.filename, oFrameInfo.lineno)

    else:
        # Information process for run closing
        oLogStream.info(' -----> Process checking: ' + sCLine + ' ... OK [run ending]')

    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to execute process
def execProcess(sCLine=None, sCPath=None):

    try:

        # Info command-line start
        oLogStream.info(' -----> Process execution: ' + sCLine + ' ... ')

        # Execute command-line
        os.chdir(sCPath)
        oProcess = subprocess.Popen(sCLine, shell=True,
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)

        # Read standard output
        while True:
            sOut = oProcess.stdout.readline()
            if isinstance(sOut, bytes):
                sOut = sOut.decode('UTF-8')

            if sOut == '' and oProcess.poll() is not None:

                if oProcess.poll() == 0:
                    Exc.getExc(' =====> WARNING: Process POOL = ' + str(oProcess.poll()) + ' KILLED!', 2, 1)
                    break
                else:
                    Exc.getExc(' =====> ERROR: run failed! Check your settings!', 1, 1)
            if sOut:
                oLogStream.info(str(sOut.strip()))

        # Collect stdout and stderr and exitcode
        sStdOut, sStdErr = oProcess.communicate()
        iStdExit = oProcess.poll()

        if sStdOut == b'' or sStdOut == '':
            sStdOut = None
        if sStdErr == b'' or sStdErr == '':
            sStdErr = None

        # Check stream process
        streamProcess(sStdOut, sStdErr)

        # Info command-line end
        oLogStream.info(' -----> Process execution: ' + sCLine + ' ... OK ')
        return sStdOut, sStdErr, iStdExit

    except subprocess.CalledProcessError:
        # Exit code for process error
        Exc.getExc(' =====> ERROR: process execution FAILED! Errors in the called executable!', 1, 1)

    except OSError:
        # Exit code for os error
        Exc.getExc(' =====> ERROR: process execution FAILED! Executable not found!', 1, 2)

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to stream process
def streamProcess(sOut=None, sErr=None):

    if sOut is None and sErr is None:
        return True
    else:
        Exc.getExc(' =====> WARNING: error(s) occurred during process execution!', 2, 1)
        return False
# -------------------------------------------------------------------------------------
