# Changelog

All notable changes to this project will be documented in this file.

---

## Version 2.1.0 [2025-10-22]

### 🧩 GENERIC_DEV
- Refactor of HyDE Python package (name, scripts, structure, and dependencies)
- Repository initialization
- Repository sources

### 🧠 Applications
**app_nwp_ecmwf_0100_main.py**
- Extended methods for managing 1h and 3h datasets

---

## Version 2.0.0 [2024-10-16]

### 🧩 GENERIC_DEV
- Refactor of HyDE Python package (name, scripts, structure, and dependencies)
- Upgrade from previous version

### 🧠 Applications
- **app_nwp_icon_2i_main.py** — Beta release  
- **app_nwp_lami_2i_main.py** — Updated app version  
- **app_nwp_ecmwf_0100_main.py** — Updated app version  
- **app_obs_ws_main.py** — Updated app version  
- **app_obs_rs_main.py** — Updated app version  
- **app_obs_hs_main.py** — Updated app version  
- **app_obs_mcm_main.py** — Updated app version  
- **app_point_time_step_src2csv.py** — Beta release  

### 🔧 Tools
- **tool_processing_datasets_adapter** — Updated app version  
- **tool_processing_datasets_generic** — Updated app version  
- **tool_processing_datasets_manager** — Updated app version  
- **tool_processing_datasets_transfer** — Updated app version  
- **tool_processing_system_cleaner** — Updated app version  
- **tool_processing_system_organizer** — Updated app version  
- **tool_processing_system_profiler** — Updated app version  

---

## Version 1.9.9 [2022-03-21]

**HYDE_DynamicData_GroundNetwork_RS.py**
- Added configuration fields for parsing CSV input and TXT output files.

---

## Version 1.9.8 [2021-08-01]

- **hyde_data_dynamic_modified_conditional_merging.py** — Updated variogram estimation and optimized performance  
- **hyde_downloader_nwp_gefs_nomads.py**, **hyde_downloader_mysql_dams.py** — Initial release for HyDE package  
- **drv_model_griso_exec.py** — Mathematical variogram fit bug fix  
- **HYDE_Model_RFarm.py** — Resampling fixes and NWP handling updates

---

## Version 1.9.7 [2021-03-01]

- **hyde_data_dynamic_weather_stations_griso.py** — New release  
- **hyde_data_dynamic_modified_conditional_merging.py** — Added dynamic GRISO interpolation and new configuration management  
- **hyde_downloader_nwp_gfs_nomads.py** — Updated for NOAA policy; supports GFS v16  
- Added various new downloaders (satellite, GFS, HSAF, etc.)  
- **HYDE_Model_RFarm.py** — Added support for GFS 0.25 products

---

## Version 1.9.6 [2021-01-13]

- Added new dynamic data modules for rainfall, MODIS snow, radar MCM, and river stations.  
- Refactored downloaders for MODIS, ODBC, and NWP data.  
- Multiple bug fixes for NWP ECMWF0100 and LAMI-2I handling.  
- **HYDE_Model_RFarm.py** — Major fixes and model updates.

---

## Version 1.9.5 [2020-05-22]

- Added drought index apps (**SSPI**, **SWDI**).  
- Added satellite and station data downloaders (DROPS2, SMAP, PERSIANN).  
- Fixed multiprocessing and slope estimation issues.  
- Improved data filtering for weather station datasets.

---

## Version 1.9.4 [2020-03-19]

- Added GSMap, NWP (GFS, ECMWF0100, WRF) data modules.  
- Added astronomical radiation core (`lib_astrorad_core.py`).  
- Improved downloader tools and HTTP/FTP request handling.  
- **HYDE_Model_RFarm.py** — Minor bug fixes.

---

## Version 1.9.3 [2019-11-22]
- **HYDE_DynamicData_HSAF_ASCAT_OBS_NRT.py** — Fixed iteration handling for selected period generation.

---

## Version 1.9.2 [2019-11-13]
- Fixed south-north convention issues in ASCAT modules (OBS_NRT, MOD_NRT).

---

## Version 1.9.1 [2019-10-18]
- **HYDE_DynamicData_NWP_WRF.py** — Fixed mismatch in “time” variable definition.

---

## Version 1.9.0 [2019-10-04]
- Added new HSAF modules (H03B, H05B, H12, H13).  
- Added quality index and georeferencing fixes.

---

## Version 1.8.0 [2019-10-03]
- **HYDE_DynamicData_HSAF_H10.py** — Beta release with improved SWI computation and refactor.

---

## Version 1.7.0 [2019-10-07]
- **HYDE_DynamicData_MODIS_Snow.py** — Beta release, refactored merging and quality index logic.

---

## Version 1.6.0 [2019-09-16]
- **HYDE_DynamicData_NWP_WRF.py** — Beta release, updated from FloodProofs library.

---

## Version 1.5.0 [2019-09-02]
- **HYDE_Model_RFarm.py** — Beta release and refactor of RainFarm core (`lib_rfarm_core.py`).

---

## Version 1.4.0 [2019-08-05]
- New ASCAT data applications for OBS_NRT and OBS_DR using pytesmo library.  
- Major updates for time-series format and SWI computation.

---

## Version 1.3.0 [2019-08-01]
- New ASCAT data applications for MOD_NRT and MOD_DR with pytesmo integration.

---

## Version 1.2.0 [2019-07-09]
- Added **HYDE_DynamicData_Radar_MCM.py** — Beta release.

---

## Version 1.1.0 [2018-12-03]
- Added **HYDE_DynamicData_NWP_LAMI_2i.py** — Beta release.

---

## Version 1.0.0 [2018-09-14]
- Added **HYDE_DynamicData_GroundNetwork_WS.py** — Beta release.

---

## Version 0.0.1 [2018-06-01]

### 🧩 GENERIC_DEV
- Initial development and configuration of HyDE Python package.  
- Integrated legacy FloodProofs libraries and operational tools.  
- Migration to Python 3.
