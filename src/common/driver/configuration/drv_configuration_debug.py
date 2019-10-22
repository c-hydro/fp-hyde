"""
Class Features

Name:          drv_configuration_debug
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20161114'
Version:       '2.0.6'

Example:

import logging                                           # import logging library
oLogStream = logging.getLogger('sLogger')
from Drv_HMC_Exception import Exc                     # import Exception class

Exc.getExc(' -----> ERROR: test error!', 1, 1)            # error mode
Exc.getExc(' -----> WARNING: test warning!', 2, 1)        # warning mode
Exc.getExc('',0,0)                                        # no error mode
"""

######################################################################################
# Library
import logging

# Log
oLogStream = logging.getLogger(__name__)
######################################################################################

# -------------------------------------------------------------------------------------
# Method to parse trace
def parserTrace(oListTrace):
    oTraceReg = []
    for sTraceList in oListTrace:

        # sTraceList = sTraceList.replace(' ', '')
        sTraceList = sTraceList.strip()
        oTraceReg.append(sTraceList)

    return oTraceReg
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Class Exc
class Exc:
    # -------------------------------------------------------------------------------------
    # Method init class
    def __init__(self):
        pass
    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Method to get exception
    @classmethod
    def getExc(cls, sExcMessage, iExcType, iExcCode=-9999, sFileName='undefined', iFileLine=-9999,
               oExcRaised=None):

        # Get global information
        cls.sExcMessage = sExcMessage
        cls.iExcType = iExcType

        # Extra information (not mandatory)
        cls.iExcCode = str(iExcCode)
        cls.sFileName = str(sFileName)
        cls.iFileLine = str(iFileLine)

        cls.oExcRaised = oExcRaised

        # Get Exception
        if cls.iExcType == 1:
            cls.__getError(cls.sExcMessage, cls.iExcCode, cls.sFileName, cls.iFileLine, cls.oExcRaised)
        elif cls.iExcType == 2:
            cls.__getWarning(cls.sExcMessage, cls.oExcRaised)
        elif cls.iExcType == 3:
            cls.__getCritical()
        if cls.iExcType == 0:
            cls.__getNone()
        else:
            pass

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get error
    @staticmethod
    def __getError(sExcMessage, iExcCode, sFileName, iFileLine, oExcRaised=None):

        # -------------------------------------------------------------------------------------
        # Library
        import traceback
        import sys

        from os.path import split
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Get system information
        oExcType, oExcOBJ, oExcTB = sys.exc_info()

        if oExcTB:
            sExpFileName = split(oExcTB.tb_frame.f_code.co_filename)[1]
            iExpFileLine = oExcTB.tb_lineno
        else:
            sExpFileName = sFileName
            iExpFileLine = iFileLine

        # Parser trace information
        oTrace = parserTrace(traceback.format_exc().splitlines())

        # Write EXC information on log
        oLogStream.info(sExcMessage)
        oLogStream.error('[EXC_INFO]: ' + str(sys.exc_info()[0]))
        oLogStream.error('[EXC_CODE]: ' + str(iExcCode))
        oLogStream.error('[EXC_FILENAME]: ' + sExpFileName)
        oLogStream.error('[EXC_FILELINE]: ' + str(iExpFileLine))

        if oExcRaised is not None:
            oLogStream.error('[EXC_RAISED]: ' + str(oExcRaised))

        for sTrace in oTrace:
            oLogStream.error('[EXC_TRACE]: ' + str(sTrace))

        # Fatal Error --> Exit the program with 1      
        sys.exit(1)
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get warning
    @staticmethod
    def __getWarning(sExcMessage, oExcRaised=None):

        # -------------------------------------------------------------------------------------
        # Write WARNING information on log
        if oExcRaised is None:
            oLogStream.info(sExcMessage)
        else:
            oLogStream.info(sExcMessage + ' == Exception Raised: [' + str(oExcRaised) + ']')

        if oExcRaised is None:
            oLogStream.warning(sExcMessage)
        else:
            oLogStream.warning(sExcMessage + ' == Exception Raised: [' + str(oExcRaised) + ']')
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get critical
    @staticmethod
    def __getCritical():
        pass

    # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Get none
    @staticmethod
    def __getNone():

        # -------------------------------------------------------------------------------------
        # Library
        import sys
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Write NO ERROR information on log
        oLogStream.info('[EXC_INFO]: None')
        oLogStream.info('[EXC_CODE]: None')
        oLogStream.info('[EXC_FILENAME]: None')
        oLogStream.info('[EXC_FILELINE]: None')
        oLogStream.info('[EXC_TRACE]: None')

        # No Error --> Exit the program with 0   
        sys.exit(0)
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
