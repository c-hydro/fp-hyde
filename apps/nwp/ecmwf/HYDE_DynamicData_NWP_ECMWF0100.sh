#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='HYDE DYNAMICDATA - NWP ECMWF 0100'
script_version="1.1.0"
script_date='2020/10/30'

virtualenv_folder='/hydro/library/fp_libs_python3/'
virtualenv_name='virtualenv_python3'
script_folder='/hydro/library/hyde/'

# Execution example:
# python3 HYDE_DynamicData_GroundNetwork_WS.py -settings_file hyde_dynamicdata_groundnetwork_ws.json -time "2020-11-02 12:00"
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get file information
script_file='HYDE_DynamicData_NWP_ECMWF0100.py'
settings_file='hyde_configuration_nwp_ecmwf0100_example.json'

# Get information (-u to get gmt time)
time_now=$(date -u +"%Y-%m-%d %H:00")
time_now='2020-11-15 09:35'
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

