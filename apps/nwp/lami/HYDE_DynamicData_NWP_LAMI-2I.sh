#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='HYDE DYNAMICDATA - NWP LAMI 2I'
script_version="1.1.0"
script_date='2020/10/30'

virtualenv_folder='/hydro/library/fp_libs_python3/'
virtualenv_name='virtualenv_python3'
script_folder='/hydro/library/hyde/'

# Execution example:
# python3 HYDE_DynamicData_NWP_LAMI-2I.py -settings_file hyde_configuration_nwp_lami-2i.json -time "2020-11-02 12:00"
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get file information
script_file='/hydro/library/hyde/apps/nwp/lami/HYDE_DynamicData_NWP_LAMI-2I.py'
settings_file='/hydro/fp_tools_preprocessing/nwp/lami-2i/hyde_dynamicdata_nwp_lami-2i_example.json'

# Get information (-u to get gmt time)
time_now=$(date -u +"%Y-%m-%d %H:00")
time_now='2020-11-20 09:35'
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

