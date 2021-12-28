#!/bin/bash

#-----------------------------------------------------------------------------------------
# Script information
script_name="HYDE UTILS - CLEANER DATASETS DEPRECATED - REALTIME"
script_version="1.0.0"
script_date="2021/02/22"
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get script information
script_file="hyde_tools_cleaner_datasets_deprecated.sh"

# Get time information (-u to get gmt time)
time_script_now=$(date -u +"%Y-%m-%d 00:00")
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Folder of remote and local machine(s)
group_datasets_name=(
	"ANALYSIS - ANCILLARY"
	"ANALYSIS - TMP"
	"ANALYSIS - HYDRAPP - MAPS"
	"ANALYSIS - HYDRAPP - TIME SERIES - SECTIONS"
	"ANALYSIS - HYDRAPP - TIME SERIES - DAMS"
	"ANALYSIS - HYDRAPP - WORKSPACE"
	"ARCHIVE - STATE - MARCHE"
	"ARCHIVE - NWP ECMWF0100 - MARCHE"
	"ARCHIVE - NWP LAMI-2I - MARCHE"
	"ARCHIVE - RADAR MCM - MARCHE"
	"ARCHIVE - RFARM ECMWF0100 - MARCHE"
	"ARCHIVE - RFARM EXPERT FORECAST - MARCHE"
	"ARCHIVE - RFARM LAMI-2I - MARCHE"
	"ARCHIVE - WEATHER STATIONS - MARCHE"
	"ARCHIVE - STATE - NERA"
	"ARCHIVE - NWP ECMWF0100 - NERA"
	"ARCHIVE - NWP LAMI-2I - NERA"
	"ARCHIVE - RADAR MCM - NERA"
	"ARCHIVE - RFARM ECMWF0100 - NERA"
	"ARCHIVE - RFARM EXPERT FORECAST - NERA"
	"ARCHIVE - RFARM LAMI-2I - NERA"
	"ARCHIVE - WEATHER STATIONS - NERA"
	"DATA - TMP"
	"DATA - DATA DYNAMIC - ANCILLARY"
	"DATA - DATA DYNAMIC - OUTCOME - EXPERT FORECAST"
	"DATA - DATA DYNAMIC - OUTCOME - NWP"
	"DATA - DATA DYNAMIC - OUTCOME - OBS"
	"DATA - DATA DYNAMIC - OUTCOME - RFARM"
	"LOG"
	"LOCK"
	"DATA - DATA DYNAMIC - SOURCE - NWP"
)

group_folder_datasets=(
	"/hydro/analysis/ancillary/" 
	"/hydro/analysis/tmp/" 
	"/hydro/analysis/hydrapp/map/"
	"/hydro/analysis/hydrapp/section/"
	"/hydro/analysis/hydrapp/dam/"
	"/hydro/analysis/hydrapp/workspace/"
    "/hydro/archive/model_dset_restart_marche/" 
	"/hydro/archive/nwp_ecmwf0100_realtime_marche/"
	"/hydro/archive/nwp_lami-2i_realtime_marche/"
    "/hydro/archive/radar_mcm_realtime_marche/"
	"/hydro/archive/rfarm_ecmwf0100_realtime_marche/"
	"/hydro/archive/rfarm_expert_forecast_realtime_marche/"
	"/hydro/archive/rfarm_lami-2i_realtime_marche/"
	"/hydro/archive/weather_stations_realtime_marche/"
    "/hydro/archive/model_dset_restart_nera/" 
	"/hydro/archive/nwp_ecmwf0100_realtime_nera/"
	"/hydro/archive/nwp_lami-2i_realtime_nera/"
    "/hydro/archive/radar_mcm_realtime_nera/"
	"/hydro/archive/rfarm_ecmwf0100_realtime_nera/"
	"/hydro/archive/rfarm_expert_forecast_realtime_nera/"
	"/hydro/archive/rfarm_lami-2i_realtime_nera/"
	"/hydro/archive/weather_stations_realtime_nera/"
	"/hydro/data/tmp/"
	"/hydro/data/data_dynamic/ancillary/"
	"/hydro/data/data_dynamic/outcome/expert_forecast/"
	"/hydro/data/data_dynamic/outcome/nwp/"
	"/hydro/data/data_dynamic/outcome/obs/"
	"/hydro/data/data_dynamic/outcome/rfarm/"
	"/hydro/log/"
	"/hydro/lock/"
	"/hydro/data/data_dynamic/source/nwp/"
)

group_file_datasets_clean=(
	true
	true
	true
	true
	true
	true
	true
	true
	true
	true
	true
	true
	true
	true
	true
	true
	true
	true
	true
	true
	true
	true
	true
	true
	true
	true
	true
	true
	true
	true
	true
)

group_file_datasets_elapsed_days=(
	5
	1
	15
	15
	15
	10
    30
    15
	15
	15
    15
    15
	15
	30
    30
    15
	15
	15
    15
    15
	15
	30
	2
	5
	15
	15
	30
	15
	5
	5
	20
)
#-----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> START ..."
echo " ===> EXECUTION ..."

time_script_now=$(date -d "$time_script_now" +'%Y-%m-%d 00:00')
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Iterate over tags
for datasets_id in "${!group_datasets_name[@]}"; do

	# ----------------------------------------------------------------------------------------
	# Get values of tag(s) and folder(s)        
	datasets_name=${group_datasets_name[datasets_id]}
	
	folder_datasets=${group_folder_datasets[datasets_id]}

	file_datasets_clean=${group_file_datasets_clean[datasets_id]} 
	file_datasets_elapsed_days=${group_file_datasets_elapsed_days[datasets_id]}
	
	# Info datasets type start
	echo " ====> DATASETS TYPE ${datasets_name} ... "
	# ----------------------------------------------------------------------------------------
	
	# ----------------------------------------------------------------------------------------
	# Check sync activation
	if ${file_datasets_clean} ; then
		
		# ----------------------------------------------------------------------------------------
		# Iterate over filename
		for file_datasets_name in $(find ${folder_datasets} -type f -mtime +${file_datasets_elapsed_days}); do
			echo " ====> DELETE FILENAME ${file_datasets_name} ... "
			
			if [ -f "$file_datasets_name" ] ; then
    			rm "$file_datasets_name"
    			echo " ====> DELETE FILENAME ${file_datasets_name} ... DONE"
			else
				echo " ====> DELETE FILENAME ${file_datasets_name} ... FAILED. FILE NOT FOUND"
			fi
			
		done
		# ----------------------------------------------------------------------------------------
		
		# ----------------------------------------------------------------------------------------
		# Find empty folders
		for folder_empty_name in $(find ${folder_datasets} -type d -empty); do
			
			echo " ====> DELETE EMPTY FOLDER ${folder_empty_name} ... "
			if [ -d "$folder_empty_name" ] ; then
				rmdir ${folder_empty_name} -vp --ignore-fail-on-non-empty {} 
				echo " ====> DELETE EMPTY FOLDER ${file_datasets_name} ... DONE"
			else
				echo " ====> DELETE EMPTY FOLDER ${file_datasets_name} ... FAILED. FOLDER NOT FOUND"
			fi
			
		done
		# ----------------------------------------------------------------------------------------
		
		# ----------------------------------------------------------------------------------------
		# Info datasets type end
		echo " ====> DATASETS TYPE ${datasets_name} ... DONE"
		# ----------------------------------------------------------------------------------------
		
	else
	
		# ----------------------------------------------------------------------------------------
		# Info tag end (not activated)
		echo " ====> DATASETS TYPE ${datasets_name} ... SKIPPED. SYNC NOT ACTIVATED"
		# ----------------------------------------------------------------------------------------
		
	fi
	# ----------------------------------------------------------------------------------------
	
done

# Info script end
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------

