"""
Library Features:

Name:          lib_db_drops_utils_sensor_ws
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180912'
Version:       '1.0.1'
"""
#######################################################################################
# Logging
import logging

from pandas import DataFrame, date_range, to_datetime, to_numeric
from datetime import datetime
from numpy import zeros, nan
#######################################################################################

# -------------------------------------------------------------------------------------
# Method to create sensor(s) data frame 
def createSensorDataFrame(a1oSensorData, a1oSensorName, a2oSensorRegistry, 
                          sSensorUnit = 'NA', sSensorFreq='H', 
                          oSensorFields=None):

    # Initialize sensor field(s)
    if oSensorFields is None:
        oSensorFields = ["longitude", "latitude", "data", "time_start", "time_end", "units", "name", "altitude", "code"]

    # Initialize sensor dataframe workspace
    oSensorDF_NAME = []
    oSensorDF_CODE = []
    oSensorDF_GEOX = []
    oSensorDF_GEOY = []
    oSensorDF_GEOZ = []
    oSensorDF_VALUE = []
    oSensorDF_TIME_START = []
    oSensorDF_TIME_END = []
    oSensorDF_UNIT = []

    # Get time and values 
    sSensorTime = a1oSensorData[0][0]
    oSensorValue = a1oSensorData[0][1]

    # Iterate over sensor registry
    for iSensorID, oSensorRegistry in enumerate(a2oSensorRegistry):

        # Parse and control sensor registry name
        sSensorRegistry_NAME = oSensorRegistry[0].strip()
        iSensorRegistry_CODE = int(oSensorRegistry[1])
        dSensorRegistry_GEOX = float(oSensorRegistry[2])
        dSensorRegistry_GEOY = float(oSensorRegistry[3])
        dSensorRegistry_GEOZ = float(oSensorRegistry[4])

        # Find DB name in registry name
        if sSensorRegistry_NAME in a1oSensorName:
            iSensorRegistry_IDX = [iX for iX, sField in enumerate(a1oSensorName) if sSensorRegistry_NAME in sField][0]
        else:
            iSensorRegistry_IDX = None

        # Check station idx
        if iSensorRegistry_IDX is not None:
            # Get section data
            dSensorData_VALUE = float(oSensorValue[iSensorRegistry_IDX])
        else:
            dSensorData_VALUE = -9999.0

        # Define sensor name
        sSensorRegistry_NAME = sSensorRegistry_NAME.replace(' ', '_')

        # Define time_from and time_to
        oSensorTime_RANGE = date_range(end=sSensorTime, periods=2, freq=sSensorFreq)

        # Store data in list object(s)
        oSensorDF_NAME.append(sSensorRegistry_NAME)
        oSensorDF_CODE.append(iSensorRegistry_CODE)
        oSensorDF_GEOX.append(dSensorRegistry_GEOX)
        oSensorDF_GEOY.append(dSensorRegistry_GEOY)
        oSensorDF_GEOZ.append(dSensorRegistry_GEOZ)
        oSensorDF_VALUE.append(dSensorData_VALUE)
        oSensorDF_TIME_START.append(oSensorTime_RANGE[0])
        oSensorDF_TIME_END.append(oSensorTime_RANGE[1])
        oSensorDF_UNIT.append(sSensorUnit)

    # Create dataframe
    oSensorDF = DataFrame({'longitude': oSensorDF_GEOX, 'latitude': oSensorDF_GEOY, 'altitude': oSensorDF_GEOZ,
                           'data': oSensorDF_VALUE, 'name': oSensorDF_NAME, 'code': oSensorDF_CODE,
                           'time_start': oSensorDF_TIME_START, 'time_end': oSensorDF_TIME_END,
                           'units': oSensorDF_UNIT},
                           columns=oSensorFields)

    # Define dataframe dtype(s)
    oSensorDF["longitude"] = to_numeric(oSensorDF["longitude"])
    oSensorDF["latitude"] = to_numeric(oSensorDF["latitude"])
    oSensorDF["altitude"] = to_numeric(oSensorDF["altitude"])
    oSensorDF["data"] = to_numeric(oSensorDF["data"])
    oSensorDF["code"] = to_numeric(oSensorDF["code"])
    oSensorDF["time_start"] = oSensorDF["time_start"]  
    oSensorDF["time_end"] = oSensorDF["time_end"]      

    return oSensorDF
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to parse sensor time in a given format time
def parseSensorTime(sSensorTime, sTimeFormat_OUT="%Y%m%d%H%M", sTimeFormat_IN='%d/%m/%Y %H:%M'):
    # Parse time
    oSensorTime = datetime.strptime(sSensorTime, sTimeFormat_IN)
    sSensorTime = oSensorTime.strftime(sTimeFormat_OUT)
    return sSensorTime
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to parse registry sensor(s)
def parseSensorRegistry(oSensorRegistry):

    # Get number sensor(s)
    iSensorN = oSensorRegistry.elementCount

    # Cycle(s) on sensor(s)
    a1oSensorName = []
    a1oSensorCode = []
    a1oSensorGeoX = []
    a1oSensorGeoY = []
    a1oSensorGeoZ = []
    for iS in range(0, iSensorN):

        # Objects sensor(s)
        oSensorInfo = oSensorRegistry.get(iS)

        # Storing code sensor(s)
        a1oSensorName.append(str(oSensorInfo.m_sName))
        # Storing code sensor(s)
        a1oSensorCode.append(int(oSensorInfo.m_sCode))
        # Storing lon sensor(s)
        a1oSensorGeoX.append(float(oSensorInfo.m_fLon))
        # Storing lat sensor(s)
        a1oSensorGeoY.append(float(oSensorInfo.m_fLat))
        # Storing lat sensor(s)
        a1oSensorGeoZ.append(float(oSensorInfo.m_iAltitude))

    a2oSensorRegistry = zip(a1oSensorName, a1oSensorCode, a1oSensorGeoX, a1oSensorGeoY, a1oSensorGeoZ)

    return a2oSensorRegistry

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to parse data sensor(s)
def parseSensorData(oSensorData, sTimeFormat="%Y%m%d%H%M"):

    # Get number sensor(s)
    iSensorN = oSensorData.m_aoDataStation.size()
    # Get time step(s)
    iTimeN = oSensorData.m_aoReferenceTimes.size()

    # Cycle(s) on time step(s)
    a1oSensorTime = []
    a1oSensorName = []
    a2dSensorData = zeros((iSensorN, iTimeN))
    a2dSensorData[:, :] = nan
    for iT in range(0, iTimeN):

        # Get time and convert using time format
        sSensorTime = parseSensorTime(oSensorData.m_aoReferenceTimes.get(iT).toString(), sTimeFormat)

        # Store times array (str array 1d)
        a1oSensorTime.append(sSensorTime)

        # Cycling on sensor number
        for iS in range(0, iSensorN):

            if iT == 0:
                # Store sensor name (first occurence)
                a1oSensorName.append(str(oSensorData.m_aoDataStation.get(iS).m_sName))

            # Storing data array (2d)
            a2dSensorData[iS, iT] = oSensorData.GetObservation(iS, iT)

    a2oSensorData = []
    for iSensorTime, sSensorTime in enumerate(sorted(a1oSensorTime)):

        oSensorTime = [sSensorTime]
        a1oSensorData = oSensorTime + [a2dSensorData[:, iSensorTime]]
        a2oSensorData.append(a1oSensorData)

    # Remove first data
    a2oSensorData = a2oSensorData[1:]

    return a2oSensorData, a1oSensorName
# -------------------------------------------------------------------------------------
