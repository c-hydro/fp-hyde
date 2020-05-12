#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='HYDE DOWNLOADER - SATELLITE SMAP'
script_version="1.0.0"
script_date='2020/05/11'

script_folder='/home/sequia/drought/code/data_download_smap/'

virtual_env_folder='/home/sequia/hyde_env/fp_libs_python3/bin/'
virtual_env_name='virtualenv_python3'
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get file information
script_file='hyde_downloader_satellite_smap.py'
setting_file='hyde_downloader_satellite_smap_realtime.json'

# Get information (-u to get gmt time)
#time_now=$(date -u +"%Y%m%d%H00")
time_now='2020-05-10 05:21' # DEBUG 
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

# Run python script (using setting and time)
python3 $script_file -settings_file $setting_file -time $time_now

# Info script end
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------

