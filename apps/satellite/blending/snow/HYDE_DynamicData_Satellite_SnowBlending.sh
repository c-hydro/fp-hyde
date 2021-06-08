#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='SNOW BLENDING - REALTIME'
script_version="1.0.0"
script_date='2021/05/31'

virtualenv_folder='/home/fp_virtualenv_python3'
virtualenv_name='fp_virtualenv_python3_hyde_libraries'
script_folder='/home/fp-hyde/apps/satellite/blending/snow/'

# Execution example:
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get file information
script_file='/home/fp-hyde/apps/satellite/blending/snow/HYDE_DynamicData_Satellite_SnowBlending.py'
settings_file='/home/blending/hyde_configuration_satellite_snowblending.json'

# Get information (-u to get gmt time)
#time_now=$(date -u +"%Y-%m-%d %H:00")
time_now='2021-04-20 17:33'
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
echo " ==> COMMAND LINE: " python3 $script_file

# Run python script 
python3 $script_file -settings_file $settings_file -time "$time_now"

# Info script end
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------

