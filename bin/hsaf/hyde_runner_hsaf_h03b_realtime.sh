#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='HYDE RUNNER - HSAF H03B'
script_version="1.0.1"
script_date='2019/10/07'

script_folder='/home/hsaf/hyde-master/'

virtual_env_folder='/home/hsaf/library/hsaf_libs_python3/bin/'
virtual_env_name='hsaf_env_python3'
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get file information
script_file='/home/hsaf/hyde-master/apps/hsaf/precipitation/HYDE_DynamicData_HSAF_H03B.py'
setting_file='/home/hsaf/hyde-master/apps/hsaf/precipitation/hyde_configuration_hsaf_h03b_realtime.json'

# Get information (-u to get gmt time)
time_now=$(date -u +"%Y%m%d%H00")
# time_now='201807230000' # DEBUG 
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
echo " ==> COMMAND LINE: " python3 $script_file -settings_file $setting_file -time $time_now

# Run python script (using setting and time)
python3 $script_file -settings_file $setting_file -time $time_now

# Info script end
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------

