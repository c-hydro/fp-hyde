#!/bin/bash

#-----------------------------------------------------------------------------------------
# Script settings
script_name='HYDE UTILS - PROFILER MEMORY USAGE - REALTIME'
script_version='1.1.0'
script_date='2021/02/19'

script_file='hyde_tools_profiler_memory_usage.sh'
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get process information
process_name='HMC_Model_V3'

# Get file information
folder_name_raw='/hydro/log/system/'
file_name_raw='hyde_tools_profiler_memory_usage_%YYYY%MM%DD.txt'
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get time information (-u to get gmt time)
time_now=$(date -u +"%Y-%m-%d %H:%M")
# time_now='2020-11-20 09:35'
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Define date parts
year=${time_now:0:4} ; month=${time_now:5:2} ; day=${time_now:8:2} ; hour=${time_now:11:2}

# Define folder_name and file_name
folder_name_def=${folder_name_raw/"%YYYY"/$year}
folder_name_def=${folder_name_def/"%MM"/$month}
folder_name_def=${folder_name_def/"%DD"/$day}
folder_name_def=${folder_name_def/"%H"/$hour}

file_name_def=${file_name_raw/"%YYYY"/$year}
file_name_def=${file_name_def/"%MM"/$month}
file_name_def=${file_name_def/"%DD"/$day}
file_name_def=${file_name_def/"%H"/$hour}

# Define file_path
file_path_def=${folder_name_def}/${file_name_def}
#-----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> COMMAND LINE: " bash $script_file -time $time_now
echo " ===> EXECUTION ..."
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
echo " ====> CREATE MEMORY REPORT FOLDER: $folder_name_def ... "
if [ ! -d $folder_name_def ]; then
	if mkdir -p $folder_name_def; then
    		echo " ====> CREATE MEMORY REPORT FOLDER: $folder_name_def ... DONE"
	else
    		echo " ====> CREATE MEMORY REPORT FOLDER: $folder_name_def ... FAILED. ERROR IN CREATING FOLDER"
	fi
else
	echo " ====> CREATE MEMORY REPORT FOLDER: $folder_name_def ... SKIPPED. FOLDER ALREADY EXISTS"
fi
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Info start
echo " ====> WRITE MEMORY REPORT FILE ... "

# Write information to report file
echo '=============================================================' >> $file_path_def
echo ' REPORT AT TIME '$time_now' ' >> $file_path_def

# Part1 -- Profile selected process 
echo ' ' >> $file_path_def
echo ' -- PROFILE '${process_name}' PROCESS MEMORY USAGE AT TIME: '$time_now' ' >> $file_path_def
echo 'USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND' >> $file_path_def
ps aux | grep $process_name >> $file_path_def
echo ' ' >> $file_path_def

# Part2 -- Profile all processes 
echo ' ' >> $file_path_def
echo ' -- PROFILE GLOBAL PROCESSES MEMORY USAGE AT TIME: '$time_now' ' >> $file_path_def
ps -eo size,pid,user,command --sort -size | grep $process_name | awk '{ hr=$1/1024 ; printf("%13.2f Mb ",hr) } { for ( x=4 ; x<=NF ; x++ ) { printf("%s ",$x) } print "" }' >> $file_path_def 
echo ' ' >> $file_path_def

# Part3 -- Profile global memory usage 
echo ' ' >> $file_path_def
echo ' -- PROFILE GLOBAL MEMORY USAGE AT TIME: '$time_now' ' >> $file_path_def
cat /proc/meminfo >> $file_path_def
echo '=============================================================' >> $file_path_def
echo ' ' >> $file_path_def

# Info end
echo " ====> WRITE MEMORY REPORT FILE ... DONE"
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Info script end
echo " ===> EXECUTION ... DONE"
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------	

