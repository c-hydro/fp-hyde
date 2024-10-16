#!/bin/sh

#-----------------------------------------------------------------------------------------
# Script information
script_name='HYDE UTILS - MANAGER DATASETS - HMC - STATE - REALTIME'
script_version="1.0.0"
script_date='2020/12/20'
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get script information
script_file='hyde_tools_manager_datasets_hmc_state.sh'

folder_datasets_gridded_source='/hydro/archive/model_dset_state/gridded/'
folder_datasets_gridded_destination='/hydro/archive/model_dset_restart/gridded/'

folder_datasets_point_source='/hydro/archive/model_dset_state/point/'
folder_datasets_point_destination='/hydro/archive/model_dset_restart/point/'


# Get time information (-u to get gmt time)
time_now=$(date -u +"%Y-%m-%d %H:00")
# time_now='2020-11-20 09:35'
#-----------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> COMMAND LINE: " bash $script_file -time $time_now
echo " ===> EXECUTION ..."

# Execution pid
execution_pid=$$

echo " ====> SYNC FOLDER GRIDDED ... "
if rsync -rtv $folder_datasets_gridded_source $folder_datasets_gridded_destination; then
    echo " ====> SYNC FOLDER GRIDDED ... DONE"
else
    echo " ====> SYNC FOLDER GRIDDED ... FAILED. ERROR IN SYNC COMMAND"
fi
         
echo " ====> SYNC FOLDER POINT ... "
if rsync -rtv $folder_datasets_point_source $folder_datasets_point_destination; then
    echo " ====> SYNC FOLDER POINT ... DONE"
else
    echo " ====> SYNC FOLDER POINT ... FAILED. ERROR IN SYNC COMMAND"
fi

echo " ===> EXECUTION ... DONE"
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------	


