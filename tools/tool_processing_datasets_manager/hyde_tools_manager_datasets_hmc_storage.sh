#!/bin/bash

#-----------------------------------------------------------------------------------------
# Script information
script_name="HYDE UTILS - MANAGER DATASETS - HMC - STORAGE - REALTIME"
script_version="1.0.0"
script_date="2021/02/22"
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get script information
script_file="hyde_tools_manager_datasets_hmc_storage.sh"

# Get time information (-u to get gmt time)
time_script_now=$(date -u +"%Y-%m-%d 00:00")
#time_script_now="2021-02-20 00:00"

time_script_period=3
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Folder of remote and local machine(s)
group_datasets_name=(
    "DYNAMIC DATA - STATE GRIDDED - MARCHE"
    "DYNAMIC DATA - STATE POINT - MARCHE"
    "DYNAMIC DATA - HYDROGRAPH TIME-SERIES JSON - WEATHER STATIONS - MARCHE"
    "DYNAMIC DATA - HYDROGRAPH TIME-SERIES JSON - RADAR MCM - MARCHE"
    "DYNAMIC DATA - HYDROGRAPH TIME-SERIES JSON - NWP ECMWF0100 - MARCHE"
    "DYNAMIC DATA - HYDROGRAPH TIME-SERIES JSON - NWP LAMI-2I - MARCHE"
    "DYNAMIC DATA - HYDROGRAPH TIME-SERIES JSON - RFARM ECMWF0100 - MARCHE"
    "DYNAMIC DATA - HYDROGRAPH TIME-SERIES JSON - RFARM LAMI-2I - MARCHE"
    "DYNAMIC DATA - HYDROGRAPH TIME-SERIES JSON - RFARM EXPERT FORECAST - MARCHE"
    "DYNAMIC DATA - STATE GRIDDED - NERA"
    "DYNAMIC DATA - STATE POINT - NERA"
    "DYNAMIC DATA - HYDROGRAPH TIME-SERIES JSON - WEATHER STATIONS - NERA"
    "DYNAMIC DATA - HYDROGRAPH TIME-SERIES JSON - RADAR MCM - NERA"
    "DYNAMIC DATA - HYDROGRAPH TIME-SERIES JSON - NWP ECMWF0100 - NERA"
    "DYNAMIC DATA - HYDROGRAPH TIME-SERIES JSON - NWP LAMI-2I - NERA"
    "DYNAMIC DATA - HYDROGRAPH TIME-SERIES JSON - RFARM ECMWF0100 - NERA"
    "DYNAMIC DATA - HYDROGRAPH TIME-SERIES JSON - RFARM LAMI-2I - NERA"
    "DYNAMIC DATA - HYDROGRAPH TIME-SERIES JSON - RFARM EXPERT FORECAST - NERA"
)

group_folder_datasets_source_raw=(
    "/hydro/archive/model_dset_restart_marche/gridded/" 
    "/hydro/archive/model_dset_restart_marche/point/"
    "/hydro/archive/weather_stations_realtime_marche/%YYYY/%mm/%dd/%HH/collections/"
    "/hydro/archive/radar_mcm_realtime_marche/%YYYY/%mm/%dd/%HH/collections/"
    "/hydro/archive/nwp_ecmwf0100_realtime_marche/%YYYY/%mm/%dd/%HH/collections/"
    "/hydro/archive/nwp_lami-2i_realtime_marche/%YYYY/%mm/%dd/%HH/collections/"
    "/hydro/archive/rfarm_ecmwf0100_realtime_marche/%YYYY/%mm/%dd/%HH/probabilistic_ensemble/collections/"
    "/hydro/archive/rfarm_lami-2i_realtime_marche/%YYYY/%mm/%dd/%HH/probabilistic_ensemble/collections/"
    "/hydro/archive/rfarm_expert_forecast_realtime_marche/%YYYY/%mm/%dd/%HH/probabilistic_ensemble/collections/"
    "/hydro/archive/model_dset_restart_nera/gridded/" 
    "/hydro/archive/model_dset_restart_nera/point/"
    "/hydro/archive/weather_stations_realtime_nera/%YYYY/%mm/%dd/%HH/collections/"
    "/hydro/archive/radar_mcm_realtime_nera/%YYYY/%mm/%dd/%HH/collections/"
    "/hydro/archive/nwp_ecmwf0100_realtime_nera/%YYYY/%mm/%dd/%HH/collections/"
    "/hydro/archive/nwp_lami-2i_realtime_nera/%YYYY/%mm/%dd/%HH/collections/"
    "/hydro/archive/rfarm_ecmwf0100_realtime_nera/%YYYY/%mm/%dd/%HH/probabilistic_ensemble/collections/"
    "/hydro/archive/rfarm_lami-2i_realtime_nera/%YYYY/%mm/%dd/%HH/probabilistic_ensemble/collections/"
    "/hydro/archive/rfarm_expert_forecast_realtime_nera/%YYYY/%mm/%dd/%HH/probabilistic_ensemble/collections/"
)

group_folder_datasets_destination_raw=(
    "/hydro/storage/hmc/model_dset_restart_marche/gridded/%YYYY/%mm/%dd/" 
    "/hydro/storage/hmc/model_dset_restart_marche/point/%YYYY/%mm/%dd/"
    "/hydro/storage/hmc/weather_stations_realtime_marche/%YYYY/%mm/%dd/%HH/"
    "/hydro/storage/hmc/radar_mcm_realtime_marche/%YYYY/%mm/%dd/%HH/"
    "/hydro/storage/hmc/nwp_ecmwf0100_realtime_marche/%YYYY/%mm/%dd/%HH/"
    "/hydro/storage/hmc/nwp_lami-2i_realtime_marche/%YYYY/%mm/%dd/%HH/"
    "/hydro/storage/hmc/rfarm_ecmwf0100_realtime_marche/%YYYY/%mm/%dd/%HH/"
    "/hydro/storage/hmc/rfarm_lami-2i_realtime_marche/%YYYY/%mm/%dd/%HH/"
    "/hydro/storage/hmc/rfarm_expert_forecast_realtime_marche/%YYYY/%mm/%dd/%HH/"
    "/hydro/storage/hmc/model_dset_restart_nera/gridded/%YYYY/%mm/%dd/" 
    "/hydro/storage/hmc/model_dset_restart_nera/point/%YYYY/%mm/%dd/"
    "/hydro/storage/hmc/weather_stations_realtime_nera/%YYYY/%mm/%dd/%HH/"
    "/hydro/storage/hmc/radar_mcm_realtime_nera/%YYYY/%mm/%dd/%HH/"
    "/hydro/storage/hmc/nwp_ecmwf0100_realtime_nera/%YYYY/%mm/%dd/%HH/"
    "/hydro/storage/hmc/nwp_lami-2i_realtime_nera/%YYYY/%mm/%dd/%HH/"
    "/hydro/storage/hmc/rfarm_ecmwf0100_realtime_nera/%YYYY/%mm/%dd/%HH/"
    "/hydro/storage/hmc/rfarm_lami-2i_realtime_nera/%YYYY/%mm/%dd/%HH/"
    "/hydro/storage/hmc/rfarm_expert_forecast_realtime_nera/%YYYY/%mm/%dd/%HH/"
)

group_file_datasets_pattern_raw=(
    "hmc.state-grid.%YYYY%mm%dd%HH00.nc.gz"
    "hmc.state-point.%YYYY%mm%dd%HH00.txt"
    "hydrograph_*_%YYYY%mm%dd%HH00.json"
    "hydrograph_*_%YYYY%mm%dd%HH00.json"
    "hydrograph_*_%YYYY%mm%dd%HH00.json"
    "hydrograph_*_%YYYY%mm%dd%HH00.json"
    "hydrograph_*_%YYYY%mm%dd%HH00.json"
    "hydrograph_*_%YYYY%mm%dd%HH00.json"
    "hydrograph_*_%YYYY%mm%dd%HH00.json"
    "hmc.state-grid.%YYYY%mm%dd%HH00.nc.gz"
    "hmc.state-point.%YYYY%mm%dd%HH00.txt"
    "hydrograph_*_%YYYY%mm%dd%HH00.json"
    "hydrograph_*_%YYYY%mm%dd%HH00.json"
    "hydrograph_*_%YYYY%mm%dd%HH00.json"
    "hydrograph_*_%YYYY%mm%dd%HH00.json"
    "hydrograph_*_%YYYY%mm%dd%HH00.json"
    "hydrograph_*_%YYYY%mm%dd%HH00.json"
    "hydrograph_*_%YYYY%mm%dd%HH00.json"
)

group_file_datasets_sync=(
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

group_file_datasets_frequency=(
    12
    12
    12
    12
    1
    1
    1
    1
    1
    12
    12
    12
    12
    1
    1
    1
    1
    1
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
	
	folder_datasets_source_raw=${group_folder_datasets_source_raw[datasets_id]}
	folder_datasets_destination_raw=${group_folder_datasets_destination_raw[datasets_id]}
	
	file_datasets_pattern_raw=${group_file_datasets_pattern_raw[datasets_id]} 

	file_datasets_sync=${group_file_datasets_sync[datasets_id]}
	file_datasets_frequency=${group_file_datasets_frequency[datasets_id]}
	
	file_datasets_period=$(( 24*${time_script_period}/${file_datasets_frequency} ))
	
	# Info datasets type start
	echo " ====> DATASETS TYPE ${datasets_name} ... "
	# ----------------------------------------------------------------------------------------
	
	# ----------------------------------------------------------------------------------------
	# Check sync activation
	if ${file_datasets_sync} ; then
	
		# ----------------------------------------------------------------------------------------
		# Iterate over datasets period
		for file_datasets_step in $(seq 0 $file_datasets_period); do
			
			# ----------------------------------------------------------------------------------------
			# Get time run information
			file_datasets_hour=$(( ${file_datasets_step}*${file_datasets_frequency} ))
			
			time_step=$(date -d "$time_script_now ${file_datasets_hour} hour ago" +'%Y-%m-%d %H:00')
			year_step=$(date -u -d "$time_step" +"%Y")
			month_step=$(date -u -d "$time_step" +"%m")
			day_step=$(date -u -d "$time_step" +"%d")
			hour_step=$(date -u -d "$time_step" +"%H")
			minute_step=$(date -u -d "$time_step" +"%M")
			
			# Info time step start
			echo " =====> TIME STEP ${time_step} ... "
			# ----------------------------------------------------------------------------------------
			
		    # ----------------------------------------------------------------------------------------
		    # Define remote and local folder(s)
		    folder_datasets_source_step=${folder_datasets_source_raw/'%YYYY'/$year_step}
		    folder_datasets_source_step=${folder_datasets_source_step/'%mm'/$month_step}
		    folder_datasets_source_step=${folder_datasets_source_step/'%dd'/$day_step}
		    folder_datasets_source_step=${folder_datasets_source_step/'%HH'/$hour_step}
		    folder_datasets_source_step=${folder_datasets_source_step/'%MM'/$minute_step}
		    
		    folder_datasets_destination_step=${folder_datasets_destination_raw/'%YYYY'/$year_step}
		    folder_datasets_destination_step=${folder_datasets_destination_step/'%mm'/$month_step}
		    folder_datasets_destination_step=${folder_datasets_destination_step/'%dd'/$day_step}
		    folder_datasets_destination_step=${folder_datasets_destination_step/'%HH'/$hour_step}
		    folder_datasets_destination_step=${folder_datasets_destination_step/'%MM'/$minute_step}
		    
		    # Define filename
		    file_datasets_pattern_step=${file_datasets_pattern_raw/'%YYYY'/$year_step}
		    file_datasets_pattern_step=${file_datasets_pattern_step/'%mm'/$month_step}
		    file_datasets_pattern_step=${file_datasets_pattern_step/'%dd'/$day_step}
		    file_datasets_pattern_step=${file_datasets_pattern_step/'%HH'/$hour_step}
		    file_datasets_pattern_step=${file_datasets_pattern_step/'%MM'/$minute_step}
			# ----------------------------------------------------------------------------------------

			# ----------------------------------------------------------------------------------------
			# Sync file from source to destination folders
			echo " ======> SYNC FILE ${file_datasets_pattern_step} ... "
			
			# Define rsync command
			if echo x"$file_datasets_pattern_step" | grep '*' > /dev/null; then
				cmd_sync="rsync -rtv --progress ${folder_datasets_source_step}${file_datasets_pattern_step} ${folder_datasets_destination_step}"
			else 
				cmd_sync="rsync -rtv --progress ${folder_datasets_source_step}${file_datasets_pattern_step} ${folder_datasets_destination_step}${file_datasets_pattern_step}"
			fi
		
			if [ -d "$folder_datasets_source_step" ]; then

				# Create local folder
				if [ ! -d "$folder_datasets_destination_step" ]; then
					mkdir -p $folder_datasets_destination_step
				fi
				
				# Execute command-line
				if ! ${cmd_sync} ; then
					# Info tag end (failed)
					echo " ======> SYNC FILE ${file_datasets_pattern_step} ... FAILED. ERRORS IN EXECUTING $cmd_sync COMMAND-LINE"
				else
					# Info tag end (completed)
					echo " ======> SYNC FILE ${file_datasets_pattern_step} ... DONE"
				fi
				
				echo " ======> CHECK DESTINATION FOLDER $folder_datasets_destination_step ... "
				if [ "$(ls -A $folder_datasets_destination_step)" ]; then
					echo " ======> CHECK DESTINATION FOLDER $folder_datasets_destination_step ... NOT EMPTY"
				else
					echo " ======> CHECK DESTINATION FOLDER $folder_datasets_destination_step ... EMPTY. REMOVE FOLDER"
					rm -rf $folder_datasets_destination_step
				fi

			else
				# Source folder does not exist
				echo " ======> SYNC FILE ${file_datasets_pattern_step} ... FAILED. FOLDER $folder_datasets_source_step DOES NOT EXIST"
			fi

			# ----------------------------------------------------------------------------------------
				
			# ----------------------------------------------------------------------------------------
			# Info time step end
			echo " =====> TIME STEP ${time_step} ... DONE"
			# ----------------------------------------------------------------------------------------
			
		done
	
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
# ----------------------------------------------------------------------------------------

# Info script end
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------





