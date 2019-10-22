#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='FP RUNNER - DATA SPLITTIN WRF Barbados'
script_version="1.0.0"
script_date='2018/07/26'

script_folder='/share/c-hydro/'
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get file information
script_file='/share/c-hydro/fp-master/apps/tools/FP_Tools_DataSplitting.py'
setting_file='/share/c-hydro/fp-master/apps/tools/fp_configuration_datasplitting_barbados_realtime.json'

# Get information (-u to get gmt time)
time_now=$(date -u +"%Y%m%d%H00")
#time_now='201810051032' # DEBUG 
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Add path to pythonpath
export PYTHONPATH="${PYTHONPATH}:$script_folder"
#-----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> START ..."
echo " ==> COMMAND LINE: " python3 $script_file -settingfile $setting_file -time $time_now

# Run python script (using setting and time)
python3 $script_file -settingfile $setting_file -time $time_now

# Info script end
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------

