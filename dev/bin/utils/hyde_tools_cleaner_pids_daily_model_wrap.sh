#!/bin/bash

#-----------------------------------------------------------------------------------------
# Script information
script_name='HYDE UTILS - CLEANER PROCESS IDS DAILY - REALTIME'
script_version="1.5.0"
script_date='2020/12/22'
#-----------------------------------------------------------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get script information
script_file='hyde_tools_cleaner_pids_daily.sh'

# Get process information
process_name_template="HMC_Model_RUN_Manager.py"
process_type_template=''
process_etime_max=43200

# Get time information (-u to get gmt time)
time_now=$(date -u +"%Y-%m-%d %H:00")
#-----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> COMMAND LINE: " bash $script_file -time $time_now
echo " ===> EXECUTION ..."

# Execution pid
execution_id=$$

# Get process pids and elapsed time information
process_ids=$(ps -eo pid,command | grep -e "$process_name_template.*$process_type_template" | grep -v grep | awk '{print $1}')
process_cmds=$(ps -eo pid,cmd,etime | grep -e "$process_name_template.*$process_type_template" | grep -v grep | awk '{print $2}')
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Iterate over pid(s)
echo " ====> SELECT PROCESS $process_name_template ... "
for process_ids_step in ${process_ids}; do
        
        # Get process information
        process_etime_step=$(ps -p $process_ids_step -oetime= | tr '-' ':' | awk -F: '{ total=0; m=1; } { for (i=0; i < NF; i++) {total += $(NF-i)*m; m *= i >= 2 ? 24 : 60 }} {print total}')
        process_name_step=$(ls -l /proc/$process_ids_step | grep exe)
        
        # Info start
        echo ' =====> PROCESS -- NAME '$process_name_step' -- PID ' $process_ids_step ' -- ETime: ' $process_etime_step ' [seconds] ... '
        echo ' ======> KILL PID '$process_ids_step' ... '
        
        # Check elapse time(s)
        if (( $process_etime_step > $process_etime_max )); then
            kill -HUP "$process_ids_step"
            echo ' ======> KILL PID '$process_ids_step' ... DONE -- [ETIME_PID '$process_etime_step' > ETIME_MAX '$process_etime_max' [seconds]'
            echo " ======> KILL PID: "$pid" ... OK  "
        else
            echo ' ======> KILL PID '$process_ids_step' ... SKIPPED -- [ETIME_PID '$process_etime_step' <= ETIME_MAX '$process_etime_max' [seconds]'
        fi
        
        # Info end
        echo ' =====> PROCESS -- NAME '$process_name_step' -- PID ' $process_ids_step ' -- ETime: ' $process_etime_step ' [seconds] ... DONE'
        
done
echo " ====> SELECT PROCESS $process_name_template ... DONE"

echo " ===> EXECUTION ... DONE"
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------	
