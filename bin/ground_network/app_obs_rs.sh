#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='HYDE APP - GROUND NETWORK - RIVER STATIONS'
script_version="1.2.0"
script_date='2024/10/15'

virtualenv_folder='/hydro/library/fp_libs_python3/'
virtualenv_name='virtualenv_python3'
script_folder='/hydro/library/hyde/'

# Execution example:
# python app_obs_rs_main.py -settings_file configuration.json -time "YYYY-MM-DD HH:MM"
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get file information
script_file='/hydro/library/hyde/apps/ground_network/ws/HYDE_DynamicData_GroundNetwork_WS.py'
settings_file='/hydro/library/hyde/apps/ground_network/ws/hyde_dynamicdata_groundnetwork_ws_local.json'

# Get information (-u to get gmt time)
time_now=$(date -u +"%Y-%m-%d %H:00")
# time_now='2018-07-23 00:00' # DEBUG 
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
echo " ==> COMMAND LINE: " python3 $script_file -settings_file $settings_file -time $time_now

# Run python script (using setting and time)
python3 $script_file -settings_file $settings_file -time "$time_now"

# Info script end
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------

