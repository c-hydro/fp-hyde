#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='HYDE - GROUND NETWORK TIME SERIES - SOIL MOISTURE 5 CM - MONTH2DB - REALTIME'
script_version="1.2.0"
script_date='2024/10/17'

virtualenv_folder='/hydro/library/fp_libs_python_hyde/'
virtualenv_name='hyde_runner_libraries'
script_folder='/hydro/library/fp_package_hyde_v2/'

# Execution example:
# python app_point_time_step_src2csv.py -settings_file configuration.json -time "YYYY-MM-DD HH:MM"
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get file information
script_file='/hydro/library/fp_package_hyde_v2/app/app_ts/join_ts/app_point_join_ts.py'
settings_file='/hydro/fp_tools_preprocessing/time_series/soil_moisture/app_point_join_ts_soil_moisture_5cm_month2db_realtime.json'

# time period hours
time_period_type='months' # 'months'
time_period_analysis=0

# Get information (-u to get gmt time)
time_now=$(date -u +"%Y-%m-%d %H:00")
#time_now='2024-10-01 00:00' # DEBUG 
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Activate virtualenv
export PATH=$virtualenv_folder/bin:$PATH
source activate $virtualenv_name

# Add path to pythonpath
export PYTHONPATH="${PYTHONPATH}:$script_folder"
#-----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> START ..."

# iterate over hour(s)
time_run=$(date -d "$time_now" +'%Y-%m-%d %H:00')
for time_period_step in $(seq 0 $time_period_analysis); do
	
    # parse time information
    if [[ "$time_period_type" == "hours" ]]; then
    	time_step=$(date -d "$time_run ${time_period_step} hour ago" +'%Y-%m-%d %H:00')
	elif [[ "$time_period_type" == "months" ]]; then
		time_step=$(date -d "$time_run ${time_period_step} month ago" +'%Y-%m-%d 00:00')
	else
		echo " ERROR TIME PERIOD TYPE ${time_period_type} IS NOT EXPECTED. EXIT! "
		exit
	fi
	
	echo " ===> COMMAND LINE: " python $script_file -settings_file $settings_file -time "$time_step"
	
	# run python script (using setting and time)
	python $script_file -settings_file $settings_file -time "$time_step"

    echo " ... DONE!"

done

# info script end
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------

