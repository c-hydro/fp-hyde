#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='HYDE DYNAMICDATA - SATELLITE SMAP - DROUGH INDEX SSPI'
script_version="1.0.0"
script_date='2020/05/11'

script_folder='/home/sequia/drought/code/SSPI/'

virtual_env_folder='/home/sequia/hyde_env/fp_libs_python3/bin/'
virtual_env_name='virtualenv_python3'
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get file information
script_file='HYDE_DynamicData_DroughtIndex_SSPI.py'
setting_file='hyde_configuration_drought_index_sspi_server_realtime.json'

# Run period in month(s)
time_month_period=100

# Get information (-u to get gmt time)
#time_now=$(date -u +"%Y%m%d%H00")
time_now='2020-05-01 00:00' # DEBUG 
#-----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Add path to pythonpath
export PYTHONPATH="${PYTHONPATH}:$script_folder"
# Add virtual env
export PATH=$virtual_env_folder:$PATH
source activate $virtual_env_name
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> START ..."
echo " ==> COMMAND LINE: " python3 $script_file -settings_file $setting_file -time $time_now

# Iterate over days
time_now=$(date -d "$time_now" +'%Y-%m-01 00:00')
for time_month_step in $(seq 0 $time_month_period); do

	# Get time step
	time_step=$(date -d "$time_now ${time_month_step} month ago" +'%Y-%m-%d %H:%M')

	# Run python script (using setting and time)
	python3 $script_file -settings_file $setting_file -time "$time_step"

done

# Info script end
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------

