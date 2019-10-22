#!/bin/bash -e

# ----------------------------------------------------------------------------------------
# Script information
script_name='HYDE DOWNLOADER - WRF BARBADOS'
script_version="1.0.1"
script_date='2019/10/10'

# Script argument(s)
data_folder_source="/share/ddsData/WRF-regrid-3/Native/%YYYY/%MM/%DD/"
data_folder_destination="/share/c-hydro/data/dynamic/source/wrf/%YYYY/%MM/%DD/"
days=3
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Get time
time_now=$(date '+%Y%m%d')
#time_now="20141007" # DEBUG 
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> START ..."
# ----------------------------------------------------------------------------------------

# Iterate over days
for day in $(seq 0 $days); do
    
    # ----------------------------------------------------------------------------------------
    # Get time step
	date_step=$(date -d "$time_now -${day} days" +'%Y%m%d')
	# ----------------------------------------------------------------------------------------
	
    # ----------------------------------------------------------------------------------------
    # Info time start
    echo " =====> TIME_STEP: "$date_step" ===> START "

    # Define time step information
    date_get=$(date -u -d "$date_step" +"%Y%m%d%H")
    doy_get=$(date -u -d "$date_step" +"%j")

    year_get=$(date -u -d "$date_step" +"%Y")
    month_get=$(date -u -d "$date_step" +"%m")
    day_get=$(date -u -d "$date_step" +"%d")
    hour_get=$(date -u -d "$date_step" +"%H")
    # ----------------------------------------------------------------------------------------
	
	# ----------------------------------------------------------------------------------------
	# Define dynamic folder(s)
    data_folder_get=${data_folder_source/'%YYYY'/$year_get}
    data_folder_get=${data_folder_get/'%MM'/$month_get}
    data_folder_get=${data_folder_get/'%DD'/$day_get}
    data_folder_get=${data_folder_get/'%HH'/$hour_get}
    
    data_folder_put=${data_folder_destination/'%YYYY'/$year_get}
    data_folder_put=${data_folder_put/'%MM'/$month_get}
    data_folder_put=${data_folder_put/'%DD'/$day_get}
    data_folder_put=${data_folder_put/'%HH'/$hour_get}
	# ----------------------------------------------------------------------------------------
    
	# ----------------------------------------------------------------------------------------	
	# Create folder(s)
	if [ ! -d "$data_folder_put" ]; then
		mkdir -p $data_folder_put
	fi
	# ----------------------------------------------------------------------------------------
	
	# ----------------------------------------------------------------------------------------
	# Synchronize data from server bb02 and bb01
	echo " =====> Sync command execution --> rsync -av $data_folder_get $data_folder_put"
    if rsync -av $data_folder_get $data_folder_put; then
        echo " =====> Sync command execution .. OK"
    else
        echo " =====> Sync command execution .. FAILED"
    fi
	# ----------------------------------------------------------------------------------------
	
	# ----------------------------------------------------------------------------------------
	# Info time end
	echo " =====> TIME_STEP: "$date_step" ===> END "
    # ----------------------------------------------------------------------------------------

done

# Info script end
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------

