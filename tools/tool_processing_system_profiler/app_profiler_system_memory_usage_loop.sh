#!/bin/bash

#-----------------------------------------------------------------------------------------
# Script settings
script_name='HYDE UTILS - PROFILER MEMORY USAGE LOOP - REALTIME'
script_version='1.1.0'
script_date='2021/02/19'

script_file='hyde_tools_profiler_memory_usage_loop.sh'
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get process information
process_name_default='HMC_Model_RUN_Manager.py'
process_node_default=1
process_monitoring_time_default=120 # in seconds
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get time information (-u to get gmt time)
time_now=$(date -u +"%Y-%m-%d %H:%M")
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Set script Help messages
script_help_text="\
Usage of script:
./hyde_tools_profiler_memory_usage_loop.sh <options>
  	-h	display this help message;
	-process-name	name of the process [default: ${process_name_default} ];
	-process-monitoring-time monitoring time of the process [default: ${process_monitoring_time_default} ];
	-process-node	node of the process [default: ${process_node_default}]"
#-----------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> COMMAND LINE: " bash $script_file -time $time_now
echo " ===> EXECUTION ..."
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Define script option(s)
echo " ===> SET SCRIPT PARAMETERS ... "
while [ -n "$1" ]; do
	case "$1" in
    	-h) 	# script calls help comment
      		echo "$script_help_text"			
      		exit 0
      		;;
		-process-name)  
			process_name_user=$2
			#shift # past argument
    		shift # past value		
			flag_process_name=true
			;;
		-process-monitoring-time)  
			process_monitoring_time_user=$2
			#shift # past argument
    		shift # past value		
			flag_process_monitoring_time=true
			;;
		-process-node)  
			process_node_user=$2
			#shift # past argument
    		shift # past value		
			flag_process_node=true
			;;
		*)  
			echo " ===> ERROR: script option $1 not recognized" 
			exit 1
			;;
	esac
	shift
done

# Define script variable(s)
echo " ===> Define process name ... "
if [ $flag_process_name ] ; then
	process_name=$process_name_user
	echo " ===> Define process name [$process_name] ... DONE (command-line definition)"
else
	process_name=$process_name_default
	echo " ===> Define process name [$process_name] ... DONE (default definition)"
fi

echo " ===> Define process monitoring time ... "
if [ $flag_process_monitoring_time ] ; then
	process_monitoring_time=$process_monitoring_time_user
	echo " ===> Define process monitoring time [$process_monitoring_time] ... DONE (command-line definition)"
else
	process_monitoring_time=$process_monitoring_time_default
	echo " ===> Define process monitoring time [$process_monitoring_time] ... DONE (default definition)"
fi

echo " ===> Define process node ... "
if [ $flag_process_node ] ; then
	process_node=$process_node_user
	echo " ===> Define process node [$process_node] ... DONE (command-line definition)"
else
	process_node=$process_node_default
	echo " ===> Define process node [$process_node] ... DONE (default definition)"
fi

echo " ===> SET SCRIPT PARAMETERS ... DONE"
# ----------------------------------------------------------------------------------------

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


#-----------------------------------------------------------------------------------------
# Get file information
folder_name_raw='/hydro/log/system/'
file_name_raw='hyde_tools_profiler_memory_usage_node_'${process_node}'_%YYYY%MM%DD.txt'

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

while sleep ${process_monitoring_time}; do
	
	# Get time information
	time_step=$(date -u +"%Y-%m-%d %H:%M")
	
	# Write information to report file
	echo '=============================================================' >> $file_path_def
	echo ' REPORT AT TIME '$time_step' ' >> $file_path_def

	# Part1 -- Profile selected process 
	echo ' ' >> $file_path_def
	echo ' -- PROFILE '${process_name}' PROCESS MEMORY USAGE AT TIME: '$time_step' ' >> $file_path_def
	echo 'USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND' >> $file_path_def
	ps aux | grep $process_name >> $file_path_def
	echo ' ' >> $file_path_def

	# Part2 -- Profile all processes 
	echo ' ' >> $file_path_def
	echo ' -- PROFILE GLOBAL PROCESSES MEMORY USAGE AT TIME: '$time_step' ' >> $file_path_def
	ps -eo size,pid,user,command --sort -size | grep $process_name | awk '{ hr=$1/1024 ; printf("%13.2f Mb ",hr) } { for ( x=4 ; x<=NF ; x++ ) { printf("%s ",$x) } print "" }' >> $file_path_def 
	echo ' ' >> $file_path_def

	# Part3 -- Profile global memory usage 
	echo ' ' >> $file_path_def
	echo ' -- PROFILE GLOBAL MEMORY USAGE AT TIME: '$time_step' ' >> $file_path_def
	cat free -h >> $file_path_def
	echo '=============================================================' >> $file_path_def
	echo ' ' >> $file_path_def

done

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

