"""
Library Features:

Name:          lib_db_drops_apps_sensor
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180912'
Version:       '1.0.1'
"""
#######################################################################################
# Logging
import logging
#######################################################################################

# -------------------------------------------------------------------------------------
# List of valid sensor type
oSensorList = ['Raingauge', 'Thermometer', 'Hydrometer', 'RadiationSensor', 'Hygrometer',
               'WindSensor', 'WindDirection', 'Snowgauge', 'Barometer']
# -------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------
# Method to get sensor(s) type
def getSensorType(sSensorType, oDROPS):

    # Check if sensor type available in sensor list
    if sSensorType in oSensorList:
        # Select sensor type
        try:
            if sSensorType == 'Raingauge':
                oSensorType = oDROPS.EObservationType.Pluviometer
            elif sSensorType == 'Thermometer':
                oSensorType = oDROPS.EObservationType.Thermometer
            elif sSensorType == 'Hydrometer':
                oSensorType = oDROPS.EObservationType.Hydrometer
            elif sSensorType == 'RadiationSensor':
                oSensorType = oDROPS.EObservationType.RadiationSensor
            elif sSensorType == 'Hygrometer':
                oSensorType = oDROPS.EObservationType.Hygrometer
            elif sSensorType == 'WindSensor':
                oSensorType = oDROPS.EObservationType.WindSensor
            elif sSensorType == 'WindDirection':
                oSensorType = oDROPS.EObservationType.WindDirection
            elif sSensorType == 'Snowgauge':
                oSensorType = oDROPS.EObservationType.Snowgauge
            elif sSensorType == 'Barometer':
                oSensorType = oDROPS.EObservationType.Barometer

        except BaseException:
            # Exit with error about sensor type
            logging.error(' ------> ERROR: Sensor type not correctly loaded!')
    else:
        # Exit with error about sensor type
        logging.error(' ------> ERROR: Sensor type not in valid definition!')

    # Return variable(s)
    return oSensorType

# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to get sensor(s) registry
def getSensorRegistry(dGeoXMin, dGeoYMin, dGeoXMax, dGeoYMax,
                       oSensorType, oDROPS, oEXPDATA):
    # Get registry supplier
    oRegistrySupplier = oDROPS.AcroFourSuppliers.CDataStationSupplier()
    # Get registry Sensor(s)
    oSensorRegistry = oRegistrySupplier.GetByArea(oEXPDATA.GeoRef.GeoWindow(dGeoXMin, dGeoYMin, dGeoXMax, dGeoYMax),
                                                   oSensorType)
    # Return variable
    return oSensorRegistry
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to get sensor(s) data
def getSensorData(sTimeFrom, sTimeTo, iTimeDelta,
                   oSensorRegistry, oSensorType, oDROPS, oEXPDATA):

    # Get data supplier
    oDataSupplier = oDROPS.AcroFourSuppliers.CObservationSupplier()
    # Get data Sensor(s)
    oSensorData = oDataSupplier.GetByDataStations(oEXPDATA.ExpDate(sTimeFrom), oEXPDATA.ExpDate(sTimeTo), iTimeDelta,
                                                   oSensorRegistry, oSensorType)
    # Return variable(s)
    return oSensorData
# -------------------------------------------------------------------------------------
