#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='HYDE UTILS - CLEANER DATASETS DAILY - REALTIME'
script_version="1.5.0"
script_date='2020/12/08'
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get script information
script_file='hyde_tools_cleaner_datasets_daily.sh'

# Get folder information
folder_list_expected=(
"/hydro/run/weather_stations_state_marche/" 
"/hydro/run/nwp_lami-2i_realtime_marche/"
"/hydro/run/nwp_ecmwf0100_realtime_marche/"
"/hydro/run/rfarm_lami-2i_realtime_marche/"
"/hydro/run/rfarm_ecmwf0100_realtime_marche/"
"/hydro/run/rfarm_expert_forecast_realtime_marche/"
"/hydro/run/weather_stations_state_nera/" 
"/hydro/run/nwp_lami-2i_realtime_nera/"
"/hydro/run/nwp_ecmwf0100_realtime_nera/"
"/hydro/run/rfarm_lami-2i_realtime_nera/"
"/hydro/run/rfarm_ecmwf0100_realtime_nera/"
"/hydro/run/rfarm_expert_forecast_realtime_nera/")

# Get time information (-u to get gmt time)
time_now=$(date -u +"%Y-%m-%d %H:00")
# time_now='2020-11-20 09:35'
#-----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Get time information
year=${time_now:0:4}
month=${time_now:5:2}
day=${time_now:8:2}
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> COMMAND LINE: " bash $script_file -time $time_now
echo " ===> EXECUTION ..."

# Execution pid
execution_pid=$$

# Iteration(s) to search folder 
echo " ====> SEARCH FOLDER ... "
for folder_name_raw in "${folder_list_expected[@]}"; do  
     
    folder_name_def=${folder_name_raw/"%YYYY"/$year}
    folder_name_def=${folder_name_def/"%MM"/$month}
    folder_name_def=${folder_name_def/"%DD"/$day}

    echo " =====> REMOVE FOLDER: $folder_name_def ... "
    if [ -d $folder_name_def ]; then
       	if rm -vrf $folder_name_def; then
       	    echo " =====> REMOVE FOLDER: $folder_name_def ... DONE"
       	else
       	    echo " =====> REMOVE FOLDER: $folder_name_def ... FAILED. ERROR IN DELETING FOLDER"
       	fi
    else
        echo " =====> REMOVE FOLDER: $folder_name_def ... SKIPPED! FOLDER NOT FOUND!"
    fi
    
    echo " =====> CREATE EMPTY FOLDER: $folder_name_def ... "
    if [ ! -d $folder_name_def ]; then
        if mkdir -p $folder_name_def; then
            echo " =====> CREATE EMPTY FOLDER: $folder_name_def ... DONE"
        else
            echo " =====> CREATE EMPTY FOLDER: $folder_name_def ... FAILED. ERROR IN CREATING FOLDER"
        fi
    else
        echo " =====> CREATE EMPTY FOLDER: $folder_name_def ... SKIPPED. FOLDER ALREADY EXISTS"
    fi
    
done
echo " ====> SEARCH FOLDER ... DONE"

echo " ===> EXECUTION ... DONE"
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------	


