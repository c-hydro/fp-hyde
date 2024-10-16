#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='HYDE TOOLS - TRANSFER DATASETS - HISTORY'
script_version="1.0.0"
script_date='2021/11/18'

# Virtualenv default definition(s)
virtualenv_folder='/home/fabio/Desktop/Library/fp_virtualenv_python3/'
virtualenv_name='fp_virtualenv_python3_hmc_libraries'

# Default script folder(s)
script_folder='/home/fabio/Desktop/HyDE_Workspace/hyde-dev/tools/tool_processing_datasets_transfer/'
configuration_folder='/home/fabio/Desktop/HyDE_Workspace/hyde-dev/tools/tool_processing_datasets_transfer/'
package_folder='/home/fabio/Desktop/HyDE_Workspace/hyde-dev/'

# Execution example:
# python3 hyde_tools_transfer_datasets.py -settings_algorithm configuration.json -time "2020-11-02 12:00"
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get file information
script_file=${script_folder}'hyde_tools_transfer_datasets.py'
settings_file=${configuration_folder}'hyde_tools_transfer_datasets_rsync_remote2local_opchain_marche.json'

# Get information (-u to get gmt time)
time_now=$(date -u +"%Y-%m-%d %H:00")
time_now='2023-05-18 18:00'
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Activate virtualenv
export PATH=$virtualenv_folder/bin:$PATH
source activate $virtualenv_name

# Add path to pythonpath
export PYTHONPATH="${PYTHONPATH}:$script_folder"
export PYTHONPATH="${PYTHONPATH}:$package_folder"
#-----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> START ..."
echo " ==> COMMAND LINE: " python $script_file -settings_file $settings_file -time $time_now

# Run python script (using setting and time)
python $script_file -settings_file $settings_file -time "$time_now"

# Info script end
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------

