#!/bin/bash -e

# ----------------------------------------------------------------------------------------
# Script information
script_name='HYDE TOOLS - REDUCE NETCDF VARIABLES'
script_version="1.0.0"
script_date='2020/04/20'

# Time Information
date_start="2020-03-19 18:00"
date_end="2020-03-20 00:00"

# Path(s) information
source_folder_name_raw="/home/fabio/Desktop/PyCharm_Workspace/hyde-ws/dynamic/source/wrf/lexis/2020_03_19_1800/"
source_file_name_raw="auxhist23_d03_%YYYY-%MM-%DD_%HH:00:00"
dest_folder_name_raw="/home/fabio/Desktop/Workspace/PyCharm_Workspace/fp-docker-ws/data/dynamic_data/nwp/wrf/lexis/%YYYY/%MM/%DD/"
dest_file_name_raw="auxhist23_d03_%YYYY-%MM-%DD_%HH:00:00"

# Variable(s)
dest_variable_list="T2,RAINNC,U10,V10,SWDOWN,SWDOWNC,Q2,T2,PSFC,Times"
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Cycle(s) over date(s)
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> START ..."

time_start=$(date -d "$date_start" +"%Y-%m-%d %H:%M")
time_end=$(date -d "$date_end +1 hour" +"%Y-%m-%d %H:%M")

time_step=$time_start
while [ "$time_step" != "$time_end" ]; do 

	echo " ===> TimeStep: $time_step ... "

	year_step=$(date -u -d "$time_step" +"%Y")
	month_step=$(date -u -d "$time_step" +"%m")
	day_step=$(date -u -d "$time_step" +"%d")
	hour_step=$(date -u -d "$time_step" +"%H")
	
	source_folder_name_step=${source_folder_name_raw/'%YYYY'/$year_step}
	source_folder_name_step=${source_folder_name_step/'%MM'/$month_step}
	source_folder_name_step=${source_folder_name_step/'%DD'/$day_step}
	source_folder_name_step=${source_folder_name_step/'%HH'/$hour_step}

	dest_folder_name_step=${dest_folder_name_raw/'%YYYY'/$year_step}
	dest_folder_name_step=${dest_folder_name_step/'%MM'/$month_step}
	dest_folder_name_step=${dest_folder_name_step/'%DD'/$day_step}
	dest_folder_name_step=${dest_folder_name_step/'%HH'/$hour_step}

	source_file_name_step=${source_file_name_raw/'%YYYY'/$year_step}
	source_file_name_step=${source_file_name_step/'%MM'/$month_step}
	source_file_name_step=${source_file_name_step/'%DD'/$day_step}
	source_file_name_step=${source_file_name_step/'%HH'/$hour_step}

	dest_file_name_step=${dest_file_name_raw/'%YYYY'/$year_step}
	dest_file_name_step=${dest_file_name_step/'%MM'/$month_step}
	dest_file_name_step=${dest_file_name_step/'%DD'/$day_step}
	dest_file_name_step=${dest_file_name_step/'%HH'/$hour_step}
	
	if [ ! -d "$dest_folder_name_step" ]; then
		mkdir -p $dest_folder_name_step
	fi
	
	source_path_name_step=${source_folder_name_step}${source_file_name_step}
	dest_path_name_step=${dest_folder_name_step}${dest_file_name_step}

	echo " ====> Filter Source $source_file_name_step to $dest_file_name_step ... "
	if [ -e ${source_path_name_step} ]; then
		if ncks -O -v ${dest_variable_list} ${source_path_name_step} ${dest_path_name_step}; then
			echo " ... DONE!"
		else
			echo " ... FAILED! Error in command execution!"
		fi
	else
		echo " ... SKIPPED! File source not available!"
	fi	
	
	echo " ===> TimeStep: $time_step ... DONE!"

	time_step=$(date -d "$time_step +1 hour" +"%Y-%m-%d %H:%M")
done

# Info script end
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="

# ----------------------------------------------------------------------------------------


