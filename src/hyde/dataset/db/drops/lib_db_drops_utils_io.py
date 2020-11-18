"""
Library Features:

Name:          lib_db_drops_apps_io
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180912'
Version:       '1.0.1'
"""
#######################################################################################
# Logging
import logging
#######################################################################################


# -------------------------------------------------------------------------------------
# Method to write dateframe in csv format
def writeSensorDataFrame(sFileName, oDataFrame, 
                         sDataSeparetor=',', sDataEncoding='utf-8', bDataIndex=False, bDataHeader=True):

    oVarName = list(oDataFrame.columns.values)

    oDataFrame.to_csv(sFileName, sep=sDataSeparetor, encoding=sDataEncoding, 
                      index=bDataIndex, index_label=False, header=bDataHeader,
                      columns=oVarName)
# -------------------------------------------------------------------------------------
