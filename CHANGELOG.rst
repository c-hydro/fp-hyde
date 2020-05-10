=========
Changelog
=========

Version 1.9.5 [2020-05-10]
**************************
BIN: **hyde_downloader_satellite_smap.py**
	- Release for Hyde package

BIN: **hyde_downloader_satellite_persiann_monthly.py**
	- Release for Hyde package

FIX: **hyde_downloader_satellite_gsmap.py**
	- Fix a major problem in multiprocessing downloader

FIX: **HYDE_Model_RFarm.py**
	- Fix the incorrect slope in time estimation

Version 1.9.4 [2020-03-19]
**************************
APP: **HYDE_DynamicData_GSMap_Rain.py**
	- Release for Hyde package

APP: **HYDE_DynamicData_NWP_GFS_025.py**
	- Release for Hyde package

APP: **HYDE_DynamicData_NWP_ECMWF_0100.py**
    - Beta release for HyDE package
    	- Previous version(s)
    		- [2017-05-10] Latest operational version for NWP ECMWF 0100
    		- [2015-09-23] Latest operational version for NWP ECMWF 0125

APP: **HYDE_DynamicData_NWP_WRF.py**
	- Application refactoring 

DRV: **lib_astrorad_core.py**
	- Beta release for HyDE package for Astronomical Radiation Model
		- Previous version(s)
			- [2017-05-23] Refactoring for Python3
			- [2015-11-03] Beta release

BIN: **hyde_downloader_satellite_gsmap.py**
	- Release for Hyde package

BIN: **hyde_downloader_nwp_gfs.py**
	- Release for Hyde package

BIN: **hyde_adapter_data_splitting_main.py**
	- Update code and release for Hyde package

ADD: **hyde_downloader_satellite_gsmap.py**
	- Request of ftp files list to avoid bad http request(s)

ADD: **hyde_downloader_nwp_gfs.py**
	- Request of url(s) list to avoid bad http request(s)

FIX: **HYDE_Model_RFarm.py**
    - Minor bugs in bash scripts and python scripts

Version 1.9.3 [2019-11-22]
**************************
APP: **HYDE_DynamicData_HSAF_ASCAT_OBS_NRT.py**
    - FIX: iterations over time(s) in main function for generating products in a selected period 

Version 1.9.2 [2019-11-13]
**************************
APP: **HYDE_DynamicData_HSAF_ASCAT_OBS_NRT.py**
    - FIX: correction of data and latitude map according with south_north convention 

APP: **HYDE_DynamicData_HSAF_ASCAT_MOD_NRT.py**
    - FIX: correction of data and latitude map according with south_north convention 

Version 1.9.1 [2019-10-18]
**************************
APP: **HYDE_DynamicData_NWP_WRF.py**
    - FIX: manage mismatch in input definition of "time" variable

Version 1.9.0 [2019-10-04]
**************************
APP: **HYDE_DynamicData_HSAF_H03B.py**
    - Beta release for HyDE package
	   - Previous version(s)
		  - [2015-09-25] Latest release used in operational chain(s)
		  - [2015-03-25] Refactor for operational chain(s)
		  - [2014-12-04] Starting version in experimental mode
		  - [2019-06-20] Fix bug in outcome data
		  - [2019-04-18] Use source data in netcdf format and add quality index
		  - [2019-04-01] Fix bug about geographical references of grib file(s) and interpolation method
		  - [2018-07-30] Refactor in FloodProofs library

APP: **HYDE_DynamicData_HSAF_H05B.py**
    - Beta release for HyDE package
	   - Previous version(s)
		  - [2019-04-18] Use source data in netcdf format and add quality index
		  - [2019-04-01] Fix bug about geographical references of grib file(s) and interpolation method
		  - [2018-08-23] Refactor in FloodProofs library
		  - [2014-12-04] Second operational release 

APP: **HYDE_DynamicData_HSAF_H12.py**
    - Beta release for HyDE package
	   - Previous version(s)
		  - [2018-06-29] Beta release for FloodProofs library

APP: **HYDE_DynamicData_HSAF_H13.py**
    - Beta release for HyDE package
	   - Previous version(s)
		  - [2018-07-26] Beta release for FloodProofs library

Version 1.8.0 [2019-10-03]
**************************
APP: **HYDE_DynamicData_HSAF_H10.py**
    - Beta release for HyDE package
	   - Previous version(s)
		  - [2018-07-13] Beta release for FloodProofs library
		  - [2014-12-04] Refactor for operational chain(s)
		  - [2013-01-11] First release

Version 1.7.0 [2019-10-07]
**************************
APP: **HYDE_DynamicData_MODIS_Snow.py**
    - Beta release for HyDE package
    	- Previous version(s)
		  - [2018-09-10] Beta release for FloodProofs library
		  - [2015-10-15] Updated codes, classes and methods
		  - [2015-07-25] Updated codes, classes and methods
		  - [2015-07-15] Added filter to compute quality index
		  - [2015-05-22] Added merging between tiles
		  - [2015-05-14] Updated output file attributes
		  - [2015-05-13] Added mosaic tile(s) option, update settings file and reader
		  - [2014-12-10] Added checking no data available on FTP server
		  - [2014-08-08] Re-arranged some functions and other stuff
		  - [2014-08-07] First Release
		  - [2014-08-05] First Code

Version 1.6.0 [2019-09-16]
**************************
APP: **HYDE_DynamicData_NWP_WRF.py**
    - Beta release for HyDE package
	   - Previous version(s)
		  - [2018-07-13] Beta release for FloodProofs library
		  - [2013-07-30] Final release for experimental mode

Version 1.5.0 [2019-09-02]
**************************
APP: **HYDE_Model_RFarm.py**
    - Beta release for HyDE package
	   - Previous version(s)
		  - [2018-09-10] Beta release for FloodProofs library
		  - [2017-11-14] Fix bugs (accumulated and istantaneous rain)
		  - [2017-05-30] Update version with coding refactor
		  - [2015-09-24] Final release for operational chain mode
		  - [2015-08-23] Final release for experimental project
		  - [2014-04-08] Final release for experimental mode

DRV: **lib_rfarm_core.py**
		- Beta release for HyDE package for RainFarm model

Version 1.4.0 [2019-08-05]
**************************
APP: **HYDE_DynamicData_HSAF_ASCAT_OBS_NRT.py**
    - Beta release for HyDE package using pytesmo library and time-series data format
	   - Previous version(s)
		  - [2016-10-10] Fix bug(s) and update code(s)
		  - [2016-06-28] Beta release for FloodProofs library
		  - [2014-07-08] Refactor for operational chain(s)
		  - [2014-02-05] Add new feature to compute SWI values
		  - [2013-03-06] Release based on operational code
		  - [2012-10-24] Release based on experimental code
		  - [2012-09-21] First relase

APP: **HYDE_DynamicData_HSAF_ASCAT_OBS_DR.py**
    - Beta release for HyDE package using pytesmo library and time-series data format
	   - Previous version(s)
	      - [2016-10-07] Fix bug(s) and update code(s)
		  - [2016-06-06] Beta release for FloodProofs library
		  - [2014-07-08] Refactor for operational chain(s)
		  - [2014-02-05] Add new feature to compute SWI values
		  - [2013-03-06] Release based on operational code
		  - [2012-10-24] Release based on experimental code
		  - [2012-09-21] First relase

Version 1.3.0 [2019-08-01]
**************************
APP: **HYDE_DynamicData_HSAF_ASCAT_MOD_NRT.py**
    - Beta release for HyDE package using pytesmo library and time-series data format
	   - Previous version(s)
		  - [2016-10-07] Fix bug(s) and update code(s)
		  - [2016-06-06] Beta release for FloodProofs library
		  - [2014-07-08] Refactor for operational chain(s)
		  - [2012-11-22] First release

APP: **HYDE_DynamicData_HSAF_ASCAT_MOD_DR.py**
    - Beta release for HyDE package using pytesmo library and time-series data format
	   - Previous version(s)
		  - [2016-10-07] Fix bug(s) and update code(s)
		  - [2016-06-06] Beta release for FloodProofs library
		  - [2014-07-08] Refactor for operational chain(s)
		  - [2012-11-22] First release

Version 1.2.0 [2019-07-09]
**************************
APP: **HYDE_DynamicData_Radar_MCM.py**
    - Beta release for HyDE package

Version 1.1.0 [2018-12-03]
**************************
APP: **HYDE_DynamicData_NWP_LAMI_2i.py**
    - Beta release for HyDE package

Version 1.0.0 [2018-09-14]
**************************
APP: **HYDE_DynamicData_GroundNetwork_WS.py**
    - Beta release for HyDE package
	   - Previous version(s)
		  - [2015-09-25] Latest release used in operational chain(s)
		  - [2015-03-25] Refactor for operational chain(s)
		  - [2014-04-01] Starting version in experimental mode

Version 0.0.1 [2018-06-01]
**************************
GENERIC_DEV
    - Start development and configuration of HyDE python package
    - Include methods, apps and tools of previous experimental and operational libraries (from FloodProofs library and other)
    - Python 3

