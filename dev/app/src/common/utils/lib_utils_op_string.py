"""
Library Features:

Name:          lib_utils_op_string
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180521'
Version:       '2.0.7'
"""

#######################################################################################
# Library
import logging

from random import randint
from sys import version_info
from datetime import datetime

from src.common.default.lib_default_args import sLoggerName
from src.common.driver.configuration.drv_configuration_debug import Exc

# Logging
oLogStream = logging.getLogger(sLoggerName)

# Debug
# import matplotlib.pylab as plt
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to create a random string
def randomString(sStringRoot='temporary', sStringSeparator='_', iMinRandom=0, iMaxRandom=1000):

    # Generate random number
    sRandomNumber = str(randint(iMinRandom, iMaxRandom))
    # Generate time now
    sTimeNow = datetime.now().strftime('%Y%m%d-%H%M%S_%f')

    # Concatenate string(s) with defined separator
    sRandomString = sStringSeparator.join([sStringRoot, sTimeNow, sRandomNumber])

    return sRandomString
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to convert string from unicode type (for different python version interpreter)
def convertString(oString):
    if version_info >= (3, 0):
        return oString
    elif version_info < (3, 0):
        return convertUnicode2ASCII(oString)

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to define string
def defineString(oDataString='', oDictTags=None):

    # Check data string
    if oDataString is None:
        oDataString == ''

    # Iterate over no-empty data string
    oString = None
    oKeys = None
    oStrings = None
    if oDataString != '':

        # Check python version to unicode and string variable conversion
        if version_info < (3, 0):

            if isinstance(oDataString, dict):
                for sKey, sValue in oDataString.items():
                    oDataString.pop(sKey, None)
                    sValue = convertUnicode2ASCII(sValue)
                    sKey = convertUnicode2ASCII(sKey)
                    oDataString[sKey] = sValue
            else:
                oDataString = convertUnicode2ASCII(oDataString)

        # Check data string format
        if isinstance(oDataString, str):
            oString = [oDataString]
        elif isinstance(oDataString, dict):
            oString = []
            oKeys = []
            for sKey, sValue in oDataString.items():
                oString.append(sValue)
                oKeys.append(sKey)

        # Iterate over selected string
        oStrings = []
        for sString in oString:

            if not oDictTags:
                pass
            elif oDictTags:

                for sKey, oValue in iter(oDictTags.items()):

                    if isinstance(oValue, list):            # list values
                        sVarKey = oValue[0]
                        oVarValue = oValue[1]
                    elif isinstance(oValue, dict):          # dict values
                        sVarKey = list(oValue.keys())[0]
                        oVarValue = list(oValue.values())[0]
                    else:                                   # scalar value
                        sVarKey = sKey
                        oVarValue = oValue

                    if isinstance(oVarValue, str):
                        sString = sString.replace(sVarKey, oVarValue)
                    elif isinstance(oVarValue, int):
                        sString = sString.replace(sVarKey, str(int(oVarValue)))
                    elif isinstance(oVarValue, float):
                        sString = sString.replace(sVarKey, str(float(oVarValue)))
                    else:
                        sString = sString.replace(sVarKey, str(oVarValue))
            if oKeys:
                oStrings.append(sString)
            else:
                oStrings = sString

        if oKeys:
            oDefString = dict(zip(oKeys, oStrings))
        else:
            oDefString = oStrings

    else:
        oDefString = None

    return oDefString
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to convert UNICODE to ASCII
def convertUnicode2ASCII(sStringUnicode, convert_option='ignore'):
    # convert_option "ignore" or "replace"
    sStringASCII = sStringUnicode.encode('ascii', convert_option)
    return sStringASCII
# -------------------------------------------------------------------------------------
