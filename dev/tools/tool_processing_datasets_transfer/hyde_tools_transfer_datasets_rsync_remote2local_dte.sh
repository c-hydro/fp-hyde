#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='HYDE TOOLS - TRANSFER DATASETS - HISTORY'
script_version="1.0.0"
script_date='2021/11/18'

# Virtualenv default definition(s)
virtualenv_folder='/home/dte/library/fp_system_env_conda/'
virtualenv_name='fp_system_conda_python3_hmc_libraries'

# Default script folder(s)
script_folder='/home/dte/library/fp_package_hyde/tools/tool_processing_datasets_transfer/'
configuration_folder='/home/dte/utils/'
package_folder='/home/dte/library/fp_package_hyde/'

# Execution example:
# python3 hyde_tools_transfer_datasets.py -settings_algorithm configuration.json -time "2020-11-02 12:00"
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get file information
script_file=${script_folder}'hyde_tools_transfer_datasets.py'
settings_file=${configuration_folder}'hyde_tools_transfer_datasets_rsync_remote2local_hmc.json'

# Get information (-u to get gmt time)
time_now=$(date -u +"%Y-%m-%d %H:00")
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

