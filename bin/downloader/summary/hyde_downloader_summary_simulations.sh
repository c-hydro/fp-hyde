#!/bin/bash -e

# ----------------------------------------------------------------------------------------
# Script information
script_name='HYDE DOWNLOADER - SUMMARY HMC SIMULATIONS'
script_version="1.0.0"
script_date='2019/07/11'

# Specific command line usage:
# rsync -v -e ssh -v regmarche@130.251.104.16:/home/regmarche/geotiff/2019/07/10/MCM_20190710160000.tif /hydro/data/dynamic_data/source/observation/mcm/2019/07/10/

# Script argument(s)
data_folder_remote_raw="/home/silvestro/Flood_Proofs_Italia/script/"
data_folder_local_raw="/hydro/summary/%YYYY/%MM/%DD/"

filename_remote='Marche_check.html'
filename_local='summary_simulations_marche.html'

days=0

remote_server='silvestro@130.251.104.67'
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Get time
time_now=$(date '+%Y-%m-%d %H:%M')
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
	date_step=`date --date="${day} days ago" +%Y%m%d`
	# ----------------------------------------------------------------------------------------
	
    # ----------------------------------------------------------------------------------------
    # Info time start
    echo " ===> TIME_STEP: "$date_step" ===> START "

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
    data_folder_remote_step=${data_folder_remote_raw/'%YYYY'/$year_get}
    data_folder_remote_step=${data_folder_remote_step/'%MM'/$month_get}
    data_folder_remote_step=${data_folder_remote_step/'%DD'/$day_get}
    data_folder_remote_step=${data_folder_remote_step/'%HH'/$hour_get}

    data_folder_local_step=${data_folder_local_raw/'%YYYY'/$year_get}
    data_folder_local_step=${data_folder_local_step/'%MM'/$month_get}
    data_folder_local_step=${data_folder_local_step/'%DD'/$day_get}
    data_folder_local_step=${data_folder_local_step/'%HH'/$hour_get}
	# ----------------------------------------------------------------------------------------

	# ----------------------------------------------------------------------------------------	
	# Create folder(s)
	if [ ! -d "$data_folder_local_step" ]; then
		mkdir -p $data_folder_local_step
	fi
	# ----------------------------------------------------------------------------------------
	
    # ----------------------------------------------------------------------------------------
    # Download file from remote to local server using rsync 
    echo -n " =====> DOWNLOAD FILES: from ${data_folder_remote_step} to ${data_folder_local_step} ..."

    if rsync -v -e ssh -v ${remote_server}:${data_folder_remote_step}${filename_remote} ${data_folder_local_step}${filename_local} > /dev/null 2>&1; then
        echo " DONE!"
    else
        echo " FAILED! Error in command execution!"
 
    fi
    # ----------------------------------------------------------------------------------------

	# ----------------------------------------------------------------------------------------
	# Info time end
	echo " ===> TIME_STEP: "$date_step" ===> END "
    # ----------------------------------------------------------------------------------------

done

# Info script end
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="

# ----------------------------------------------------------------------------------------

