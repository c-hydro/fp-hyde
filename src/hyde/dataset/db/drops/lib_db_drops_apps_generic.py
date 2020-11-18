"""
Library Features:

Name:          lib_db_drops_apps_generic
Author(s):     Fabio Delogu (fabio.delogu@cimafoundation.org)
Date:          '20180912'
Version:       '1.0.1'

Install jpype library:
pip3 install jpype-py3

Set DB Drops service local connection adding these lines in /etc/network/interfaces
auto eth0:1
- iface eth0:1 inet static
-        address 172.16.104.136
-        netmask 255.255.255.0
Write in command-line the following statements:
-     sudo ifdown eth0:1
-     sudo ifup eth0:1

"""
#################################################################################
# Logging
import logging

from os.path import join
import jpype
from jpype import *
#################################################################################

# -------------------------------------------------------------------------------------
# List of valid sensor type
oSensorList = ['Raingauge', 'Thermometer', 'Hydrometer', 'RadiationSensor', 'Hygrometer',
               'WindSensor', 'WindDirection', 'Snowgauge', 'Barometer']
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Dictionary to store drops setting(s)
oDrops_Settings_Default = {
    "library_path": "/home/fabio/Documents/Working_Area/Code_Development/Library/Acrofour_Merged/",
    "library_jvm": None,
    "library_source": "MERGED",
    "library_file": {
      "JTDS": "jtds-1.2.jar",
      "LDAP": "ldap.jar",
      "ACRO4": "ACR4_Lib_MAURY.jar"
    },
    "library_server": {
      "HTTP": "130.251.104.243",
      "LDAP": "130.251.104.19",
      "Drops": "130.251.104.19"
    }
}
# -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
# Method to initialize DB drops
def initDropsDB(oDrops_Settings=oDrops_Settings_Default):

    # -------------------------------------------------------------------------------------
    # Check DB connection
    try:
        # -------------------------------------------------------------------------------------
        # Info start
        logging.info(' ===> DATABASE DROPS (v.1.07.00) ... ')

        # Get db connection and library information
        sLibPath = oDrops_Settings["library_path"]
        sLibSource = oDrops_Settings["library_source"]
        sLibFile_JTDS = oDrops_Settings["library_file"]['JTDS']
        sLibFile_LDAP = oDrops_Settings["library_file"]['LDAP']
        sLibFile_ACRO4 = oDrops_Settings["library_file"]['ACRO4']
        sLibServer_HTTP = oDrops_Settings["library_server"]['HTTP']
        sLibServer_LDAP = oDrops_Settings["library_server"]['LDAP']
        sLibServer_Drops = oDrops_Settings["library_server"]['Drops']

        if "library_jvm" in oDrops_Settings:
            sLibJVM = oDrops_Settings["library_jvm"]
        else:
            sLibJVM = None
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Path of jar libraries
        oLibJar = ([join(sLibPath, sLibFile_JTDS),
                    join(sLibPath, sLibFile_LDAP),
                    join(sLibPath, sLibFile_ACRO4)])

        # Start java machine
        if sLibJVM is None:
            logging.info(' ====> Set default system JVM ... ')
            startJVM(jpype.getDefaultJVMPath(), "-Djava.class.path=%s" % ':'.join(oLibJar))
            logging.info(' ====> Set default system JVM ... OK')
        else:
            logging.info(' ====> Set alternative system JVM ... ')
            logging.info(' ====> JVM path: ' + sLibJVM)
            startJVM(sLibJVM, "-Djava.class.path=%s" % ':'.join(oLibJar))
            logging.info(' ====> Set alternative system JVM ... OK')

        # Define hour reference
        java.util.TimeZone.setDefault(java.util.TimeZone.getTimeZone('GMT'))

        # Define Services
        oDROPS = JPackage('Experience.Lib.Suppliers.Drops')
        oAPI = JPackage('Experience.Lib.API')
        oEXPDATA = JPackage('Experience.Data')
        oEXPSTRUCTURES = JPackage('Experience.Corba.StructuresDefinition')
        # -------------------------------------------------------------------------------------

        # -------------------------------------------------------------------------------------
        # Initialize DB
        oDROPS.SrvDROPS.setServerHTTP(sLibServer_HTTP)
        oDROPS.SrvDROPS.setServerLDAP(sLibServer_LDAP)
        oDROPS.SrvDROPS.setSrvExpDropsApp(sLibServer_Drops)
        oDROPS.SrvDROPS.setPortExpDropsApp(1922)
        oDROPS.SrvDROPS.setStationDatasource(sLibSource)
        oDROPS.CDataStationSupplier.SetLdapServer(
            "ldap://" + oDROPS.SrvDROPS.getServerLDAP() +
            ":" + oDROPS.SrvDROPS.getPortLDAP() +
            "|cn=admin,dc=experience|ldap4test")
        oDROPS.CDataStationSupplier.InitializeRegistry()
        oDROPS.SrvDROPS.setAcroFourSuppliersVerbose(True)

        oDROPS.SrvDROPS.Init()
        oAPI.CMediatore.init()
        # Info end
        logging.info(' ===> DATABASE DROPS (v.1.07.00) ... OK')
        # -------------------------------------------------------------------------------------
    except BaseException as BExp:
        # -------------------------------------------------------------------------------------
        # Exit from db connection (DB connection failed)
        logging.exception('===> DATABASE DROPS (v.1.07.00) ... FAILED!')
        # this log will just include content in sys.exit
        logging.error(str(BExp))

        raise
        # -------------------------------------------------------------------------------------

    # -------------------------------------------------------------------------------------
    # Return variable(s)
    return oDROPS, oEXPDATA
    # -------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------
