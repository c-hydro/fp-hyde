#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='HYDE RUNNER - HSAF ASCAT MOD [ECMWF-RZSM] - DR'
script_version="1.0.0"
script_date='2019/08/07'

script_folder='/home/hsaf/hyde-master/'

virtual_env_folder='/home/hsaf/library/hsaf_libs_python3/bin/'
virtual_env_name='hsaf_env_python3'
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get file information
script_file='/home/hsaf/hyde-master/apps/hsaf/soil_moisture/HYDE_DynamicData_HSAF_ASCAT_MOD_DR.py'
setting_file='/home/hsaf/hyde-master/apps/hsaf/soil_moisture/hyde_configuration_hsaf_ascat_mod_dr_realtime.json'
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Add path to pythonpath
export PYTHONPATH="${PYTHONPATH}:$script_folder"
# Add virtual env
export PATH=$virtual_env_folder:$PATH
source activate $virtual_env_name
#-----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> START ..."
echo " ==> COMMAND LINE: " python $script_file -settingfile $setting_file

# Run python script (using setting and time)
python3 $script_file -settingsfile $setting_file

# Info script end
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------

